"""Guarded entry point for authorized acceptance and stationary controls only."""
import argparse
import hashlib
import json
import subprocess
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import torch

from .config import ACTIVE_REVISION, MAX_CANDIDATES, V05_PROTOCOL_SHA256
from .pool import candidate_seeds
from .records import Records
from .validation import WORKSPACE, environment, require_current_validation, source_inventory
from .workflow import run_allowed_stages


REMOTE = "https://github.com/FearmessOp/continual-pilot.git"
RECEIPT = "continual_pilot/line2/PREREGISTRATION_DRAFT.md.ots"
RECEIPT_SHA256 = "7ded550e25972aa61660ce10d9519cf1f32fc37db9f8918c90ca039c3cec2de3"


def git(*arguments):
    return subprocess.check_output(
        ["git", *arguments], cwd=WORKSPACE, timeout=60)


def verify_backup(sources):
    """Require exact committed source bytes and matching remote branch tip."""
    head = git("rev-parse", "HEAD").decode().strip()
    if git("remote", "get-url", "origin").decode().strip() != REMOTE:
        raise ValueError("Unexpected backup remote")
    remote = git("ls-remote", "origin", "refs/heads/master").decode().split()
    if len(remote) != 2 or remote[0] != head:
        raise ValueError("Current commit has not been verified on the remote branch")
    for name, digest in {**sources, RECEIPT: RECEIPT_SHA256}.items():
        committed = git("show", f"{head}:{name}")
        local = (WORKSPACE / name).read_bytes()
        if (hashlib.sha256(committed).hexdigest() != digest
                or hashlib.sha256(local).hexdigest() != digest):
            raise ValueError(f"Uncommitted or changed required artifact: {name}")
    return {"commit": head, "remote": REMOTE, "branch": "master",
            "verified_utc": datetime.now(timezone.utc).isoformat()}


def require_external_archive():
    """Require the completed remote-download verification, not upload alone."""
    path = WORKSPACE / "continual_pilot/line2/BACKUP_V04_VERIFICATION_2026-09-16.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    if (report.get("schema") != "external-backup-verification-v1"
            or report.get("all_files_match") is not True
            or report.get("repository") != "FearmessOp/continual-pilot"
            or report.get("release_id") != 390088986
            or report.get("verified_files_including_manifest") != 3651
            or report.get("verified_bytes_including_manifest") != 5832842691
            or report.get("original_manifest_sha256") !=
            "2c37cd3ff958c0fae9f0a7983958bdd85ba924de4af41fe796b4391baa89c29d"
            or len(report.get("parts", [])) != 11):
        raise ValueError("Complete verified external archive is required before v0.5")
    return report


def execute(*, output, validation_path):
    """No bypass flags, parameter search, automatic retry or later experiment."""
    validation = require_current_validation(validation_path)
    sources = source_inventory()
    backup = verify_backup(sources)
    external_archive = require_external_archive()
    records = Records(output)
    started = time.perf_counter()
    try:
        records.json("prerun/validation.json", validation)
        records.json("prerun/backup.json", backup)
        records.json("prerun/external_archive_verification.json", external_archive)
        for name, expected in sources.items():
            data = (WORKSPACE / name).read_bytes()
            if hashlib.sha256(data).hexdigest() != expected:
                raise ValueError("Source changed during prerequisite archiving")
            records.bytes(f"prerun/sources/{name}", data)
        receipt = (WORKSPACE / RECEIPT).read_bytes()
        if hashlib.sha256(receipt).hexdigest() != RECEIPT_SHA256:
            raise ValueError("Original timestamp receipt changed")
        records.bytes("prerun/original_protocol.ots", receipt)
        records.json("prerun/seed_plan.json", {
            "control_candidates": [candidate_seeds(i) for i in range(MAX_CANDIDATES)],
            "selection": "first_three_accepted_in_order_no_learner_feedback",
        })
        torch.set_num_threads(1)
        torch.use_deterministic_algorithms(True)
        records.json("prerun/environment.json", {
            **environment(), "threads": torch.get_num_threads(),
            "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "active_revision": ACTIVE_REVISION,
            "v05_protocol_sha256": V05_PROTOCOL_SHA256,
            "external_archive_verified": True,
            "bitcoin_status": "previous_verification_archived_with_sources",
            "bitcoin_trust_model": "local_proof_and_two_explorers_not_full_chain",
            "authorization": "final_v05_preregistration_2026-09-16",
        })
        if sources != source_inventory():
            raise ValueError("Source inventory changed before experiment")
        report = run_allowed_stages(records)
        if sources != source_inventory():
            raise ValueError("Source inventory changed during experiment")
        records.json("execution.json", {
            "completed_utc": datetime.now(timezone.utc).isoformat(),
            "wall_seconds": time.perf_counter() - started,
            "scientific_checks_passed": report["passed"],
            "next_action": "close_line_publish_lessons_no_more_scientific_runs",
            "final_scientific_attempt": True,
        })
        records.finish()
    except Exception as error:
        # Preserve partial artifacts. Never rerun or relabel numerical failures.
        records.json("execution_failure.json", {
            "error_type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
            "utc": datetime.now(timezone.utc).isoformat(),
            "next_action": "stop_for_documented_resolution_no_automatic_retry",
        })
        raise
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--validation", type=Path, required=True)
    args = parser.parse_args()
    report = execute(output=args.output, validation_path=args.validation)
    print(f"Authorized stages stopped: {report['stop_reason']}", flush=True)


if __name__ == "__main__":
    main()