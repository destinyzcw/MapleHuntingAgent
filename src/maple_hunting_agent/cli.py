"""Read-only scaffold inspection; no desktop control or model loading."""

import argparse
import importlib.metadata
import json
from pathlib import Path
import platform
import sys
import tomllib

from . import __version__
from .config import load_config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    doctor = commands.add_parser("doctor", help="Inspect config and environment")
    doctor.add_argument("--config", type=Path, default=Path("config/local.example.toml"))
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        if not config.rules_file.is_file():
            raise ValueError(f"Missing rules file: {config.rules_file}")
        with config.actions_file.open(encoding="utf-8") as handle:
            actions = json.load(handle)
        if actions.get("schema_version") != 1 or not isinstance(actions.get("actions"), list):
            raise ValueError("Actions file must contain schema_version 1 and an actions list.")
        if not actions["actions"]:
            raise ValueError("Actions list must not be empty.")
        ids = [action["id"] for action in actions["actions"]]
        if any(not isinstance(item, str) or not item for item in ids):
            raise ValueError("Every action ID must be a nonempty string.")
        if len(set(ids)) != len(ids):
            raise ValueError("Action IDs must be unique.")
    except (OSError, ValueError, KeyError, TypeError, AttributeError, tomllib.TOMLDecodeError) as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
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
        "actions": ids,
        "action_definitions_status": actions.get("status", "unspecified"),
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
