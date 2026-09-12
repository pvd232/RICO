"""Contract tests for automatic PairBlock proposal-gate status."""

from __future__ import annotations

import ast
import json
import shutil
from dataclasses import fields, replace
from datetime import datetime, timezone
from pathlib import Path

import pytest
from conftest import (
    CHECKLIST_PATH,
    CONTRACT_PATH,
    DEPENDENCY_PAIR_BLOCK_ID,
    FIXTURE_SOURCE_PATH,
    PAIR_BLOCK_ID,
    REQUIREMENT_ID,
    SOURCE_PATH,
    TEST_PATH,
    TEST_PROFILE,
    UNKNOWN_PAIR_BLOCK_ID,
    PairBlockFixture,
    RepositoryFactory,
)
from tools.execution_identity import ExecutionIdentity
from tools.profile import MANTRA_PHASE0_PROFILE, ChecklistProfile, LifecyclePolicy
from tools.run_pairblock_gate import (
    DEFAULT_MASTER_CHECKLIST_VALIDATOR,
    GateReceipt,
    PairBlockGateError,
    run_gate,
    validate_traceability,
)

NOW = datetime(2026, 9, 11, 16, 0, tzinfo=timezone.utc)


def validate_test_repository(
    repository: Path,
) -> tuple[dict[str, object], dict[str, object]]:
    """Validate one generated repository with the generic test profile."""

    return validate_traceability(repository, profile=TEST_PROFILE)


def run_test_gate(
    repository: Path,
    pair_block_id: str = PAIR_BLOCK_ID,
    *,
    validator_path: Path = DEFAULT_MASTER_CHECKLIST_VALIDATOR,
) -> Path:
    """Run one generated repository's gate with the generic test profile."""

    return run_gate(
        repository,
        pair_block_id,
        now=NOW,
        validator_path=validator_path,
        profile=TEST_PROFILE,
    )


def passing_command() -> str:
    """Return a gate that names both bounded files and reports two passes."""

    return (
        "python -c 'print(\"2 passed in 0.01s\")' "
        f"{SOURCE_PATH.as_posix()} {TEST_PATH.as_posix()}"
    )


def failing_command() -> str:
    """Return a failing gate that still names both bounded files."""

    return (
        "python -c 'import sys; print(\"failed\"); sys.exit(1)' "
        f"{SOURCE_PATH.as_posix()} {TEST_PATH.as_posix()}"
    )


def test_profile_fixture_compiles_with_global_validator(
    repository_factory: RepositoryFactory,
) -> None:
    """Compile the generic profile and pass it through the global validator."""

    repository = repository_factory(command=passing_command())
    rows, manifest = validate_test_repository(repository)

    assert set(rows) == {PAIR_BLOCK_ID}
    assert manifest["schema_version"] == 2


def test_lifecycle_policy_rejects_undeclared_transition_status() -> None:
    """Reject a transition whose status has no normalized-state definition."""

    with pytest.raises(ValueError, match="undeclared statuses"):
        replace(TEST_PROFILE.lifecycle, review_status="Unlisted")


def test_checklist_profile_requires_two_phase_capture_groups() -> None:
    """Require the phase expression to expose both ordering components."""

    with pytest.raises(ValueError, match="numeric and letter groups"):
        replace(TEST_PROFILE, phase_pattern=r"[0-9]+[A-Z]")


def test_mantra_profile_compiles_current_contract() -> None:
    """Compile the real MANTRA documents through their project profile."""

    repository = Path(__file__).parents[3]
    rows, manifest = validate_traceability(
        repository,
        profile=MANTRA_PHASE0_PROFILE,
    )

    assert "P0-PB-10" in rows
    assert manifest["checklist_id"] == MANTRA_PHASE0_PROFILE.checklist_id


