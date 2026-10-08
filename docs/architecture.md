# Architecture

## Deployment boundary

The Mac hosts capture, perception, context construction, JEV, input execution, and trace storage. UU远程 transports the remote game's display and the Mac's input. There is no remote game API or game-memory integration in this design.

## Components

| Component | Responsibility | Initial implementation |
|---|---|---|
| Capture source | Obtain timestamped frames and viewport geometry | Recorded images, followed by macOS window capture |
| Perception | Extract decision-relevant facts and retain uncertainty | Manual state/replay baseline, followed by visual/OCR extraction |
| Action provider | Offer valid, bounded actions for the current state | Authored rules; never ask the model to invent commands |
| Objective provider | Maintain a goal/phase across decisions, refreshing at milestones | User-authored objective and phase rules first; a planner is optional |
| Decision backend | Return probabilities aligned with supplied action IDs | JEV MLX System 1 |
| Executor | Map an approved action to local input and report dispatch | Recording executor, followed by macOS UU远程 input |
| Result validator | Compare fresh evidence with explicit success criteria | Deterministic checks where possible; JEV for ambiguous judgments |
| Orchestrator | Own sequencing, deadlines, retry limits, and shutdown | Implemented after recording and offline decisions work |
| Trace writer | Store observations, choices, execution, and outcome | Local JSONL plus referenced images |
| Learning memory | Record evidence-backed lessons and retrieve relevant context | Local SQLite plus a bounded recent-state buffer |

Interfaces live in `contracts.py`, and the records they exchange live in `domain.py`. Adapter status is explicit: this scaffold has no working capture or executor.

The split follows [lessons from JEV Minecraft](minecraft-lessons.md): objective changes and candidate filtering belong outside the choice model. A recent failure may alter candidates without asking a planner to rewrite the whole goal.

## Loop sequencing

1. Capture a fresh frame and inspect connection/window state.
2. Build observed facts, retaining unknown values rather than guessing them.
3. Construct available actions from rules and the active objective.
4. Ask JEV to select among those actions.
5. Check action membership, frame freshness, focus, and execution mode.
6. Execute one bounded action. Do not overlap decision/execution cycles initially.
7. Wait for an observable effect and a newer remote frame.
8. Validate execution, immediate effect, and goal progress separately.
9. Continue, retry within a bound, recover, or stop; append evidence at every step.

Reconsider the objective on a completed milestone, map/phase transition, repeated failures, no useful candidates, or an elapsed review deadline. Include a short recent action/result history in the next decision. Recheck the selected action against current prerequisites immediately before execution, since inference may outlast the observation interval.

There is no implementation of this loop yet. An executor acknowledgement proves dispatch, not that MapleStory received the input or that the chosen action was good.

The normal observation/decision cadence is configurable and defaults to one second. Authorized repeatable actions can execute at a shorter cadence between observations; they expire and are canceled by invalidating evidence. See [keyboard actions and scheduling](actions-and-scheduling.md). The executor supports arbitrary configured keys/chords/sequences; the action provider still presents a finite candidate list to JEV.

Confirmed lessons from initial observation and later outcomes become scoped prompt context. They do not update model weights. See [persistent learning memory](memory.md).

## Modes

Planned modes are `observe`, `replay`, and `live`. Only `observe` configuration is accepted by the scaffold. In replay, recorded decisions have no desktop side effects. Live mode will require working focus detection, viewport mapping, deadlines, input release, and user interruption before it is exposed.

## Decision runtime

Keep JEV loaded for a whole session and serialize calls initially. Use System 1 for action probabilities. Any future reasoning/escalation path must explicitly account for the selected MLX conversion's capabilities: the recommended nativ build has a merged System 1 adapter and does not preserve the untouched System 2 path.
