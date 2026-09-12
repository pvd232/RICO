"""Freeze the complete Phase 0 evidence set into one content-bound index."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

REQUIRED_EVIDENCE_ROLES = frozenset(
    {
        "capacity_receipt",
        "cross_workspace_assessment",
        "dependency_graph",
        "environment_receipt",
        "graph_completeness_report",
        "hopfield_replay_receipt",
        "mil_replay_receipt",
        "restoration_bindings",
        "restoration_receipt",
        "stage_file_access_receipt",
        "viper_graph_receipt",
    }
)
ASSESSMENT_FIELDS = frozenset(
    {
        "check_id",
        "claimed_guarantee",
        "observed_result",
        "defect_classification",
        "independent_check",
        "ordinary_check_equivalent",
        "false_alarms",
        "infrastructure_failures",
        "elapsed_seconds",
        "work_added",
        "later_reuse",
    }
)
CONFIRMED_DEFECTS = frozenset({"framework_gap", "implementation_defect"})
DEFECT_CLASSIFICATIONS = CONFIRMED_DEFECTS | frozenset(
    {"expected_behavior", "false_alarm", "infrastructure_failure", "intentional_restriction"}
)
TEXT_ASSESSMENT_FIELDS = ASSESSMENT_FIELDS - {
    "false_alarms",
    "infrastructure_failures",
    "elapsed_seconds",
}


class Phase0EvidenceError(ValueError):
    """Report an incomplete, ambiguous, or malformed Phase 0 evidence set."""


@dataclass(frozen=True, slots=True)
class EvidenceLocation:
    """Identify one evidence file by repository owner and relative path."""

    repository: str
    path: str

    def __post_init__(self) -> None:
        """Require a named repository and a normalized relative path."""

        candidate = Path(self.path)
        if (
            not self.repository
            or candidate.is_absolute()
            or ".." in candidate.parts
            or "\\" in self.path
        ):
            raise Phase0EvidenceError("evidence location must use a repository-relative path")
        if candidate.as_posix() != self.path or self.path in {"", "."}:
            raise Phase0EvidenceError("evidence path must use normalized POSIX syntax")


def sha256_file(path: Path) -> str:
    """Return one file's SHA-256 digest using bounded reads."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _resolve_location(
    location: EvidenceLocation,
    repository_roots: Mapping[str, Path],
) -> Path:
    """Resolve one evidence location beneath its declared repository root."""

    if location.repository not in repository_roots:
        raise Phase0EvidenceError(
            f"unknown evidence repository: {location.repository}"
        )
    root = repository_roots[location.repository].resolve(strict=True)
    resolved = (root / location.path).resolve(strict=True)
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise Phase0EvidenceError(
            f"evidence path is outside its repository: {location.path}"
        )
    return resolved


def _evidence_identity(
    location: EvidenceLocation,
    repository_roots: Mapping[str, Path],
) -> dict[str, object]:
    """Bind one repository-relative evidence path to its byte identity."""

    resolved = _resolve_location(location, repository_roots)
    return {
        "repository": location.repository,
        "path": location.path,
        "byte_count": resolved.stat().st_size,
        "sha256": sha256_file(resolved),
    }


