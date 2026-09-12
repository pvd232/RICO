"""Contract tests for evidence-backed PairBlock lifecycle updates."""

from __future__ import annotations

import ast
import json
import shutil
import sys
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
    TEST_ADAPTER,
    TEST_DIALECT,
    TEST_PATH,
    TEST_PROFILE,
    UNKNOWN_PAIR_BLOCK_ID,
    PairBlockFixture,
    RepositoryFactory,
)

from tools.pairblock_status.checklist_profile import (
    MANTRA_PHASE0_ADAPTER,
    MarkdownChecklistAdapter,
)
from tools.pairblock_status.pairblock_controller import (
    DEFAULT_MASTER_CHECKLIST_VALIDATOR,
    EvidenceRef,
    PairBlockGateError,
    advance_pairblock,
    run_gate,
)
from tools.pairblock_status.profile import MANTRA_PHASE0_PROFILE, ChecklistProfile

NOW = datetime(2026, 9, 11, 16, 0, tzinfo=timezone.utc)


def validate_test_repository(
    repository: Path,
) -> tuple[dict[str, object], dict[str, object]]:
    """Validate one generated repository with the generic test profile."""

    return TEST_ADAPTER.validate_traceability(repository)


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
        adapter=TEST_ADAPTER,
    )


def advance_test_block(
    repository: Path,
    event: str,
    *,
    evidence_kind: str = "external",
) -> Path:
    """Advance the test PairBlock with one compact evidence reference."""

    return advance_pairblock(
        repository,
        PAIR_BLOCK_ID,
        event,
        EvidenceRef(
            kind=evidence_kind,
            target=f"{event} evidence",
            revision="test-revision",
        ),
        now=NOW,
        adapter=TEST_ADAPTER,
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


def test_lifecycle_policy_rejects_disconnected_transition_chain() -> None:
    """Require each lifecycle event to consume the preceding event's status."""

    with pytest.raises(ValueError, match="transition chain expected Review"):
        replace(
            TEST_PROFILE.lifecycle,
            transitions=(("approve", "Approved", "Applied"),),
        )


def test_lifecycle_policy_rejects_duplicate_non_code_event() -> None:
    """Keep non-code and implementation event names unambiguous."""

    with pytest.raises(ValueError, match="transition events must be unique"):
        replace(TEST_PROFILE.lifecycle, non_code_complete_event="approve")


def test_checklist_profile_requires_two_phase_capture_groups() -> None:
    """Require the phase expression to expose both ordering components."""

    with pytest.raises(ValueError, match="numeric and letter groups"):
        replace(TEST_PROFILE, phase_pattern=r"[0-9]+[A-Z]")


def test_project_profile_excludes_markdown_dialect() -> None:
    """Keep document layout out of the project policy model."""

    names = {model_field.name for model_field in fields(ChecklistProfile)}
    assert not names & {
        "pair_block_table_header",
        "requirement_table_header",
        "requirement_map_header",
        "contract_table_header",
        "contract_link_prefix",
        "proposed_code_link_prefix",
    }


@pytest.mark.parametrize(
    "field_name",
    [
        "pair_block_table_header",
        "requirement_table_header",
        "requirement_map_header",
        "contract_table_header",
        "contract_link_prefix",
        "proposed_code_link_prefix",
    ],
)
def test_markdown_dialect_rejects_empty_markers(field_name: str) -> None:
    """Require every RICO Markdown extension used by the adapter."""

    with pytest.raises(ValueError, match=f"{field_name} must not be empty"):
        replace(TEST_DIALECT, **{field_name: ""})


def test_gate_controller_does_not_parse_or_render_markdown() -> None:
    """Keep Markdown row manipulation inside the checklist adapter."""

    controller = (
        Path(__file__).parents[2]
        / "tools/pairblock_status/pairblock_controller.py"
    )
    tree = ast.parse(controller.read_text(encoding="utf-8"), filename=str(controller))
    function_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    string_literals = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }

    assert "_split_row" not in function_names
    assert "_replace_status_row" not in function_names
    assert not any("[receipt](" in value for value in string_literals)
    assert not any(" | " in value for value in string_literals)


