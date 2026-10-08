# JEV inputs and remaining calibration

`jev_inputs.py` prepares two stages with the MLX port's `state` and `questions` interface. It imports no MLX, downloads no weights, and dispatches no input. The Mac adapter will load the actual image and call `predict(model, processor, state, questions)`.

## Inputs already supplied

| Input | Current value |
|---|---|
| Host | M4 Max, 128 GB, macOS runtime; current workstation is authoring only |
| Game/character | China MapleStory (CMS), Kanna sample profile |
| Transport | UU远程 window on the Mac; game runs remotely |
| Objective | Stay near the center of the current map and hunt; map name is not required |
| Movement | Arrow push/release; bindings are profile-controlled |
| Teleport | S plus a direction in the sample; optional for other characters |
| Attacks | E → W → Q → D in the sample; configurable priority numbers and count |
| Readiness | Q/D have cooldowns; E/W greying means unavailable; no invented durations |
| Periodic action | 1 is used every 60 seconds after confirmed use, with ready startup use enabled; distinct F6 is disabled until milestone 2 |
| UI | Top-left minimap; bottom-right skill keys/cooldowns; bottom row of top-right buff list |
| Rune | Dark-purple/block notice; pause for manual activation while solving is TODO |
| Timing | 1000-ms observation target, shorter authorized repeats; actual latency unmeasured |

## Stage 1: visual facts

`build_perception_input()` creates choice questions for usable gameplay, rune requirement, minimap center relation, configured action readiness, configured greyed-out checks, and optional effect presence. All activations share a single profile list and their natural-language usage is included. Disabled actions and missing capabilities generate no questions. An optional expected map name adds a map-change question; the sample omits it.

Each visual question includes an `unknown` option. Metadata maps choices to fact names/values. For example:

```json
{
  "state": ["<frame/profile/session JSON>", {"image": "/local/game-frame.png"}],
  "questions": {
    "ready_0": {
      "type": "choice",
      "instructions": "Is this configured skill ready? Choose unknown if unclear.",
      "criteria": {
        "ready": "Ready to activate.",
        "unavailable": "Greyed out, on cooldown, or otherwise unavailable.",
        "unknown": "Readiness cannot be established."
      }
    }
  }
}
```

These questions are prepared, not executed. The future adapter must map returned `answers.<name>.value` through `metadata.fact_mappings`, validate probabilities, and retain unknown when the answer is uncertain or conflicts with evidence. Capture freshness, held keys, pending actions, and elapsed timers come from code, not image inference. Question probabilities are not guaranteed to be calibrated for CMS.

For periodic actions, visual questions establish only cooldown/resource readiness. Due time is computed separately from the configured interval, confirmed-use history, and monotonic elapsed time. These are separate gates; no image-derived timer is fabricated.

The minimap question produces `minimap.center_relation = left/center/right/unknown`. This avoids inventing an exact X coordinate from a categorical answer. The policy also accepts measured `minimap.player_x`; conflicting position evidence yields unknown.

## Stage 2: action selection

`build_jev_input()` includes:

- Profile ID, fingerprinted context version, character context, and objective phase.
- Frame ID/time, viewport, source window, held keys, observed facts, and explicit nulls for missing facts.
- The current screenshot reference, when available.
- Applicable rules, up to five recent outcome records, and up to eight confirmed profile-scoped learnings.
- Candidate IDs, descriptions, bindings, priority numbers, durations, and success criteria.
- A choice question whose criteria map stable action IDs to descriptions.

The policy filters candidates first: center-directed movement, owned-input release, or ready unified actions with the lowest numeric priority. Usage text accompanies every candidate. Ties go to JEV. Rune pauses and unusable/stale evidence restrict choices to release/wait/stop. The option budget is checked after filtering, not against the whole character catalog.

The output exposes `metadata.missing_facts`, `metadata.missing_context`, and `metadata.input_issues`. Missing screenshots or unverified/old remote frames cannot produce gameplay candidates. A new local capture timestamp alone does not establish a new remote frame.

### Preview without inference

Prepared examples from the incomplete observation are available as [action request](examples/jev-action-input.example.json), [perception request](examples/jev-perception-input.example.json), and [readable state](examples/jev-state.example.json). They contain no real screenshot or successful gameplay evidence. Their fixture clock matches the synthetic record; live previews also check current frame age.

```bash
maple-agent inputs --config config/local.example.toml \
  --observation game_context/observations/unknown.example.json --stage action

maple-agent inputs --config config/local.example.toml \
  --observation game_context/observations/unknown.example.json --stage perception
```

The example is deliberately unknown, stale, and has no real screenshot. Action preview offers wait/stop, demonstrating the missing-input path; it is not gameplay evidence. Actual records use a timezone-aware capture time, the true viewport, executor-owned keys, and a local screenshot path relative to the observation JSON.

`PreparedJevInput.to_predict_inputs(image_loader)` converts portable image references to the image objects expected by the selected MLX implementation. On the Mac, a loader may use `Image.open(path).convert("RGB")`. The JSON preview's metadata is for logging, not an extra model API argument.

The full sample perception preview has 12 independent questions. The selected port may perform a forward pass per question. Actual throughput must be measured on the Mac; one-second capture does not guarantee all questions finish every second. The future adapter should cache unchanged calibration and schedule only relevant fresh probes within the measured budget.

## Inputs still needed

| Missing input | How to obtain it | Why needed |
|---|---|---|
| Actual game viewport and UU window/display scale | User-session screenshot and Mac capture metadata | Crop correctly and map pixels to input points |
| Minimap bounds and player marker | Clear top-left minimap screenshot | Establish the real center band and distinguish markers |
| Skill slots and icons by stable ID | Bottom-right HUD in ready/cooldown/grey states | Identify E/W/Q/D and buff readiness without assuming durations |
| Buff 1 icon/effect | Top-right buff list before/after user activation | Verify the correct buff, distinct from F6 |
| Observed key timing and remote delay | Short user-performed inputs recorded before/after | Calibrate provisional tap/hold/teleport durations |
| Rune notice example | Screenshot when the notice appears | Reliable pause detection; activation remains deferred |
| Session completion/stop preference | User context | Decide session duration and what should stop or pause hunting |

Map name is optional and not requested for the sample. No enemy-route database, cross-map planner, login credentials, or model retraining data is required for milestone 1.
