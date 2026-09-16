"""Artifact tests confined to temporary directories; no experimental runs."""
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import torch

from .learner import Learner
from .records import Records, file_digest, tree_digest


class RecordsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "run"

    def test_digest_preserves_types_shapes_and_values(self):
        self.assertNotEqual(tree_digest([1]), tree_digest((1,)))
        self.assertNotEqual(tree_digest(1), tree_digest(True))
        self.assertNotEqual(tree_digest(np.zeros(2)), tree_digest(np.zeros((1, 2))))
        self.assertNotEqual(tree_digest(np.zeros(2, dtype=np.float32)),
                            tree_digest(np.zeros(2, dtype=np.float64)))
        self.assertNotEqual(tree_digest(torch.zeros(2)),
                            tree_digest(np.zeros(2, dtype=np.float32)))
        self.assertEqual(tree_digest({"b": 2, "a": 1}),
                         tree_digest({"a": 1, "b": 2}))
        with self.assertRaises(TypeError):
            tree_digest(np.array([object()], dtype=object))

    def test_array_roundtrip_and_manifest(self):
        records = Records(self.root)
        arrays = {
            "x": np.arange(64, dtype=np.float32).reshape(2, 32),
            "z": np.arange(16, dtype=np.float64).reshape(2, 8),
            "labels": np.array([0, 3], dtype=np.int64),
        }
        records.arrays("data/input.npz", arrays)
        records.json("summary.json", {"count": 2})
        records.finish()
        with (self.root / "manifest.json").open(encoding="utf-8") as handle:
            manifest = json.load(handle)
        self.assertEqual(set(manifest), {"data/input.npz", "summary.json"})
        for name, entry in manifest.items():
            self.assertEqual(entry["sha256"], file_digest(self.root / name))
            self.assertEqual(entry["bytes"], (self.root / name).stat().st_size)
        self.assertEqual(manifest["data/input.npz"]["state_sha256"],
                         tree_digest(arrays))

    def test_existing_directory_and_artifacts_are_not_overwritten(self):
        records = Records(self.root)
        with self.assertRaises(FileExistsError):
            Records(self.root)
        records.bytes("original.bin", b"original")
        with self.assertRaises(FileExistsError):
            records.bytes("original.bin", b"replacement")
        self.assertEqual((self.root / "original.bin").read_bytes(), b"original")
        records.finish()
        with self.assertRaises(RuntimeError):
            records.bytes("late.bin", b"late")
        with self.assertRaises(RuntimeError):
            records.finish()

    def test_escaping_and_reserved_paths_are_rejected(self):
        records = Records(self.root)
        for name in ("../escape.bin", "manifest.json", "",
                     str(Path(self.temporary.name) / "outside.bin")):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    records.bytes(name, b"invalid")
        self.assertFalse((Path(self.temporary.name) / "escape.bin").exists())

    def test_modified_artifact_prevents_finalization(self):
        records = Records(self.root)
        records.bytes("value.bin", b"before")
        (self.root / "value.bin").write_bytes(b"after")
        with self.assertRaises(AssertionError):
            records.finish()
        self.assertFalse((self.root / "manifest.json").exists())

    def test_unregistered_file_prevents_finalization(self):
        records = Records(self.root)
        (self.root / "unregistered.bin").write_bytes(b"unexpected")
        with self.assertRaises(AssertionError):
            records.finish()

    def test_nonportable_arrays_and_nonfinite_json_are_rejected(self):
        records = Records(self.root)
        with self.assertRaises(TypeError):
            records.arrays("objects.npz", {"bad": np.array([{}], dtype=object)})
        with self.assertRaises(ValueError):
            records.json("invalid.json", {"value": float("nan")})
        self.assertEqual(list(self.root.iterdir()), [])

    def test_checkpoint_disk_reload_predictions_and_continuation(self):
        previous_threads = torch.get_num_threads()
        torch.set_num_threads(1)
        self.addCleanup(torch.set_num_threads, previous_threads)
        learner = Learner("D", seeds={
            "model0": 7, "model1": 8, "cpr0": 9, "cpr1": 10,
        })
        x = np.arange(512, dtype=np.float32).reshape(16, 32) / 512
        labels = np.arange(16, dtype=np.int64) % 4
        for row, label in zip(x, labels):
            learner.predict(row)
            learner.observe(label)
        before = tree_digest(learner.checkpoint())
        records = Records(self.root)
        records.arrays("verification.npz", {"x": x})
        restored = records.checkpoint(
            "model/state.pt", learner, verification_inputs=x)
        self.assertEqual(before, tree_digest(learner.checkpoint()))
        self.assertEqual(before, tree_digest(restored.checkpoint()))
        for row, label in zip(x, labels):
            self.assertEqual(learner.predict(row), restored.predict(row))
            learner.observe(label)
            restored.observe(label)
        self.assertEqual(tree_digest(learner.checkpoint()),
                         tree_digest(restored.checkpoint()))
        records.finish()
        self.assertEqual(records.files["model/state.pt"]["prediction_verification_count"],
                         16)


if __name__ == "__main__":
    unittest.main()