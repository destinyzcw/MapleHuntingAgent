# Keyboard actions and scheduling

Status: requirements and contracts only; no input or scheduler implementation yet.

## Any keyboard input, finite choices per decision

The executor must support arbitrary configured physical keys, not a hardcoded list of MapleStory commands. The initial primitives are press/tap, bounded hold, release, simultaneous chord, and wait. An action may compose several primitives into an ordered sequence. Repeated actions reuse these primitives.

Key identifiers and Mac-to-remote mapping will be defined during integration. Letter keys, arrows, modifiers, function keys, and other physical keys must be representable. The executor owns translation to the selected macOS input API and UU远程 forwarding behavior.

JEV's choice interface selects among candidates; it does not generate an unrestricted keyboard program. The action provider may offer any configured key or combination, filtered by current state. The first implementation offers at most 16 candidates per call. If a task needs more, use hierarchical choices (action family, then key/variant) or deliberately enable the model's wider-choice path after evaluation.

An action definition needs a stable ID, key steps, total duration bound, repeat permission, preconditions, and success criteria. Do not assume a control binding until the user supplies or verifies it.

## Two cadences

| Setting | Default | Meaning |
|---|---:|---|
| `observation_interval_ms` | 1000 | Capture a screenshot and request a fresh decision regularly |
| `repeat_interval_ms` | 250 | Earliest interval for re-executing an approved repeatable action |
| `max_repeat_observation_age_ms` | 1500 | Stop repeats if the supporting observation becomes too old |
| `max_repeat_span_ms` | 2000 | Limit a repeat authorization window before explicit reapproval |
| `max_key_hold_ms` | 500 | Bound the duration of an individual hold step |

These are editable starting values, not measured performance claims. Cadence is a target, not a guarantee: a 27B image decision may take longer than one second. Capture uses a latest-frame buffer; outdated frames must not accumulate in a queue. Serialize JEV calls and action execution initially. Schedule by monotonic deadlines, and skip missed ticks rather than catching up with input bursts.

## Repeat semantics

A repeat means re-executing the same authorized action, not making a new model call every repeat tick. Only definitions marked repeatable qualify. Repeat authorization ends at the bounded time window, on stale evidence, new invalidating observations, focus loss, session interruption, or a conflicting new decision.

The scheduler must stop repeats while validating or replacing the action unless the action's policy explicitly permits continued execution. A new screenshot can suspend an action immediately without waiting for a slow model call. Once suspended, the scheduler must not reuse that authorization. A visually frozen remote stream must not be treated as fresh solely because captures continue.

Repeating a tap and holding a key are different. Make the intended behavior explicit; never silently turn one into the other. Only one executor owns held keys. On every stop/error path, release all keys owned by that executor.

Future faster observation for a specific action can use a separate observation override. It must remain distinct from the repeat-input interval and fit the measured capture/inference budget.
