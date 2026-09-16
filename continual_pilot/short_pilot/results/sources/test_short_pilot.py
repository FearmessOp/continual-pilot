"""Short-pilot decision tests; synthetic outcomes are not experimental evidence."""
import copy
import unittest

from asymmetric_pilot.engine import CONFIG as BASE_CONFIG
from short_pilot.run import CONFIG, decide


def make_rows(short_damage=0.30, long_damage=0.35, baseline=0.88):
    return [
        {
            "seed": seed,
            "method": "A",
            "phase3_count": length,
            "frozen": {"2": {"r1_accuracy": baseline}},
            "damage": damage,
        }
        for seed in CONFIG["stream_seeds"]
        for length, damage in ((1024, short_damage), (1536, long_damage))
    ]


class ShortPilotTests(unittest.TestCase):
    def test_configuration_is_separate_and_aligned(self):
        self.assertEqual(BASE_CONFIG["phase3_candidates"], [2000, 4000])
        self.assertEqual(BASE_CONFIG["minimum_phase2_accuracy"], 0.80)
        self.assertEqual(CONFIG["phase3_candidates"], [1024, 1536])
        self.assertEqual(CONFIG["stream_seeds"], [240001, 240002, 240003])
        self.assertEqual(CONFIG["minimum_phase2_accuracy"], 0.86)
        self.assertEqual(CONFIG["evaluation_seed"], 249001)
        self.assertEqual(
            [n // CONFIG["minibatch"] for n in CONFIG["phase3_candidates"]],
            [64, 96])
        for key in ("phase1_count", "phase2_count", "phase4_count",
                    "model_seed", "lr", "capacity", "replay_per_new_example"):
            self.assertEqual(CONFIG[key], BASE_CONFIG[key])
        self.assertEqual(CONFIG["window_updates"] * CONFIG["minibatch"], 480)

    def test_shortest_eligible_and_closed_boundaries(self):
        result = decide(make_rows(0.20, 0.40, baseline=0.86), CONFIG)
        self.assertEqual(result["status"], "selected")
        self.assertEqual(result["eligible_candidates"], [1024, 1536])
        self.assertEqual(result["selected_phase3_count"], 1024)
        self.assertIsNone(result["suggested_future_candidate"])

    def test_long_selected_if_short_fails_one_seed(self):
        rows = make_rows()
        rows[0]["damage"] = 0.19
        self.assertEqual(decide(rows, CONFIG)["selected_phase3_count"], 1536)

    def test_baseline_failure_overrides_all_other_branches(self):
        for damages in ((0.10, 0.15), (0.30, 0.35), (0.41, 0.50)):
            rows = make_rows(*damages)
            for row in rows:
                if row["seed"] == 240003:
                    row["frozen"]["2"]["r1_accuracy"] = 0.85995
            result = decide(rows, CONFIG)
            self.assertEqual(result["status"], "phase2_control_failed")
            self.assertEqual(result["eligible_candidates"], [])
            self.assertIsNone(result["selected_phase3_count"])
            self.assertIsNone(result["suggested_future_candidate"])

    def test_below_and_above_suggest_but_never_execute(self):
        for damages, status, candidate in (
                ((0.10, 0.19), "all_below_band", 1792),
                ((0.40005, 0.50), "all_above_band", 768)):
            result = decide(make_rows(*damages), CONFIG)
            self.assertEqual(result["status"], status)
            self.assertEqual(result["suggested_future_candidate"], candidate)
            self.assertFalse(result["future_candidate_executed"])
            self.assertIsNone(result["selected_phase3_count"])

    def test_mixed_results_have_no_automatic_suggestion(self):
        result = decide(make_rows(0.19, 0.41), CONFIG)
        self.assertEqual(result["status"], "mixed_no_selection")
        self.assertIsNone(result["suggested_future_candidate"])
        rows = make_rows(0.10, 0.15)
        rows[0]["damage"] = 0.20
        self.assertEqual(decide(rows, CONFIG)["status"], "mixed_no_selection")

    def test_replay_does_not_determine_selection_or_mutate_inputs(self):
        rows = make_rows()
        replay = copy.deepcopy(rows)
        for row in replay:
            row["method"] = "replay"
            row["damage"] = 0.01
        combined = rows + replay
        before = copy.deepcopy(combined)
        self.assertEqual(decide(combined, CONFIG), decide(rows, CONFIG))
        self.assertEqual(combined, before)

    def test_incomplete_duplicate_unexpected_and_nonfinite_rows_fail(self):
        rows = make_rows()
        invalid_cases = [rows[:-1], rows + [copy.deepcopy(rows[0])]]
        wrong_seed = copy.deepcopy(rows)
        wrong_seed[0]["seed"] = 999
        invalid_cases.append(wrong_seed)
        for field in ("damage", "baseline"):
            for value in (float("nan"), float("inf"), 2.0):
                invalid = copy.deepcopy(rows)
                if field == "damage":
                    invalid[0]["damage"] = value
                else:
                    invalid[0]["frozen"]["2"]["r1_accuracy"] = value
                invalid_cases.append(invalid)
        for invalid in invalid_cases:
            with self.assertRaises(ValueError):
                decide(invalid, CONFIG)

    def test_candidates_must_have_identical_phase2_reference(self):
        rows = make_rows()
        rows[0]["frozen"]["2"]["r1_accuracy"] = 0.89
        with self.assertRaisesRegex(ValueError, "share their phase-2"):
            decide(rows, CONFIG)


if __name__ == "__main__":
    unittest.main()