def test_mantra_profile_compiles_current_contract() -> None:
    """Compile the real MANTRA documents through their project profile."""

    repository = Path(__file__).parents[2]
    rows, manifest = MANTRA_PHASE0_ADAPTER.validate_traceability(
        repository,
    )

    assert "P0-PB-10" in rows
    assert manifest["checklist_id"] == MANTRA_PHASE0_PROFILE.checklist_id


def test_applied_blocks_do_not_link_staging_proposals() -> None:
    """Require accepted blocks to point at active code or contract records."""

    repository = Path(__file__).parents[2]
    rows, _ = MANTRA_PHASE0_ADAPTER.validate_traceability(repository)

    for row in rows.values():
        if row.status in {"Applied", "Complete"}:
            assert "/staging/" not in row.proposed_code


def test_passing_gate_writes_receipt_and_advances_one_status(
    repository_factory: RepositoryFactory,
) -> None:
    """Bind a pass to evidence before advancing the authoritative row."""

    repository = repository_factory(command=passing_command())
    receipt_path = run_test_gate(repository)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    checklist = (repository / CHECKLIST_PATH).read_text(encoding="utf-8")

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


def test_gate_preserves_the_controller_python_environment(
    repository_factory: RepositoryFactory,
) -> None:
    """Run the declared command with the controller's active Python."""

    command = (
        "python -c 'import sys; "
        f'assert sys.executable == "{Path(sys.executable)}"; '
        'print("2 passed in 0.01s")\' '
        f"{SOURCE_PATH.as_posix()} {TEST_PATH.as_posix()}"
    )
    repository = repository_factory(command=command)

    receipt = json.loads(run_test_gate(repository).read_text(encoding="utf-8"))

    assert receipt["result"] == "passed"


def test_lifecycle_completion_updates_every_derived_status(
    repository_factory: RepositoryFactory,
) -> None:
    """Propagate one receipt chain through block, checkbox, requirement, and contract."""

    repository = repository_factory(command=passing_command())
    run_test_gate(repository)
    approval = advance_test_block(repository, "approve")
    accepted = advance_test_block(repository, "accept")
    completed = advance_test_block(repository, "register")
    rows, manifest = validate_test_repository(repository)
    checklist = (repository / CHECKLIST_PATH).read_text(encoding="utf-8")
    block = next(
        item
        for item in manifest["pair_blocks"]
        if item["pair_block_id"] == PAIR_BLOCK_ID
    )
    requirement = next(
        item
        for item in manifest["requirements"]
        if item["requirement_id"] == REQUIREMENT_ID
    )

    assert json.loads(approval.read_text(encoding="utf-8"))["status_after"] == "Approved"
    assert json.loads(accepted.read_text(encoding="utf-8"))["status_after"] == "Applied"
    assert json.loads(completed.read_text(encoding="utf-8"))["result"] == "applied"
    assert rows[PAIR_BLOCK_ID].status == "Complete"
    assert "- [x] Exercise `PB-GATE`." in checklist
    assert f"| `{REQUIREMENT_ID}` | Complete |" in checklist
    assert "| [Contract](../contracts/contract.md) | Complete |" in checklist
    assert block["state"] == requirement["state"] == "complete"
    assert block["completion_evidence"] == requirement["completion_evidence"]
    assert manifest["contracts"][0]["state"] == "complete"


def test_non_code_review_completion_updates_every_derived_status(
    repository_factory: RepositoryFactory,
) -> None:
    """Complete a documentation-only block from two external review receipts."""

    repository = repository_factory(command=passing_command(), proposed=False)
    submitted = advance_test_block(repository, "submit")
    confirmed = advance_test_block(repository, "confirm")
    rows, manifest = validate_test_repository(repository)
    checklist = (repository / CHECKLIST_PATH).read_text(encoding="utf-8")

    assert json.loads(submitted.read_text(encoding="utf-8"))["status_after"] == "Review"
    assert json.loads(confirmed.read_text(encoding="utf-8"))["status_after"] == "Complete"
    assert rows[PAIR_BLOCK_ID].status == "Complete"
    assert "- [x] Exercise `PB-GATE`." in checklist
    assert manifest["pair_blocks"][0]["state"] == "complete"
    assert manifest["requirements"][0]["state"] == "complete"
    assert manifest["contracts"][0]["state"] == "complete"


