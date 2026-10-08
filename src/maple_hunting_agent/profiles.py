"""Compile editable TOML character profiles into validated keyboard actions."""

from pathlib import Path
import hashlib
import json
import re
import tomllib

from .actions import ActionCatalog, parse_actions

DIRECTIONS = ("left", "right", "up", "down")


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string.")
    return value.strip()


def _positive(value: object, name: str) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{name} must be a positive integer.")
    return value


def _enabled(value: dict, name: str) -> bool:
    result = value.get("enabled", True)
    if type(result) is not bool:
        raise ValueError(f"{name}.enabled must be a boolean.")
    return result


def _keys(value: object, name: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{name} must be a nonempty key list.")
    result = [_text(key, name).lower() for key in value]
    if len(set(result)) != len(result):
        raise ValueError(f"{name} must not contain duplicate keys.")
    return result


def _step(operation: str, keys: list[str], duration: int = 0) -> dict:
    return {"operation": operation, "keys": keys, "duration_ms": duration}


def _action(action_id: str, description: str, category: str, steps: list[dict], duration: int, **extra) -> dict:
    return {
        "id": action_id, "description": description, "category": category,
        "execution": {"kind": "none" if category == "wait" else "stop" if category == "stop" else "keyboard", "duration_ms": duration},
        "keyboard_steps": steps,
        "preconditions": [] if category in ("wait", "stop", "release") else ["Verify game focus, fresh evidence, and current prerequisites before dispatch."],
        "success_criteria": ["Validate the action's visible effect using a fresh observation; dispatch is not proof of success."],
        **extra,
    }


def load_character_profile(path: Path, *, max_key_hold_ms: int) -> ActionCatalog:
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    return compile_character_profile(data, max_key_hold_ms=max_key_hold_ms)


def compile_character_profile(data: dict, *, max_key_hold_ms: int) -> ActionCatalog:
    if not isinstance(data, dict):
        raise ValueError("Character profile must be a table.")
    if data.get("schema_version") != 1:
        raise ValueError("Character profile must have schema_version 1.")
    if "attacks" in data or "buffs" in data:
        raise ValueError("Use one [[actions]] list; separate attacks/buffs tables are no longer supported.")
    profile_id = _text(data["id"], "profile.id")
    version = _text(data["context_version"], "profile.context_version")
    fingerprint = hashlib.sha256(json.dumps(data, sort_keys=True, allow_nan=False).encode()).hexdigest()[:12]
    version = f"{version}:{fingerprint}"
    character = data.get("character", {})
    if not isinstance(character, dict) or any(key not in ("edition_region", "character_class") for key in character):
        raise ValueError("character may define edition_region and character_class.")
    character = {key: _text(value, f"character.{key}") for key, value in character.items()}
    movement = data.get("movement", {})
    if not isinstance(movement, dict):
        raise ValueError("movement must be a table.")
    bindings = movement.get("bindings", {direction: direction for direction in DIRECTIONS})
    if not isinstance(bindings, dict) or set(bindings) != set(DIRECTIONS):
        raise ValueError("movement.bindings must define left, right, up, and down.")
    bindings = {direction: _text(bindings[direction], f"movement.{direction}").lower() for direction in DIRECTIONS}
    if len(set(bindings.values())) != 4:
        raise ValueError("Movement directions need distinct keys.")
    lease = _positive(movement.get("lease_ms", 500), "movement.lease_ms")
    rows = []
    all_movement_keys = list(bindings.values())
    for direction, key in bindings.items():
        rows.append(_action(
            f"move_{direction}_down", f"Move {direction} using {key}; renew the bounded key-down lease while approved.", "movement",
            [_step("release", [other for other in all_movement_keys if other != key]), _step("key_down", [key], lease)], lease,
            direction=direction, repeatable=True, required_facts={"control.gameplay_ready": True}, excluded_held_keys=[key],
        ))
        rows.append(_action(
            f"move_{direction}_up", f"Release executor-owned {key} to stop {direction} movement.", "release",
            [_step("release", [key])], 0, direction=direction, required_held_keys=[key],
        ))
    teleport = data.get("teleport", {"enabled": False})
    if not isinstance(teleport, dict):
        raise ValueError("teleport must be a table.")
    if _enabled(teleport, "teleport"):
        keys = _keys(teleport["keys"], "teleport.keys")
        if set(keys) & set(all_movement_keys):
            raise ValueError("teleport.keys must not duplicate direction keys.")
        duration = _positive(teleport.get("press_ms", 80), "teleport.press_ms")
        direction_lease = _positive(teleport.get("direction_lease_ms", 200), "teleport.direction_lease_ms")
        settle = teleport.get("settle_ms", 40)
        if type(settle) is not int or settle < 0:
            raise ValueError("teleport.settle_ms must be a nonnegative integer.")
        directions = teleport.get("directions", list(DIRECTIONS))
        if not isinstance(directions, list) or not directions or len(set(directions)) != len(directions) or any(d not in DIRECTIONS for d in directions):
            raise ValueError("teleport.directions must list unique supported directions.")
        ready_fact = _text(teleport.get("available_fact", "action.teleport.ready"), "teleport.available_fact")
        for direction in directions:
            key = bindings[direction]
            rows.append(_action(
                f"teleport_{direction}", f"Teleport {direction}: hold {key}, activate {'+'.join(keys)}, release.", "teleport",
                [_step("release", all_movement_keys), _step("key_down", [key], direction_lease),
                 _step("press" if len(keys) == 1 else "chord", keys, duration), _step("wait", [], settle), _step("release", [key, *keys])],
                max(direction_lease, duration + settle), direction=direction, required_facts={"control.gameplay_ready": True, ready_fact: True},
                unavailable_facts=["action.teleport.pending"],
            ))
    seen_skills = set()
    group, category = "actions", "skill"
    skills = data.get(group, [])
    if not isinstance(skills, list):
        raise ValueError(f"{group} must be an array of tables (or an empty array).")
    for skill in skills:
        if not isinstance(skill, dict):
            raise ValueError(f"Every {category} must be a table.")
        action_id = _text(skill["id"], f"{category}.id")
        if not re.fullmatch(r"[a-z][a-z0-9_]*", action_id) or action_id in seen_skills:
            raise ValueError("Skill IDs must be unique lowercase identifiers.")
        seen_skills.add(action_id)
        if not _enabled(skill, action_id):
            continue
        keys = _keys(skill["keys"], f"{action_id}.keys")
        priority = skill["priority"]
        if type(priority) is not int or priority < 0:
            raise ValueError(f"{action_id}.priority must be a nonnegative integer; lower runs first.")
        duration = _positive(skill.get("press_ms", 80), f"{action_id}.press_ms")
        readiness = skill.get("availability", "observed")
        if readiness not in ("observed", "always"):
            raise ValueError(f"{action_id}.availability must be observed or always.")
        facts = {"control.gameplay_ready": True}
        if readiness == "observed":
            facts[_text(skill.get("ready_fact", f"action.{action_id}.ready"), f"{action_id}.ready_fact")] = True
        unavailable = [f"action.{action_id}.pending"]
        grey = skill.get("detect_greyed_out", False)
        if type(grey) is not bool:
            raise ValueError(f"{action_id}.detect_greyed_out must be boolean.")
        if grey:
            unavailable.append(_text(skill.get("greyed_out_fact", f"action.{action_id}.greyed_out"), f"{action_id}.greyed_out_fact"))
        strategy = skill.get("strategy", "available")
        usage = _text(skill["usage"], f"{action_id}.usage")
        refresh = {"effect_active_fact": skill.get("effect_present_fact"), "effect_hint": skill.get("effect_hint")}
        if strategy == "interval_or_missing":
            refresh.update({
                "refresh_interval_ms": _positive(skill["refresh_interval_ms"], f"{action_id}.refresh_interval_ms"),
                "effect_active_fact": skill.get("effect_present_fact", f"action.{action_id}.effect_present"),
                "elapsed_since_use_fact": f"action.{action_id}.elapsed_since_confirmed_ms",
            })
        elif strategy == "periodic":
            run_on_start = skill.get("run_on_start", True)
            if type(run_on_start) is not bool:
                raise ValueError(f"{action_id}.run_on_start must be boolean.")
            refresh.update({
                "refresh_interval_ms": _positive(skill["interval_ms"], f"{action_id}.interval_ms"),
                "elapsed_since_use_fact": f"action.{action_id}.elapsed_since_confirmed_ms",
                "has_confirmed_use_fact": f"action.{action_id}.has_confirmed_use",
                "run_on_start": run_on_start,
            })
        elif strategy != "available":
            raise ValueError(f"{action_id}: unsupported {category} strategy {strategy!r}.")
        rows.append(_action(
            action_id, f"{category.title()} {action_id}: binding {'+'.join(keys)}, priority {priority}. " + _text(skill.get("description", "Use when the configured readiness and strategy conditions are met."), f"{action_id}.description"), category,
            [_step("press" if len(keys) == 1 else "chord", keys, duration)], duration,
            priority=priority, timing_strategy=strategy, usage_strategy=usage, required_facts=facts, unavailable_facts=unavailable, **refresh,
        ))
    rows.extend([
        _action("wait", "Wait for new evidence or skill readiness without sending input.", "wait", [], 250),
        _action("stop", "Stop and release all executor-owned inputs.", "stop", [], 0),
    ])
    return parse_actions({
        "schema_version": 1, "status": "configured_profile_unverified_timing", "profile_id": profile_id,
        "context_version": version, "actions": rows,
        "character_context": character,
    }, max_key_hold_ms=max_key_hold_ms)
