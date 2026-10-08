"""Build traceable JEV state/questions/candidates without importing MLX."""

from dataclasses import asdict, dataclass, replace
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Callable

from .actions import ActionCatalog
from .domain import ActionOption, LearningRecord, LearningStatus, Observation, ValidationResult, Viewport
from .hunting import CenterHuntingPolicy


@dataclass(frozen=True)
class PreparedJevInput:
    state: list
    questions: dict
    metadata: dict
    candidates: tuple[ActionOption, ...]

    def to_dict(self) -> dict:
        return {"state": self.state, "questions": self.questions, "metadata": self.metadata}

    def to_predict_inputs(self, image_loader: Callable[[Path], object]) -> tuple[list, dict]:
        """The Mac adapter supplies a loader such as Image.open(...).convert('RGB')."""
        state = [image_loader(Path(part["image"])) if isinstance(part, dict) and "image" in part else part for part in self.state]
        return state, self.questions


def _missing_context(value: dict, prefix: str = "session") -> list[str]:
    missing = []
    for key, item in value.items():
        name = f"{prefix}.{key}"
        if item is None:
            missing.append(name)
        elif isinstance(item, dict):
            missing.extend(_missing_context(item, name))
    return missing


def _session_context(catalog: ActionCatalog, session: dict | None) -> dict:
    result = deepcopy(session or {})
    game = result.setdefault("game", {})
    if not isinstance(game, dict):
        raise ValueError("session.game must be an object.")
    game.update(dict(catalog.character_context))
    return result


def _input_issues(observation: Observation, now: datetime, max_age_ms: int) -> tuple[float, list[str]]:
    if observation.captured_at.tzinfo is None or now.tzinfo is None:
        raise ValueError("Observation and current time must be timezone-aware.")
    if type(max_age_ms) is not int or max_age_ms <= 0:
        raise ValueError("max_observation_age_ms must be a positive integer.")
    age_ms = (now - observation.captured_at).total_seconds() * 1000
    issues = []
    if age_ms < 0 or age_ms > max_age_ms:
        issues.append("future_capture_timestamp" if age_ms < 0 else "observation_stale")
    if observation.facts.get("remote.frame_fresh") is not True:
        issues.append("remote_frame_freshness_unverified")
    if observation.image_path is None:
        issues.append("no_screenshot")
    elif not observation.image_path.is_file():
        issues.append("screenshot_file_missing")
    return age_ms, issues


def load_observation(path: Path) -> Observation:
    """Load a replay/preview record. Relative images resolve beside this record."""
    with path.open(encoding="utf-8") as handle:
        row = json.load(handle)
    captured = datetime.fromisoformat(row["captured_at"].replace("Z", "+00:00"))
    if captured.tzinfo is None or captured.utcoffset() is None:
        raise ValueError("captured_at must include a timezone.")
    viewport = row["viewport"]
    values = [viewport[key] for key in ("x", "y", "width", "height")]
    if any(type(value) is not int for value in values) or any(value < 0 for value in values[:2]) or any(value <= 0 for value in values[2:]):
        raise ValueError("viewport needs nonnegative x/y and positive width/height integers.")
    facts = row.get("facts", {})
    if not isinstance(facts, dict) or any(not isinstance(k, str) or not k for k in facts):
        raise ValueError("facts must be an object keyed by nonempty strings.")
    for value in facts.values():
        if value is not None and type(value) not in (str, int, float, bool):
            raise ValueError("Fact values must be scalar or null.")
        if type(value) is float and not math.isfinite(value):
            raise ValueError("Numeric facts must be finite.")
    held = row.get("held_keys", [])
    if not isinstance(held, list) or any(not isinstance(k, str) or not k.strip() for k in held) or len(set(held)) != len(held):
        raise ValueError("held_keys must be a unique list of executor-owned keys.")
    for key in ("frame_id", "source_window_id"):
        if not isinstance(row[key], str) or not row[key]:
            raise ValueError(f"{key} must be a nonempty string.")
    image = row.get("image_path")
    if image is not None and (not isinstance(image, str) or not image):
        raise ValueError("image_path must be a path string or null.")
    image_path = None
    if image:
        candidate = Path(image).expanduser()
        image_path = (candidate if candidate.is_absolute() else path.parent / candidate).resolve()
    return Observation(row["frame_id"], captured, image_path, Viewport(*values), row["source_window_id"], facts, tuple(held))