def _validate_assessment_ledger(value: object) -> None:
    """Require one complete assessment for every ledger-declared VIPER check."""

    if not isinstance(value, dict) or set(value) != {
        "schema_version",
        "assessed_checks",
        "assessments",
    }:
        raise Phase0EvidenceError("VIPER usefulness ledger fields differ")
    if value["schema_version"] != "rico.viper_usefulness.v1":
        raise Phase0EvidenceError("VIPER usefulness ledger schema differs")
    check_ids = value["assessed_checks"]
    assessments = value["assessments"]
    if (
        not isinstance(check_ids, list)
        or not check_ids
        or any(not isinstance(item, str) or not item for item in check_ids)
        or len(check_ids) != len(set(check_ids))
    ):
        raise Phase0EvidenceError("assessed check IDs must be unique non-empty strings")
    if not isinstance(assessments, list):
        raise Phase0EvidenceError("VIPER assessments must be an array")
    observed_ids: list[str] = []
    for index, assessment in enumerate(assessments):
        if not isinstance(assessment, dict) or set(assessment) != ASSESSMENT_FIELDS:
            raise Phase0EvidenceError(f"VIPER assessment {index} fields differ")
        check_id = assessment["check_id"]
        if any(
            not isinstance(assessment[field], str) or not assessment[field]
            for field in TEXT_ASSESSMENT_FIELDS - {"independent_check"}
        ):
            raise Phase0EvidenceError(f"VIPER assessment {index} text fields differ")
        if not isinstance(assessment["independent_check"], str):
            raise Phase0EvidenceError(
                f"VIPER assessment {index} independent check differs"
            )
        if assessment["defect_classification"] not in DEFECT_CLASSIFICATIONS:
            raise Phase0EvidenceError(
                f"VIPER assessment {index} defect classification differs"
            )
        for field in ("false_alarms", "infrastructure_failures"):
            values = assessment[field]
            if not isinstance(values, list) or any(
                not isinstance(item, str) or not item for item in values
            ):
                raise Phase0EvidenceError(
                    f"VIPER assessment {index} {field} differs"
                )
        elapsed = assessment["elapsed_seconds"]
        if (
            isinstance(elapsed, bool)
            or not isinstance(elapsed, (int, float))
            or not math.isfinite(elapsed)
            or elapsed < 0
        ):
            raise Phase0EvidenceError(
                f"VIPER assessment {index} elapsed seconds differs"
            )
        observed_ids.append(check_id)
        if assessment["defect_classification"] in CONFIRMED_DEFECTS and not assessment[
            "independent_check"
        ]:
            raise Phase0EvidenceError(
                f"VIPER assessment {check_id} lacks independent confirmation"
            )
    if len(observed_ids) != len(set(observed_ids)) or set(observed_ids) != set(
        check_ids
    ):
        raise Phase0EvidenceError("assessed checks and assessment rows differ")


def freeze_phase0(
    *,
    repository_roots: Mapping[str, Path],
    evidence: Mapping[str, EvidenceLocation],
    assessment_ledger: EvidenceLocation,
    output: EvidenceLocation,
) -> dict[str, object]:
    """Write the deterministic identity index for the complete Phase 0 evidence."""

    if set(evidence) != REQUIRED_EVIDENCE_ROLES:
        raise Phase0EvidenceError(
            "evidence roles differ: "
            f"missing={sorted(REQUIRED_EVIDENCE_ROLES - set(evidence))}, "
            f"unexpected={sorted(set(evidence) - REQUIRED_EVIDENCE_ROLES)}"
        )
    resolved_roots = [path.resolve(strict=True) for path in repository_roots.values()]
    if len(resolved_roots) != len(set(resolved_roots)):
        raise Phase0EvidenceError("repository roots must identify distinct directories")
    locations = list(evidence.values()) + [assessment_ledger]
    location_keys = [(item.repository, item.path) for item in locations]
    if len(location_keys) != len(set(location_keys)):
        raise Phase0EvidenceError("each evidence role must resolve to a distinct file")
    ledger_path = _resolve_location(assessment_ledger, repository_roots)
    try:
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise Phase0EvidenceError("VIPER usefulness ledger is unreadable") from error
    _validate_assessment_ledger(ledger)
    if (output.repository, output.path) in location_keys:
        raise Phase0EvidenceError("Phase 0 index must not overwrite its evidence")
    if output.repository not in repository_roots:
        raise Phase0EvidenceError(f"unknown output repository: {output.repository}")
    output_root = repository_roots[output.repository].resolve(strict=True)
    output_path = (output_root / output.path).resolve()
    if not output_path.is_relative_to(output_root):
        raise Phase0EvidenceError("Phase 0 index path is outside its repository")
    payload = {
        "schema_version": "rico.phase0_evidence.v1",
        "evidence": {
            role: _evidence_identity(location, repository_roots)
            for role, location in sorted(evidence.items())
        },
        "viper_usefulness_ledger": _evidence_identity(
            assessment_ledger,
            repository_roots,
        ),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload
