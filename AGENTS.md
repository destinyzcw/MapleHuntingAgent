# Project working instructions

## Target environment

- Runtime target: Apple Silicon Mac, initially M4 Max with 128 GB unified memory.
- Game: MapleStory on another computer, viewed/controlled through UU远程.
- Current Windows workstation is for authoring only. Do not install project dependencies or download model weights here. Standard-library syntax/configuration checks are permitted.
- No game-state APIs or game-memory access are assumed. Observations come from the remote desktop display.

## Current scope

Build the scaffold, documentation, configuration, and interfaces first. Concrete game rules, key bindings, screenshots, and hunting actions will be supplied collaboratively. Clearly distinguish working components from planned ones.

## Agent handoff

1. Read the current-status table in `README.md` before implementing a feature. The current version has an action catalog/filter, but no keyboard dispatch or gameplay loop.
2. Read `docs/architecture.md`, `docs/actions-and-scheduling.md`, `docs/memory.md`, and `docs/minecraft-lessons.md` for accepted design decisions.
3. Read `config/characters/README.md` and the selected profile. All character activations are a single `[[actions]]` list with keys, numeric priority, and natural-language usage; no hardcoded attack/buff split. The sample is CMS Kanna with 1=0, E=10, W=20, Q=30, D=40. Q/D have cooldowns, E/W can grey out, F6 is disabled until milestone 2. Map name is not required.
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
- Milestone 1 is single-map centered hunting, with no map changes. Use the top-left minimap for position and bottom-right HUD for readiness. Read `game_context/hunting.md` before changing candidate rules.
- The CMS Kanna sample prioritizes ready actions as 1, then E → W → Q → D. Q/D have cooldowns, greyed-out E/W are unavailable. All entries share the same action schema; their game purposes do not require separate classification.
- `buff_1` is periodic every 60 seconds after confirmed use; startup activation is configurable and enabled by default. It must not run on every ready frame or early when its effect disappears. Due time still respects cooldown/pending checks. Timer state belongs to code, not visual inference.
- The default profile implements that order via priority numbers. Other profiles may remap keys, omit teleport, or have any number of unified actions. Do not hardcode sample keys/priorities into the policy or JEV prompts.
- Use `jev_inputs.py` for state/questions/candidates and explicit unknowns. Visual fact extraction and action selection are separate prepared stages; model execution remains unimplemented. Read `docs/jev-inputs.md` for known inputs and calibration gaps.
- Rune activation is deferred in `docs/TODO.md`. A detected requirement pauses routine hunting for manual activation; do not implement or assume the interaction/puzzle without a session test.
