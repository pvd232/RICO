"""Test required receipts, independent confirmation, and frozen identities."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools.freeze_phase0 import (
    REQUIRED_RECEIPTS,
    Phase0EvidenceError,
    freeze_phase0,
)


def assessment(*, confirmed_defect: bool = False, independent_check: str = "test"):
    """Return one complete VIPER usefulness assessment."""

    return {
        "check_id": "graph-completeness",
        "claimed_guarantee": "Every required input reaches the replay.",
        "outcome": "passed",
        "independent_check": independent_check,
        "ordinary_check_equivalent": "focused pytest",
        "elapsed_seconds": 1.0,
        "confirmed_defect": confirmed_defect,
        "later_reuse": "pending",
    }


def write_inputs(root: Path):
    """Write one receipt per required role and a complete assessment ledger."""

    receipts = {}
    for role in REQUIRED_RECEIPTS:
        path = root / "evidence" / f"{role}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f'{{"role": "{role}"}}\n', encoding="utf-8")
        receipts[role] = path
    ledger = root / "evidence/viper_assessments.json"
    ledger.write_text(json.dumps([assessment()]), encoding="utf-8")
    return receipts, ledger


def test_freezes_every_required_receipt_and_assessment(tmp_path: Path) -> None:
    """Write one digest-bound identity for each Phase 0 evidence role."""

    receipts, ledger = write_inputs(tmp_path)
    output = tmp_path / "evidence/phase0.json"
    payload = freeze_phase0(
        repository_root=tmp_path,
        receipts=receipts,
        assessment_path=ledger,
        output_path=output,
    )

    assert set(payload["receipts"]) == REQUIRED_RECEIPTS
    assert payload["schema_version"] == "rico.phase0_evidence.v1"
    assert output.is_file()


def test_rejects_missing_receipt_role(tmp_path: Path) -> None:
    """Reject a freeze that omits one required result."""

    receipts, ledger = write_inputs(tmp_path)
    receipts.pop("mil_replay")
    with pytest.raises(Phase0EvidenceError, match="receipt roles differ"):
        freeze_phase0(
            repository_root=tmp_path,
            receipts=receipts,
            assessment_path=ledger,
            output_path=tmp_path / "phase0.json",
        )


def test_confirmed_defect_requires_independent_check(tmp_path: Path) -> None:
    """Require a named independent check for each VIPER defect claim."""

    receipts, ledger = write_inputs(tmp_path)
    ledger.write_text(
        json.dumps([assessment(confirmed_defect=True, independent_check="")]),
        encoding="utf-8",
    )
    with pytest.raises(Phase0EvidenceError, match="independent confirmation"):
        freeze_phase0(
            repository_root=tmp_path,
            receipts=receipts,
            assessment_path=ledger,
            output_path=tmp_path / "phase0.json",
        )
