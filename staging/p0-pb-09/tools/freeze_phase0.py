"""Freeze Phase 0 receipts and VIPER assessments into one hashed index.

``freeze_phase0`` checks the required receipt roles, validates each usefulness
assessment, hashes every input, and writes the index consumed by the final
VIPER evidence stage.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path

REQUIRED_RECEIPTS = {
    "capacity",
    "restoration",
    "graph_verification",
    "severed_graph_rejection",
    "hopfield_replay",
    "mil_replay",
}
ASSESSMENT_FIELDS = {
    "check_id",
    "claimed_guarantee",
    "outcome",
    "independent_check",
    "ordinary_check_equivalent",
    "elapsed_seconds",
    "confirmed_defect",
    "later_reuse",
}


class Phase0EvidenceError(ValueError):
    """Raised when required Phase 0 evidence is missing or malformed."""


def sha256_file(path: Path) -> str:
    """Return the digest of one retained evidence file."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _evidence_identity(path: Path, repository_root: Path) -> dict[str, object]:
    """Return the repository-relative path, byte count, and digest."""

    resolved = path.resolve(strict=True)
    try:
        relative = resolved.relative_to(repository_root.resolve(strict=True))
    except ValueError as error:
        raise Phase0EvidenceError(f"evidence is outside its repository: {path}") from error
    return {
        "path": relative.as_posix(),
        "byte_count": resolved.stat().st_size,
        "sha256": sha256_file(resolved),
    }


def freeze_phase0(
    *,
    repository_root: Path,
    receipts: Mapping[str, Path],
    assessment_path: Path,
    output_path: Path,
) -> dict[str, object]:
    """Write a complete digest-bound index of Phase 0 evidence."""

    if set(receipts) != REQUIRED_RECEIPTS:
        raise Phase0EvidenceError(
            "receipt roles differ: "
            f"missing={sorted(REQUIRED_RECEIPTS - set(receipts))}, "
            f"unexpected={sorted(set(receipts) - REQUIRED_RECEIPTS)}"
        )
    assessments = json.loads(assessment_path.read_text(encoding="utf-8"))
    if not isinstance(assessments, list) or not assessments:
        raise Phase0EvidenceError("VIPER assessment ledger must be a non-empty array")
    for index, assessment in enumerate(assessments):
        if not isinstance(assessment, dict) or set(assessment) != ASSESSMENT_FIELDS:
            raise Phase0EvidenceError(f"VIPER assessment {index} fields differ")
        if assessment["confirmed_defect"] and not assessment["independent_check"]:
            raise Phase0EvidenceError(
                f"VIPER assessment {index} lacks independent confirmation"
            )

    payload = {
        "schema_version": "rico.phase0_evidence.v1",
        "receipts": {
            role: _evidence_identity(path, repository_root)
            for role, path in sorted(receipts.items())
        },
        "viper_assessments": _evidence_identity(assessment_path, repository_root),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload
