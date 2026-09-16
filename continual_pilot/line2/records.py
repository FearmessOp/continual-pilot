"""Exclusive artifact storage and exact round-trip checks; no runs on import."""
import hashlib
import json
from pathlib import Path

import numpy as np
import torch

from .learner import Learner


def tree_digest(value):
    """Type-aware digest of portable nested state, independent of pickle bytes."""
    digest = hashlib.sha256()

    def token(tag, data=b""):
        digest.update(tag.encode("ascii") + b":" + str(len(data)).encode("ascii"))
        digest.update(b":" + data)

    def visit(item):
        if isinstance(item, torch.Tensor):
            token("tensor")
            visit(item.detach().cpu().numpy())
        elif isinstance(item, np.ndarray):
            if item.dtype.hasobject:
                raise TypeError("Object arrays are not portable numerical state")
            token("array")
            visit(item.dtype.str)
            visit(tuple(item.shape))
            token("bytes", np.ascontiguousarray(item).tobytes())
        elif isinstance(item, np.generic):
            token("numpy-scalar")
            visit(np.asarray(item))
        elif isinstance(item, dict):
            token("dict")
            visit(len(item))
            if any(type(key) not in (str, int) for key in item):
                raise TypeError("State dictionary keys must be strings or integers")
            for key in sorted(item, key=lambda key: (type(key).__name__, key)):
                visit(key)
                visit(item[key])
        elif isinstance(item, (list, tuple)):
            token(type(item).__name__)
            visit(len(item))
            for child in item:
                visit(child)
        elif item is None or type(item) in (str, int, float, bool):
            token(type(item).__name__, json.dumps(
                item, ensure_ascii=False, allow_nan=False).encode("utf-8"))
        else:
            raise TypeError(f"Unsupported state type: {type(item).__name__}")

    visit(value)
    return digest.hexdigest()


def file_digest(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


class Records:
    """One new directory per run; validated artifacts and a final manifest."""

    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=False)
        self.files = {}
        self.closed = False

    def _path(self, name):
        if self.closed:
            raise RuntimeError("Artifact manifest is already finalized")
        relative = Path(name)
        if (relative.is_absolute() or relative.drive or ".." in relative.parts
                or not relative.parts or relative.as_posix() == "manifest.json"):
            raise ValueError("Expected a contained, nonreserved relative artifact path")
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root) or path == self.root:
            raise ValueError("Artifact path escapes run directory")
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _register(self, path, **metadata):
        name = path.relative_to(self.root).as_posix()
        self.files[name] = {
            "sha256": file_digest(path), "bytes": path.stat().st_size, **metadata
        }

    def arrays(self, name, arrays):
        if any(not isinstance(value, np.ndarray) or value.dtype.hasobject
               for value in arrays.values()):
            raise TypeError("Array archives require non-object NumPy arrays")
        expected = tree_digest(arrays)
        path = self._path(name)
        with path.open("xb") as handle:
            np.savez_compressed(handle, **arrays)
        with np.load(path, allow_pickle=False) as loaded:
            restored = {key: loaded[key] for key in loaded.files}
            if tree_digest(restored) != expected:
                raise AssertionError("Array archive round-trip mismatch")
        self._register(path, state_sha256=expected)

    def state(self, name, state):
        expected = tree_digest(state)
        path = self._path(name)
        with path.open("xb") as handle:
            torch.save(state, handle)
        restored = torch.load(path, map_location="cpu", weights_only=True)
        if tree_digest(restored) != expected:
            raise AssertionError("Portable state round-trip mismatch")
        self._register(path, state_sha256=expected)
        return restored

    def checkpoint(self, name, learner, *, verification_inputs):
        before = learner.checkpoint()
        expected = tree_digest(before)
        predictions = learner.frozen_predictions(verification_inputs)
        loaded = self.state(name, before)
        restored = Learner.from_checkpoint(loaded)
        if tree_digest(restored.checkpoint()) != expected:
            raise AssertionError("Reconstructed learner state differs")
        other = restored.frozen_predictions(verification_inputs)
        if tree_digest(predictions) != tree_digest(other):
            raise AssertionError("Loaded learner predictions differ")
        if (tree_digest(learner.checkpoint()) != expected
                or tree_digest(restored.checkpoint()) != expected):
            raise AssertionError("Checkpoint verification mutated prediction state")
        self.files[Path(name).as_posix()].update({
            "prediction_verification_count": len(predictions),
            "prediction_sha256": tree_digest(predictions),
            "verification_inputs_sha256": tree_digest(verification_inputs),
        })
        return restored

    def json(self, name, value):
        encoded = json.dumps(
            value, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8")
        self.bytes(name, encoded)

    def bytes(self, name, value):
        path = self._path(name)
        with path.open("xb") as handle:
            handle.write(value)
        if path.read_bytes() != value:
            raise AssertionError("Byte artifact round-trip mismatch")
        self._register(path)

    def finish(self):
        if self.closed:
            raise RuntimeError("Artifact manifest is already finalized")
        actual = {path.relative_to(self.root).as_posix()
                  for path in self.root.rglob("*") if path.is_file()}
        if actual != set(self.files):
            raise AssertionError("Unregistered or missing artifacts")
        for name, entry in self.files.items():
            if file_digest(self.root / name) != entry["sha256"]:
                raise AssertionError(f"Artifact changed during run: {name}")
        with (self.root / "manifest.json").open("x", encoding="utf-8") as handle:
            json.dump(self.files, handle, indent=2, allow_nan=False)
        self.closed = True