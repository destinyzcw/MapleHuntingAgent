"""Single-map center hunting policy over supplied facts; no perception or input."""

from dataclasses import dataclass, replace
import math

from .actions import ActionCatalog
from .domain import ActionOption, KeyboardOperation, ObjectivePlan, Observation, ValidationResult


@dataclass(frozen=True)
class CenterHuntingPolicy:
    catalog: ActionCatalog
    center_x: float = 0.5
    center_tolerance: float = 0.05
    max_options: int = 16

    def __post_init__(self) -> None:
        if not 0 <= self.center_x <= 1 or not 0 < self.center_tolerance <= 0.5:
            raise ValueError("Center settings must be normalized minimap fractions.")
        if type(self.max_options) is not int or self.max_options < 2:
            raise ValueError("max_options must be an integer of at least 2.")

    def _bounded(self, choices: tuple[ActionOption, ...]) -> tuple[ActionOption, ...]:
        if len(choices) > self.max_options:
            raise ValueError("Available choices exceed max_options; separate tied priorities or increase the supported option budget.")
        return choices

    def _player_x(self, observation: Observation) -> float | None:
        value = observation.facts.get("minimap.player_x")
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
            return None
        return float(value)

    def _center_relation(self, observation: Observation) -> str:
        measured = self._player_x(observation)
        supplied = observation.facts.get("minimap.center_relation")
        if measured is not None:
            relation = "center" if self.center_x - self.center_tolerance <= measured <= self.center_x + self.center_tolerance else "left" if measured < self.center_x else "right"
            if supplied in ("left", "center", "right") and supplied != relation:
                return "unknown"
            return relation
        return supplied if supplied in ("left", "center", "right") else "unknown"

    def current(self, observation: Observation, recent_outcomes: tuple[ValidationResult, ...] = ()) -> ObjectivePlan:
        facts = observation.facts
        if facts.get("rune.required") is True:
            phase, description = "rune_pending", "Pause hunting: rune activation requires manual intervention; implementation is TODO."
        elif facts.get("map.changed") is True:
            phase, description = "wrong_map", "Pause: the single-map hunting session moved to a different map."
        elif facts.get("control.gameplay_ready") is not True or facts.get("rune.required") is not False:
            phase, description = "observe", "Obtain usable gameplay and rune-status evidence before choosing hunting actions."
        elif (relation := self._center_relation(observation)) == "unknown":
            phase, description = "observe", "Locate the player in the top-left minimap before moving."
        elif relation != "center":
            phase, description = "center", "Return to the horizontal center band of the current map; do not change maps."
        else:
            phase, description = "hunt", f"Stay centered and use the available configured action with the lowest priority number in profile {self.catalog.profile_id}. Follow its usage strategy."
        return ObjectivePlan("single_map_center_hunt", description, phase, ("Remain on the starting map.",), self.catalog.context_version)

    def available(self, observation: Observation, objective: ObjectivePlan) -> tuple[ActionOption, ...]:
        # Recompute phase rather than trusting a plan built from an older frame.
        phase = self.current(observation).phase
        candidates = self.catalog.available(observation, objective)
        stops = tuple(a for a in candidates if a.category == "stop")
        releases = tuple(a for a in candidates if a.category == "release")
        fallback = tuple(a for a in candidates if a.category in ("wait", "stop"))
        if phase in ("observe", "rune_pending", "wrong_map"):
            return self._bounded(releases + fallback)
        movement = {a.direction: a for a in self.catalog.actions if a.category == "movement"}
        direction_keys = {
            direction: next(step.keys[0] for step in action.keyboard_steps if step.operation == KeyboardOperation.KEY_DOWN)
            for direction, action in movement.items()
        }
        held_movement = set(observation.held_keys) & set(direction_keys.values())
        if phase == "hunt":
            if held_movement:
                return self._bounded(releases + stops)
            skills = tuple(a for a in candidates if a.category == "skill")
            if skills:
                priority = min(a.priority for a in skills)
                return self._bounded(tuple(a for a in skills if a.priority == priority) + stops)
            return self._bounded(fallback)
        direction = "right" if self._center_relation(observation) == "left" else "left"
        key = direction_keys[direction]
        if held_movement - {key}:
            return self._bounded(releases + stops)
        useful = [a for a in candidates if a.direction == direction and a.category in ("movement", "teleport")]
        original = movement[direction]
        if key in held_movement and not any(a.category == "movement" for a in useful):
            # A held direction may be reapproved as an idempotent lease renewal.
            if all(observation.facts.get(k) is v for k, v in original.required_facts) and observation.facts.get(f"action.{original.action_id}.blocked") is not True:
                useful.insert(0, replace(original, description=f"Continue moving {direction} with {key}; renew the bounded key lease.", excluded_held_keys=()))
        return self._bounded(tuple(useful) + stops if useful else releases + fallback)
