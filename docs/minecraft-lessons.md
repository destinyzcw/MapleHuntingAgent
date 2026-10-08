# Lessons from JEV Minecraft projects

Reviewed on 2026-10-08. These are architectural adaptations from inspected source, not copied implementations or proof of MapleStory performance.

## Sources inspected

| Project | Pinned source | Relevant behavior |
|---|---|---|
| rmalde/minecraft-agent | [models.mjs](https://github.com/rmalde/minecraft-agent/blob/78b40ed59514e5e2abde33a05ce398ecb2c39e05/models.mjs) | Compacts observation/history, validates the selected action, separates planning from JEV choice |
| rmalde/minecraft-agent | [nether-agent.mjs](https://github.com/rmalde/minecraft-agent/blob/78b40ed59514e5e2abde33a05ce398ecb2c39e05/nether-agent.mjs) | Bounded execution, failed-action suppression, stage tracking, action/result events |
| rmalde/minecraft-agent | [optimization/policy.mjs](https://github.com/rmalde/minecraft-agent/blob/78b40ed59514e5e2abde33a05ce398ecb2c39e05/optimization/policy.mjs) | Replanning triggers, failure cooldowns, completed-waypoint removal, useful-action filtering |
| teknium1/hermes-and-jev-play-minecraft | [controller.mjs](https://github.com/teknium1/hermes-and-jev-play-minecraft/blob/440bec09ee76523a706510601efcbda57df030ad/controller.mjs) | Bounded controller loop, milestone objectives, small recent history, decision records |
| teknium1/hermes-and-jev-play-minecraft | [harness.mjs](https://github.com/teknium1/hermes-and-jev-play-minecraft/blob/440bec09ee76523a706510601efcbda57df030ad/harness.mjs) | Code owns candidate validity, busy state, execution feedback, and completed-target filtering |

The original project's snapshot has no stated code license; this project uses independently authored interfaces and documentation. No source implementation is imported.

## Patterns to adopt

### Code offers valid actions; JEV chooses among them

The Minecraft harness removes mining when inventory targets are met and excludes waiting when useful actions exist. Its reproduction notes report that action filtering resolved over-mining and unnecessary waiting.

For MapleStory, offer any configured keyboard input through bounded definitions, but check prerequisites first: visible target, movement route, resource estimate, known cooldown, menu state, and session focus. A completed objective or temporarily failed action should stop being offered. Unknown prerequisites must be represented explicitly; do not turn uncertain visual estimates into facts.

Waiting remains a legitimate MapleStory option while a skill animation, remote frame update, result check, or cooldown is pending. We will not blindly copy Minecraft's wait suppression.

### Objectives last longer than individual decisions

Minecraft uses a planner to maintain an objective and refreshes it on milestones, stage changes, repeated failures, or a periodic deadline. It does not ask a large planner to reconsider everything on every action.

Start MapleStory with user-authored objectives and a small phase controller. Candidate phases might be approaching a target area, attacking, repositioning, and recovering, but their transitions remain unverified until game context is supplied. A future planner is optional and must be a separate backend. The selected nativ JEV build is a System 1 decision model; it cannot be assumed to supply a pristine System 2 planner.

### Commands own execution details

Minecraft's selected action delegates navigation/timing to Mineflayer and local code. The model chooses a bounded intent rather than sending arbitrary executable code.

Our executor will similarly own key translation, holds, releases, chords, ordered sequences, and repeat timing. JEV chooses an action ID. Any key may be configured, but a finite choice call cannot invent an unrestricted program. Unknown bindings require context or a learning experiment first.

### Failures change the next option set

The original project tracks failures and applies action-specific cooldowns. The harness reports busy status and rejects unknown commands.

Track execution failures separately from unfavorable game outcomes and missing evidence. Temporarily withhold a confirmed failed action, refresh observations, and change objective or recover after repeated lack of progress. Do not mark delayed remote video as action failure prematurely. Every retry needs a limit.

### Keep history small and evidence complete

Minecraft supplies a short recent action/result history to the model while retaining full local events. Adopt the same split: a compact recent-state buffer and scoped confirmed learnings in prompts, plus full frame-linked run traces for review.

Do not equate model self-validation with objective evidence. Track dispatch, visible execution, effect, and goal progress separately.

## Differences we must account for

| Minecraft reference | MapleHuntingAgent |
|---|---|
| Structured coordinates, inventory, entity state | Screenshot-derived estimates with possible OCR/perception errors |
| Mineflayer pathfinding and protocol interactions | Local Mac input forwarded through UU远程 |
| Hosted TypeSafe Jev, around 0.2 s in reported runs | Local JEV-27B-VL MLX; actual image latency must be measured |
| Longer bounded actions managed by code | One-second observations plus shorter expiring repeat windows |
| Known route/seed in reported dragon run | Map layout and hunting strategy supplied/learned for our session |
| Direct game completion events | Visual or otherwise independently observed outcome criteria |

The strategic decomposition is useful, but MapleStory perception and remote transport are new sources of uncertainty. The Minecraft result does not establish that local image inference can complete every one-second tick.

## How this changes the implementation plan

1. Record frames and manual state before wiring a live executor.
2. Add a persistent objective/phase record and evidence-linked recent outcomes.
3. Build valid-action selection and failure cooldowns independently of the JEV adapter.
4. Measure local JEV latency and remote input delay before tuning repeat authorization.
5. Learn verified bindings/timing/ranges from initial experiments and persist scoped memory.
6. Run a small hunting loop with explicit progress checks before expanding behavior.
