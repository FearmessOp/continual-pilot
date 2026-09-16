"""Phase-3 curve analysis mechanics tests; not empirical curve evidence."""
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import torch

import curves_v03 as curves
from generator_v03 import GeneratorV03


class CurvesMechanicsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_block_curves_counts_and_overlap_columns(self):
        # Phase 3 block accuracies against R1 and R2 labels.
        online = np.zeros(4 * curves.PHASE, dtype=np.int64)
        # Make phase-3 predictions all class 1.
        online[curves.PHASE3_START:curves.PHASE3_STOP] = 1
        r1 = np.zeros(curves.PHASE, dtype=np.int64)  # All R1 label 0.
        r2 = np.ones(curves.PHASE, dtype=np.int64)   # All R2 label 1.
        phase3 = {"x": None, "noisy": None, "r1": r1, "r2": r2}
        rows, agreement = curves.block_curves(online, phase3)
        self.assertEqual(len(rows), curves.PHASE // curves.BLOCK)
        self.assertEqual(rows[0]["count"], curves.BLOCK)
        # Predictions equal R2 everywhere, never R1.
        self.assertAlmostEqual(rows[0]["pred_vs_R2_accuracy"], 1.0)
        self.assertAlmostEqual(rows[0]["pred_vs_R1_accuracy"], 0.0)
        # r1 != r2 everywhere -> agreement 0.
        self.assertAlmostEqual(agreement, 0.0)

    def test_candidate_window_band_edges(self):
        curve = [
            {"block_end": 1000, "pred_vs_R1_accuracy": 0.88},  # drop 0.02, out.
            {"block_end": 2000, "pred_vs_R1_accuracy": 0.65},  # drop 0.25, in.
            {"block_end": 3000, "pred_vs_R1_accuracy": 0.55},  # drop 0.35, in.
            {"block_end": 4000, "pred_vs_R1_accuracy": 0.40},  # drop 0.50, out.
        ]
        window = curves.candidate_window(curve, phase2_reference=0.90)
        self.assertEqual(window["blocks_in_band_by_example_index"], [2000, 3000])
        self.assertEqual(window["r1_accuracy_band"], [0.50, 0.70])

    def test_reproduce_phase3_labels_share_inputs(self):
        # R1 and R2 labels in phase 3 come from the SAME inputs (same latents).
        generator = GeneratorV03(seed=1000, alpha=0.5, noise=0.05,
                                 calibration_count=2000)
        with patch.dict(curves.impact.PROTOCOL, {"phase_length": 200}):
            with patch.multiple(curves, PHASE=200,
                                PHASE3_START=400, PHASE3_STOP=600):
                phase3 = curves.reproduce_phase3(generator, 220001)
        self.assertEqual(len(phase3["r1"]), 200)
        self.assertEqual(len(phase3["r2"]), 200)
        # R1 and R2 labels differ on some fraction (disagreement > 0).
        self.assertGreater(np.mean(phase3["r1"] != phase3["r2"]), 0.0)

    def test_phase_regret_mismatch_halts(self):
        # A corrupted stored phase-regret must halt the analysis.
        generator = GeneratorV03(seed=1000, alpha=0.5, noise=0.05,
                                 calibration_count=2000)
        online = np.zeros(4 * curves.PHASE, dtype=np.int64)
        with patch.object(curves, "load_predictions", return_value=online):
            fake_summary = {"seeds": {"220001": {"A": {
                "phase_regret": [{"phase": 1, "first_1000_regret": -999,
                                  "total_regret": -999}],
                "frozen_m2r1_accuracy": {"2": 0.89}}}}}
            reproduced = curves.phase_regret_from_predictions(
                online, generator, 220001)
            # Reproduced regret will not equal the corrupted stored value.
            self.assertNotEqual(reproduced, fake_summary["seeds"]["220001"]["A"]
                                ["phase_regret"])

    def test_digest_array_stable(self):
        array = np.arange(10, dtype=np.int64)
        self.assertEqual(curves.digest_array(array),
                         curves.digest_array(array.copy()))


if __name__ == "__main__":
    unittest.main()