def build_jev_input(
    observation: Observation,
    catalog: ActionCatalog,
    policy: CenterHuntingPolicy,
    rules: str,
    *,
    session: dict | None = None,
    recent_outcomes: tuple[ValidationResult, ...] = (),
    learnings: tuple[LearningRecord, ...] = (),
    now: datetime | None = None,
    max_observation_age_ms: int = 1500,
) -> PreparedJevInput:
    now = now or datetime.now(timezone.utc)
    session = _session_context(catalog, session)
    age_ms, issues = _input_issues(observation, now, max_observation_age_ms)
    effective = observation
    if issues:
        effective = replace(observation, facts={**observation.facts, "control.gameplay_ready": False})
    plan = policy.current(effective, recent_outcomes)
    options = policy.available(effective, plan)
    ids = [action.action_id for action in options]
    if not ids or len(ids) > policy.max_options or len(ids) != len(set(ids)):
        raise ValueError("JEV needs a nonempty, unique candidate set within max_options.")
    confirmed = []
    for learning in learnings:
        if learning.status != LearningStatus.CONFIRMED:
            continue
        scope = learning.scope
        expected = {"profile_id": catalog.profile_id, "context_version": catalog.context_version, "map_id": observation.facts.get("map.id")}
        if scope.get("profile_id") != catalog.profile_id or scope.get("context_version") != catalog.context_version:
            continue
        if any(key not in expected or expected[key] != value for key, value in scope.items()):
            continue
        confirmed.append({"id": learning.learning_id, "content": learning.content, "evidence_refs": learning.evidence_refs})
    supported_facts = {key: None for action in catalog.actions for key, _ in action.required_facts}
    supported_facts.update({key: None for action in catalog.actions for key in action.unavailable_facts})
    supported_facts.update({key: None for action in catalog.actions for key in (action.effect_active_fact, action.elapsed_since_use_fact) if key})
    supported_facts.update({"minimap.player_x": None, "minimap.center_relation": None, "rune.required": None, "map.changed": None, "remote.frame_fresh": None})
    supported_facts.update(effective.facts)
    state_text = {
        "schema_version": 1,
        "profile_id": catalog.profile_id,
        "context_version": catalog.context_version,
        "session": session or {},
        "objective": asdict(plan),
        "observation": {"frame_id": observation.frame_id, "captured_at": observation.captured_at.isoformat(), "age_ms": round(age_ms, 3), "viewport": asdict(observation.viewport), "source_window_id": observation.source_window_id, "held_keys": observation.held_keys, "facts": supported_facts},
        "candidate_details": [{"id": a.action_id, "description": a.description, "usage_strategy": a.usage_strategy, "category": a.category, "priority": a.priority, "keys": [list(step.keys) for step in a.keyboard_steps if step.keys], "max_duration_ms": a.max_duration_ms, "repeatable": a.repeatable, "success_criteria": a.success_criteria} for a in options],
        "recent_outcomes": [asdict(outcome) for outcome in recent_outcomes[-5:]],
        "confirmed_learnings": confirmed[-8:],
        "rules": rules,
        "input_issues": issues,
    }
    state = [json.dumps(state_text, ensure_ascii=False, allow_nan=False)]
    if observation.image_path is not None and observation.image_path.is_file():
        state += ["Current game viewport screenshot:", {"image": str(observation.image_path)}]
    question = (
        "Choose the single supplied action that advances the current single-map hunting objective. "
        "Use the configured bindings and priority numbers; lower numbers run first and ties may be compared. "
        "Unknown is not ready; greyed-out or pending skills are unavailable. "
        "Do not invent actions, bypass a rune pause, change maps, or treat dispatch as success. "
        "If input issues prevent gameplay, only release owned inputs, wait, or stop. "
        f"Current phase: {plan.phase}."
    )
    questions = {"action": {"type": "choice", "instructions": question, "criteria": {a.action_id: a.description + (" Usage: " + a.usage_strategy if a.usage_strategy else "") for a in options}}}
    metadata = {
        "frame_id": observation.frame_id, "profile_id": catalog.profile_id, "context_version": catalog.context_version,
        "rules_sha256": hashlib.sha256(rules.encode()).hexdigest(), "candidate_ids": ids,
        "missing_facts": sorted(key for key, value in supported_facts.items() if value is None),
        "missing_context": _missing_context(session or {}),
        "input_issues": issues, "phase": plan.phase, "has_screenshot": len(state) > 1,
        "status": "prepared_input_only; no inference or execution",
    }
    return PreparedJevInput(state, questions, metadata, options)


