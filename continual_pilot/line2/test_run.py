"""Entry-point guard tests; no network requests or scientific execution."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import torch

from . import run


class RunTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.output = self.root / "results"
        self.validation_path = self.root / "evidence.json"
        threads = torch.get_num_threads()
        deterministic = torch.are_deterministic_algorithms_enabled()
        warn_only = torch.is_deterministic_algorithms_warn_only_enabled()
        self.addCleanup(torch.set_num_threads, threads)
        self.addCleanup(torch.use_deterministic_algorithms,
                        deterministic, warn_only=warn_only)

    def test_invalid_validation_prevents_backup_and_directory_creation(self):
        with patch.object(run, "require_current_validation",
                          side_effect=ValueError("Stale evidence")):
            with patch.object(run, "verify_backup") as backup:
                with patch.object(run, "run_allowed_stages") as workflow:
                    with self.assertRaises(ValueError):
                        run.execute(output=self.output, validation_path=self.validation_path)
                    backup.assert_not_called()
                    workflow.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_unverified_backup_prevents_execution(self):
        with patch.object(run, "require_current_validation", return_value={}):
            with patch.object(run, "verify_backup",
                              side_effect=ValueError("Remote mismatch")):
                with patch.object(run, "run_allowed_stages") as workflow:
                    with self.assertRaises(ValueError):
                        run.execute(output=self.output, validation_path=self.validation_path)
                    workflow.assert_not_called()
        self.assertFalse(self.output.exists())

    def backup_fixture(self, *, remote_head="abc", committed=b"source"):
        source = self.root / "source.txt"
        source.write_bytes(b"source")
        receipt = self.root / "receipt.ots"
        receipt.write_bytes(b"receipt")
        sources = {"source.txt": hashlib.sha256(b"source").hexdigest()}

        def git(*arguments):
            if arguments == ("rev-parse", "HEAD"):
                return b"abc\n"
            if arguments == ("remote", "get-url", "origin"):
                return (run.REMOTE + "\n").encode()
            if arguments == ("ls-remote", "origin", "refs/heads/master"):
                return f"{remote_head}\trefs/heads/master\n".encode()
            if arguments == ("show", "abc:source.txt"):
                return committed
            if arguments == ("show", "abc:receipt.ots"):
                return b"receipt"
            raise AssertionError(f"Unexpected Git request: {arguments}")

        with patch.object(run, "WORKSPACE", self.root):
            with patch.object(run, "RECEIPT", "receipt.ots"):
                with patch.object(run, "RECEIPT_SHA256",
                                  hashlib.sha256(b"receipt").hexdigest()):
                    with patch.object(run, "git", side_effect=git):
                        return run.verify_backup(sources)

    def test_backup_requires_matching_remote_tip_and_exact_bytes(self):
        result = self.backup_fixture()
        self.assertEqual(result["commit"], "abc")
        self.assertEqual(result["branch"], "master")
        with self.assertRaises(ValueError):
            self.backup_fixture(remote_head="different")
        with self.assertRaises(ValueError):
            self.backup_fixture(committed=b"different source")

    def test_success_archives_prerequisites_before_mock_workflow(self):
        def workflow(records):
            self.assertTrue((records.root / "prerun/validation.json").exists())
            self.assertTrue((records.root / "prerun/environment.json").exists())
            self.assertTrue((records.root / "prerun/seed_plan.json").exists())
            self.assertTrue((records.root / "prerun/original_protocol.ots").exists())
            records.json("summary.json", {"mock": True})
            return {"passed": False, "stop_reason": "mock_acceptance_failure"}

        with patch.object(run, "require_current_validation", return_value={"fixture": True}):
            with patch.object(run, "verify_backup", return_value={"mock": True}):
                with patch.object(run, "run_allowed_stages", side_effect=workflow) as invoked:
                    result = run.execute(
                        output=self.output, validation_path=self.validation_path)
                    self.assertEqual(invoked.call_count, 1)
        self.assertFalse(result["passed"])
        self.assertTrue((self.output / "manifest.json").exists())
        execution = json.loads((self.output / "execution.json").read_text())
        self.assertEqual(execution["next_action"], "stop_for_user")

    def test_failure_retains_partial_records_without_retry(self):
        def fail(records):
            records.json("partial.json", {"preserved": True})
            raise ValueError("Intentional fixture failure")

        with patch.object(run, "require_current_validation", return_value={"fixture": True}):
            with patch.object(run, "verify_backup", return_value={"mock": True}):
                with patch.object(run, "run_allowed_stages", side_effect=fail) as invoked:
                    with self.assertRaisesRegex(ValueError, "Intentional fixture failure"):
                        run.execute(output=self.output, validation_path=self.validation_path)
                    self.assertEqual(invoked.call_count, 1)
        self.assertTrue((self.output / "partial.json").exists())
        self.assertFalse((self.output / "manifest.json").exists())
        failure = json.loads((self.output / "execution_failure.json").read_text())
        self.assertEqual(failure["error_type"], "ValueError")
        self.assertEqual(failure["next_action"],
                         "stop_for_documented_resolution_no_automatic_retry")


if __name__ == "__main__":
    unittest.main()