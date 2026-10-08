# Adapter implementation plan

No concrete adapter is implemented yet. Keep desktop/MLX imports out of package initialization and configuration inspection.

Planned modules:

- `recorded_capture.py`: replay timestamped screenshots for offline decisions.
- `macos_capture.py`: capture the chosen UU远程 window and game viewport.
- `jev_mlx.py`: persistently load the configured JEV checkpoint and normalize typed decision outputs.
- `recording_executor.py`: record selected actions without sending input.
- `macos_executor.py`: execute authored, bounded input in the intended remote window.
- `result_validation.py`: apply deterministic criteria and optional JEV result judgments.
- `sqlite_memory.py`: persist scoped learning records and retrieve relevant confirmed notes.

Implement one backend per interface in `contracts.py`. Record an explicit error when an integration is unavailable; do not substitute invented game state or a random action.