def test_passing_gate_writes_receipt_and_advances_one_status(
    repository_factory: RepositoryFactory,
) -> None:
    """Bind a pass to evidence before advancing the authoritative row."""

    repository = repository_factory(command=passing_command())
    receipt_path = run_test_gate(repository)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    checklist = (
        repository / CHECKLIST_PATH
    ).read_text(encoding="utf-8")

    assert receipt["result"] == "passed"
    assert receipt["status_before"] == TEST_PROFILE.lifecycle.drafting_status
    assert receipt["status_after"] == TEST_PROFILE.lifecycle.review_status
    assert receipt["exit_code"] == 0
    assert len(receipt["identity_before"]["source_sha256"]) == 2
    assert receipt["master_validator_path"].endswith(
        ".agents/scripts/validate-master-checklist.py"
    )
    assert receipt["identity_before"] == receipt["identity_after"]
    assert receipt["identity_drift"] == {}
    assert receipt["normalized_manifest"]["schema_version"] == 2
    assert "Passed: `2` tests" in checklist
    assert TEST_PROFILE.lifecycle.review_status in checklist
    assert receipt_path.name in checklist


def test_failing_gate_retains_receipt_without_changing_checklist(
    repository_factory: RepositoryFactory,
) -> None:
    """Preserve checklist bytes when the observing command fails."""

    repository = repository_factory(command=failing_command())
    checklist_path = repository / CHECKLIST_PATH
    before = checklist_path.read_bytes()
    receipt_path = run_test_gate(repository)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert receipt["result"] == "failed"
    assert receipt["status_after"] == TEST_PROFILE.lifecycle.drafting_status
    assert receipt["exit_code"] == 1
    assert checklist_path.read_bytes() == before
    assert (
        receipt["identity_before"]["checklist_sha256"]
        == receipt["identity_after"]["checklist_sha256"]
        == receipt["checklist_written_sha256"]
    )


def test_unknown_pair_block_is_rejected(
    repository_factory: RepositoryFactory,
) -> None:
    """Refuse a gate that lacks an authoritative checklist row."""

    repository = repository_factory(command=passing_command())
    with pytest.raises(PairBlockGateError, match="unknown PairBlock"):
        run_test_gate(repository, UNKNOWN_PAIR_BLOCK_ID)


def test_duplicate_status_anchor_is_rejected(
    repository_factory: RepositoryFactory,
) -> None:
    """Require one status row for each PairBlock identity."""

    repository = repository_factory(command=passing_command())
    checklist = repository / CHECKLIST_PATH
    text = checklist.read_text(encoding="utf-8")
    row = next(
        line
        for line in text.splitlines()
        if f"status-{PAIR_BLOCK_ID.lower()}" in line
    )
    checklist.write_text(text.replace(row, row + "\n" + row), encoding="utf-8")

    with pytest.raises(PairBlockGateError, match="duplicate PairBlock row"):
        validate_test_repository(repository)


def test_unknown_dependency_is_rejected(
    repository_factory: RepositoryFactory,
) -> None:
    """Require every dependency to resolve to another status row."""

    repository = repository_factory(
        command=passing_command(),
        dependencies=(UNKNOWN_PAIR_BLOCK_ID,),
    )

    with pytest.raises(PairBlockGateError, match="unknown dependency"):
        validate_test_repository(repository)


def test_missing_owner_is_rejected(
    repository_factory: RepositoryFactory,
) -> None:
    """Keep every executable proposal connected to a named owner."""

    repository = repository_factory(command=passing_command())
    contract = repository / CONTRACT_PATH
    text = contract.read_text(encoding="utf-8").replace(
        "Test author.", ""
    )
    contract.write_text(text, encoding="utf-8")

    with pytest.raises(PairBlockGateError, match="implementation owner is missing"):
        validate_test_repository(repository)


def test_missing_proposed_source_is_rejected(
    repository_factory: RepositoryFactory,
) -> None:
    """Keep every declared code boundary connected to an existing file."""

    repository = repository_factory(command=passing_command())
    (repository / SOURCE_PATH).unlink()

    with pytest.raises(PairBlockGateError, match="proposed source is missing"):
        validate_test_repository(repository)


