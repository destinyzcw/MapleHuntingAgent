# MapleHuntingAgent

A Python project for MapleStory hunting, hosted on an Apple Silicon Mac. The game runs on a remote computer and is viewed and controlled through **UU远程**. JEV's MLX implementation will select from an explicit list of available actions and assess their results.

![MapleStory gameplay showing characters and NPCs in a colorful side-scrolling town](docs/assets/maplestory-gameplay.jpg)

*Illustrative screenshot from the official [MapleStory Steam listing](https://store.steampowered.com/app/216150/MapleStory/). It is not a capture of our target session or a calibration/training image. [Image provenance](docs/assets/README.md).*

The target includes arbitrary configured keyboard keys, holds, releases, chords, and sequences; screenshots and fresh decisions every **1 second by default**; a shorter configurable repeat cadence; and persistent learning memory from initial calibration and gameplay outcomes.

**Current status: offline configuration and input preparation.** Character-profile compilation, configuration/action inspection, candidate filtering, and JEV state/question/candidate builders are implemented. Screen capture, model inference, input execution, and the live gameplay loop are not implemented. Nothing in this version sends keyboard or mouse events or downloads model weights.

## Current status — 2026-10-08

Version `0.1.0` contains the repository scaffold, configurable profiles, and offline JEV input preparation. An agent continuing this project should treat the following table as the implementation baseline, not infer functionality from interface names or example settings.

| Area | Implemented now | Remaining work |
|---|---|---|
| Package and CLI | Python package, `doctor`, `actions`, and perception/action `inputs` previews | Capture/replay/live commands |
| Configuration | TOML loading, basic validation, resolved local paths | Integration-specific validation and runtime settings |
| Data contracts | Observations, objectives, keyboard steps, decisions, execution receipts, result checks, learning records | Concrete adapters and orchestration |
| Character configuration | CMS Kanna sample, unified action list, numeric priorities, natural-language usage, optional teleport, and a minimal profile | Real icon calibration and measured key timing |
| Hunting policy | Center/rune-pause filtering and lowest-priority ready action selection; equal priorities offered together | Model-driven visual facts, live scheduling, and input execution |
| JEV inputs | State, visual questions, stable-ID candidates, profile-scoped memory, missing-input reporting, stale-frame fallback | Calling JEV and validating/mapping its answers |
| UU远程 integration | Capture/input boundaries and coordinate-mapping design | macOS window capture, focus checks, viewport mapping, and input forwarding |
| JEV MLX | Selected 8-bit model/runtime profile and documented setup | Model adapter, inference, probability validation, and Mac latency measurement |
| Keyboard actions | Catalog loader, duration validation, owned-key release choices, Boolean readiness filtering | macOS executor, owned-input release, and interruption |
| Timing and repeats | Configurable 1000-ms observations and 250-ms repeats, with expiry settings | Scheduler, fresh-frame checks, repeat cancellation, and overruns |
| Result validation | Before/after evidence contract and three outcome states | Deterministic/JEV validators and recovery policies |
| Memory | Scoped learning record contract and SQLite design | Storage, confirmation/correction workflow, and retrieval |
| Documentation | Architecture, Minecraft source review, milestones, and agent handoff | Update alongside each implementation milestone |

**Validation performed:** standard-library syntax/configuration checks, profile/remapping/priority/optional-capability cases, JEV input preparation and missing/stale-frame paths, and documentation-link/whitespace checks. These checks ran on the authoring workstation. No project dependencies or model weights were installed here. Metal inference, screenshots, UU远程 inputs, scheduling, memory persistence, and gameplay have not been tested.

The 11 dependency-free regression checks can be repeated with `python -m unittest discover -s tests -v`. They exercise configuration and input preparation only.

**Next milestone:** obtain real session context and screenshots, establish the UU远程 viewport, then implement recorded-frame replay and offline decisions. The public screenshot above cannot substitute for those inputs. Start with [AGENTS.md](AGENTS.md), [game context](game_context/README.md), and [development milestones](docs/development.md).

## Intended setup

```text
Remote computer: MapleStory
          ↕ UU远程 video and input transport
Mac: UU远程 window → capture → perception → available actions
                                             ↓
                                      JEV decision
                                             ↓
                               local keyboard/mouse execution
                                             ↓
                              fresh observation → result check
```

The host knows about the UU远程 window and its visible game viewport. It must not assume that the remote game's window coordinates are Mac desktop coordinates. See [remote desktop integration](docs/remote-desktop.md).

## Development setup

Python 3.12 or newer is required. On your Mac, create an isolated environment:

```bash
cd MapleHuntingAgent
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
cp config/local.example.toml config/local.toml
maple-agent doctor --config config/local.toml
```

Alternatively, inspect the scaffold without installing it:

```bash
PYTHONPATH=src python3.12 -m maple_hunting_agent doctor \
  --config config/local.example.toml
```

`doctor` checks the configuration and reports the environment, paths, and adapter status. It does not validate game connectivity or load JEV. Core inspection also works on Windows, where this repository is initially being authored; desktop execution will target macOS.

## JEV on your M4 Max

Your 128 GB Mac has enough memory for the community [JEV-27B-VL MLX 8-bit conversion](https://huggingface.co/nativ-community/JEV-27B-VL-MLX-8bit), which has approximately 30.7 GB of weights. Its decision readout requires the matching MLX-VLM fork. If JEV is not already installed, the model card's runtime can be installed into this environment:

```bash
python -m pip install \
  "git+https://github.com/Lazarus-931/mlx-vlm.git@24b24bb471dd36039fa5933f063f7dbc30a68c04"
```

The core package deliberately does not install MLX automatically. This preserves the choice of runtime and lets the scaffold run on non-Mac development machines. The future JEV adapter will import MLX only when selected and keep the model loaded between decisions.

Use the conversion and its matching runtime together. The [Bayway 4-bit conversion](https://huggingface.co/Bayway/JEV-27B-VL-MLX-4bit) uses a different checkpoint format/fork and will need its own adapter profile. Community conversions are not yet a verified gameplay deployment; probabilities and action choices need validation on our game inputs.

## Project layout

```text
config/                         machine-specific settings example
  characters/                   editable unified action profiles and guide
game_context/                   game rules and action definitions to author together
docs/                           architecture, remote desktop, decisions, development plan
  assets/                       README illustration and source attribution
src/maple_hunting_agent/
  cli.py                        configuration inspection entry point
  actions.py                    action loading and readiness/held-key filtering
  profiles.py                   character TOML → validated keyboard definitions
  hunting.py                    single-map center objective and candidate policy
  jev_inputs.py                  perception/action state, questions, and candidates
  config.py                     TOML configuration loader
  domain.py                     observations, requests, choices, result-check records
  contracts.py                  boundaries between pipeline components
  adapters/                     integration status and planned adapter locations
data/captures/                  local screenshot recordings, ignored by Git
data/runs/                      local traces and outcomes, ignored by Git
data/memory/                    local learning database, ignored by Git
```

## Next steps together

1. Fill in [game basics](game_context/README.md): MapleStory edition, character, map, goals, controls, and visible indicators.
2. Add representative screenshots and establish the UU远程 game viewport.
3. Implement recording and replay before enabling input execution.
4. Define valid hunting actions, their preconditions, duration, and success criteria.
5. Connect JEV, evaluate recorded decisions, then implement bounded live execution and recovery.

See [development milestones](docs/development.md) for acceptance criteria and [decision and validation contracts](docs/decisions.md) for the loop design.

The planner/controller and valid-action design draws on reviewed JEV Minecraft implementations. See [Minecraft lessons](docs/minecraft-lessons.md) for pinned sources, useful patterns, and the differences introduced by screenshot perception and UU远程.

Keyboard actions and timing are described in [action scheduling](docs/actions-and-scheduling.md). The memory design is in [learning memory](docs/memory.md). Both are specified for future implementation, not running in this scaffold.

The first [control profile](game_context/actions.md) is now authored. Use `maple-agent actions --config config/local.example.toml` to inspect it. Keyboard execution remains unimplemented.

Change bindings, action count, priorities, and natural-language usage in [character profiles](config/characters/README.md). No attack/buff classification is required, and characters can have no teleport or no effect-maintenance action.

Preview all JEV inputs without inference:

```bash
maple-agent inputs --config config/local.example.toml \
  --observation game_context/observations/unknown.example.json --stage action
```

Use `--stage perception` for visual questions. The example has no real screenshot and produces a missing-input fallback. [JEV input inventory](docs/jev-inputs.md) lists the known CMS Kanna context and the remaining screenshot/calibration inputs.

**Milestone 1 scope:** [stay centered and hunt on one map](game_context/hunting.md). The sample is CMS Kanna; map name is optional. Position comes from the top-left minimap and readiness from the bottom-right HUD. Its default priorities select 1 when ready, then **E → W → Q → D**; Q/D have cooldowns, and greyed-out E/W are unavailable. All five are unified actions with usage strategies. F6 stays disabled until milestone 2 in [TODO.md](docs/TODO.md). Rune activation is also deferred; detection pauses hunting for manual activation until that workflow is tested.