def build_perception_input(
    observation: Observation,
    catalog: ActionCatalog,
    *,
    session: dict | None = None,
    center_x: float = 0.5,
    center_tolerance: float = 0.05,
    now: datetime | None = None,
    max_observation_age_ms: int = 1500,
) -> PreparedJevInput:
    """Prepare visual fact questions; applying answers remains the adapter's job."""
    if not 0 <= center_x <= 1 or not 0 < center_tolerance <= 0.5:
        raise ValueError("Center settings must be normalized minimap fractions.")
    age, issues = _input_issues(observation, now or datetime.now(timezone.utc), max_observation_age_ms)
    questions, mappings = {}, {}

    def choice(name: str, instruction: str, fact: str, values: dict, descriptions: dict) -> None:
        questions[name] = {"type": "choice", "instructions": instruction + " Choose unknown when the image is absent, stale, unreadable, or insufficient; do not guess.", "criteria": descriptions}
        mappings[name] = {"fact": fact, "values": values}

    choice("gameplay_ready", "Does the viewport show usable gameplay rather than a menu, death, disconnection, or blocking dialog?", "control.gameplay_ready", {"ready": True, "blocked": False, "unknown": None}, {"ready": "Usable gameplay is visible.", "blocked": "Gameplay is blocked.", "unknown": "Insufficient evidence."})
    choice("rune_required", "Is a rune-required dark-purple/block notice visible?", "rune.required", {"required": True, "clear": False, "unknown": None}, {"required": "Rune activation is required.", "clear": "The calibrated notice area is visible and has no requirement.", "unknown": "Notice state cannot be established."})
    choice("minimap_center", f"Locate the player marker in the top-left minimap. Is its horizontal position below {center_x - center_tolerance:.3f}, inside the central band, or above {center_x + center_tolerance:.3f} of the minimap width?", "minimap.center_relation", {"left": "left", "center": "center", "right": "right", "unknown": None}, {"left": "Left of the configured center band.", "center": "Inside the center band.", "right": "Right of the center band.", "unknown": "Player/minimap bounds are unclear."})
    session = _session_context(catalog, session)
    map_name = session.get("game", {}).get("map_name")
    if map_name:
        choice("map_changed", f"Does the displayed map name differ from the starting map {map_name!r}?", "map.changed", {"changed": True, "same": False, "unknown": None}, {"changed": "A different map is visible.", "same": "The supplied starting map matches.", "unknown": "The map identity is unreadable."})
    skills = []
    asked_ready, asked_grey, asked_effect = set(), set(), set()
    for action in catalog.actions:
        if action.category not in ("skill", "teleport"):
            continue
        keys = [list(step.keys) for step in action.keyboard_steps if step.operation.value in ("press", "chord")]
        skills.append({"id": action.action_id, "keys": keys, "priority": action.priority, "usage_strategy": action.usage_strategy})
        for fact, expected in action.required_facts:
            if expected is True and fact != "control.gameplay_ready" and fact not in asked_ready:
                name = f"ready_{len(asked_ready)}"
                choice(name, f"Can configured action {action.action_id} ({keys}) be used now under this usage strategy: {action.usage_strategy or 'Use only when ready.'}? Inspect the bottom-right HUD and supplied context.", fact, {"ready": True, "unavailable": False, "unknown": None}, {"ready": "Ready under its usage strategy.", "unavailable": "Greyed out, on cooldown, resource-blocked, or otherwise unavailable.", "unknown": "Readiness cannot be established."})
                asked_ready.add(fact)
        for fact in action.unavailable_facts:
            if fact.endswith(".greyed_out") and fact not in asked_grey:
                choice(f"grey_{len(asked_grey)}", f"Is the HUD icon for {action.action_id} ({keys}) greyed out?", fact, {"greyed": True, "not_greyed": False, "unknown": None}, {"greyed": "Visibly greyed out; unavailable.", "not_greyed": "Clearly not greyed out; this alone does not prove readiness.", "unknown": "Icon state is unclear."})
                asked_grey.add(fact)
        effect_fact = action.effect_active_fact
        if effect_fact and effect_fact not in asked_effect:
            choice(f"effect_{len(asked_effect)}", f"Is the configured effect for {action.action_id} present? {action.effect_hint or 'Use only its calibrated effect indicator.'}", effect_fact, {"active": True, "missing": False, "unknown": None}, {"active": "Its calibrated effect indicator is present.", "missing": "The calibrated area is visible and the effect is absent.", "unknown": "The specific effect cannot be identified."})
            asked_effect.add(effect_fact)
    state = [json.dumps({"profile_id": catalog.profile_id, "context_version": catalog.context_version, "session": session, "frame_id": observation.frame_id, "viewport": asdict(observation.viewport), "facts": observation.facts, "skills": skills, "input_issues": issues}, ensure_ascii=False, allow_nan=False)]
    if observation.image_path is not None and observation.image_path.is_file():
        state += ["Current game viewport screenshot:", {"image": str(observation.image_path)}]
    return PreparedJevInput(state, questions, {
        "stage": "perception", "frame_id": observation.frame_id, "age_ms": round(age, 3),
        "input_issues": issues, "fact_mappings": mappings, "missing_context": _missing_context(session),
        "status": "prepared_visual_questions_only; no inference or fact extraction executed",
    }, ())