def test_non_code_review_rejects_runnable_proposal(
    repository_factory: RepositoryFactory,
) -> None:
    """Require executable proposals to reach review through their test gate."""

    repository = repository_factory(command=passing_command())

    with pytest.raises(PairBlockGateError, match="run its gate"):
        advance_test_block(repository, "submit")


def test_non_code_review_requires_external_evidence(
    repository_factory: RepositoryFactory,
) -> None:
    """Require a person or external review system to submit a non-code block."""

    repository = repository_factory(command=passing_command(), proposed=False)

    with pytest.raises(PairBlockGateError, match="external review evidence"):
        advance_test_block(repository, "submit", evidence_kind="test")


def test_completion_rejects_a_broken_receipt_chain(
    repository_factory: RepositoryFactory,
) -> None:
    """Reject a final receipt that skips the accepted implementation event."""

    repository = repository_factory(command=passing_command())
    run_test_gate(repository)
    advance_test_block(repository, "approve")
    advance_test_block(repository, "accept")
    completed = advance_test_block(repository, "register")
    receipt = json.loads(completed.read_text(encoding="utf-8"))
    receipt["event"] = "accept"
    completed.write_text(json.dumps(receipt), encoding="utf-8")

    with pytest.raises(PairBlockGateError, match="chain differs"):
        validate_test_repository(repository)


def test_illegal_lifecycle_event_changes_no_status(
    repository_factory: RepositoryFactory,
) -> None:
    """Reject approval before a proposal reaches review."""

    repository = repository_factory(command=passing_command())
    checklist = repository / CHECKLIST_PATH
    before = checklist.read_bytes()

    with pytest.raises(PairBlockGateError, match="approve cannot advance Drafting"):
        advance_test_block(repository, "approve")

    assert checklist.read_bytes() == before
    assert not (repository / "evidence").exists()


def test_checkbox_must_match_pairblock_completion(
    repository_factory: RepositoryFactory,
) -> None:
    """Reject a checked execution box while its PairBlock remains open."""

    repository = repository_factory(command=passing_command())
    checklist = repository / CHECKLIST_PATH
    text = checklist.read_text(encoding="utf-8").replace(
        "- [ ] Exercise `PB-GATE`.",
        "- [x] Exercise `PB-GATE`.",
    )
    checklist.write_text(text, encoding="utf-8")

    with pytest.raises(PairBlockGateError, match="checkbox must be unchecked"):
        validate_test_repository(repository)


def test_accepted_dependency_releases_waiting_block(
    repository_factory: RepositoryFactory,
) -> None:
    """Move a waiting block to drafting after its dependency is applied."""

    dependency = PairBlockFixture(DEPENDENCY_PAIR_BLOCK_ID, "Approved")
    repository = repository_factory(
        command=passing_command(),
        status=f"Waiting for {DEPENDENCY_PAIR_BLOCK_ID}",
        dependencies=(DEPENDENCY_PAIR_BLOCK_ID,),
        dependency=dependency,
    )
    advance_pairblock(
        repository,
        DEPENDENCY_PAIR_BLOCK_ID,
        "accept",
        EvidenceRef(
            kind="test",
            target="accepted implementation",
            revision="test-revision",
        ),
        now=NOW,
        adapter=TEST_ADAPTER,
    )
    rows, _ = validate_test_repository(repository)

    assert rows[DEPENDENCY_PAIR_BLOCK_ID].status == "Applied"
    assert rows[PAIR_BLOCK_ID].status == "Drafting"


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


