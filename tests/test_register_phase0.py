"""Test Phase 0 identity registration and its VIPER stage boundary."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from viper.artifacts import StageArtifactRef
from viper.authoring import input, run_artifact
from viper.references import LocalFileRef, ResolvedRunRef

from tools.freeze_phase0 import REQUIRED_EVIDENCE_ROLES, sha256_file
from tools.register_phase0 import (
    DIRECT_EVIDENCE_ROLES,
    PRIOR_RUN_EVIDENCE_ROLES,
    REQUIRED_STAGE_INPUTS,
    RESTORATION_BUNDLE_FILES,
    Phase0RegistrationError,
    build_phase0_registration_study,
    register_phase0,
)


def write_fixture(root: Path) -> SimpleNamespace:
    """Write one complete materialized evidence set and its frozen index."""

    bundle = root / "restoration"
    bundle.mkdir()
    inputs: dict[str, Path] = {"restoration_evidence": bundle}
    evidence: dict[str, dict[str, object]] = {}
    for role in sorted(REQUIRED_EVIDENCE_ROLES):
        if role in RESTORATION_BUNDLE_FILES:
            path = bundle / RESTORATION_BUNDLE_FILES[role]
        else:
            path = root / f"{role}.json"
            inputs[role] = path
        path.write_text(f'{{"role": "{role}"}}\n', encoding="utf-8")
        evidence[role] = {
            "repository": "fixture",
            "path": f"evidence/{role}.json",
            "byte_count": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    ledger = root / "ledger.json"
    ledger.write_text('{"ledger": true}\n', encoding="utf-8")
    inputs["ledger"] = ledger
    index = root / "index.json"
    index.write_text(
        json.dumps(
            {
                "schema_version": "rico.phase0_evidence.v1",
                "evidence": evidence,
                "viper_usefulness_ledger": {
                    "repository": "fixture",
                    "path": "evidence/ledger.json",
                    "byte_count": ledger.stat().st_size,
                    "sha256": sha256_file(ledger),
                },
            }
        ),
        encoding="utf-8",
    )
    inputs["index"] = index
    return SimpleNamespace(
        inputs=inputs,
        outputs={"receipt": root / "receipt.json"},
        config=SimpleNamespace(),
    )


def declared_stage_inputs(tmp_path: Path) -> dict[str, object]:
    """Declare direct RICO evidence and prior-run MANTRA evidence."""

    stage_inputs: dict[str, object] = {
        name: input(name, path=f"evidence/{name}.json", data_role="benchmark")
        for name in REQUIRED_STAGE_INPUTS - PRIOR_RUN_EVIDENCE_ROLES
    }
    run = ResolvedRunRef(
        sha256="a" * 64,
        bytes=1,
        stored_at=LocalFileRef(
            workspace=tmp_path,
            store_id="0" * 32,
            commit="b" * 64,
            path="runs/source/resolved.yaml",
        ),
    )
    for name in PRIOR_RUN_EVIDENCE_ROLES:
        stage_inputs[name] = run_artifact(
            run,
            StageArtifactRef(stage_id="build", artifact_name=name),
            path=f"evidence/{name}.json",
            data_role="benchmark",
        )
    return stage_inputs


def test_registers_every_indexed_evidence_identity(tmp_path: Path) -> None:
    """Write the terminal receipt after every indexed byte identity agrees."""

    context = write_fixture(tmp_path)
    register_phase0(context)
    receipt = json.loads(context.outputs["receipt"].read_text(encoding="utf-8"))

    assert receipt["passed"] is True
    assert set(receipt["evidence"]) == REQUIRED_EVIDENCE_ROLES
    assert receipt["index_sha256"] == sha256_file(context.inputs["index"])


def test_reads_the_approved_disk_import_receipt_from_restoration_evidence() -> None:
    """Bind the restoration role to the receipt produced by the disk-import route."""

    assert RESTORATION_BUNDLE_FILES["restoration_receipt"] == (
        "disk_import_receipt.json"
    )


@pytest.mark.parametrize("role", sorted(REQUIRED_EVIDENCE_ROLES))
def test_rejects_changed_evidence_identity(tmp_path: Path, role: str) -> None:
    """Expose a changed direct or restoration-bundle evidence file."""

    context = write_fixture(tmp_path)
    if role in RESTORATION_BUNDLE_FILES:
        path = context.inputs["restoration_evidence"] / RESTORATION_BUNDLE_FILES[role]
    else:
        path = context.inputs[role]
    path.write_bytes(path.read_bytes() + b"changed")

    with pytest.raises(Phase0RegistrationError, match=role):
        register_phase0(context)


def test_rejects_changed_usefulness_ledger(tmp_path: Path) -> None:
    """Expose a usefulness ledger that differs from the frozen identity."""

    context = write_fixture(tmp_path)
    context.inputs["ledger"].write_bytes(b"changed")

    with pytest.raises(Phase0RegistrationError, match="ledger identity differs"):
        register_phase0(context)


def test_declares_one_governed_registration_stage(tmp_path: Path) -> None:
    """Connect each named evidence source to one terminal VIPER receipt."""

    stage_inputs = declared_stage_inputs(tmp_path)
    study = build_phase0_registration_study(stage_inputs)
    registration = study.variants["complete"].stages["register"]

    assert set(registration.spec.inputs) == REQUIRED_STAGE_INPUTS
    assert set(registration.spec.outputs.keys()) == {"receipt"}
    assert registration.spec.file_access == "declared"
    assert study.variants["complete"].estimator == registration.outputs["receipt"]
    assert DIRECT_EVIDENCE_ROLES < REQUIRED_STAGE_INPUTS


def test_rejects_incomplete_stage_input_map() -> None:
    """Require every direct and prior-run evidence input before compilation."""

    with pytest.raises(Phase0RegistrationError, match="inputs differ"):
        build_phase0_registration_study({})


@pytest.mark.parametrize("role", sorted(PRIOR_RUN_EVIDENCE_ROLES))
def test_rejects_disconnected_mantra_evidence(tmp_path: Path, role: str) -> None:
    """Reject a local file substituted for one MANTRA producer artifact."""

    stage_inputs = declared_stage_inputs(tmp_path)
    stage_inputs[role] = input(
        role,
        path=f"evidence/{role}.json",
        data_role="benchmark",
    )

    with pytest.raises(Phase0RegistrationError, match="prior-run evidence inputs"):
        build_phase0_registration_study(stage_inputs)


def test_rico_declares_its_viper_workspace_and_runtime_dependency() -> None:
    """Supply the workspace marker and lockfile consumed by the real run."""

    proposal_root = Path(__file__).parents[1]

    assert (proposal_root / "viper.toml").read_text(encoding="utf-8") == (
        "[workspace]\nschema_version = 2\n"
    )
    assert (proposal_root / "requirements.txt").read_text(encoding="utf-8") == (
        "viper-provenance\n"
    )
