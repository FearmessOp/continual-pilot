"""Acceptance decision tests with constructed counts, not generator candidates."""
import unittest

import numpy as np

from .acceptance import _within, assess_candidate
from .config import CLASS_BAND, DISAGREEMENT_BAND, MAX_PROPOSALS


class AcceptanceTests(unittest.TestCase):
    @staticmethod
    def fixture():
        first = np.arange(20000, dtype=np.int64) % 4
        second = first.copy()
        second[:10000] = (second[:10000] + 1) % 4
        labels = np.column_stack((first, second))
        return {
            "exclusion_masks": {
                0: np.ones(100000, dtype=bool),
                1: np.ones(100000, dtype=bool),
            },
            "accepted_labels": {0: labels.copy(), 1: labels.copy()},
            "proposal_counts": {0: 25000, 1: 25000},
        }

    def test_valid_candidate_requires_both_mixtures(self):
        report = assess_candidate(**self.fixture())
        self.assertTrue(report["accepted"])
        self.assertEqual(report["reasons"], [])
        for row in report["mixtures"].values():
            self.assertEqual(row["class_counts"], [[5000] * 4, [5000] * 4])
            self.assertEqual(row["disagreement_count"], 10000)

    def test_decimal_boundaries_are_inclusive_without_rounding(self):
        for band, low, high in (
                (CLASS_BAND, 3600, 7000),
                (DISAGREEMENT_BAND, 8000, 14000)):
            with self.subTest(band=band):
                self.assertTrue(_within(low, 20000, band))
                self.assertTrue(_within(high, 20000, band))
                self.assertFalse(_within(low - 1, 20000, band))
                self.assertFalse(_within(high + 1, 20000, band))

    def test_exclusion_exact_limit_passes_one_more_fails(self):
        data = self.fixture()
        data["exclusion_masks"][1][:30000] = False
        self.assertTrue(assess_candidate(**data)["accepted"])
        data["exclusion_masks"][1][30000] = False
        report = assess_candidate(**data)
        self.assertFalse(report["accepted"])
        self.assertEqual(report["reasons"], [{"mixture": 1, "criterion": "exclusion"}])
        self.assertEqual(report["mixtures"]["M2"]["excluded_count"], 30001)

    def test_balance_and_disagreement_reasons_are_separate(self):
        data = self.fixture()
        data["accepted_labels"][0][:] = 0
        report = assess_candidate(**data)
        self.assertFalse(report["accepted"])
        self.assertEqual(report["reasons"], [
            {"mixture": 0, "criterion": "balance"},
            {"mixture": 0, "criterion": "disagreement"},
        ])
        self.assertTrue(report["mixtures"]["M2"]["balance_passed"])

    def test_balanced_identical_rules_fail_only_disagreement(self):
        data = self.fixture()
        data["accepted_labels"][1][:, 1] = data["accepted_labels"][1][:, 0]
        report = assess_candidate(**data)
        self.assertEqual(report["reasons"], [
            {"mixture": 1, "criterion": "disagreement"}])

    def test_exhaustion_is_rejection_not_missing_data_success(self):
        data = self.fixture()
        del data["accepted_labels"][0]
        data["proposal_counts"][0] = MAX_PROPOSALS
        report = assess_candidate(**data, budget_exhausted=(0,))
        self.assertFalse(report["accepted"])
        self.assertEqual(report["reasons"], [
            {"mixture": 0, "criterion": "proposal_budget"}])
        self.assertIsNone(report["mixtures"]["M1"]["balance_passed"])
        self.assertIsNone(report["mixtures"]["M1"]["accepted_sample_count"])

    def test_incomplete_or_contradictory_records_raise(self):
        data = self.fixture()
        del data["accepted_labels"][0]
        with self.assertRaises(ValueError):
            assess_candidate(**data)
        with self.assertRaises(ValueError):
            assess_candidate(**data, budget_exhausted=(0,))
        data = self.fixture()
        with self.assertRaises(ValueError):
            assess_candidate(**data, budget_exhausted=(0,))
        del data["exclusion_masks"][1]
        with self.assertRaises(ValueError):
            assess_candidate(**data)

    def test_malformed_labels_masks_and_proposal_counts_raise(self):
        for key, mixture, value in (
                ("accepted_labels", 0, np.zeros((19999, 2), dtype=np.int64)),
                ("accepted_labels", 0, np.zeros((20000, 2), dtype=np.float64)),
                ("accepted_labels", 0, np.full((20000, 2), 4, dtype=np.int64)),
                ("exclusion_masks", 0, np.ones(100000, dtype=np.int64)),
                ("exclusion_masks", 0, np.ones(99999, dtype=bool)),
                ("proposal_counts", 0, 19999),
                ("proposal_counts", 0, MAX_PROPOSALS + 1),
                ("proposal_counts", 0, True)):
            with self.subTest(key=key, shape=getattr(value, "shape", None)):
                data = self.fixture()
                data[key][mixture] = value
                with self.assertRaises(ValueError):
                    assess_candidate(**data)


if __name__ == "__main__":
    unittest.main()