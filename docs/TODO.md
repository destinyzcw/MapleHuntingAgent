# Pending gameplay work

## Milestone 2: F6 buff upkeep

Deferred by the user; do not offer or execute this action in milestone 1.

- [ ] Add F6 as a buff action after milestone 1 is working.
- [ ] Identify its buff icon in the bottom row of the top-right buff list.
- [ ] Refresh every 30 minutes after a confirmed application, or when the buff disappears.
- [ ] Track pending activation and remote-frame delay to avoid duplicate presses.
- [ ] Test F6 forwarding through UU远程 and define independent activation evidence.

The 1 action is already part of milestone 1 and is periodic every 60 seconds after confirmed use. It has a different purpose and timing strategy; do not substitute F6 or its 30-minute/effect-missing rule for 1.

## Rune activation

Status: deliberately deferred until a user-session test.

- [ ] Capture the actual rune-required dark-purple/block notice and verify the reported experience restriction.
- [ ] Detect the rune marker on the minimap and distinguish it from the player and other markers.
- [ ] Define movement to the position underneath the rune, including platform/vertical traversal.
- [ ] Test the actual interaction key and whether it opens an activation challenge.
- [ ] Identify and test the challenge inputs, timing, and ordering.
- [ ] Define independent success evidence: cleared notice, rune effect, restored experience gain, or verified HUD state.
- [ ] Define timeout/cancellation and recovery when activation is interrupted or fails.
- [ ] Resume the single-map center policy from fresh observations after activation.

Until implemented, the `rune_pending` phase withholds normal movement, attack, and buff candidates, offers owned-key release/wait/stop, and requires manual activation. It must not fabricate activation completion from a chosen command.
