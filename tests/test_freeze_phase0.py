"""Test Phase 0 role coverage, repository custody, and ledger completeness."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.freeze_phase0 import (
    REQUIRED_EVIDENCE_ROLES,
    EvidenceLocation,
    Phase0EvidenceError,
    freeze_phase0,
)


def assessment(
    check_id: str = "graph-completeness",
    *,
    classification: str = "expected_behavior",
    independent_check: str = "tests/test_graph.py::test_complete",
) -> dict[str, object]:
    """Return one complete usefulness assessment for a fixture ledger."""

    return {
        "check_id": check_id,
        "claimed_guarantee": "Every required input reaches the replay.",
        "observed_result": "passed",
        "defect_classification": classification,
        "independent_check": independent_check,
        "ordinary_check_equivalent": "focused pytest",
        "false_alarms": [],
        "infrastructure_failures": [],
        "elapsed_seconds": 1.0,
        "work_added": "one gate invocation",
        "later_reuse": "pending",
    }


def write_inputs(
    root: Path,
) -> tuple[dict[str, Path], dict[str, EvidenceLocation], EvidenceLocation]:
    """Write fixture evidence across two declared repository roots."""

    roots = {"rico": root / "rico", "mantra": root / "mantra"}
    for repository_root in roots.values():
        repository_root.mkdir()
    evidence = {}
    for index, role in enumerate(sorted(REQUIRED_EVIDENCE_ROLES)):
        owner = "rico" if index % 2 == 0 else "mantra"
        relative = f"evidence/{role}.json"
        path = roots[owner] / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f'{{"role": "{role}"}}\n', encoding="utf-8")
        evidence[role] = EvidenceLocation(owner, relative)
    ledger_path = roots["rico"] / "evidence/viper-usefulness.json"
    ledger_path.write_text(
        json.dumps(
            {
                "schema_version": "rico.viper_usefulness.v1",
                "assessed_checks": ["graph-completeness"],
                "assessments": [assessment()],
            }
        ),
        encoding="utf-8",
    )
    return roots, evidence, EvidenceLocation("rico", "evidence/viper-usefulness.json")


def freeze_fixture(root: Path) -> dict[str, object]:
    """Freeze one complete fixture and return its parsed payload."""

    roots, evidence, ledger = write_inputs(root)
    return freeze_phase0(
        repository_roots=roots,
        evidence=evidence,
        assessment_ledger=ledger,
        output=EvidenceLocation("rico", "evidence/phase0.json"),
    )


def test_freezes_every_required_role_across_repository_owners(tmp_path: Path) -> None:
    """Retain a portable identity for every contract-required evidence role."""

    payload = freeze_fixture(tmp_path)

    assert set(payload["evidence"]) == REQUIRED_EVIDENCE_ROLES
    assert payload["schema_version"] == "rico.phase0_evidence.v1"
    assert {item["repository"] for item in payload["evidence"].values()} == {
        "rico",
        "mantra",
    }


def test_output_is_deterministic(tmp_path: Path) -> None:
    """Produce identical bytes from the same evidence identities."""

    roots, evidence, ledger = write_inputs(tmp_path)
    first = roots["rico"] / "evidence/first.json"
    second = roots["rico"] / "evidence/second.json"
    for output in (first, second):
        freeze_phase0(
            repository_roots=roots,
            evidence=evidence,
            assessment_ledger=ledger,
            output=EvidenceLocation("rico", output.relative_to(roots["rico"]).as_posix()),
        )

    assert first.read_bytes() == second.read_bytes()


def test_rejects_missing_evidence_role(tmp_path: Path) -> None:
    """Expose one omitted contract-required evidence role."""

    roots, evidence, ledger = write_inputs(tmp_path)
    evidence.pop("mil_replay_receipt")
    with pytest.raises(Phase0EvidenceError, match="evidence roles differ"):
        freeze_phase0(
            repository_roots=roots,
            evidence=evidence,
            assessment_ledger=ledger,
            output=EvidenceLocation("rico", "phase0.json"),
        )


@pytest.mark.parametrize(
    ("location", "message"),
    [
        (EvidenceLocation("unknown", "evidence/a.json"), "unknown evidence repository"),
        (EvidenceLocation("rico", "evidence/missing.json"), "No such file"),
    ],
)
def test_rejects_unresolvable_evidence(
    tmp_path: Path,
    location: EvidenceLocation,
    message: str,
) -> None:
    """Expose an unknown owner or absent evidence file."""

    roots, evidence, ledger = write_inputs(tmp_path)
    evidence["capacity_receipt"] = location
    with pytest.raises((Phase0EvidenceError, FileNotFoundError), match=message):
        freeze_phase0(
            repository_roots=roots,
            evidence=evidence,
            assessment_ledger=ledger,
            output=EvidenceLocation("rico", "phase0.json"),
        )


@pytest.mark.parametrize(
    "path",
    ["/absolute.json", "../escape.json", "a/../b.json", "windows\\path.json", ""],
)
def test_rejects_noncanonical_evidence_paths(path: str) -> None:
    """Require stable repository-relative POSIX evidence paths."""

    with pytest.raises(Phase0EvidenceError, match="evidence"):
        EvidenceLocation("rico", path)


def test_rejects_duplicate_evidence_location(tmp_path: Path) -> None:
    """Require each semantic role to bind a distinct evidence file."""

    roots, evidence, ledger = write_inputs(tmp_path)
    evidence["capacity_receipt"] = evidence["dependency_graph"]
    with pytest.raises(Phase0EvidenceError, match="distinct file"):
        freeze_phase0(
            repository_roots=roots,
            evidence=evidence,
            assessment_ledger=ledger,
            output=EvidenceLocation("rico", "phase0.json"),
        )


def test_rejects_unassessed_declared_check(tmp_path: Path) -> None:
    """Require the assessment rows to cover the ledger's declared check set."""

    roots, evidence, ledger = write_inputs(tmp_path)
    ledger_path = roots[ledger.repository] / ledger.path
    value = json.loads(ledger_path.read_text(encoding="utf-8"))
    value["assessed_checks"].append("file-access")
    ledger_path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(Phase0EvidenceError, match="assessment rows differ"):
        freeze_phase0(
            repository_roots=roots,
            evidence=evidence,
            assessment_ledger=ledger,
            output=EvidenceLocation("rico", "phase0.json"),
        )


