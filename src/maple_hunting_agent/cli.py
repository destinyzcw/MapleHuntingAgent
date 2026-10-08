"""Read-only scaffold inspection; no desktop control or model loading."""

import argparse
import importlib.metadata
import json
from pathlib import Path
import platform
import sys
import tomllib
from dataclasses import asdict

from . import __version__
from .config import load_config
from .profiles import load_character_profile
from .hunting import CenterHuntingPolicy
from .jev_inputs import build_jev_input, build_perception_input, load_observation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    doctor = commands.add_parser("doctor", help="Inspect config and environment")
    doctor.add_argument("--config", type=Path, default=Path("config/local.example.toml"))
    actions_command = commands.add_parser("actions", help="Inspect keyboard definitions without executing input")
    actions_command.add_argument("--config", type=Path, default=Path("config/local.example.toml"))
    inputs_command = commands.add_parser("inputs", help="Preview JEV state, question, and candidates without inference")
    inputs_command.add_argument("--config", type=Path, default=Path("config/local.example.toml"))
    inputs_command.add_argument("--observation", type=Path, required=True, help="A replay/preview observation JSON file")
    inputs_command.add_argument("--stage", choices=("action", "perception"), default="action")
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        if not config.rules_file.is_file():
            raise ValueError(f"Missing rules file: {config.rules_file}")
        catalog = load_character_profile(config.character_profile_file, max_key_hold_ms=config.max_key_hold_ms)
        ids = [action.action_id for action in catalog.actions]
        with config.session_file.open(encoding="utf-8") as handle:
            session = json.load(handle)
        if not isinstance(session, dict):
            raise ValueError("Session context must be a JSON object.")
        if args.command == "inputs":
            observation = load_observation(args.observation.resolve())
            policy = CenterHuntingPolicy(catalog, config.center_x, config.center_tolerance, config.max_options)
            if args.stage == "perception":
                prepared = build_perception_input(
                    observation, catalog, session=session, center_x=config.center_x, center_tolerance=config.center_tolerance,
                    max_observation_age_ms=config.max_repeat_observation_age_ms,
                )
            else:
                prepared = build_jev_input(
                    observation, catalog, policy, config.rules_file.read_text(encoding="utf-8"),
                    session=session, max_observation_age_ms=config.max_repeat_observation_age_ms,
                )
    except (OSError, ValueError, KeyError, TypeError, AttributeError, tomllib.TOMLDecodeError) as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
    if args.command == "inputs":
        print(json.dumps(prepared.to_dict(), indent=2, ensure_ascii=False))
        return 0
    if args.command == "actions":
        print(json.dumps({
            "status": catalog.status,
            "profile_id": catalog.profile_id,
            "character": dict(catalog.character_context),
            "context_version": catalog.context_version,
            "priority_rule": "lower number first across configured actions; ties offered together",
            "actions": [asdict(action) for action in catalog.actions],
            "execution": "inspection only; no input dispatched",
        }, indent=2, ensure_ascii=False))
        return 0
    try:
        mlx_vlm_version = importlib.metadata.version("mlx-vlm")
    except importlib.metadata.PackageNotFoundError:
        mlx_vlm_version = "not installed (not required for scaffold inspection)"
    report = {
        "status": "scaffold_config_valid",
        "version": __version__,
        "platform": platform.system(),
        "architecture": platform.machine(),
        "target_platform": "macOS Apple Silicon",
        "mode": config.mode,
        "remote_app": config.remote_app_name,
        "model_id": config.model_id,
        "mlx_vlm": mlx_vlm_version,
        "runtime_revision": config.runtime_revision,
        "runtime_compatibility": "not verified by this command",
        "rules_file": str(config.rules_file),
        "session_file": str(config.session_file),
        "character_profile_file": str(config.character_profile_file),
        "profile_id": catalog.profile_id,
        "character": dict(catalog.character_context),
        "action_priorities": {a.action_id: a.priority for a in catalog.actions if a.category == "skill"},
        "actions": ids,
        "action_definitions_status": catalog.status,
        "capture_dir": str(config.capture_dir),
        "run_dir": str(config.run_dir),
        "scheduling": {
            "observation_interval_ms": config.observation_interval_ms,
            "repeat_interval_ms": config.repeat_interval_ms,
            "max_repeat_observation_age_ms": config.max_repeat_observation_age_ms,
            "max_repeat_span_ms": config.max_repeat_span_ms,
            "max_key_hold_ms": config.max_key_hold_ms,
            "status": "not implemented",
        },
        "memory": {
            "enabled": config.memory_enabled,
            "backend": config.memory_backend,
            "database": str(config.memory_database),
            "status": "not implemented",
        },
        "hunting": {
            "strategy": config.hunting_strategy,
            "map_change_enabled": config.map_change_enabled,
            "center_x": config.center_x,
            "center_tolerance": config.center_tolerance,
            "status": "offline candidate policy implemented; live loop pending",
            "rune_activation": "TODO; detected requirement pauses hunting",
        },
        "integrations": {
            "capture": "not implemented",
            "perception": "not implemented",
            "jev_decisions": "not implemented",
            "executor": "not implemented",
            "validator": "not implemented",
            "gameplay_loop": "not implemented",
        },
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0
