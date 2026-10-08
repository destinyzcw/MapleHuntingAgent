# Game context

This directory holds game context and input examples. The sample is China MapleStory (CMS), Kanna. Its controls are configured in one [action profile](../config/characters/README.md). Map name is optional; exact timing and UI geometry remain unverified.

The model will receive relevant rules, the current objective, observed state, and only the actions currently available. Do not rely on general game knowledge for edition-specific mechanics.

## Information to establish together

| Topic | Needed information |
|---|---|
| Game | Edition/region/server and client language |
| Character | Class, level, movement skills, attack range, HP/MP behavior |
| Hunting map | Platforms, ladders, portals, spawn areas, preferred hunting route |
| Controls | Actual movement, attack, jump, skill, potion, and interaction bindings |
| Repeats | Which inputs are tapped, held, or repeated, and their timing limits |
| Goal | Target enemies, experience/item goals, session duration, acceptable recovery behavior |
| Visual state | Player position, enemies, HP/MP, cooldowns, death state, menus, disconnection |
| Remote session | UU远程 window mode, viewport scaling, latency, keyboard mapping |
| Outcome | What visibly proves each action worked, and how long its effect takes |

The executor will support any configured keyboard input, not only the controls listed above. Learning from initial observations is recorded in local persistent memory; confirmed rules can later be promoted to these authored files.

## Files

- `rules.template.md`: human-readable, versioned context. Unknown facts stay unknown.
- `actions.md`: unified action semantics, default sample, and links to editable profiles.
- `hunting.md`: milestone-1 single-map center objective, minimap/HUD facts, attack priority, and deferred rune activation.
- `session.example.json`: known UI hints and null calibration fields; character identity is overlaid from the active profile.
- `observations/unknown.example.json`: deliberately incomplete input for CLI previews, not a real capture.
- `actions.example.json`: action schema example. Only wait/stop definitions are present; no key bindings or combat actions exist yet.

Screenshots belong in `data/captures/`, not in rule files. Link observations to their frame IDs when reviewing failures. Avoid including account details or credentials in committed examples.
