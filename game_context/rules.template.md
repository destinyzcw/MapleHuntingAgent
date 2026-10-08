# MapleStory rules and hunting context

Context version: generic-hunting-v1

Status: user-provided game context; timing and visual calibration incomplete

## Objective

Milestone 1 stays on the current map, returns to its horizontal center band, and uses configured character actions when their usage strategies permit. Map identity is not required. Do not choose map changes. The center band, keys, priorities, capabilities, and natural-language usage are supplied by the active profile/configuration; do not assume the sample character's bindings for another profile.

## Character

The sample is China MapleStory (CMS), Kanna. Character identity comes from the active profile, which takes precedence over examples in documentation. There is no separate attack/buff classification in the profile; all activation actions share bindings, priorities, and usage strategies.

## Visual state

MapleStory is a 2D scrolling game. The top-left minimap indicates character position; use its player marker rather than the scrolling main view's center. The bottom-right action HUD shows keys/cooldowns. Effect icons are in the bottom row of the top-right buff list.

The sample Q and D actions have cooldowns. E and W may be greyed out, which means unavailable. Exact icon locations, names, resource costs, and cooldown durations are not yet calibrated. Unknown readiness is not available.

## Default strategy

For the CMS Kanna sample, 1 is periodic every 60 seconds after a confirmed application, with one ready startup use enabled by default. When it is due and ready it takes priority over E → W → Q → D; pending or cooldown-blocked input is withheld. Effect disappearance does not shorten its period. Numeric profile priorities are authoritative. F6 is a distinct maintenance action disabled until milestone 2; its schedule must not be applied to 1. Other profiles may have different keys, priorities, action counts, no effect-maintenance actions, or no teleport.

## Rune requirement

A dark-purple/block notice indicates a rune must be activated or no experience is gained, according to the user. Finding it in the minimap, approaching underneath, and activation remain in [TODO.md](../docs/TODO.md). Pause normal hunting for manual activation; do not infer that a chosen input successfully activated it.

## Execution and evidence

Recheck focus, frame freshness, pending actions, and current prerequisites before bounded input. Track expected effects independently from dispatch. Use fresh observations to resume hunting after a rune pause and to re-center after manual movement. Exact viewport geometry, input timing, and remote delay must be measured from the real session.
