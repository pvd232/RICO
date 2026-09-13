"""Contract tests for evidence-backed PairBlock lifecycle updates."""

from __future__ import annotations

import ast
import json
import shutil
import sys
from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone
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
    NormalizedManifest,
    PairBlockRow,
)
from tools.pairblock_status.execution_identity import sha256_file
from tools.pairblock_status.pairblock_controller import (
    DEFAULT_MASTER_CHECKLIST_VALIDATOR,
    EvidenceRef,
    PairBlockGateError,
    accept_declaration_revision,
    advance_pairblock,
    plan_declaration_revision,
    run_gate,
    write_declaration_revision_plan,
)
from tools.pairblock_status.profile import (
    MANTRA_PHASE0_PROFILE,
    ChecklistProfile,
    EvidenceKind,
)

NOW = datetime(2026, 9, 11, 16, 0, tzinfo=timezone.utc)
NATIVE_PAIR_BLOCK_ID = "PB-NATIVE"


def validate_test_repository(
    repository: Path,
) -> tuple[dict[str, PairBlockRow], NormalizedManifest]:
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
    evidence_kind: EvidenceKind = "external",
    certification_reason: str | None = None,
) -> Path:
    """Advance the test PairBlock with one compact evidence reference."""

    target = f"{event} evidence"
    revision = "test-revision"
    if evidence_kind == "artifact":
        artifact = repository / "evidence" / "terminal.json"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text('{"passed": true}\n', encoding="utf-8")
        target = artifact.relative_to(repository).as_posix()
        revision = sha256_file(artifact)
    return advance_pairblock(
        repository,
        PAIR_BLOCK_ID,
        event,
        EvidenceRef(
            kind=evidence_kind,
            target=target,
            revision=revision,
        ),
        certification_reason=certification_reason,
        now=NOW,
        adapter=TEST_ADAPTER,
    )


def passing_command() -> str:
    """Return a gate that names both bounded files and reports two passes."""

    return (
        "python -c 'print(\"2 passed in 0.01s\")' "
        f"{SOURCE_PATH.as_posix()} {TEST_PATH.as_posix()}"
    )


def native_artifact_evidence(repository: Path, name: str) -> EvidenceRef:
    """Create one retained native lifecycle artifact and its exact identity."""

    artifact = repository / "evidence" / "native" / f"{name}.json"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(json.dumps({"event": name}) + "\n", encoding="utf-8")
    return EvidenceRef(
        "artifact",
        artifact.relative_to(repository).as_posix(),
        sha256_file(artifact),
    )


def failing_command() -> str:
    """Return a failing gate that still names both bounded files."""

    return (
        "python -c 'import sys; print(\"failed\"); sys.exit(1)' "
        f"{SOURCE_PATH.as_posix()} {TEST_PATH.as_posix()}"
    )


def accept_fixture_declarations(
    repository: Path,
    adapter: MarkdownChecklistAdapter,
    *,
    now: datetime = NOW,
) -> Path:
    """Accept the fixture manifest through an external review reference."""

    plan = write_declaration_revision_plan(repository, now=now, adapter=adapter)
    return accept_declaration_revision(
        repository,
        EvidenceRef("external", "user review", "review-message"),
        plan_path=plan,
        plan_sha256=sha256_file(plan),
        now=now,
        adapter=adapter,
    )


def add_dependent_native_block(repository: Path, profile: ChecklistProfile) -> None:
    """Add one native block that shares the fixture requirement."""

    manifest = repository / profile.require_declaration_path()
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            'pair_block_ids = ["PB-NATIVE"]',
            'pair_block_ids = ["PB-NATIVE", "PB-DEPENDENT"]',
        )
        + """

[[pair_blocks]]
id = "PB-DEPENDENT"
requirement_ids = ["REQ-NATIVE"]
depends_on = ["PB-NATIVE"]
section = "0B"
repository = "test"
source_paths = ["tools/pairblock_status/checklist_profile.py"]
test_paths = ["tests/pairblock_status/test_pairblock_controller.py"]

[pair_blocks.gate]
repository = "test"
working_directory = "."
argv = ["python", "-c", "print('2 passed in 0.01s')"]
environment = { PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1" }
""",
        encoding="utf-8",
    )


