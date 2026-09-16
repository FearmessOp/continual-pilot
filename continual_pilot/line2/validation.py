"""Source-bound mechanical test evidence; never starts scientific experiments."""
import hashlib
import importlib
import inspect
import io
import json
import platform
import sys
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch

from .config import (
    ACTIVE_REVISION, PROTOCOL_SHA256, V05_PROTOCOL_SHA256, verify_v05_protocol,
)


DIRECTORY = Path(__file__).resolve().parent
WORKSPACE = DIRECTORY.parents[1]
ADDENDUM_SHA256 = "f7e8e9c441a4673894e01aa2dd9ee481d4882bfb5f5ae04f79a0d2c7f1c9ef98"


def source_inventory():
    """Include implementation/tests and legacy dependencies used by parity tests."""
    paths = list(DIRECTORY.glob("*.py"))
    paths += [
        DIRECTORY / "PREREGISTRATION_DRAFT.md",
        DIRECTORY / "IMPLEMENTATION_ADDENDUM_2026-09-16.md",
        DIRECTORY / "PREREGISTRATION_V05_2026-09-16.md",
        DIRECTORY / "LOCK_V05_2026-09-16.md",
        DIRECTORY / "BACKUP_V04_VERIFICATION_2026-09-16.json",
        DIRECTORY / "OTS_VERIFICATION_2026-09-16.json",
        DIRECTORY / "PREREGISTRATION_DRAFT.md.upgraded.ots",
        DIRECTORY.parent / "pilot.py",
        DIRECTORY.parent / "diagnose.py",
        DIRECTORY.parent / "generator_v03.py",
    ]
    return {
        path.relative_to(WORKSPACE).as_posix():
        hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(paths)
    }


def verify_documents():
    verify_v05_protocol()
    path = DIRECTORY / "IMPLEMENTATION_ADDENDUM_2026-09-16.md"
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != ADDENDUM_SHA256:
        raise ValueError("Approved implementation addendum bytes changed")


def environment():
    return {
        "python": platform.python_version(),
        "numpy": str(np.__version__),
        "torch": str(torch.__version__),
        "platform": platform.platform(),
        "device": "cpu",
    }


def mechanical_suite():
    """Discover only test classes owned by each module, avoiding imported duplicates."""
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for path in sorted(DIRECTORY.glob("test_*.py")):
        module = importlib.import_module(f"continual_pilot.line2.{path.stem}")
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if cls.__module__ == module.__name__ and issubclass(cls, unittest.TestCase):
                suite.addTests(loader.loadTestsFromTestCase(cls))
    return suite


def validate_to(path):
    """Exclusive, source-bound evidence including the complete mechanical-test log."""
    path = Path(path)
    verify_documents()
    before = source_inventory()
    runtime = environment()
    started_utc = datetime.now(timezone.utc).isoformat()
    # Reserve the output before running tests; never overwrite historical evidence.
    with path.open("x", encoding="utf-8") as handle:
        log = io.StringIO()
        started = time.perf_counter()
        suite = mechanical_suite()
        count = suite.countTestCases()
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
        unchanged = before == source_inventory()
        passed = bool(count > 0 and result.wasSuccessful()
                      and result.testsRun == count and not result.skipped
                      and not result.expectedFailures and unchanged)
        report = {
            "schema": "line2-mechanical-validation-v05",
            "active_revision": ACTIVE_REVISION,
            "v05_protocol_sha256": V05_PROTOCOL_SHA256,
            "started_utc": started_utc,
            "completed_utc": datetime.now(timezone.utc).isoformat(),
            "seconds": time.perf_counter() - started,
            "tests_planned": count,
            "tests_run": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped),
            "expected_failures": len(result.expectedFailures),
            "passed": passed,
            "sources_unchanged": unchanged,
            "sources": before,
            "environment": runtime,
            "protocol_sha256": PROTOCOL_SHA256,
            "addendum_sha256": ADDENDUM_SHA256,
            "scientific_experiment_started": False,
            "test_log": log.getvalue(),
        }
        json.dump(report, handle, ensure_ascii=False, indent=2, allow_nan=False)
    print(log.getvalue(), end="")
    if not passed:
        raise RuntimeError("Mechanical validation failed; scientific runs prohibited")
    return report


def require_current_validation(path):
    """Fail closed on stale sources, changed runtime, or unsuccessful test evidence."""
    verify_documents()
    report = json.loads(Path(path).read_text(encoding="utf-8"))
    if (report.get("schema") != "line2-mechanical-validation-v05"
            or report.get("active_revision") != ACTIVE_REVISION
            or report.get("v05_protocol_sha256") != V05_PROTOCOL_SHA256
            or report.get("passed") is not True
            or report.get("sources_unchanged") is not True
            or report.get("scientific_experiment_started") is not False
            or report.get("tests_run", 0) <= 0
            or report.get("tests_run") != report.get("tests_planned")
            or any(report.get(key) != 0 for key in (
                "failures", "errors", "skipped", "expected_failures"))
            or report.get("protocol_sha256") != PROTOCOL_SHA256
            or report.get("addendum_sha256") != ADDENDUM_SHA256
            or report.get("sources") != source_inventory()
            or report.get("environment") != environment()):
        raise ValueError("Missing, stale or failed mechanical validation evidence")
    return report


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m continual_pilot.line2.validation NEW_REPORT_PATH")
    validate_to(sys.argv[1])