def test_duplicate_status_row_is_rejected(
    repository_factory: RepositoryFactory,
) -> None:
    """Require one status row for each PairBlock identity."""

    repository = repository_factory(command=passing_command())
    checklist = repository / CHECKLIST_PATH
    text = checklist.read_text(encoding="utf-8")
    row = next(
        line
        for line in text.splitlines()
        if line.startswith(f"| `{PAIR_BLOCK_ID}` |")
    )
    checklist.write_text(text.replace(row, row + "\n" + row), encoding="utf-8")

    with pytest.raises(PairBlockGateError, match="duplicate PairBlock row"):
        validate_test_repository(repository)


def test_html_declaration_anchor_is_not_a_navigation_target(
    repository_factory: RepositoryFactory,
) -> None:
    """Reject a raw HTML anchor where a renderer-visible heading is required."""

    repository = repository_factory(command=passing_command())
    contract = repository / CONTRACT_PATH
    heading = f"#### {PAIR_BLOCK_ID}"
    html_anchor = f'<a id="{PAIR_BLOCK_ID.lower()}"></a>'
    text = contract.read_text(encoding="utf-8").replace(heading, html_anchor)
    contract.write_text(text, encoding="utf-8")

    with pytest.raises(PairBlockGateError, match="native PairBlock heading"):
        validate_test_repository(repository)


def test_broken_document_fragment_is_rejected(
    repository_factory: RepositoryFactory,
) -> None:
    """Reject any contract or checklist link that names no native heading."""

    repository = repository_factory(command=passing_command())
    checklist = repository / CHECKLIST_PATH
    checklist.write_text(
        checklist.read_text(encoding="utf-8")
        + "\n[Broken record](../contracts/contract.md#missing-heading)\n",
        encoding="utf-8",
    )

    with pytest.raises(PairBlockGateError, match="does not name a native heading"):
        validate_test_repository(repository)


def test_external_document_fragment_is_outside_repository_validation(
    repository_factory: RepositoryFactory,
) -> None:
    """Leave an HTTPS fragment for its remote document to resolve."""

    repository = repository_factory(command=passing_command())
    checklist = repository / CHECKLIST_PATH
    checklist.write_text(
        checklist.read_text(encoding="utf-8")
        + "\n[External source](https://example.com/specification#requirement)\n",
        encoding="utf-8",
    )

    validate_test_repository(repository)


def test_sibling_document_fragment_requires_approved_owner(
    repository_factory: RepositoryFactory,
) -> None:
    """Reject a local fragment outside the checklist's approved owner roots."""

    repository = repository_factory(command=passing_command())
    sibling = repository.parent / "unapproved-owner"
    sibling.mkdir()
    (sibling / "guide.md").write_text("# Owner guide\n", encoding="utf-8")
    checklist = repository / CHECKLIST_PATH
    checklist.write_text(
        checklist.read_text(encoding="utf-8")
        + "\n[Owner guide](../../../unapproved-owner/guide.md#owner-guide)\n",
        encoding="utf-8",
    )

    with pytest.raises(PairBlockGateError, match="approved owner roots"):
        validate_test_repository(repository)


def test_standard_pair_block_contract_marker_is_required(
    repository_factory: RepositoryFactory,
) -> None:
    """Keep each project row connected through the global checklist marker."""

    repository = repository_factory(command=passing_command())
    checklist = repository / CHECKLIST_PATH
    text = checklist.read_text(encoding="utf-8")
    marker = (
        f"<!-- pair-block-contract: {PAIR_BLOCK_ID} "
        f"contract={CONTRACT_PATH.as_posix()} -->"
    )
    checklist.write_text(text.replace(marker, ""), encoding="utf-8")

    with pytest.raises(PairBlockGateError, match="standard contract marker"):
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
    text = contract.read_text(encoding="utf-8").replace("Test author.", "")
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


