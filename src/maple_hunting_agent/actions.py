"""Read and filter keyboard action definitions without dispatching input."""

from dataclasses import dataclass
import json
import math
from pathlib import Path

from .domain import ActionOption, KeyboardOperation, KeyboardStep, Observation, ObjectivePlan


def _strings(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value):
        raise ValueError(f"{field} must be a list of nonempty strings.")
    if len(set(value)) != len(value):
        raise ValueError(f"{field} must not contain duplicate values.")
    return tuple(value)


def _duration(value: object, field: str, *, positive: bool = False) -> int:
    if type(value) is not int or value < (1 if positive else 0):
        raise ValueError(f"{field} must be a {'positive' if positive else 'nonnegative'} integer.")
    return value


@dataclass(frozen=True)
class ActionCatalog:
    status: str
    actions: tuple[ActionOption, ...]
    profile_id: str = "legacy"
    context_version: str = "legacy"
    character_context: tuple[tuple[str, str], ...] = ()

    def available(self, observation: Observation, objective: ObjectivePlan) -> tuple[ActionOption, ...]:
        """Unknown readiness withholds activation; owned-key release stays available."""
        held = set(observation.held_keys)
        candidates = []
        for action in self.actions:
            if any(observation.facts.get(key) is not expected for key, expected in action.required_facts):
                continue
            # Known greyed-out evidence overrides a contradictory ready flag.
            if any(
                expected is True and key.startswith("skill.") and key.endswith(".available")
                and observation.facts.get(key.removesuffix("available") + "greyed_out") is True
                for key, expected in action.required_facts
            ):
                continue
            if any(observation.facts.get(key) is True for key in action.unavailable_facts):
                continue
            if action.refresh_interval_ms is not None:
                active = observation.facts.get(action.effect_active_fact)
                elapsed = observation.facts.get(action.elapsed_since_use_fact)
                expired = (
                    type(elapsed) in (int, float) and math.isfinite(elapsed)
                    and elapsed >= action.refresh_interval_ms
                )
                if action.timing_strategy == "periodic":
                    unused = observation.facts.get(action.has_confirmed_use_fact) is False
                    initial = action.run_on_start and unused
                    session_elapsed = observation.facts.get("session.elapsed_ms")
                    first_interval = unused and not action.run_on_start and type(session_elapsed) in (int, float) and math.isfinite(session_elapsed) and session_elapsed >= action.refresh_interval_ms
                    if not expired and not initial and not first_interval:
                        continue
                elif active is not False and not expired:
                    continue
            if not set(action.required_held_keys).issubset(held):
                continue
            if set(action.excluded_held_keys) & held:
                continue
            if observation.facts.get(f"action.{action.action_id}.blocked") is True:
                continue
            candidates.append(action)
        return tuple(candidates)


def load_actions(path: Path, *, max_key_hold_ms: int) -> ActionCatalog:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    return parse_actions(data, max_key_hold_ms=max_key_hold_ms)


