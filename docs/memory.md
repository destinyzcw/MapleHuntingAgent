# Persistent learning memory

Status: design and record contracts only. SQLite storage and retrieval are not implemented yet.

## What learning means here

JEV's weights remain fixed during an initial session. Learning means collecting evidence, recording confirmed rules/observations, and retrieving relevant notes into future decision requests. This is persistent context memory, not online model training. Any future fine-tuning would be a separate dataset and training workflow.

## Memory layers

| Layer | Examples | Lifetime |
|---|---|---|
| Recent state | Latest frames, current action, before/after state, validation still pending | Bounded session buffer |
| Episodic records | A key press, its observed effect, failure, recovery, and latency | Session trace with screenshot references |
| Learned rules | A verified binding, skill range, timing estimate, map traversal behavior, recurring obstacle | Persistent, scoped SQLite records |

Scope rules to edition, character/class, hunting map, control-profile version, and remote viewport/session profile. A rule learned for one map or key layout must not silently apply to another.

## Initial learning process

1. Establish manual context and record representative observations.
2. Observe user-performed inputs or later run one approved bounded experiment.
3. Compare the expected result with actual fresh observations.
4. Record a proposed learning with evidence references and uncertainty.
5. Promote it to confirmed only after user review or repeated externally verified outcomes, according to the learning policy we define together.
6. Retrieve a small relevant set into later prompts; retain contrary evidence and expire outdated rules.

Do not store JEV's own assertion as confirmed merely because JEV agrees with itself. Store observed effects separately from the model's interpretation. Success/contradiction counts and verification provenance are more useful than an unsupported confidence number.

## Storage

Use the standard-library SQLite driver for the eventual local adapter. The example path is `data/memory/learnings.sqlite3`, ignored by Git. Keep raw events in `data/runs/`; memory records reference run/frame IDs instead of duplicating images. Authored game rules remain versioned files in `game_context/`.

Initial retrieval can filter by scope and keywords without another embedding model. Add semantic retrieval only if examples show it improves decisions. Set a prompt budget so old notes do not overwhelm current observations.

## Inspection and correction

Provide future list/show/confirm/reject/export commands and record revisions. A corrected binding or disproven tactic must stop being retrieved. Export reviewed episodes separately if we later build a training dataset; raw memory is not automatically training data.