def test_missing_fixture_source_is_rejected(
    repository_factory: RepositoryFactory,
) -> None:
    """Keep every declared fixture inside the hashed proposal boundary."""

    repository = repository_factory(command=passing_command())
    fixture = repository / FIXTURE_SOURCE_PATH
    fixture.parent.mkdir(parents=True)
    fixture.write_text("profile\n", encoding="utf-8")
    contract = repository / CONTRACT_PATH
    text = contract.read_text(encoding="utf-8").replace(
        "**Focused check:**",
        "**Fixture boundary:**\n\n"
        f"- [profile.md](../../{FIXTURE_SOURCE_PATH.as_posix()})\n\n"
        "**Focused check:**",
    )
    contract.write_text(text, encoding="utf-8")
    fixture.unlink()

    with pytest.raises(PairBlockGateError, match="proposed source is missing"):
        validate_test_repository(repository)


def test_gate_must_name_every_observing_test(
    repository_factory: RepositoryFactory,
) -> None:
    """Require the focused command to execute every declared observing test."""

    command = (
        "python -c 'print(\"2 passed in 0.01s\")' "
        f"{TEST_PATH.name}"
    )
    repository = repository_factory(command=command)

    with pytest.raises(PairBlockGateError, match="focused check does not name"):
        validate_test_repository(repository)


def test_duplicate_requirement_id_is_rejected(
    repository_factory: RepositoryFactory,
) -> None:
    """Keep stable requirement identities unique in the governing contract."""

    repository = repository_factory(command=passing_command())
    contract = repository / CONTRACT_PATH
    text = contract.read_text(encoding="utf-8")
    row = (
        f"| `{REQUIREMENT_ID}` | Retain gate evidence. | "
        f"[`{PAIR_BLOCK_ID}`](#{PAIR_BLOCK_ID.lower()}-declaration) |\n"
    )
    contract.write_text(text.replace(row, row + row), encoding="utf-8")

    with pytest.raises(PairBlockGateError, match="duplicate requirement_id"):
        validate_test_repository(repository)


def test_unmapped_pair_block_is_rejected(
    repository_factory: RepositoryFactory,
) -> None:
    """Keep every staged block reachable from a contract requirement."""

    repository = repository_factory(command=passing_command())
    contract = repository / CONTRACT_PATH
    text = contract.read_text(encoding="utf-8").replace(
        f"(#{PAIR_BLOCK_ID.lower()}-declaration)",
        f"(#{UNKNOWN_PAIR_BLOCK_ID.lower()}-declaration)",
        1,
    )
    contract.write_text(text, encoding="utf-8")

    with pytest.raises(PairBlockGateError, match="requirement-map link differs"):
        validate_test_repository(repository)


def test_proposed_code_must_stay_in_governing_contract(
    repository_factory: RepositoryFactory,
) -> None:
    """Reject a code pointer that leaves its requirement's contract."""

    repository = repository_factory(command=passing_command())
    checklist = repository / CHECKLIST_PATH
    text = checklist.read_text(encoding="utf-8").replace(
        f"../contracts/{CONTRACT_PATH.name}#{PAIR_BLOCK_ID.lower()}-proposed-code",
        f"../contracts/other.md#{PAIR_BLOCK_ID.lower()}-proposed-code",
    )
    checklist.write_text(text, encoding="utf-8")

    with pytest.raises(PairBlockGateError, match="leaves the governing contract"):
        validate_test_repository(repository)


def test_every_contract_pair_block_requires_one_status_row(
    repository_factory: RepositoryFactory,
) -> None:
    """Keep the status inventory equal to the contract's PairBlock inventory."""

    repository = repository_factory(command=passing_command())
    contract = repository / CONTRACT_PATH
    text = contract.read_text(encoding="utf-8").replace(
        "## Ownership",
        "## Ownership\n\n"
        f'| <a id="{DEPENDENCY_PAIR_BLOCK_ID.lower()}-declaration"></a>'
        f"[`{DEPENDENCY_PAIR_BLOCK_ID}`](#) | Exercise dependency. | "
        "Test author. | Pending | Gate. |",
    )
    contract.write_text(text, encoding="utf-8")

    with pytest.raises(PairBlockGateError, match="PairBlock inventory differs"):
        validate_test_repository(repository)