def parse_actions(data: object, *, max_key_hold_ms: int) -> ActionCatalog:
    """Shared validation for low-level JSON and generated character profiles."""
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("Actions file must have schema_version 1.")
    rows = data.get("actions")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Actions file must contain a nonempty actions list.")
    result = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Every action must be an object.")
        action_id, description = row["id"], row["description"]
        if not isinstance(action_id, str) or not action_id.strip():
            raise ValueError("Every action ID must be a nonempty string.")
        if not isinstance(description, str) or not description.strip():
            raise ValueError(f"{action_id}: description must be a nonempty string.")
        execution = row["execution"]
        kind = execution["kind"]
        if kind not in ("none", "stop", "keyboard"):
            raise ValueError(f"{action_id}: unsupported execution kind {kind!r}.")
        bound = _duration(execution["duration_ms"], f"{action_id}.execution.duration_ms")
        repeatable = row.get("repeatable", False)
        if type(repeatable) is not bool or (kind == "stop" and repeatable):
            raise ValueError(f"{action_id}: invalid repeatable setting.")
        raw_steps = row.get("keyboard_steps", [])
        if not isinstance(raw_steps, list):
            raise ValueError(f"{action_id}: keyboard_steps must be a list.")
        steps = []
        blocking_duration = 0
        for raw in raw_steps:
            operation = KeyboardOperation(raw["operation"])
            keys = _strings(raw.get("keys", []), f"{action_id}.keys")
            duration = _duration(raw.get("duration_ms", 0), f"{action_id}.duration_ms")
            if operation == KeyboardOperation.WAIT:
                if keys:
                    raise ValueError(f"{action_id}: wait steps must not have keys.")
            elif not keys:
                raise ValueError(f"{action_id}: keyboard steps require keys.")
            if operation in (KeyboardOperation.KEY_DOWN, KeyboardOperation.PRESS, KeyboardOperation.HOLD, KeyboardOperation.CHORD):
                if not 0 < duration <= max_key_hold_ms:
                    raise ValueError(f"{action_id}: key duration must be within max_key_hold_ms.")
            if operation == KeyboardOperation.RELEASE and duration != 0:
                raise ValueError(f"{action_id}: release duration must be zero.")
            if operation == KeyboardOperation.KEY_DOWN:
                if duration > bound:
                    raise ValueError(f"{action_id}: key lease exceeds action duration bound.")
            else:
                blocking_duration += duration
            steps.append(KeyboardStep(operation, keys, duration))
        if blocking_duration > bound:
            raise ValueError(f"{action_id}: step durations exceed action duration bound.")
        if kind != "keyboard" and steps:
            raise ValueError(f"{action_id}: non-keyboard actions cannot contain keyboard steps.")
        if kind == "keyboard" and not steps:
            raise ValueError(f"{action_id}: keyboard actions need steps.")
        facts = row.get("required_facts", {})
        if not isinstance(facts, dict) or any(not isinstance(k, str) or not k or type(v) is not bool for k, v in facts.items()):
            raise ValueError(f"{action_id}: required_facts must map names to booleans.")
        category = row.get("category", kind if kind == "stop" else "wait" if kind == "none" else "custom")
        if category not in ("movement", "release", "teleport", "skill", "wait", "stop", "custom"):
            raise ValueError(f"{action_id}: unsupported category {category!r}.")
        priority = _duration(row.get("priority", 100), f"{action_id}.priority")
        direction = row.get("direction")
        if direction is not None and direction not in ("left", "right", "up", "down"):
            raise ValueError(f"{action_id}: unsupported movement direction.")
        interval = row.get("refresh_interval_ms")
        timing = row.get("timing_strategy", "interval_or_missing" if interval is not None else "available")
        if timing not in ("available", "interval_or_missing", "periodic"):
            raise ValueError(f"{action_id}: unsupported timing strategy.")
        if timing != "available" and interval is None:
            raise ValueError(f"{action_id}: timed strategies need an interval.")
        active_fact = row.get("effect_active_fact")
        elapsed_fact = row.get("elapsed_since_use_fact")
        run_on_start = row.get("run_on_start", False)
        has_confirmed = row.get("has_confirmed_use_fact")
        if type(run_on_start) is not bool:
            raise ValueError(f"{action_id}: run_on_start must be boolean.")
        if interval is not None:
            interval = _duration(interval, f"{action_id}.refresh_interval_ms", positive=True)
            required = (elapsed_fact, has_confirmed) if timing == "periodic" else (active_fact, elapsed_fact)
            if category != "skill" or any(not isinstance(key, str) or not key for key in required):
                raise ValueError(f"{action_id}: timed strategies need valid action timing facts.")
        usage = row.get("usage_strategy", "")
        hint = row.get("effect_hint")
        if not isinstance(usage, str) or (hint is not None and (not isinstance(hint, str) or not hint.strip())):
            raise ValueError(f"{action_id}: usage/effect hints must be text.")
        if active_fact is not None and (not isinstance(active_fact, str) or not active_fact):
            raise ValueError(f"{action_id}: effect_active_fact must be a nonempty string.")
        result.append(ActionOption(
            action_id=action_id,
            description=description,
            preconditions=_strings(row["preconditions"], f"{action_id}.preconditions"),
            success_criteria=_strings(row["success_criteria"], f"{action_id}.success_criteria"),
            max_duration_ms=bound,
            keyboard_steps=tuple(steps),
            repeatable=repeatable,
            execution_kind=kind,
            required_facts=tuple(facts.items()),
            required_held_keys=_strings(row.get("required_held_keys", []), f"{action_id}.required_held_keys"),
            excluded_held_keys=_strings(row.get("excluded_held_keys", []), f"{action_id}.excluded_held_keys"),
            category=category,
            priority=priority,
            direction=direction,
            unavailable_facts=_strings(row.get("unavailable_facts", []), f"{action_id}.unavailable_facts"),
            refresh_interval_ms=interval,
            effect_active_fact=active_fact,
            elapsed_since_use_fact=elapsed_fact,
            usage_strategy=usage,
            effect_hint=hint,
            timing_strategy=timing,
            run_on_start=run_on_start,
            has_confirmed_use_fact=has_confirmed,
        ))
    if len({a.action_id for a in result}) != len(result):
        raise ValueError("Action IDs must be unique.")
    return ActionCatalog(
        str(data.get("status", "unspecified")), tuple(result),
        str(data.get("profile_id", "legacy")), str(data.get("context_version", "legacy")),
        tuple(data.get("character_context", {}).items()),
    )