def test_confirmed_defect_requires_independent_check(tmp_path: Path) -> None:
    """Bind each confirmed framework defect to an independent check."""

    roots, evidence, ledger = write_inputs(tmp_path)
    ledger_path = roots[ledger.repository] / ledger.path
    value = json.loads(ledger_path.read_text(encoding="utf-8"))
    value["assessments"] = [
        assessment(classification="framework_gap", independent_check="")
    ]
    ledger_path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(Phase0EvidenceError, match="independent confirmation"):
        freeze_phase0(
            repository_roots=roots,
            evidence=evidence,
            assessment_ledger=ledger,
            output=EvidenceLocation("rico", "phase0.json"),
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("elapsed_seconds", True, "elapsed seconds differs"),
        ("elapsed_seconds", -1, "elapsed seconds differs"),
        ("false_alarms", [""], "false_alarms differs"),
        ("claimed_guarantee", "", "text fields differ"),
        ("defect_classification", "unknown", "defect classification differs"),
    ],
)
def test_rejects_malformed_assessment_field(
    tmp_path: Path,
    field: str,
    value: object,
    message: str,
) -> None:
    """Require field types that support a stable usefulness assessment."""

    roots, evidence, ledger = write_inputs(tmp_path)
    ledger_path = roots[ledger.repository] / ledger.path
    document = json.loads(ledger_path.read_text(encoding="utf-8"))
    document["assessments"][0][field] = value
    ledger_path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(Phase0EvidenceError, match=message):
        freeze_phase0(
            repository_roots=roots,
            evidence=evidence,
            assessment_ledger=ledger,
            output=EvidenceLocation("rico", "phase0.json"),
        )


def test_rejects_repository_aliases(tmp_path: Path) -> None:
    """Require each repository label to identify one distinct custody root."""

    roots, evidence, ledger = write_inputs(tmp_path)
    roots["mantra"] = roots["rico"]
    with pytest.raises(Phase0EvidenceError, match="distinct directories"):
        freeze_phase0(
            repository_roots=roots,
            evidence=evidence,
            assessment_ledger=ledger,
            output=EvidenceLocation("rico", "phase0.json"),
        )


def test_rejects_output_that_overwrites_evidence(tmp_path: Path) -> None:
    """Preserve every indexed input when the Phase 0 index is written."""

    roots, evidence, ledger = write_inputs(tmp_path)
    with pytest.raises(Phase0EvidenceError, match="must not overwrite"):
        freeze_phase0(
            repository_roots=roots,
            evidence=evidence,
            assessment_ledger=ledger,
            output=ledger,
        )
