# Actions and usage strategies

Character-specific bindings and usage rules live in [character profiles](../config/characters/README.md), not in Python code or a duplicate JSON catalog. The profile compiler generates keyboard definitions and the center-hunting policy filters candidates without dispatching input.

## CMS Kanna sample

| Binding | Priority | Usage |
|---|---:|---|
| 1 | 0 | Periodic: once when ready at startup by default, then every 60 seconds after confirmed use |
| E | 10 | Cooldown ready and not greyed out |
| W | 20 | Cooldown ready and not greyed out |
| Q | 30 | Cooldown ready |
| D | 40 | Cooldown ready |
| F6 | 5, disabled | Milestone 2: every 30 minutes or when its distinct effect disappears |

These are all unified action entries. Lower priority runs first, and optional natural-language usage explains the conditions to JEV. F6 generates no active candidate in milestone 1. Other characters can omit any entry, use different keys/chords, or have a different number of actions.

`buff_1` uses `strategy = "periodic"` and `interval_ms = 60000`. Due time does not bypass readiness or pending-input checks, and a missing effect does not trigger it before 60 seconds. Its timer resets after a confirmed application. Live scheduling/input remains unimplemented.

## Movement and teleport

Generated `move_<direction>_down` choices use leased key-down. `duration_ms` is the maximum lease without renewal, not a blocking sleep. The repeat scheduler will renew an authorized movement idempotently. Generated release choices are offered only for executor-owned keys; stop must release all owned keys.

Teleport is optional. In the sample it establishes the direction, taps S briefly, and releases owned input. It cancels old movement authorization and does not silently resume movement. Only horizontal teleport toward the center is offered by milestone 1; profile directions/timings remain editable and uncalibrated.

## Readiness and selection

Facts use stable action IDs: `action.attack_e.ready`, `action.attack_e.greyed_out`, `action.buff_1.ready`, and so on. Known greyed-out E/W are unavailable even if readiness conflicts. Non-grey is not by itself proof that cooldowns/resources permit use. Pending/blocked actions are withheld.

The number of definitions is profile-dependent. The policy filters by phase, readiness, and priority before enforcing the decision option budget. It never truncates a large set of tied ready actions silently.

`maple-agent actions --config config/local.example.toml` prints the generated definitions. No model is loaded and no keyboard input is sent. See [JEV input preparation](../docs/jev-inputs.md) for the next stage.