def test_unresolved_pair_block_dependency_blocks_gate(
    repository_factory: RepositoryFactory,
) -> None:
    """Do not run a proposal whose declared predecessor remains in drafting."""

    dependency = PairBlockFixture(
        DEPENDENCY_PAIR_BLOCK_ID,
        TEST_PROFILE.lifecycle.drafting_status,
    )
    repository = repository_factory(
        command=passing_command(),
        dependencies=(DEPENDENCY_PAIR_BLOCK_ID,),
        dependency=dependency,
    )

    with pytest.raises(
        PairBlockGateError,
        match=f"dependency {DEPENDENCY_PAIR_BLOCK_ID} is not resolved",
    ):
        run_test_gate(repository)


@pytest.mark.parametrize(
    ("target", "drift_field"),
    [
        ("source", "source_sha256"),
        ("contract", "contract_sha256"),
        ("checklist", "checklist_sha256"),
        ("validator", "master_validator_sha256"),
        ("head", "git_head"),
    ],
)
def test_execution_identity_drift_invalidates_pass(
    tmp_path: Path,
    repository_factory: RepositoryFactory,
    target: str,
    drift_field: str,
) -> None:
    """Reject a nominal pass when any execution identity changes in flight."""

    repository = repository_factory(command=passing_command())
    validator = tmp_path / "validate-master-checklist.py"
    shutil.copyfile(DEFAULT_MASTER_CHECKLIST_VALIDATOR, validator)
    paths = {
        "source": SOURCE_PATH.as_posix(),
        "contract": CONTRACT_PATH.as_posix(),
        "checklist": CHECKLIST_PATH.as_posix(),
        "validator": str(validator),
    }
    if target == "head":
        command = (
            "git commit --allow-empty -q -m drift && "
            "python -c 'print(\"2 passed in 0.01s\")' "
            f"{SOURCE_PATH.as_posix()} {TEST_PATH.as_posix()}"
        )
    else:
        path = paths[target]
        command = (
            "python -c 'from pathlib import Path; "
            f"path = Path(\"{path}\"); "
            "path.write_bytes(path.read_bytes() + b\"\\n\"); "
            "print(\"2 passed in 0.01s\")' "
            f"{SOURCE_PATH.as_posix()} {TEST_PATH.as_posix()}"
        )
    contract = repository / CONTRACT_PATH
    contract.write_text(
        contract.read_text(encoding="utf-8").replace(passing_command(), command),
        encoding="utf-8",
    )

    receipt_path = run_test_gate(repository, validator_path=validator)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    checklist = (
        repository / CHECKLIST_PATH
    ).read_text(encoding="utf-8")

    assert receipt["result"] == "invalidated"
    assert receipt["status_after"] == TEST_PROFILE.lifecycle.drafting_status
    assert drift_field in receipt["identity_drift"]
    assert TEST_PROFILE.lifecycle.review_status not in checklist


def test_persisted_schema_fields_have_descriptions() -> None:
    """Give every persisted receipt field machine-readable semantic meaning."""

    for model in (
        ExecutionIdentity,
        GateReceipt,
        LifecyclePolicy,
        ChecklistProfile,
    ):
        for model_field in fields(model):
            assert model_field.metadata.get("description"), (
                f"{model.__name__}.{model_field.name} lacks a description"
            )


def test_active_modules_and_definitions_have_docstrings() -> None:
    """Keep every active module, class, function, and method documented."""

    root = Path(__file__).parents[1]
    paths = [
        root / "tools/__init__.py",
        root / "tools/checklist_profile.py",
        root / "tools/execution_identity.py",
        root / "tools/profile.py",
        root / "tools/run_pairblock_gate.py",
        root / "tests/conftest.py",
        Path(__file__),
    ]
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        assert ast.get_docstring(tree), f"{path} lacks a module docstring"
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                assert ast.get_docstring(node), (
                    f"{path}:{node.lineno} {node.name} lacks a docstring"
                )
