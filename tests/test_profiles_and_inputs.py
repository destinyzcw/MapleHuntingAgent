"""Dependency-free configuration/input checks; no inference or desktop activity."""

from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import io
import contextlib
import json
from pathlib import Path
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from maple_hunting_agent.cli import main
from maple_hunting_agent.domain import LearningRecord, LearningStatus, Observation, Viewport
from maple_hunting_agent.hunting import CenterHuntingPolicy
from maple_hunting_agent.jev_inputs import build_jev_input, build_perception_input
from maple_hunting_agent.profiles import compile_character_profile, load_character_profile


class ProfileAndInputChecks(unittest.TestCase):
    def setUp(self):
        self.data = tomllib.loads((ROOT / "config/characters/default.toml").read_text(encoding="utf-8"))
        self.catalog = compile_character_profile(self.data, max_key_hold_ms=500)
        self.now = datetime(2026, 10, 8, tzinfo=timezone.utc)
        self.base = {"control.gameplay_ready": True, "rune.required": False, "minimap.player_x": 0.5, "remote.frame_fresh": True}

    def observation(self, facts=None, held=(), image=None):
        return Observation("synthetic-input-check", self.now, image, Viewport(0, 0, 1, 1), "synthetic-window", {**self.base, **(facts or {})}, held)

    def choices(self, observation, catalog=None, max_options=16):
        policy = CenterHuntingPolicy(catalog or self.catalog, max_options=max_options)
        return policy.available(observation, policy.current(observation))

    def test_default_priorities_grey_override_and_pending(self):
        ready = {f"action.{name}.ready": True for name in ("attack_e", "attack_w", "attack_q", "attack_d", "buff_1")}
        self.assertEqual(self.choices(self.observation(ready))[0].action_id, "buff_1")
        ready["action.buff_1.pending"] = True
        self.assertEqual(self.choices(self.observation(ready))[0].action_id, "attack_e")
        ready["action.attack_e.greyed_out"] = True
        self.assertEqual(self.choices(self.observation(ready))[0].action_id, "attack_w")
        ready["action.attack_w.greyed_out"] = True
        self.assertEqual(self.choices(self.observation(ready))[0].action_id, "attack_q")
        ready["action.attack_q.ready"] = None
        self.assertEqual(self.choices(self.observation(ready))[0].action_id, "attack_d")

    def test_priorities_and_bindings_are_configuration(self):
        changed = deepcopy(self.data)
        for action in changed["actions"]:
            if action["id"] == "attack_q":
                action.update(keys=["r"], priority=0)
            elif action["id"] == "buff_1":
                action["priority"] = 100
        catalog = compile_character_profile(changed, max_key_hold_ms=500)
        selected = self.choices(self.observation({"action.attack_q.ready": True, "action.buff_1.ready": True}), catalog)[0]
        self.assertEqual(selected.action_id, "attack_q")
        self.assertEqual(selected.keyboard_steps[0].keys, ("r",))
        self.assertNotEqual(catalog.context_version, self.catalog.context_version)

    def test_optional_capabilities_and_variable_count(self):
        minimal = load_character_profile(ROOT / "config/characters/minimal.example.toml", max_key_hold_ms=500)
        self.assertEqual(sum(a.category == "skill" for a in minimal.actions), 1)
        self.assertFalse(any(a.category == "teleport" for a in minimal.actions))
        changed = {"schema_version": 1, "id": "many", "context_version": "v1", "actions": [
            {"id": f"option_{i}", "keys": ["x"], "priority": i, "usage": "Use when ready."} for i in range(25)
        ]}
        catalog = compile_character_profile(changed, max_key_hold_ms=500)
        self.assertEqual(sum(a.category == "skill" for a in catalog.actions), 25)
        self.assertEqual(self.choices(self.observation({"action.option_24.ready": True}), catalog)[0].action_id, "option_24")
        changed["actions"] = []
        empty = compile_character_profile(changed, max_key_hold_ms=500)
        self.assertEqual({a.action_id for a in self.choices(self.observation(), empty)}, {"wait", "stop"})

    def test_ties_go_to_jev_but_option_overflow_is_not_silent(self):
        data = {"schema_version": 1, "id": "ties", "context_version": "v1", "actions": [
            {"id": f"tie_{i}", "keys": ["x"], "priority": 10, "usage": "Use when ready."} for i in range(3)
        ]}
        catalog = compile_character_profile(data, max_key_hold_ms=500)
        observation = self.observation({f"action.tie_{i}.ready": True for i in range(3)})
        self.assertEqual(len(self.choices(observation, catalog)), 4)
        with self.assertRaises(ValueError):
            self.choices(observation, catalog, max_options=3)

    def test_remapped_movement_and_no_teleport(self):
        data = deepcopy(self.data)
        data["movement"]["bindings"] = {"left": "h", "right": "l", "up": "k", "down": "j"}
        data["teleport"] = {"enabled": False}
        catalog = compile_character_profile(data, max_key_hold_ms=500)
        selected = self.choices(self.observation({"minimap.player_x": 0.1}), catalog)[0]
        self.assertEqual(selected.keyboard_steps[-1].keys, ("l",))
        renewed = self.choices(self.observation({"minimap.player_x": 0.1}, ("l",)), catalog)[0]
        self.assertEqual(renewed.action_id, "move_right_down")
        centered = self.choices(self.observation(held=("l",)), catalog)[0]
        self.assertEqual(centered.action_id, "move_right_up")

    def test_generic_refresh_strategy_and_disabled_default(self):
        self.assertFalse(any(a.action_id == "buff_f6" for a in self.catalog.actions))
        data = deepcopy(self.data)
        maintenance = next(a for a in data["actions"] if a["id"] == "buff_f6")
        maintenance["enabled"] = True
        catalog = compile_character_profile(data, max_key_hold_ms=500)
        self.assertNotIn("buff_f6", {a.action_id for a in self.choices(self.observation(), catalog)})
        elapsed = self.observation({"action.buff_f6.effect_present": True, "action.buff_f6.elapsed_since_confirmed_ms": 1800000})
        self.assertEqual(self.choices(elapsed, catalog)[0].action_id, "buff_f6")
        disappeared = self.observation({"action.buff_f6.effect_present": False})
        self.assertEqual(self.choices(disappeared, catalog)[0].action_id, "buff_f6")
        pending = self.observation({"action.buff_f6.effect_present": False, "action.buff_f6.pending": True})
        self.assertNotIn("buff_f6", {a.action_id for a in self.choices(pending, catalog)})

    def test_invalid_profiles_fail(self):
        for mutate in (
            lambda d: d["actions"][0].update(priority=True),
            lambda d: d["actions"][0].update(press_ms=501),
            lambda d: d["actions"].append(deepcopy(d["actions"][0])),
            lambda d: d.update(buffs=[]),
        ):
            data = deepcopy(self.data)
            mutate(data)
            with self.assertRaises(ValueError):
                compile_character_profile(data, max_key_hold_ms=500)

    def test_natural_usage_and_memory_are_in_action_inputs(self):
        with tempfile.TemporaryDirectory() as folder:
            image = Path(folder) / "fixture.png"
            image.write_bytes(b"synthetic file-existence fixture; not decoded or used for vision")
            observation = self.observation({"action.attack_e.ready": True}, image=image)
            matching = LearningRecord("verified", {"profile_id": self.catalog.profile_id, "context_version": self.catalog.context_version}, "Verified timing note.", LearningStatus.CONFIRMED, ("run/frame",), self.now)
            wrong = replace(matching, learning_id="other", scope={"profile_id": "other", "context_version": "other"})
            proposed = replace(matching, learning_id="unverified", status=LearningStatus.PROPOSED)
            packet = build_jev_input(observation, self.catalog, CenterHuntingPolicy(self.catalog), "Use the active profile.", learnings=(matching, wrong, proposed), now=self.now)
            self.assertEqual(packet.metadata["candidate_ids"], ["attack_e", "stop"])
            self.assertIn("cooldown", packet.questions["action"]["criteria"]["attack_e"])
            body = json.loads(packet.state[0])
            self.assertEqual(body["session"]["game"]["character_class"], "Kanna")
            self.assertEqual([entry["id"] for entry in body["confirmed_learnings"]], ["verified"])
            state, _ = packet.to_predict_inputs(lambda path: ("image-object-placeholder", path.name))
            self.assertEqual(state[-1], ("image-object-placeholder", "fixture.png"))
            stale = build_jev_input(observation, self.catalog, CenterHuntingPolicy(self.catalog), "", now=self.now + timedelta(seconds=3))
            self.assertEqual(set(stale.metadata["candidate_ids"]), {"wait", "stop"})

    def test_perception_questions_and_unknown_fallback(self):
        observation = self.observation()
        packet = build_perception_input(observation, self.catalog, now=self.now)
        facts = {entry["fact"] for entry in packet.metadata["fact_mappings"].values()}
        self.assertIn("action.attack_q.ready", facts)
        self.assertIn("action.attack_e.greyed_out", facts)
        self.assertIn("action.buff_1.effect_present", facts)
        self.assertNotIn("action.buff_f6.effect_present", facts)
        self.assertNotIn("map.changed", facts)
        self.assertTrue(all("unknown" in question["criteria"] for question in packet.questions.values()))
        fallback = build_jev_input(observation, self.catalog, CenterHuntingPolicy(self.catalog), "", now=self.now)
        self.assertEqual(set(fallback.metadata["candidate_ids"]), {"wait", "stop"})

    def test_categorical_position_without_invented_coordinates(self):
        observation = self.observation({"minimap.player_x": None, "minimap.center_relation": "left"})
        self.assertEqual(self.choices(observation)[0].action_id, "move_right_down")
        conflicting = self.observation({"minimap.player_x": 0.9, "minimap.center_relation": "left"})
        self.assertEqual({a.action_id for a in self.choices(conflicting)}, {"wait", "stop"})
        self.assertEqual(CenterHuntingPolicy(self.catalog).current(self.observation({"minimap.player_x": 0.55})).phase, "hunt")

    def test_cli_previews_no_dependencies(self):
        config = str(ROOT / "config/local.example.toml")
        record = str(ROOT / "game_context/observations/unknown.example.json")
        for args in (["doctor", "--config", config], ["actions", "--config", config], ["inputs", "--config", config, "--observation", record], ["inputs", "--config", config, "--observation", record, "--stage", "perception"]):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(main(args), 0)
            self.assertIsInstance(json.loads(output.getvalue()), dict)


if __name__ == "__main__":
    unittest.main()
