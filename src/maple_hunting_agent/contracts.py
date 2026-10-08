"""Component interfaces. Concrete integrations are deliberately not present yet."""

from typing import Protocol

from .domain import (
    ActionOption,
    DecisionRequest,
    DecisionResult,
    ExecutionReceipt,
    LearningRecord,
    Observation,
    ObjectivePlan,
    ValidationResult,
)


class CaptureSource(Protocol):
    def capture(self) -> Observation: ...


class PerceptionBackend(Protocol):
    def analyze(self, observation: Observation) -> Observation: ...


class ActionProvider(Protocol):
    def available(
        self, observation: Observation, objective: ObjectivePlan
    ) -> tuple[ActionOption, ...]: ...


class ObjectiveProvider(Protocol):
    def current(
        self, observation: Observation, recent_outcomes: tuple[ValidationResult, ...]
    ) -> ObjectivePlan: ...


class DecisionBackend(Protocol):
    def decide(self, request: DecisionRequest) -> DecisionResult: ...


class ActionExecutor(Protocol):
    def execute(self, action: ActionOption) -> ExecutionReceipt: ...

    def release_all(self) -> None: ...


class ResultValidator(Protocol):
    def validate(
        self,
        before: Observation,
        action: ActionOption,
        receipt: ExecutionReceipt,
        after: Observation,
    ) -> ValidationResult: ...


class LearningMemory(Protocol):
    def record(self, learning: LearningRecord) -> None: ...

    def relevant(
        self, scope: dict[str, str], objective: str
    ) -> tuple[LearningRecord, ...]: ...
