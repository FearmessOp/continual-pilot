"""Validation-evidence tests; temporary reports and isolated miniature suites."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from . import validation


class ValidationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "validation.json"

    @staticmethod
    def miniature_suite():
        return unittest.TestSuite([unittest.FunctionTestCase(lambda: None)])

    def create_evidence(self):
        with patch.object(validation, "mechanical_suite",
                          side_effect=self.miniature_suite):
            with contextlib.redirect_stdout(io.StringIO()):
                return validation.validate_to(self.path)

    def test_successful_evidence_matches_sources_and_runtime(self):
        expected = self.create_evidence()
        actual = validation.require_current_validation(self.path)
        self.assertEqual(actual, expected)
        self.assertEqual(actual["tests_run"], 1)
        self.assertFalse(actual["scientific_experiment_started"])
        self.assertIn("OK", actual["test_log"])

    def test_changed_source_or_runtime_rejects_evidence(self):
        self.create_evidence()
        with patch.object(validation, "source_inventory", return_value={}):
            with self.assertRaises(ValueError):
                validation.require_current_validation(self.path)
        with patch.object(validation, "environment", return_value={}):
            with self.assertRaises(ValueError):
                validation.require_current_validation(self.path)

    def test_failed_or_incomplete_evidence_is_rejected(self):
        original = self.create_evidence()
        for key, value in (
                ("passed", False), ("tests_run", 0), ("tests_planned", 2),
                ("errors", 1), ("skipped", 1), ("expected_failures", 1),
                ("sources_unchanged", False), ("addendum_sha256", "invalid")):
            with self.subTest(key=key):
                changed = dict(original)
                changed[key] = value
                self.path.write_text(json.dumps(changed), encoding="utf-8")
                with self.assertRaises(ValueError):
                    validation.require_current_validation(self.path)

    def test_failed_test_is_archived_but_does_not_authorize_runs(self):
        def fail():
            raise AssertionError("Intentional validation-fixture failure")

        suite = unittest.TestSuite([unittest.FunctionTestCase(fail)])
        with patch.object(validation, "mechanical_suite", return_value=suite):
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(RuntimeError):
                    validation.validate_to(self.path)
        report = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertFalse(report["passed"])
        self.assertEqual(report["failures"], 1)
        with self.assertRaises(ValueError):
            validation.require_current_validation(self.path)

    def test_existing_evidence_is_not_overwritten(self):
        self.create_evidence()
        before = self.path.read_bytes()
        with patch.object(validation, "mechanical_suite") as suite:
            with self.assertRaises(FileExistsError):
                validation.validate_to(self.path)
            suite.assert_not_called()
        self.assertEqual(self.path.read_bytes(), before)

    def test_source_changes_during_tests_invalidate_evidence(self):
        inventory = validation.source_inventory()
        with patch.object(validation, "source_inventory",
                          side_effect=[inventory, {}]):
            with patch.object(validation, "mechanical_suite",
                              side_effect=self.miniature_suite):
                with contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(RuntimeError):
                        validation.validate_to(self.path)
        report = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertFalse(report["sources_unchanged"])
        self.assertFalse(report["passed"])


if __name__ == "__main__":
    unittest.main()