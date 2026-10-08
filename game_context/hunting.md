# Milestone 1: centered hunting on a single map

User-provided objective for milestone 1: stay near the center of the current map and use configured actions when their usage strategies permit. The sample character is CMS Kanna with 1/E/W/Q/D; map name is not required. Map changes, cross-map routes, and the disabled F6 action are out of scope.

MapleStory is a 2D scrolling game. The top-left minimap tells us where the character is in the map; the bottom-right skill/action HUD shows keyboard bindings and cooldowns. The scrolling main view's center is not a reliable world-position target.

Buff indicators are in the bottom row of the top-right buff list. The 1 and F6 buffs serve different purposes; their exact icons/effects still need identification from the session.

## Centering

Track the player marker in the cropped minimap. Initial configuration interprets center as the horizontal midpoint (`center_x = 0.5`), with a provisional 45%-55% band. Keep the existing standing platform rather than trying to reach the geometric vertical midpoint. Actual platform geometry and the center tolerance will be verified from session screenshots.

When left of the band, offer right movement and, if S is ready, right teleport. When right of the band, offer the corresponding left actions. Do not offer vertical teleport, portal interaction, or map changes for this milestone. Release conflicting held arrows before changing direction. Once centered, release held arrows before activating skills so the character does not drift away.

Key-down in the current direction may be selected again to renew its lease; the future executor must treat renewal as idempotent rather than toggle the key. No movement or input is actually performed by the current policy.

## Skills at the center

- Use the ready configured action with the lowest numeric priority. The sample assigns 1=0, E=10, W=20, Q=30, D=40; equal-priority actions go to JEV together.
- All activations use one profile list; there is no attack/buff distinction in selection. Natural-language usage accompanies each action in JEV inputs.
- Greyed-out E/W icons in the bottom-right HUD mean unavailable. Skip them and consider the next attack; do not press all four together.
- After activation, track pending effects and update readiness from fresh HUD evidence. Do not reuse an old ready flag or blindly assume a cooldown duration.
- If no skill is ready, wait for a new frame. If minimap position or readiness is unknown, obtain more evidence rather than invent state.

The priorities are configurable. The user confirms Q/D have cooldowns; neither is always ready. Exact durations, icons, costs, and animation constraints remain to be calibrated. The 1 action does not use a 30-minute interval. F6's separate usage strategy remains disabled until milestone 2 in [TODO.md](../docs/TODO.md).

## Rune activation — TODO

The user reports that a dark-purple/block notice indicates a rune needs activation, otherwise no experience is gained. The rune must be found on the minimap, approached from underneath, and activated. The exact notice appearance, interaction key, puzzle, and success indicators need a session test.

For now, a detected rune requirement pauses normal hunting, releases owned movement, and reports `rune_pending` for manual activation. Do not claim a successful activation or navigate to/solve a rune automatically.

See the [rune TODO](../docs/TODO.md). Normal hunting resumes only after fresh evidence confirms the requirement is cleared; re-center first if manual activation moved the character.

## Facts used by the offline policy

```text
control.gameplay_ready: true / false / unknown
minimap.player_x: normalized player X in [0, 1], or unknown
map.changed: true if the initial map has changed
rune.required: true / false / unknown
action.teleport.ready: true / false / unknown
action.<stable_id>.ready: true / false / unknown
action.<stable_id>.greyed_out: true / false / unknown
action.<stable_id>.pending: true / false / unknown
action.<stable_id>.effect_present: true / false / unknown, when configured
minimap.center_relation: left / center / right / unknown
```

Held-key state comes from the executor, not the image. These facts are currently supplied by offline examples; no minimap/HUD/rune perception adapter exists yet. `CenterHuntingPolicy` in `hunting.py` implements the objective phases and candidate rules only.

`jev_inputs.py` prepares visual questions and action choices from the active profile, with explicit unknown options and result-to-fact mappings. It does not run inference. See [input preparation](../docs/jev-inputs.md).