def test_profile_may_name_a_sibling_proposal_owner(
    repository_factory: RepositoryFactory,
) -> None:
    """Hash proposal files from a profile-declared sibling repository."""

    repository = repository_factory(command=passing_command())
    source_owner = repository.parent / "source-owner"
    source = source_owner / "source.py"
    test = source_owner / "test_source.py"
    guide = source_owner / "guide.md"
    source_owner.mkdir()
    source.write_text("VALUE = 1\n", encoding="utf-8")
    test.write_text("def test_value():\n    assert 1 == 1\n", encoding="utf-8")
    guide.write_text("# Owner guide\n", encoding="utf-8")

    contract = repository / CONTRACT_PATH
    text = contract.read_text(encoding="utf-8")
    text = text.replace(
        "../../tools/pairblock_status/checklist_profile.py",
        "../../../source-owner/source.py",
    ).replace(
        "../../tests/pairblock_status/test_pairblock_controller.py",
        "../../../source-owner/test_source.py",
    )
    text = text.replace(passing_command(), f"python {source} {test}")
    text = text.replace(
        "# Contract",
        "# Contract\n\n[Owner guide](../../../source-owner/guide.md#owner-guide)",
    )
    contract.write_text(text, encoding="utf-8")

    profile = replace(
        TEST_PROFILE,
        proposal_source_roots=(Path("../source-owner"),),
    )
    adapter = MarkdownChecklistAdapter(profile=profile, dialect=TEST_DIALECT)
    rows, _ = adapter.validate_traceability(repository)
    proposal = adapter.load_proposal_contract(
        repository,
        repository / CHECKLIST_PATH,
        rows[PAIR_BLOCK_ID],
    )

    assert proposal.source_paths == (source, test)


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

    command = f"python -c 'print(\"2 passed in 0.01s\")' {TEST_PATH.name}"
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
        f"[`{PAIR_BLOCK_ID}`](#{PAIR_BLOCK_ID.lower()}) |\n"
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
        f"(#{PAIR_BLOCK_ID.lower()})",
        f"(#{UNKNOWN_PAIR_BLOCK_ID.lower()})",
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
        f"#### {DEPENDENCY_PAIR_BLOCK_ID}\n\n"
        f"| [`{DEPENDENCY_PAIR_BLOCK_ID}`](#pairblock-resolution) | "
        "Exercise dependency. | Test author. | Pending | Gate. |",
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


def test_nested_conda_run_is_rejected_before_gate_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    repository_factory: RepositoryFactory,
) -> None:
    """Keep the controller environment from overriding a declared Conda target."""

    execution_marker = tmp_path / "nested-conda-ran"
    command = (
        "conda run -n mantra python -c 'from pathlib import Path; "
        f'Path("{execution_marker}").touch(); print("2 passed in 0.01s")\' '
        f"{SOURCE_PATH.as_posix()} {TEST_PATH.as_posix()}"
    )
    repository = repository_factory(command=command)
    monkeypatch.setenv("CONDA_DEFAULT_ENV", "mantra")

    with pytest.raises(PairBlockGateError, match="must run outside"):
        run_test_gate(repository)

    assert not execution_marker.exists()
    assert not (repository / "evidence").exists()


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
            f'path = Path("{path}"); '
            'path.write_bytes(path.read_bytes() + b"\\n"); '
            'print("2 passed in 0.01s")\' '
            f"{SOURCE_PATH.as_posix()} {TEST_PATH.as_posix()}"
        )
    contract = repository / CONTRACT_PATH
    contract.write_text(
        contract.read_text(encoding="utf-8").replace(passing_command(), command),
        encoding="utf-8",
    )

    receipt_path = run_test_gate(repository, validator_path=validator)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    checklist = (repository / CHECKLIST_PATH).read_text(encoding="utf-8")

    assert receipt["result"] == "invalidated"
    assert receipt["status_after"] == TEST_PROFILE.lifecycle.drafting_status
    assert drift_field in receipt["identity_drift"]
    assert TEST_PROFILE.lifecycle.review_status not in checklist


def test_active_modules_and_definitions_have_docstrings() -> None:
    """Keep every active module, class, function, and method documented."""

    root = Path(__file__).parents[2]
    paths = [
        root / "tools/pairblock_status/__init__.py",
        root / "tools/pairblock_status/checklist_profile.py",
        root / "tools/pairblock_status/execution_identity.py",
        root / "tools/pairblock_status/profile.py",
        root / "tools/pairblock_status/pairblock_controller.py",
        root / "tests/pairblock_status/conftest.py",
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
