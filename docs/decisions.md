# Decisions and result validation

## Decision input

Each request contains an objective, relevant verified rules, an observation ID, observed facts with unknown values retained, a screenshot or frame sequence, and an available-action list. Each option has a stable ID plus a concise description that explains when to use it.

The initial action budget is at most 16 options, matching JEV's trained choice slots. This is a project simplification, not JEV's overall API limit. Action validity belongs to code/context rules; JEV ranks the valid candidates.

## Decision output

Return the selected action ID and a finite, normalized probability distribution aligned with the request's IDs. Validate the complete option set before execution. Confidence is evidence for routing, not proof of correctness or a game win probability. Do not copy calibration guarantees from a benchmark into MapleStory.

## Result checks

After a bounded action, capture new evidence and ask a specific question:

| Check | Example, once game mechanics are verified |
|---|---|
| Dispatch/execution | Was the selected skill visibly activated? |
| Immediate effect | Did the player reach the intended platform or did an enemy's health decrease? |
| Goal progress | Is the hunting route progressing without an unresolved obstacle? |

Prefer deterministic state checks when reliable measurements exist. A JEV validation question may choose `success`, `failure`, or `not_yet_observable`. Its record must reference before/after observations and an explicit success criterion. Do not retry a potion or skill merely because the remote video has not updated yet.

## Failure diagnosis

Store enough evidence to replay the exact request. Compare screenshot input with manually verified text state, then vary rules, history, option order, and precision one at a time. A later natural-language explanation is not a trace of System 1's internal computation.

Track causes separately: perception, missing rules/history, action selection, stale frame, remote focus/transport, executor, outcome validation, and unknown. A choice and its validator can share the same error; external state checks are the stronger confirmation.

## Trace events

Planned JSONL events: `observation`, `perception`, `available_actions`, `decision`, `execution_started`, `execution_finished`, `validation`, `recovery`, and `session_stopped`. Include session/step IDs, timestamps, model/runtime versions, context version, action probabilities, durations, and referenced frame paths. Store no credentials in traces.
