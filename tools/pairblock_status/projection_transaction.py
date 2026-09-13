"""Publish receipt-derived Markdown projections with crash recovery.

A prepared transaction stores the final receipt and both rendered documents
before any of those targets change. The controller writes and validates the
documents, publishes the receipt as the commit record, and then removes the
prepared transaction. Reapplying the same record is idempotent.
"""

from __future__ import annotations

import base64
import json
import os
import tempfile
from collections.abc import Callable, Mapping
from pathlib import Path

from .execution_identity import sha256_bytes
from .profile import PairBlockGateError


def atomic_write(path: Path, content: bytes) -> None:
    """Replace one file and flush both its bytes and parent directory entry."""

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary = Path(temporary_name)
        if temporary.exists():
            temporary.unlink()


def _relative(repository: Path, path: Path) -> str:
    """Return a repository-contained relative path."""

    resolved = path.resolve()
    if not resolved.is_relative_to(repository):
        raise PairBlockGateError(f"transaction target leaves repository: {path}")
    return resolved.relative_to(repository).as_posix()


def prepare_projection(
    repository: Path,
    transaction_id: str,
    *,
    receipt_path: Path,
    receipt: bytes,
    documents: Mapping[Path, bytes],
) -> Path:
    """Persist every byte required to finish one projection transition."""

    repository = repository.resolve()
    journal = (
        repository / "evidence" / "projection-transactions" / f"{transaction_id}.json"
    )
    if journal.exists():
        raise PairBlockGateError(f"projection transaction already exists: {journal}")
    payload = {
        "schema_version": 1,
        "receipt": {
            "path": _relative(repository, receipt_path),
            "sha256": sha256_bytes(receipt),
            "content": base64.b64encode(receipt).decode("ascii"),
        },
        "documents": [
            {
                "path": _relative(repository, path),
                "sha256": sha256_bytes(content),
                "content": base64.b64encode(content).decode("ascii"),
            }
            for path, content in sorted(
                documents.items(), key=lambda item: item[0].as_posix()
            )
        ],
    }
    atomic_write(
        journal, (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    )
    return journal


def _decode_entry(repository: Path, entry: object) -> tuple[Path, bytes]:
    """Validate and decode one prepared target."""

    if not isinstance(entry, dict) or set(entry) != {"path", "sha256", "content"}:
        raise PairBlockGateError("projection transaction target fields differ")
    relative = entry["path"]
    digest = entry["sha256"]
    encoded = entry["content"]
    if not all(isinstance(value, str) for value in (relative, digest, encoded)):
        raise PairBlockGateError("projection transaction target values differ")
    path = (repository / relative).resolve()
    if Path(relative).is_absolute() or not path.is_relative_to(repository):
        raise PairBlockGateError("projection transaction target leaves repository")
    try:
        content = base64.b64decode(encoded, validate=True)
    except ValueError as error:
        raise PairBlockGateError("projection transaction content is invalid") from error
    if sha256_bytes(content) != digest:
        raise PairBlockGateError("projection transaction content digest differs")
    return path, content


def apply_projection(
    repository: Path,
    journal: Path,
    *,
    validate_documents: Callable[[], object],
    validate_committed: Callable[[], object] | None = None,
) -> Path:
    """Write, validate, and commit one prepared transition idempotently."""

    repository = repository.resolve()
    try:
        payload = json.loads(journal.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PairBlockGateError(
            f"invalid projection transaction: {journal}"
        ) from error
    if not isinstance(payload, dict) or set(payload) != {
        "schema_version",
        "receipt",
        "documents",
    }:
        raise PairBlockGateError(f"projection transaction fields differ: {journal}")
    if payload["schema_version"] != 1 or not isinstance(payload["documents"], list):
        raise PairBlockGateError(f"projection transaction envelope differs: {journal}")
    receipt_path, receipt = _decode_entry(repository, payload["receipt"])
    documents = [_decode_entry(repository, item) for item in payload["documents"]]
    for path, content in documents:
        atomic_write(path, content)
    for path, content in documents:
        if path.read_bytes() != content:
            raise PairBlockGateError(
                f"projection target differs after atomic write: {path}"
            )
    validate_documents()
    if receipt_path.exists() and receipt_path.read_bytes() != receipt:
        raise PairBlockGateError(
            "projection receipt target already contains other bytes"
        )
    atomic_write(receipt_path, receipt)
    if validate_committed is not None:
        validate_committed()
    journal.unlink()
    return receipt_path


def pending_projections(repository: Path) -> tuple[Path, ...]:
    """Return prepared projection journals in deterministic order."""

    directory = repository.resolve() / "evidence" / "projection-transactions"
    if not directory.is_dir():
        return ()
    return tuple(sorted(directory.glob("*.json")))
