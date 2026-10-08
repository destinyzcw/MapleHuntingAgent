"""Records shared by capture, decisions, execution, and validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import TypeAlias

FactValue: TypeAlias = str | int | float | bool | None


class KeyboardOperation(StrEnum):
    KEY_DOWN = "key_down"
    PRESS = "press"
    HOLD = "hold"
    RELEASE = "release"
    CHORD = "chord"
    WAIT = "wait"


@dataclass(frozen=True)
class KeyboardStep:
    """An executor translates arbitrary configured key IDs to macOS events."""

    operation: KeyboardOperation
    keys: tuple[str, ...] = ()
    duration_ms: int = 0


@dataclass(frozen=True)
class Viewport:
    """Game crop bounds in capture pixels; desktop-point mapping comes later."""

    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class Observation:
    frame_id: str
    captured_at: datetime  # timezone-aware UTC; not proof of remote freshness
    image_path: Path | None
    viewport: Viewport
    source_window_id: str
    facts: dict[str, FactValue] = field(default_factory=dict)
    held_keys: tuple[str, ...] = ()  # only keys owned by our executor


@dataclass(frozen=True)
class ActionOption:
    action_id: str
    description: str
    preconditions: tuple[str, ...]
    success_criteria: tuple[str, ...]
    max_duration_ms: int
    keyboard_steps: tuple[KeyboardStep, ...] = ()
    repeatable: bool = False
    execution_kind: str = "keyboard"
    required_facts: tuple[tuple[str, bool], ...] = ()
    required_held_keys: tuple[str, ...] = ()
    excluded_held_keys: tuple[str, ...] = ()
    category: str = "custom"
    priority: int = 100
    direction: str | None = None
    unavailable_facts: tuple[str, ...] = ()
    refresh_interval_ms: int | None = None
    effect_active_fact: str | None = None
    elapsed_since_use_fact: str | None = None
    usage_strategy: str = ""
    effect_hint: str | None = None


@dataclass(frozen=True)
class ObjectivePlan:
    objective_id: str
    description: str
    phase: str
    completion_criteria: tuple[str, ...]
    context_version: str


@dataclass(frozen=True)
class DecisionRequest:
    observation: Observation
    objective: str
    rules: str
    context_version: str
    options: tuple[ActionOption, ...]
    learning_notes: tuple[str, ...] = ()
    recent_outcomes: tuple[ValidationResult, ...] = ()


@dataclass(frozen=True)
class DecisionResult:
    selected_action_id: str
    probabilities: dict[str, float]
    model_id: str
    elapsed_ms: float


@dataclass(frozen=True)
class ExecutionReceipt:
    action_id: str
    started_at: datetime
    finished_at: datetime
    dispatched: bool  # game effects require separate validation
    detail: str


class ValidationStatus(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    NOT_YET_OBSERVABLE = "not_yet_observable"


@dataclass(frozen=True)
class ValidationResult:
    status: ValidationStatus
    criterion: str
    before_frame_id: str
    after_frame_id: str
    evidence: tuple[str, ...]
    probabilities: dict[str, float] | None = None


class LearningStatus(StrEnum):
    PROPOSED = "proposed"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


@dataclass(frozen=True)
class LearningRecord:
    learning_id: str
    scope: dict[str, str]
    content: str
    status: LearningStatus
    evidence_refs: tuple[str, ...]
    created_at: datetime
    support_count: int = 0
    contradiction_count: int = 0
