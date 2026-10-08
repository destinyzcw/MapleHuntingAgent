"""Load scaffold settings without importing Mac-specific dependencies."""

from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass(frozen=True)
class AppConfig:
    project_root: Path
    mode: str
    capture_dir: Path
    run_dir: Path
    remote_app_name: str
    window_title: str
    require_focused_window: bool
    decision_backend: str
    model_id: str
    runtime_revision: str
    max_options: int
    rules_file: Path
    session_file: Path
    character_profile_file: Path
    observation_interval_ms: int
    repeat_interval_ms: int
    max_repeat_observation_age_ms: int
    max_repeat_span_ms: int
    max_key_hold_ms: int
    memory_enabled: bool
    memory_backend: str
    memory_database: Path
    hunting_strategy: str
    map_change_enabled: bool
    center_x: float
    center_tolerance: float


def load_config(path: Path) -> AppConfig:
    path = path.expanduser().resolve()
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    root = next(
        (parent for parent in path.parents if (parent / "pyproject.toml").is_file()),
        None,
    )
    if root is None:
        raise ValueError("Configuration must be inside a MapleHuntingAgent checkout.")
    runtime = data["runtime"]
    remote = data["remote"]
    decision = data["decision"]
    context = data["context"]
    scheduling = data["scheduling"]
    memory = data["memory"]
    hunting = data["hunting"]
    if runtime["mode"] != "observe":
        raise ValueError("Only observe mode is available in this scaffold.")
    if decision["backend"] != "jev_mlx":
        raise ValueError("The scaffold currently defines only the jev_mlx backend.")
    max_options = decision["max_options"]
    if type(max_options) is not int or not 2 <= max_options <= 16:
        raise ValueError("max_options must be an integer from 2 to 16.")
    if type(remote["require_focused_window"]) is not bool:
        raise ValueError("require_focused_window must be a boolean.")
    for key in ("model_id", "runtime_revision"):
        if not isinstance(decision[key], str) or not decision[key].strip():
            raise ValueError(f"decision.{key} must be a nonempty string.")
    if not isinstance(remote["app_name"], str) or not remote["app_name"].strip():
        raise ValueError("remote.app_name must be a nonempty string.")
    for key in (
        "observation_interval_ms", "repeat_interval_ms",
        "max_repeat_observation_age_ms", "max_repeat_span_ms", "max_key_hold_ms",
    ):
        if type(scheduling[key]) is not int or scheduling[key] <= 0:
            raise ValueError(f"scheduling.{key} must be a positive integer.")
    if scheduling["repeat_interval_ms"] > scheduling["observation_interval_ms"]:
        raise ValueError("Repeat interval must not exceed the observation interval.")
    if type(memory["enabled"]) is not bool or memory["backend"] != "sqlite":
        raise ValueError("Memory requires a boolean enabled field and the sqlite backend.")
    if hunting["strategy"] != "single_map_center" or hunting["map_change_enabled"] is not False:
        raise ValueError("Milestone 1 requires single_map_center with map changes disabled.")
    for key in ("center_x", "center_tolerance"):
        if type(hunting[key]) not in (int, float):
            raise ValueError(f"hunting.{key} must be numeric.")
    if not 0 <= hunting["center_x"] <= 1 or not 0 < hunting["center_tolerance"] <= 0.5:
        raise ValueError("Center settings must be normalized minimap fractions.")

    def resolve(value: str) -> Path:
        item = Path(value).expanduser()
        return (item if item.is_absolute() else root / item).resolve()

    return AppConfig(
        project_root=root,
        mode=runtime["mode"],
        capture_dir=resolve(runtime["capture_dir"]),
        run_dir=resolve(runtime["run_dir"]),
        remote_app_name=remote["app_name"],
        window_title=remote["window_title"],
        require_focused_window=remote["require_focused_window"],
        decision_backend=decision["backend"],
        model_id=decision["model_id"],
        runtime_revision=decision["runtime_revision"],
        max_options=max_options,
        rules_file=resolve(context["rules_file"]),
        session_file=resolve(context["session_file"]),
        character_profile_file=resolve(context["character_profile_file"]),
        observation_interval_ms=scheduling["observation_interval_ms"],
        repeat_interval_ms=scheduling["repeat_interval_ms"],
        max_repeat_observation_age_ms=scheduling["max_repeat_observation_age_ms"],
        max_repeat_span_ms=scheduling["max_repeat_span_ms"],
        max_key_hold_ms=scheduling["max_key_hold_ms"],
        memory_enabled=memory["enabled"],
        memory_backend=memory["backend"],
        memory_database=resolve(memory["database"]),
        hunting_strategy=hunting["strategy"],
        map_change_enabled=hunting["map_change_enabled"],
        center_x=float(hunting["center_x"]),
        center_tolerance=float(hunting["center_tolerance"]),
    )
