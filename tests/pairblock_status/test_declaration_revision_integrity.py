"""Verify schema and reviewed-plan integrity for declaration revisions."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone

import pytest
from conftest import TEST_ADAPTER, RepositoryFactory

from tools.pairblock_status.declaration_manifest import (
    declarations_from_payload,
    load_declarations,
)
from tools.pairblock_status.execution_identity import sha256_file
from tools.pairblock_status.pairblock_controller import (
    EvidenceRef,
    accept_declaration_revision,
    write_declaration_revision_plan,
)
from tools.pairblock_status.profile import ChecklistProfile, PairBlockGateError

NOW = datetime(2026, 9, 13, 13, 0, tzinfo=timezone.utc)
PASSING_COMMAND = (
    "python -c 'print(\"2 passed in 0.01s\")' "
    "tools/pairblock_status/checklist_profile.py "
    "tests/pairblock_status/test_pairblock_controller.py"
)


@pytest.mark.parametrize("version", [0, 2, True])
def test_live_and_snapshot_declarations_reject_other_schema_versions(
    repository_factory: RepositoryFactory,
    declaration_profile: ChecklistProfile,
    version: object,
) -> None:
    """Apply one schema-version rule to TOML and accepted JSON snapshots."""

    repository = repository_factory(command=PASSING_COMMAND)
    manifest = repository / "declarations.toml"
    text = manifest.read_text(encoding="utf-8")
    manifest.write_text(
        text.replace("schema_version = 1", f"schema_version = {str(version).lower()}"),
        encoding="utf-8",
    )
    with pytest.raises(PairBlockGateError, match="schema_version"):
        load_declarations(manifest, declaration_profile)

    manifest.write_text(text, encoding="utf-8")
    payload = load_declarations(manifest, declaration_profile).canonical_payload()
    payload["schema_version"] = version
    with pytest.raises(PairBlockGateError, match="schema_version"):
        declarations_from_payload(payload, declaration_profile, repository)


def test_revision_acceptance_rejects_a_candidate_changed_after_planning(
    repository_factory: RepositoryFactory,
    declaration_profile: ChecklistProfile,
) -> None:
    """Bind approval to the exact candidate bytes recorded in its plan."""

    repository = repository_factory(command=PASSING_COMMAND)
    adapter = replace(TEST_ADAPTER, profile=declaration_profile)
    plan = write_declaration_revision_plan(repository, now=NOW, adapter=adapter)
    manifest = repository / "declarations.toml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            "The proposal gate retains its result.",
            "The proposal gate retains a different result.",
        ),
        encoding="utf-8",
    )

    with pytest.raises(PairBlockGateError, match="reviewed plan"):
        accept_declaration_revision(
            repository,
            EvidenceRef("external", "review", "message"),
            plan_path=plan,
            plan_sha256=sha256_file(plan),
            adapter=adapter,
        )


def test_revision_plan_digest_rejects_changed_plan_bytes(
    repository_factory: RepositoryFactory,
    declaration_profile: ChecklistProfile,
) -> None:
    """Reject a plan edited after the reviewer received its digest."""

    repository = repository_factory(command=PASSING_COMMAND)
    adapter = replace(TEST_ADAPTER, profile=declaration_profile)
    plan = write_declaration_revision_plan(repository, now=NOW, adapter=adapter)
    digest = sha256_file(plan)
    payload = json.loads(plan.read_text(encoding="utf-8"))
    payload["affected_pair_blocks"] = []
    plan.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(PairBlockGateError, match="digest differs"):
        accept_declaration_revision(
            repository,
            EvidenceRef("external", "review", "message"),
            plan_path=plan,
            plan_sha256=digest,
            adapter=adapter,
        )