class TestProfileDefinition:
    """Validate the generic and MANTRA checklist profile definitions."""

    def test_profile_fixture_compiles_with_global_validator(
        self,
        repository_factory: RepositoryFactory,
    ) -> None:
        """Compile the generic profile and pass it through the global validator."""

        repository = repository_factory(command=passing_command())
        rows, manifest = validate_test_repository(repository)

        assert set(rows) == {PAIR_BLOCK_ID}
        assert manifest["schema_version"] == 2

    def test_lifecycle_policy_rejects_undeclared_transition_status(self) -> None:
        """Reject a transition whose status lacks a normalized-state definition."""

        with pytest.raises(ValueError, match="undeclared statuses"):
            replace(TEST_PROFILE.lifecycle, review_status="Unlisted")

    def test_lifecycle_policy_rejects_disconnected_transition_chain(self) -> None:
        """Require each lifecycle event to consume the preceding event's status."""

        with pytest.raises(ValueError, match="transition chain expected Review"):
            replace(
                TEST_PROFILE.lifecycle,
                transitions=(("approve", "Approved", "Applied"),),
            )

    def test_lifecycle_policy_rejects_duplicate_non_code_event(self) -> None:
        """Keep non-code and implementation event names unambiguous."""

        with pytest.raises(ValueError, match="transition events must be unique"):
            replace(TEST_PROFILE.lifecycle, non_code_complete_event="approve")

    def test_checklist_profile_requires_two_phase_capture_groups(self) -> None:
        """Require the phase expression to expose both ordering components."""

        with pytest.raises(ValueError, match="numeric and letter groups"):
            replace(TEST_PROFILE, phase_pattern=r"[0-9]+[A-Z]")

    def test_project_profile_excludes_markdown_dialect(self) -> None:
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
    def test_markdown_dialect_rejects_empty_markers(self, field_name: str) -> None:
        """Require every RICO Markdown extension used by the adapter."""

        with pytest.raises(ValueError, match=f"{field_name} must not be empty"):
            replace(TEST_DIALECT, **{field_name: ""})

    def test_gate_controller_does_not_parse_or_render_markdown(self) -> None:
        """Keep Markdown row manipulation inside the checklist adapter."""

        controller = (
            Path(__file__).parents[2] / "tools/pairblock_status/pairblock_controller.py"
        )
        tree = ast.parse(
            controller.read_text(encoding="utf-8"), filename=str(controller)
        )
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

    def test_mantra_profile_compiles_current_contract(self) -> None:
        """Compile the real MANTRA documents through their project profile."""

        repository = Path(__file__).parents[2]
        rows, manifest = MANTRA_PHASE0_ADAPTER.validate_traceability(
            repository,
        )

        assert "P0-PB-10" in rows
        assert manifest["checklist_id"] == MANTRA_PHASE0_PROFILE.checklist_id

    def test_applied_blocks_do_not_link_staging_proposals(self) -> None:
        """Require accepted blocks to point at active code or contract records."""

        repository = Path(__file__).parents[2]
        rows, _ = MANTRA_PHASE0_ADAPTER.validate_traceability(repository)

        for row in rows.values():
            if row.status in {"Applied", "Complete"}:
                assert "/staging/" not in row.proposed_code
                assert (
                    MANTRA_PHASE0_ADAPTER.dialect.proposed_code_link_prefix
                    not in row.proposed_code
                )

    @pytest.mark.parametrize("status", ["Applied", "Complete"])
    def test_validator_rejects_resolved_block_with_staging_links(
        self,
        repository_factory: RepositoryFactory,
        status: str,
    ) -> None:
        """Reject a resolved status whose code links still name its proposal."""

        repository = repository_factory(command=passing_command(), status=status)

        with pytest.raises(
            PairBlockGateError,
            match=f"{PAIR_BLOCK_ID} resolved status points to proposed code",
        ):
            validate_test_repository(repository)


