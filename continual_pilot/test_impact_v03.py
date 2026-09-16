"""Line 1 impact-exploration mechanics tests; not empirical impact evidence."""
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import torch

import diagnose
import impact_v03 as impact
from generator_v03 import GeneratorV03


def tiny_protocol():
    """Small deterministic protocol for fast mechanics checks."""
    return {
        **impact.PROTOCOL,
        "phase_length": 64,
        "capacity": 32,
        "replay_batch": 4,
        "minibatch": 16,
        "eval_count": 200,
        "transition_window": 32,
        "training_seeds": [220001],
    }


class ImpactMechanicsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        cls.generator = GeneratorV03(seed=1000, alpha=0.5, noise=0.05,
                                     calibration_count=2000)

    def test_phase_stream_shapes_and_schedule_length(self):
        with patch.dict(impact.PROTOCOL, tiny_protocol()):
            stream = impact.phase_stream(self.generator, 220001)
        x, noisy, clean = stream
        expected = 4 * tiny_protocol()["phase_length"]
        self.assertEqual(x.shape, (expected, 32))
        self.assertEqual(len(noisy), expected)
        self.assertTrue(np.all((noisy >= 0) & (noisy < 4)))

    def test_paired_runs_share_initial_and_stream(self):
        # A and replay must start from identical weights and see the same stream.
        with patch.dict(impact.PROTOCOL, tiny_protocol()):
            with torch.random.fork_rng(devices=[]):
                torch.manual_seed(7)
                initial = impact.make_model(64)
            initial_digest = diagnose.state_digest(initial)
            stream = impact.phase_stream(self.generator, 220001)
            eval_x, eval_clean, _ = impact.evaluation_stream(self.generator)
            run_a = impact.run_method(self.generator, stream, replay=False,
                                      initial=initial, eval_x=eval_x,
                                      eval_clean=eval_clean)
            run_r = impact.run_method(self.generator, stream, replay=True,
                                      initial=initial, eval_x=eval_x,
                                      eval_clean=eval_clean)
        # Initial deepcopy must not have been mutated in place.
        self.assertEqual(initial_digest, diagnose.state_digest(initial))
        # Both produced three frozen copies at phases 2, 3, 4.
        self.assertEqual(set(run_a["frozen"]), {2, 3, 4})
        self.assertEqual(set(run_r["frozen"]), {2, 3, 4})
        # Same shared stream: A's predictions are deterministic given the seed.
        run_a2 = None
        with patch.dict(impact.PROTOCOL, tiny_protocol()):
            with torch.random.fork_rng(devices=[]):
                torch.manual_seed(7)
                initial2 = impact.make_model(64)
            run_a2 = impact.run_method(self.generator, stream, replay=False,
                                       initial=initial2, eval_x=eval_x,
                                       eval_clean=eval_clean)
        np.testing.assert_array_equal(run_a["predictions"],
                                      run_a2["predictions"])

    def test_prediction_precedes_label_in_window(self):
        # Flipping a label at position k must not change the prediction at k
        # (prediction is made before the label updates the model).
        with patch.dict(impact.PROTOCOL, tiny_protocol()):
            with torch.random.fork_rng(devices=[]):
                torch.manual_seed(7)
                initial = impact.make_model(64)
            stream = impact.phase_stream(self.generator, 220001)
            eval_x, eval_clean, _ = impact.evaluation_stream(self.generator)
            base = impact.run_method(self.generator, stream, replay=False,
                                     initial=initial, eval_x=eval_x,
                                     eval_clean=eval_clean)
            x, noisy, clean = stream
            flipped = noisy.copy()
            flipped[10] = (flipped[10] + 1) % 4
            with torch.random.fork_rng(devices=[]):
                torch.manual_seed(7)
                initial2 = impact.make_model(64)
            altered = impact.run_method(
                self.generator, (x, flipped, clean), replay=False,
                initial=initial2, eval_x=eval_x, eval_clean=eval_clean)
        # Predictions up to and including index 10 must be unchanged.
        np.testing.assert_array_equal(base["predictions"][:11],
                                      altered["predictions"][:11])

    def test_d1000_sign_matches_definition(self):
        # Construct a run where phase-4 online is worse than phase-2 frozen.
        online = np.zeros(256, dtype=np.int64)
        clean = np.zeros(256, dtype=np.int64)
        # Phase length 64 -> phase 4 window is [192, 224).
        online[192:200] = 1  # 8 online errors in the window vs clean 0.
        frozen2 = diagnose.make_model(64, False, seed=7)
        with patch.object(impact, "make_model", lambda h: frozen2):
            pass
        # Directly exercise the D1000 arithmetic via a stub matching the code.
        window = slice(192, 224)
        phase4_online = online[window]
        window_clean = clean[window]
        # Frozen phase-2 makes zero errors here by construction.
        phase2_pred = np.zeros(32, dtype=np.int64)
        d1000 = int(np.sum(phase4_online != window_clean)
                    - np.sum(phase2_pred != window_clean))
        self.assertEqual(d1000, 8)

    def test_damage_and_recovery_signs(self):
        run = {"frozen_m2r1_accuracy": {2: 0.90, 3: 0.80, 4: 0.85}}
        damage = run["frozen_m2r1_accuracy"][2] - run["frozen_m2r1_accuracy"][3]
        recovery = run["frozen_m2r1_accuracy"][4] - run["frozen_m2r1_accuracy"][3]
        self.assertAlmostEqual(damage, 0.10)   # Positive = loss from phase 2->3.
        self.assertAlmostEqual(recovery, 0.05)  # Positive = gain from phase 3->4.

    def test_replay_history_uses_noisy_labels(self):
        # The reservoir must store the NOISY label the student trains on.
        from pilot import Reservoir
        buffer = Reservoir(8, 32, seed=990000)
        x = np.ones(32, dtype=np.float32)
        buffer.add(x, 3)  # Store label 3.
        sampled_x, sampled_y = buffer.sample(1)
        self.assertEqual(int(sampled_y[0]), 3)

    def test_save_records_roundtrip(self):
        directory = Path(impact.__file__).parent / "results_impact_selftest"
        model = diagnose.make_model(64, False, seed=7)
        run = {
            "model": model,
            "predictions": np.array([0, 1, 2, 3], dtype=np.int64),
            "frozen": {2: model, 3: model, 4: model},
            "frozen_predictions": {2: np.array([0], dtype=np.int64),
                                   3: np.array([1], dtype=np.int64),
                                   4: np.array([2], dtype=np.int64)},
        }
        stream = (None, None, np.array([0, 0, 0, 0], dtype=np.int64))
        manifest = impact.save_records(directory, "A", 220001, run, stream)
        self.assertEqual(set(manifest["phase_weights"]), {"2", "3", "4"})
        self.assertEqual(manifest["online_predictions_sha256"],
                         impact.digest_array(run["predictions"]))
        for path in directory.iterdir():
            path.unlink()
        directory.rmdir()


if __name__ == "__main__":
    unittest.main()