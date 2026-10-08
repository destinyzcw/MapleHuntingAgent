# Project working instructions

## Target environment

- Runtime target: Apple Silicon Mac, initially M4 Max with 128 GB unified memory.
- Game: MapleStory on another computer, viewed/controlled through UU远程.
- Current Windows workstation is for authoring only. Do not install project dependencies or download model weights here. Standard-library syntax/configuration checks are permitted.
- No game-state APIs or game-memory access are assumed. Observations come from the remote desktop display.

## Current scope

Build the scaffold, documentation, configuration, and interfaces first. Concrete game rules, key bindings, screenshots, and hunting actions will be supplied collaboratively. Clearly distinguish working components from planned ones.

## Agent handoff

1. Read the current-status table in `README.md` before implementing a feature. The current version is an inert scaffold, not a working gameplay agent.
2. Read `docs/architecture.md`, `docs/actions-and-scheduling.md`, `docs/memory.md`, and `docs/minecraft-lessons.md` for accepted design decisions.
3. Review `game_context/README.md` and `rules.template.md`. Game edition, character, hunting map, actual key bindings, and viewport geometry are not yet supplied.
4. Continue with the capture/context milestone in `docs/development.md`; use real user-session frames for calibration. The README's Steam screenshot is illustrative only.
5. Keep the README status and validation evidence current when a component becomes implemented. Do not label a defined interface, configuration field, or dependency installation as a working integration.

For dependency-free checks on this authoring workstation, compile source with Python's `compile()` and put `src` on `sys.path` to call `maple_hunting_agent.cli.main(["doctor", "--config", "config/local.example.toml"])`. No package installation is needed.

## Requirements

- Support arbitrary configured keyboard keys, holds, releases, chords, and ordered sequences.
- Default screenshot/decision interval: 1000 ms, configurable. Repeated approved actions can use a shorter interval with explicit expiration and cancellation.
- Keep persistent evidence-backed learning memory; do not describe prompt memory as online weight training.
- Preserve a finite available-action list for JEV and validate outputs before execution.
- Keep capture, perception, objectives, action filtering, decisions, execution, validation, memory, and traces separate.
- Use the Minecraft projects as architectural references. Read `docs/minecraft-lessons.md` for the inspected revisions and adaptation boundaries.
- Do not invent game mechanics, key bindings, or successful validation evidence.
