# Character profiles

One `[[actions]]` list represents every character action. There are no separate attack and buff lists: each entry has bindings, a priority, and natural-language `usage` instructions passed to JEV.

Select the file in `config/local.toml`:

```toml
[context]
rules_file = "game_context/rules.template.md"
session_file = "game_context/session.example.json"
character_profile_file = "config/characters/default.toml"
```

Paths resolve from the repository root. Older local configs should replace `actions_file` with `character_profile_file` and add `session_file`. Copy a profile to `local-kanna.toml` for private changes; `local*.toml` profiles are ignored by Git.

## Included examples

- [default.toml](default.toml): **China MapleStory (CMS), Kanna**, using 1=0, E=10, W=20, Q=30, D=40. The 1 action is periodic every 60 seconds, gated by readiness. Q/D have cooldowns; E/W can be greyed out. S teleport is enabled. The distinct F6 action is disabled until milestone 2.
- [minimal.example.toml](minimal.example.toml): one X action and no teleport. It demonstrates a character without buffs or teleport; it is not a verified game setup.

## An action

```toml
[[actions]]
id = "primary"
keys = ["r"]
priority = 10
usage = "Use when cooldown is ready and the icon is not greyed out."
availability = "observed"
detect_greyed_out = true
press_ms = 80
```

Change the keys, add/remove any number of entries, or set `enabled = false`; no code changes are required. Omit the list or set `actions = []` at the top of the file for a movement-only profile. `keys = ["ctrl", "r"]` produces a simultaneous chord. Tap/hold durations must fit `scheduling.max_key_hold_ms`; initial timings are uncalibrated.

IDs are stable identifiers, not the physical key. Remapping `primary` from R to T keeps its facts as `action.primary.ready`, `action.primary.greyed_out`, and `action.primary.pending`. Descriptions and usage text should reflect the current binding.

## Priority and usage

**Lower nonnegative priority numbers run first across the unified list.** Equal-priority ready actions are offered together to JEV. A ready tie that exceeds the configured option budget reports an error instead of silently omitting options. Numeric priority is authoritative if free-text notes conflict.

`usage` is included in the visual-readiness question, action state, and choice description. Code does not parse arbitrary natural language into timers or keyboard programs. Known readiness, greying, pending-input, duration, and optional refresh checks remain structured guards around JEV's choice.

- `availability = "observed"` (default): require `action.<id>.ready = true` from fresh evidence. Unknown/false withholds the action.
- `availability = "always"`: explicit configuration for an action without cooldown/readiness restrictions. Gameplay, pending/blocked state, and any refresh strategy still apply. This is not appropriate for the sample Q/D.
- `detect_greyed_out = true`: generate a visual check for `action.<id>.greyed_out`; known greying overrides a ready flag.
- `action.<id>.pending = true`: withhold while the previous activation is unresolved.
- `action.<id>.blocked = true`: withhold a confirmed failed action until the controller clears the block.

Optional `ready_fact` and `greyed_out_fact` fields can connect an existing perception pipeline. No hardcoded cooldown seconds are assumed for Q/D or E/W.

## Usage strategies

`strategy = "available"` (default) uses the action when its readiness guards and priority permit. For periodic actions:

```toml
[[actions]]
id = "buff_1"
keys = ["1"]
priority = 0
usage = "Use at session start when ready, then every 60 seconds after confirmed use."
availability = "observed"
strategy = "periodic"
interval_ms = 60000
run_on_start = true
```

`periodic` becomes due at the interval boundary after a confirmed application. Effect disappearance does not make it due early. Cooldown/readiness, pending/blocked state, and gameplay checks still apply. The default starts once at the first ready hunting opportunity when `action.<id>.has_confirmed_use = false`; unknown history does not imply never used. With `run_on_start = false`, the first use is due after `session.elapsed_ms` reaches the interval. Following uses need `action.<id>.elapsed_since_confirmed_ms`.

The live controller will own monotonic session/timer history, set pending before input, and reset the timer only after confirmation. Due actions delayed by unavailable skills or a paused session wait for the next valid opportunity; missed periods do not generate catch-up input bursts. Actual scheduler/input execution is not implemented yet.

For a different strategy that also responds to a missing effect:

```toml
[[actions]]
id = "maintenance"
keys = ["f6"]
enabled = false
priority = 5
usage = "Refresh every 30 minutes or when the effect disappears."
availability = "always"
strategy = "interval_or_missing"
refresh_interval_ms = 1800000
effect_hint = "Identify its specific icon in the bottom row of the top-right buff list."
```

This strategy needs `action.<id>.effect_present` and `action.<id>.elapsed_since_confirmed_ms`. It becomes due when the effect is definitely absent or the interval expires after a confirmed use. Unknown effect/time alone does not trigger it; pending state still withholds it. Live timer tracking and effect detection remain unimplemented. The default F6 entry stays disabled for milestone 1.

Any action can define `effect_present_fact` and `effect_hint` for result verification, without being classified as a buff. The default 1 action does so and is distinct from F6.

## Teleport and movement

Omit `[teleport]`, or write `enabled = false`, for a character without teleport. When enabled, set `keys`, optional `directions`, timing, and `available_fact` (default `action.teleport.ready`). The compiler combines these with configured direction keys. Center hunting only offers horizontal teleport toward the center.

Movement is configured in `[movement].bindings` and must have distinct left/right/up/down keys. The executor tracks leased key-down and release using the configured keys, rather than assuming arrow names.

Optional `[character]` fields are `edition_region` and `character_class`. No map name is required. The profile's `context_version` is fingerprinted automatically: key/priority/usage changes invalidate incompatible persistent memory.

Inspect with `maple-agent actions --config config/local.toml`. See [JEV inputs](../../docs/jev-inputs.md) for state/question/candidate previews.
