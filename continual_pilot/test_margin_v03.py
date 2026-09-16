"""Margin diagnostic mechanics tests; not empirical margin evidence."""
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import torch

import diagnose
import diagnose_v02 as diagnostics
import margin_v03 as margin
from pilot import Generator
from generator_v03 import GeneratorV03


class MarginMechanicsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_score_std_is_population_over_all_elements(self):
        scores = np.array([[1.0, 3.0], [5.0, 7.0]])
        result = margin.score_std(lambda z, r: z, scores, rule=0)
        self.assertAlmostEqual(result, float(np.std(scores)))

    def test_margin_report_quintiles_and_shares(self):
        # 10 examples, ascending raw margin, errors only in the lowest quintile.
        scores = np.zeros((10, 2))
        scores[:, 1] = np.arange(10, dtype=float) / 10.0  # margin = col1 - col0.
        predictions = np.zeros(10, dtype=np.int64)
        clean = np.zeros(10, dtype=np.int64)
        clean[0] = 1  # One error at the smallest margin.
        clean[1] = 1  # Second error also in the lowest quintile (first 2 of 10).
        report = margin.margin_report(scores, predictions, clean, scale=2.0)
        self.assertEqual(report["total_errors"], 2)
        self.assertEqual(len(report["quintiles"]), 5)
        self.assertEqual(report["quintiles"][0]["count"], 2)
        self.assertEqual(report["quintiles"][0]["error_count"], 2)
        self.assertAlmostEqual(report["lowest_quintile_error_share"], 1.0)
        self.assertTrue(report["concentration_flag"])
        # Normalized margin = raw / 2; below-0.1 share counts raw<0.2 i.e. idx 0,1.
        self.assertAlmostEqual(
            report["normalized_below_fixed_thresholds"]["below_0.1"], 0.2)

    def test_margin_report_zero_errors_is_undefined_not_flagged(self):
        scores = np.zeros((5, 2))
        scores[:, 1] = np.arange(5, dtype=float)
        clean = np.zeros(5, dtype=np.int64)
        report = margin.margin_report(scores, clean.copy(), clean, scale=1.0)
        self.assertEqual(report["total_errors"], 0)
        self.assertIsNone(report["lowest_quintile_error_share"])
        self.assertIsNone(report["concentration_flag"])

    def test_reproduced_eval_latents_match_actual_evaluation(self):
        # The reproduced latents must yield the SAME clean labels the frozen
        # evaluation assigns; otherwise the halt condition must trigger.
        generator = GeneratorV03(seed=1000, alpha=0.5, noise=0.05,
                                 calibration_count=2000)
        model = diagnose.make_model(64, False, seed=7)
        predictions, clean, noisy = diagnostics.frozen_evaluation(
            model, generator, use_context=False, context_window=64,
            seed=120300, count=500)
        z = margin.reproduce_eval_latents(generator, seed=120301, count=500)
        scores = generator._base_scores(z, 0) + generator.offsets[0]
        np.testing.assert_array_equal(scores.argmax(axis=1), clean)

    def test_v02_scores_exclude_offset_and_match_generator_labels(self):
        generator = Generator(seed=7, alpha=0.5, noise=0.05)
        rng = np.random.default_rng(3)
        _, _, clean, z = generator.sample(400, 0, 0, rng)
        scores = margin.v02_base_scores(generator, z, 0)
        np.testing.assert_array_equal(scores.argmax(axis=1), clean)

    def test_save_records_roundtrip_and_manifest(self):
        directory = Path(margin.__file__).parent / "results_margin_v03_selftest"
        model = diagnose.make_model(8, False, seed=7)
        train = np.array([0, 1, 2], dtype=np.int64)
        evalp = np.array([1, 1, 0, 3], dtype=np.int64)
        clean = np.array([1, 0, 0, 3], dtype=np.int64)
        noisy = np.array([1, 2, 0, 3], dtype=np.int64)
        margin.save_records(directory, model, train, evalp, clean, noisy)
        manifest = json.loads((directory / "manifest.json").read_text())
        with np.load(directory / "predictions.npz") as loaded:
            self.assertEqual(manifest["arrays"]["eval_clean"]["sha256"],
                             margin.digest_array(clean))
            np.testing.assert_array_equal(loaded["eval_predictions"], evalp)
        self.assertEqual(manifest["final_state_sha256"],
                         diagnose.state_digest(model))
        for name in ("final_weights.pt", "predictions.npz", "manifest.json"):
            (directory / name).unlink()
        directory.rmdir()

    def test_halt_on_confusion_matrix_mismatch(self):
        # Corrupt the stored v0.3 confusion matrix; reproduction must halt.
        path = Path(margin.__file__).parent / "results_gate_v03" / "summary.json"
        original = path.read_text(encoding="utf-8")
        data = json.loads(original)
        data["controls"]["64"]["evaluation"][
            "confusion_matrix_true_by_pred"][0][0] += 1
        try:
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "confusion matrix"):
                margin.reproduce_v03(
                    None, Path(margin.__file__).parent / "unused_records")
        finally:
            path.write_text(original, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()