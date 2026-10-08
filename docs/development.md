# Development milestones

## 0. Scaffold — current

- Package layout, machine configuration, and data contracts.
- Inspection CLI without desktop side effects.
- Rule/action templates and deployment documentation.

## 1. Game context and capture

Agree on edition, character, map, controls, and hunting goal. Record representative UU远程 frames and establish viewport geometry. Acceptance: saved frames show the correct game region and enough metadata to map coordinates and investigate stale video.

Start a recent-state buffer and collect proposed binding/timing learnings from user-performed inputs. Confirm or reject them with evidence before retrieving them into decision prompts.

## 2. Offline decisions

Implement a recorded-frame source and JEV backend. Create reviewed examples with manual game state, valid options, and expected choices. Acceptance: output probabilities match option IDs; failures are replayable; latency and model precision are measured on the Mac.

## 3. Bounded input

Implement the macOS executor with focus checks, short input durations, interruption, and input release. Acceptance: neutral/short movement commands reach the remote game and abort/release behavior works when focus or the connection changes.

Support arbitrary configured keys, modifiers, chords, and sequences. Add the one-second configurable observation scheduler and a shorter repeat cadence; test expiry and cancellation rather than assuming each inference finishes inside a tick.

## 4. Hunting loop

Add one small, verified hunting behavior first. Observe before/after, validate outcomes, and enforce retry/deadline bounds. Acceptance: recorded traces distinguish a bad choice from a failed execution, and no-progress behavior stops or recovers predictably.

Persist outcome-backed learnings to scoped SQLite records and retrieve only relevant confirmed notes. Keep contradictions, provenance, and user corrections available for review.

## 5. Expanded behavior

Add movement skills, resource management, route recovery, and map-specific behavior only after their rules and expected effects are established. Evaluate changes against recorded failures rather than assuming more prompt text improves decisions.

## Local checks for scaffold edits

This Windows workstation is for authoring only. Do not install dependencies or fetch model weights here. Standard-library checks can run directly from `src`; the following installed-CLI example is for the eventual Mac environment.

```bash
python -m compileall -q src
maple-agent doctor --config config/local.example.toml
```

Mac-only integrations must be verified on the target Mac. Passing scaffold checks on Windows does not validate Metal inference, screen capture, or UU远程 input forwarding.