class TestPairBlockLifecycle:
    """Validate gate execution and PairBlock lifecycle transitions."""

    def test_passing_gate_writes_receipt_and_advances_one_status(
        self,
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
        self,
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
        self,
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

        assert (
            json.loads(approval.read_text(encoding="utf-8"))["status_after"]
            == "Approved"
        )
        assert (
            json.loads(accepted.read_text(encoding="utf-8"))["status_after"]
            == "Applied"
        )
        assert json.loads(completed.read_text(encoding="utf-8"))["result"] == "applied"
        assert rows[PAIR_BLOCK_ID].status == "Complete"
        assert "- [x] Exercise `PB-GATE`." in checklist
        assert f"| `{REQUIREMENT_ID}` | Complete |" in checklist
        assert "| [Contract](../contracts/contract.md) | Complete |" in checklist
        assert block["state"] == requirement["state"] == "complete"
        assert block["completion_evidence"] == requirement["completion_evidence"]
        assert manifest["contracts"][0]["state"] == "complete"

    def test_accept_promotes_staging_links_to_active_code(
        self,
        repository_factory: RepositoryFactory,
    ) -> None:
        """Replace every accepted staging link in the authoritative status row."""

        repository = repository_factory(command=passing_command())
        run_test_gate(repository)
        advance_test_block(repository, "approve")
        advance_test_block(repository, "accept")

        rows, _ = validate_test_repository(repository)
        proposed_code = rows[PAIR_BLOCK_ID].proposed_code

        assert proposed_code == (
            "[Source](../../tools/pairblock_status/checklist_profile.py) · "
            "[Tests](../../tests/pairblock_status/test_pairblock_controller.py)"
        )
        assert "/staging/" not in proposed_code
        assert TEST_DIALECT.proposed_code_link_prefix not in proposed_code

    def test_accept_removes_proposal_marker_from_active_links(
        self,
        repository_factory: RepositoryFactory,
    ) -> None:
        """Remove the contract proposal link when code links are already active."""

        repository = repository_factory(command=passing_command())
        run_test_gate(repository)
        advance_test_block(repository, "approve")
        checklist = repository / CHECKLIST_PATH
        checklist.write_text(
            checklist.read_text(encoding="utf-8").replace(
                f"/staging/{PAIR_BLOCK_ID.lower()}",
                "",
            ),
            encoding="utf-8",
        )

        advance_test_block(repository, "accept")

        rows, _ = validate_test_repository(repository)
        assert rows[PAIR_BLOCK_ID].proposed_code == (
            "[Source](../../tools/pairblock_status/checklist_profile.py) · "
            "[Tests](../../tests/pairblock_status/test_pairblock_controller.py)"
        )

    def test_accept_rejects_a_staging_link_owned_by_another_block(
        self,
        repository_factory: RepositoryFactory,
    ) -> None:
        """Keep the checklist unchanged when proposal ownership is ambiguous."""

        repository = repository_factory(command=passing_command())
        run_test_gate(repository)
        advance_test_block(repository, "approve")
        checklist = repository / CHECKLIST_PATH
        before = checklist.read_text(encoding="utf-8")
        checklist.write_text(
            before.replace(
                f"/staging/{PAIR_BLOCK_ID.lower()}/",
                "/staging/pb-other/",
            ),
            encoding="utf-8",
        )
        malformed = checklist.read_bytes()

        with pytest.raises(PairBlockGateError, match="proposal link does not use"):
            advance_test_block(repository, "accept")

        assert checklist.read_bytes() == malformed

    def test_non_code_review_completion_updates_every_derived_status(
        self,
        repository_factory: RepositoryFactory,
    ) -> None:
        """Complete a documentation-only block from two external review receipts."""

        repository = repository_factory(command=passing_command(), proposed=False)
        submitted = advance_test_block(repository, "submit")
        confirmed = advance_test_block(repository, "confirm")
        rows, manifest = validate_test_repository(repository)
        checklist = (repository / CHECKLIST_PATH).read_text(encoding="utf-8")

        assert (
            json.loads(submitted.read_text(encoding="utf-8"))["status_after"]
            == "Review"
        )
        assert (
            json.loads(confirmed.read_text(encoding="utf-8"))["status_after"]
            == "Complete"
        )
        assert rows[PAIR_BLOCK_ID].status == "Complete"
        assert "- [x] Exercise `PB-GATE`." in checklist
        assert manifest["pair_blocks"][0]["state"] == "complete"
        assert manifest["requirements"][0]["state"] == "complete"
        assert manifest["contracts"][0]["state"] == "complete"

    def test_non_code_review_rejects_runnable_proposal(
        self,
        repository_factory: RepositoryFactory,
    ) -> None:
        """Require executable proposals to reach review through their test gate."""

        repository = repository_factory(command=passing_command())

        with pytest.raises(PairBlockGateError, match="run its gate"):
            advance_test_block(repository, "submit")

    def test_non_code_review_requires_external_evidence(
        self,
        repository_factory: RepositoryFactory,
    ) -> None:
        """Require a person or external review system to submit a non-code block."""

        repository = repository_factory(command=passing_command(), proposed=False)

        with pytest.raises(PairBlockGateError, match="external review evidence"):
            advance_test_block(repository, "submit", evidence_kind="test")

    def test_completion_rejects_a_broken_receipt_chain(
        self,
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

    def test_legacy_certification_closes_one_named_applied_block(
        self,
        repository_factory: RepositoryFactory,
    ) -> None:
        """Close a named legacy block while preserving its existing receipt."""

        repository = repository_factory(command=passing_command())
        run_test_gate(repository)
        advance_test_block(repository, "approve")
        accepted = advance_test_block(repository, "accept")

        certified = advance_test_block(
            repository,
            "certify",
            evidence_kind="artifact",
            certification_reason="The retained approval predates receipt chaining.",
        )
        receipt = json.loads(certified.read_text(encoding="utf-8"))
        rows, manifest = validate_test_repository(repository)

        assert receipt["previous_receipt"].endswith(accepted.name)
        assert receipt["schema_version"] == 2
        assert receipt["certification_reason"].startswith("The retained approval")
        assert rows[PAIR_BLOCK_ID].status == "Complete"
        assert manifest["pair_blocks"][0]["state"] == "complete"

    @pytest.mark.parametrize(
        ("evidence_kind", "reason", "message"),
        [
            ("external", "Historical chain.", "requires artifact evidence"),
            ("artifact", None, "requires a reason"),
        ],
    )
    def test_legacy_certification_requires_artifact_and_reason(
        self,
        repository_factory: RepositoryFactory,
        evidence_kind: EvidenceKind,
        reason: str | None,
        message: str,
    ) -> None:
        """Require artifact evidence and a reason for compatibility closure."""

        repository = repository_factory(command=passing_command())
        run_test_gate(repository)
        advance_test_block(repository, "approve")
        advance_test_block(repository, "accept")

        with pytest.raises(PairBlockGateError, match=message):
            advance_test_block(
                repository,
                "certify",
                evidence_kind=evidence_kind,
                certification_reason=reason,
            )

    def test_legacy_certification_rejects_an_unnamed_block(
        self,
        repository_factory: RepositoryFactory,
    ) -> None:
        """Keep compatibility closure limited to the profile's explicit set."""

        repository = repository_factory(command=passing_command())
        run_test_gate(repository)
        advance_test_block(repository, "approve")
        advance_test_block(repository, "accept")
        adapter = replace(
            TEST_ADAPTER,
            profile=replace(TEST_PROFILE, legacy_certifiable_pair_blocks=frozenset()),
        )

        with pytest.raises(PairBlockGateError, match="not approved"):
            advance_pairblock(
                repository,
                PAIR_BLOCK_ID,
                "certify",
                EvidenceRef("artifact", "terminal receipt", "test-revision"),
                certification_reason="Historical chain.",
                now=NOW,
                adapter=adapter,
            )

    def test_legacy_certification_rejects_a_changed_terminal_artifact(
        self,
        repository_factory: RepositoryFactory,
    ) -> None:
        """Reject a completed legacy block after its terminal artifact changes."""

        repository = repository_factory(command=passing_command())
        run_test_gate(repository)
        advance_test_block(repository, "approve")
        advance_test_block(repository, "accept")
        advance_test_block(
            repository,
            "certify",
            evidence_kind="artifact",
            certification_reason="The retained approval predates receipt chaining.",
        )
        (repository / "evidence" / "terminal.json").write_text(
            '{"passed": false}\n', encoding="utf-8"
        )

        with pytest.raises(PairBlockGateError, match="artifact differs"):
            validate_test_repository(repository)

    def test_legacy_certification_rejects_a_nonterminal_artifact(
        self,
        repository_factory: RepositoryFactory,
    ) -> None:
        """Reject a valid file identity that names another repository artifact."""

        repository = repository_factory(command=passing_command())
        run_test_gate(repository)
        advance_test_block(repository, "approve")
        advance_test_block(repository, "accept")
        other = repository / "evidence" / "other.json"
        other.parent.mkdir(parents=True, exist_ok=True)
        other.write_text('{"passed": true}\n', encoding="utf-8")

        with pytest.raises(PairBlockGateError, match="configured terminal artifact"):
            advance_pairblock(
                repository,
                PAIR_BLOCK_ID,
                "certify",
                EvidenceRef("artifact", "evidence/other.json", sha256_file(other)),
                certification_reason="Historical chain.",
                now=NOW,
                adapter=TEST_ADAPTER,
            )

    def test_legacy_completion_rejects_a_nonterminal_artifact(
        self,
        repository_factory: RepositoryFactory,
    ) -> None:
        """Recheck the configured terminal path when loading completion evidence."""

        repository = repository_factory(command=passing_command())
        run_test_gate(repository)
        advance_test_block(repository, "approve")
        advance_test_block(repository, "accept")
        certified = advance_test_block(
            repository,
            "certify",
            evidence_kind="artifact",
            certification_reason="The retained approval predates receipt chaining.",
        )
        other = repository / "evidence" / "other.json"
        other.write_text('{"passed": true}\n', encoding="utf-8")
        receipt = json.loads(certified.read_text(encoding="utf-8"))
        receipt["evidence"]["target"] = "evidence/other.json"
        receipt["evidence"]["revision"] = sha256_file(other)
        certified.write_text(json.dumps(receipt), encoding="utf-8")

        with pytest.raises(PairBlockGateError, match="artifact differs"):
            validate_test_repository(repository)

    def test_legacy_certification_profile_requires_a_terminal_artifact(self) -> None:
        """Reject an enabled certification route with no artifact identity."""

        with pytest.raises(ValueError, match="requires an event and terminal artifact"):
            replace(TEST_PROFILE, legacy_certification_artifact=None)

    def test_illegal_lifecycle_event_changes_no_status(
        self,
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
        self,
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
        self,
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
        self,
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

    def test_earlier_command_failure_cannot_be_masked(
        self,
        repository_factory: RepositoryFactory,
    ) -> None:
        """Stop a legacy gate when an earlier command exits unsuccessfully."""

        paths = f"{SOURCE_PATH.as_posix()} {TEST_PATH.as_posix()}"
        command = (
            f"python -c 'raise SystemExit(7)' {paths}\n"
            f"python -c 'print(\"2 passed in 0.01s\")' {paths}"
        )
        repository = repository_factory(command=command)

        receipt_path = run_test_gate(repository)
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

        assert receipt["result"] == "failed"
        assert receipt["exit_code"] == 7
        assert "2 passed" not in receipt["stdout"]


class TestDeclarationRevision:
    """Validate declaration revision identity and dependent reopening."""

    def test_revision_receipt_binds_manifest_and_record_digests(
        self,
        repository_factory: RepositoryFactory,
        declaration_profile: ChecklistProfile,
    ) -> None:
        """Retain the accepted declaration, changed records, and user approval."""

        repository = repository_factory(command=passing_command())
        adapter = replace(TEST_ADAPTER, profile=declaration_profile)

        plan = plan_declaration_revision(repository, adapter=adapter)
        receipt_path = accept_fixture_declarations(repository, adapter)
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

        assert plan.changed
        assert plan.affected_pair_blocks == (NATIVE_PAIR_BLOCK_ID,)
        assert receipt["before_sha256"] == plan.before_sha256
        assert receipt["after_sha256"] == plan.after_sha256
        assert receipt["approval"] == {
            "kind": "external",
            "revision": "review-message",
            "target": "user review",
        }
        assert (
            receipt["accepted_manifest"]["pair_blocks"][0]["id"] == NATIVE_PAIR_BLOCK_ID
        )
        assert {record["record"] for record in receipt["records"]} == {
            "pair_block:PB-NATIVE",
            "requirement:REQ-NATIVE",
            "verifier:VR-NATIVE",
        }

    def test_revision_receipt_digests_must_join(
        self,
        repository_factory: RepositoryFactory,
        declaration_profile: ChecklistProfile,
    ) -> None:
        """Reject a revision whose before digest differs from its predecessor."""

        repository = repository_factory(command=passing_command())
        adapter = replace(TEST_ADAPTER, profile=declaration_profile)
        accept_fixture_declarations(repository, adapter)
        manifest = repository / declaration_profile.require_declaration_path()
        manifest.write_text(
            manifest.read_text(encoding="utf-8").replace(
                "The proposal gate retains its result.",
                "The proposal gate retains its exact result.",
            ),
            encoding="utf-8",
        )
        receipt_path = accept_fixture_declarations(
            repository, adapter, now=NOW + timedelta(seconds=1)
        )
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["before_sha256"] = "0" * 64
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

        with pytest.raises(PairBlockGateError, match="digests do not join"):
            plan_declaration_revision(repository, adapter=adapter)

    @pytest.mark.parametrize(
        ("field", "replacement", "message"),
        [
            ("records", [], "record changes differ"),
            ("affected_pair_blocks", [], "affected blocks differ"),
            (
                "approval",
                {"kind": "artifact", "target": "user review", "revision": "message"},
                "approval is not external",
            ),
            (
                "superseded_receipt_heads",
                {NATIVE_PAIR_BLOCK_ID: "evidence/missing.json"},
                "superseded receipt is missing",
            ),
        ],
    )
    def test_revision_receipt_recomputes_or_validates_each_evidence_claim(
        self,
        repository_factory: RepositoryFactory,
        declaration_profile: ChecklistProfile,
        field: str,
        replacement: object,
        message: str,
    ) -> None:
        """Reject a stored revision claim that its source records cannot support."""

        repository = repository_factory(command=passing_command())
        adapter = replace(TEST_ADAPTER, profile=declaration_profile)
        receipt_path = accept_fixture_declarations(repository, adapter)
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt[field] = replacement
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

        with pytest.raises(PairBlockGateError, match=message):
            plan_declaration_revision(repository, adapter=adapter)

    def test_manifest_native_block_completes_through_receipt_derived_views(
        self,
        repository_factory: RepositoryFactory,
        declaration_profile: ChecklistProfile,
    ) -> None:
        """Run a native gate and all three later lifecycle transitions."""

        repository = repository_factory(command=passing_command())
        adapter = replace(TEST_ADAPTER, profile=declaration_profile)
        accept_fixture_declarations(repository, adapter)

        gate = run_gate(repository, NATIVE_PAIR_BLOCK_ID, now=NOW, adapter=adapter)
        approval = advance_pairblock(
            repository,
            NATIVE_PAIR_BLOCK_ID,
            "approve",
            EvidenceRef("external", "code review", "review-message"),
            now=NOW + timedelta(seconds=1),
            adapter=adapter,
        )
        accepted = advance_pairblock(
            repository,
            NATIVE_PAIR_BLOCK_ID,
            "accept",
            native_artifact_evidence(repository, "implementation"),
            now=NOW + timedelta(seconds=2),
            adapter=adapter,
        )
        completed = advance_pairblock(
            repository,
            NATIVE_PAIR_BLOCK_ID,
            "register",
            native_artifact_evidence(repository, "viper"),
            now=NOW + timedelta(seconds=3),
            adapter=adapter,
        )
        contract = (repository / CONTRACT_PATH).read_text(encoding="utf-8")
        checklist = (repository / CHECKLIST_PATH).read_text(encoding="utf-8")

        assert json.loads(gate.read_text(encoding="utf-8"))["status_after"] == "Review"
        assert (
            json.loads(approval.read_text(encoding="utf-8"))["status_after"]
            == "Approved"
        )
        assert (
            json.loads(accepted.read_text(encoding="utf-8"))["status_after"]
            == "Applied"
        )
        assert (
            json.loads(completed.read_text(encoding="utf-8"))["status_after"]
            == "Complete"
        )
        assert "**Status:** Complete" in contract
        assert "| `PB-NATIVE` | Complete |" in checklist

    def test_unapproved_declaration_change_blocks_execution(
        self,
        repository_factory: RepositoryFactory,
        declaration_profile: ChecklistProfile,
    ) -> None:
        """Stop before process launch when the working declaration changed."""

        repository = repository_factory(command=passing_command())
        adapter = replace(TEST_ADAPTER, profile=declaration_profile)
        accept_fixture_declarations(repository, adapter)
        manifest = repository / declaration_profile.require_declaration_path()
        manifest.write_text(
            manifest.read_text(encoding="utf-8").replace(
                "The proposal gate retains its result.",
                "The proposal gate retains its exact result.",
            ),
            encoding="utf-8",
        )

        with pytest.raises(PairBlockGateError, match="record revise first"):
            run_gate(repository, NATIVE_PAIR_BLOCK_ID, adapter=adapter)

        assert not (repository / "evidence/pairblock-gates/pb-native").exists()

    def test_corrupt_native_receipt_reference_blocks_transition(
        self,
        repository_factory: RepositoryFactory,
        declaration_profile: ChecklistProfile,
    ) -> None:
        """Reject a native lifecycle chain whose predecessor receipt is absent."""

        repository = repository_factory(command=passing_command())
        adapter = replace(TEST_ADAPTER, profile=declaration_profile)
        accept_fixture_declarations(repository, adapter)
        run_gate(repository, NATIVE_PAIR_BLOCK_ID, now=NOW, adapter=adapter)
        approval = advance_pairblock(
            repository,
            NATIVE_PAIR_BLOCK_ID,
            "approve",
            EvidenceRef("external", "code review", "review-message"),
            now=NOW + timedelta(seconds=1),
            adapter=adapter,
        )
        receipt = json.loads(approval.read_text(encoding="utf-8"))
        receipt["previous_receipt"] = "evidence/missing.json"
        approval.write_text(json.dumps(receipt), encoding="utf-8")

        with pytest.raises(PairBlockGateError, match="missing receipts"):
            advance_pairblock(
                repository,
                NATIVE_PAIR_BLOCK_ID,
                "accept",
                native_artifact_evidence(repository, "implementation"),
                adapter=adapter,
            )

    def test_duplicate_legacy_and_native_owner_blocks_revision(
        self,
        repository_factory: RepositoryFactory,
        declaration_profile: ChecklistProfile,
    ) -> None:
        """Reject a PairBlock ID declared by both authority paths."""

        repository = repository_factory(command=passing_command())
        adapter = replace(TEST_ADAPTER, profile=declaration_profile)
        manifest = repository / declaration_profile.require_declaration_path()
        manifest.write_text(
            manifest.read_text(encoding="utf-8").replace("PB-NATIVE", "PB-GATE"),
            encoding="utf-8",
        )

        with pytest.raises(PairBlockGateError, match="legacy and typed owners"):
            accept_fixture_declarations(repository, adapter)

    def test_changed_verifier_reopens_owner_and_dependents(
        self,
        repository_factory: RepositoryFactory,
        declaration_profile: ChecklistProfile,
    ) -> None:
        """Reopen dependents and retain the exact superseded receipt head."""

        repository = repository_factory(command=passing_command())
        adapter = replace(TEST_ADAPTER, profile=declaration_profile)
        add_dependent_native_block(repository, declaration_profile)
        accept_fixture_declarations(repository, adapter)
        gate = run_gate(repository, NATIVE_PAIR_BLOCK_ID, now=NOW, adapter=adapter)
        advance_pairblock(
            repository,
            NATIVE_PAIR_BLOCK_ID,
            "approve",
            EvidenceRef("external", "code review", "review-message"),
            now=NOW + timedelta(seconds=1),
            adapter=adapter,
        )
        advance_pairblock(
            repository,
            NATIVE_PAIR_BLOCK_ID,
            "accept",
            native_artifact_evidence(repository, "implementation"),
            now=NOW + timedelta(seconds=2),
            adapter=adapter,
        )
        completed = advance_pairblock(
            repository,
            NATIVE_PAIR_BLOCK_ID,
            "register",
            native_artifact_evidence(repository, "viper"),
            now=NOW + timedelta(seconds=3),
            adapter=adapter,
        )
        manifest = repository / declaration_profile.require_declaration_path()
        manifest.write_text(
            manifest.read_text(encoding="utf-8").replace(
                "The declared test command passes.",
                "The declared test command passes twice.",
            ),
            encoding="utf-8",
        )

        revision = accept_fixture_declarations(
            repository, adapter, now=NOW + timedelta(seconds=4)
        )
        receipt = json.loads(revision.read_text(encoding="utf-8"))
        contract = (repository / CONTRACT_PATH).read_text(encoding="utf-8")

        assert receipt["affected_pair_blocks"] == ["PB-DEPENDENT", NATIVE_PAIR_BLOCK_ID]
        assert receipt["superseded_receipt_heads"] == {
            NATIVE_PAIR_BLOCK_ID: completed.relative_to(repository).as_posix()
        }
        assert "**Status:** Drafting" in contract
        dependent_block = contract.split("#### Manifest-native block PB-DEPENDENT", 1)[
            1
        ]
        dependent_block = dependent_block.split(
            "#### Manifest-native block PB-NATIVE", 1
        )[0]
        assert "**Status:** Waiting for PB-NATIVE" in dependent_block

        receipt["superseded_receipt_heads"] = {
            NATIVE_PAIR_BLOCK_ID: gate.relative_to(repository).as_posix()
        }
        revision.write_text(json.dumps(receipt), encoding="utf-8")
        with pytest.raises(PairBlockGateError, match="superseded receipt heads differ"):
            plan_declaration_revision(repository, adapter=adapter)

    def test_unrelated_declaration_change_preserves_receipts(
        self,
        repository_factory: RepositoryFactory,
        declaration_profile: ChecklistProfile,
    ) -> None:
        """Keep a completed block current when an independent block is added."""

        repository = repository_factory(command=passing_command())
        adapter = replace(TEST_ADAPTER, profile=declaration_profile)
        accept_fixture_declarations(repository, adapter)
        run_gate(repository, NATIVE_PAIR_BLOCK_ID, now=NOW, adapter=adapter)
        for seconds, event in enumerate(("approve", "accept", "register"), start=1):
            evidence = (
                EvidenceRef("external", "approve evidence", "approve revision")
                if event == "approve"
                else native_artifact_evidence(repository, event)
            )
            advance_pairblock(
                repository,
                NATIVE_PAIR_BLOCK_ID,
                event,
                evidence,
                now=NOW + timedelta(seconds=seconds),
                adapter=adapter,
            )
        manifest = repository / declaration_profile.require_declaration_path()
        manifest.write_text(
            manifest.read_text(encoding="utf-8")
            + """

    [[requirements]]
    id = "REQ-OTHER"
    claim = "An independent block retains its own result."
    phase = 0
    order = 2
    depends_on = []
    gate = { kind = "test", target = "VR-OTHER" }
    verifier_ids = ["VR-OTHER"]
    pair_block_ids = ["PB-OTHER"]

    [[verifiers]]
    id = "VR-OTHER"
    requirement_ids = ["REQ-OTHER"]
    conditions = ["The independent command passes."]
    success_case = "The independent receipt records the command."
    rejection_cases = ["The independent command fails."]

    [[pair_blocks]]
    id = "PB-OTHER"
    requirement_ids = ["REQ-OTHER"]
    depends_on = []
    section = "0B"
    repository = "test"
    source_paths = ["tools/pairblock_status/checklist_profile.py"]
    test_paths = ["tests/pairblock_status/test_pairblock_controller.py"]

    [pair_blocks.gate]
    repository = "test"
    working_directory = "."
    argv = ["python", "-c", "print('2 passed in 0.01s')"]
    environment = { PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1" }
    """,
            encoding="utf-8",
        )

        revision = accept_fixture_declarations(
            repository, adapter, now=NOW + timedelta(seconds=4)
        )
        receipt = json.loads(revision.read_text(encoding="utf-8"))
        contract = (repository / CONTRACT_PATH).read_text(encoding="utf-8")

        assert receipt["affected_pair_blocks"] == ["PB-OTHER"]
        assert receipt["superseded_receipt_heads"] == {}
        native_block = contract.split("#### Manifest-native block PB-NATIVE", 1)[1]
        native_block = native_block.split("#### Manifest-native block PB-OTHER", 1)[0]
        assert "**Status:** Complete" in native_block
        assert "register.json" in native_block


class TestLegacyTraceability:
    """Validate legacy Markdown ownership, links, and gate boundaries."""

    def test_unknown_pair_block_is_rejected(
        self,
        repository_factory: RepositoryFactory,
    ) -> None:
        """Refuse a gate that lacks an authoritative checklist row."""

        repository = repository_factory(command=passing_command())
        with pytest.raises(PairBlockGateError, match="unknown PairBlock"):
            run_test_gate(repository, UNKNOWN_PAIR_BLOCK_ID)

    def test_duplicate_status_row_is_rejected(
        self,
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
        self,
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
        self,
        repository_factory: RepositoryFactory,
    ) -> None:
        """Reject a contract or checklist link that misses every native heading."""

        repository = repository_factory(command=passing_command())
        checklist = repository / CHECKLIST_PATH
        checklist.write_text(
            checklist.read_text(encoding="utf-8")
            + "\n[Broken record](../contracts/contract.md#missing-heading)\n",
            encoding="utf-8",
        )

        with pytest.raises(PairBlockGateError, match="does not name a native heading"):
            validate_test_repository(repository)

    def test_linked_current_receipt_must_exist(
        self,
        repository_factory: RepositoryFactory,
    ) -> None:
        """Reject a status row whose current receipt target is absent."""

        repository = repository_factory(command=passing_command(), status="Review")
        checklist = repository / CHECKLIST_PATH
        checklist.write_text(
            checklist.read_text(encoding="utf-8").replace(
                "| Pending | Review |",
                "| Passed: `2` tests ([receipt](../../evidence/missing.json)) | Review |",
            ),
            encoding="utf-8",
        )

        with pytest.raises(PairBlockGateError, match="current receipt is missing"):
            validate_test_repository(repository)

    def test_external_document_fragment_is_outside_repository_validation(
        self,
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
        self,
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
        self,
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
        self,
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
        self,
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
        self,
        repository_factory: RepositoryFactory,
    ) -> None:
        """Keep every declared code boundary connected to an existing file."""

        repository = repository_factory(command=passing_command())
        (repository / SOURCE_PATH).unlink()

        with pytest.raises(PairBlockGateError, match="proposed source is missing"):
            validate_test_repository(repository)

    def test_profile_may_name_a_sibling_proposal_owner(
        self,
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
        self,
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
        self,
        repository_factory: RepositoryFactory,
    ) -> None:
        """Require the focused command to execute every declared observing test."""

        command = f"python -c 'print(\"2 passed in 0.01s\")' {TEST_PATH.name}"
        repository = repository_factory(command=command)

        with pytest.raises(PairBlockGateError, match="focused check does not name"):
            validate_test_repository(repository)

    def test_duplicate_requirement_id_is_rejected(
        self,
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
        self,
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
        self,
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
        self,
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
        self,
        repository_factory: RepositoryFactory,
    ) -> None:
        """Block a proposal while its declared predecessor remains in drafting."""

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
        self,
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


class TestExecutionIdentity:
    """Validate execution identity capture across a running gate."""

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
        self,
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


def test_pairblock_modules_and_definitions_have_documentation() -> None:
    """Document every active definition and persisted record field it owns."""

    root = Path(__file__).parents[2]
    paths = sorted((root / "tools/pairblock_status").glob("*.py"))
    paths.extend(sorted((root / "tests/pairblock_status").glob("*.py")))
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        assert ast.get_docstring(tree), f"{path} lacks a module docstring"
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                docstring = ast.get_docstring(node)
                assert docstring, f"{path}:{node.lineno} {node.name} lacks a docstring"
                is_dataclass = isinstance(node, ast.ClassDef) and any(
                    (isinstance(decorator, ast.Name) and decorator.id == "dataclass")
                    or (
                        isinstance(decorator, ast.Call)
                        and isinstance(decorator.func, ast.Name)
                        and decorator.func.id == "dataclass"
                    )
                    for decorator in node.decorator_list
                )
                is_typed_dict = isinstance(node, ast.ClassDef) and any(
                    isinstance(base, ast.Name) and base.id == "TypedDict"
                    for base in node.bases
                )
                if is_dataclass or is_typed_dict:
                    owned_fields = [
                        statement.target.id
                        for statement in node.body
                        if isinstance(statement, ast.AnnAssign)
                        and isinstance(statement.target, ast.Name)
                    ]
                    undocumented = [
                        field for field in owned_fields if f"{field}:" not in docstring
                    ]
                    assert not undocumented, (
                        f"{path}:{node.lineno} {node.name} lacks field descriptions: "
                        f"{undocumented}"
                    )
