"""Verify event-specific evidence policy for manifest-native PairBlocks."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from conftest import TEST_ADAPTER, RepositoryFactory

from tools.pairblock_status.checklist_profile import MarkdownChecklistAdapter
from tools.pairblock_status.execution_identity import sha256_file
from tools.pairblock_status.pairblock_controller import (
    EvidenceRef,
    accept_declaration_revision,
    advance_pairblock,
    run_gate,
    write_declaration_revision_plan,
)
from tools.pairblock_status.profile import ChecklistProfile, PairBlockGateError

NOW = datetime(2026, 9, 13, 12, 0, tzinfo=timezone.utc)
PASSING_COMMAND = (
    "python -c 'print(\"2 passed in 0.01s\")' "
    "tools/pairblock_status/checklist_profile.py "
    "tests/pairblock_status/test_pairblock_controller.py"
)


def _accepted_repository(
    repository_factory: RepositoryFactory,
    profile: ChecklistProfile,
) -> tuple[Path, MarkdownChecklistAdapter]:
    """Create and accept the native fixture declarations."""

    repository = repository_factory(command=PASSING_COMMAND)
    adapter = replace(TEST_ADAPTER, profile=profile)
    plan = write_declaration_revision_plan(repository, now=NOW, adapter=adapter)
    accept_declaration_revision(
        repository,
        EvidenceRef("external", "review", "message"),
        plan_path=plan,
        plan_sha256=sha256_file(plan),
        now=NOW,
        adapter=adapter,
    )
    run_gate(repository, "PB-NATIVE", now=NOW + timedelta(seconds=1), adapter=adapter)
    return repository, adapter


@pytest.mark.parametrize(
    ("event", "evidence", "message"),
    [
        ("approve", EvidenceRef("test", "tests/example.py", "node"), "external"),
        ("accept", EvidenceRef("external", "review", "message"), "artifact"),
        ("register", EvidenceRef("command", "viper verify", "run"), "artifact"),
    ],
)
def test_native_events_reject_other_evidence_categories(
    repository_factory: RepositoryFactory,
    declaration_profile: ChecklistProfile,
    event: str,
    evidence: EvidenceRef,
    message: str,
) -> None:
    """Reject each counterexample before writing its lifecycle receipt."""

    repository, adapter = _accepted_repository(repository_factory, declaration_profile)
    if event != "approve":
        advance_pairblock(
            repository,
            "PB-NATIVE",
            "approve",
            EvidenceRef("external", "review", "message"),
            now=NOW + timedelta(seconds=2),
            adapter=adapter,
        )
    if event == "register":
        artifact = repository / "evidence/accepted.json"
        artifact.write_text('{"accepted": true}\n', encoding="utf-8")
        advance_pairblock(
            repository,
            "PB-NATIVE",
            "accept",
            EvidenceRef(
                "artifact",
                artifact.relative_to(repository).as_posix(),
                sha256_file(artifact),
            ),
            now=NOW + timedelta(seconds=3),
            adapter=adapter,
        )

    with pytest.raises(PairBlockGateError, match=message):
        advance_pairblock(
            repository,
            "PB-NATIVE",
            event,
            evidence,
            now=NOW + timedelta(seconds=4),
            adapter=adapter,
        )


def test_native_artifact_evidence_requires_matching_retained_bytes(
    repository_factory: RepositoryFactory,
    declaration_profile: ChecklistProfile,
) -> None:
    """Reject a missing artifact and a digest that names different bytes."""

    repository, adapter = _accepted_repository(repository_factory, declaration_profile)
    advance_pairblock(
        repository,
        "PB-NATIVE",
        "approve",
        EvidenceRef("external", "review", "message"),
        now=NOW + timedelta(seconds=2),
        adapter=adapter,
    )

    with pytest.raises(PairBlockGateError, match="missing"):
        advance_pairblock(
            repository,
            "PB-NATIVE",
            "accept",
            EvidenceRef("artifact", "evidence/missing.json", "0" * 64),
            adapter=adapter,
        )

    artifact = repository / "evidence/review.json"
    artifact.write_text('{"accepted": true}\n', encoding="utf-8")
    with pytest.raises(PairBlockGateError, match="digest"):
        advance_pairblock(
            repository,
            "PB-NATIVE",
            "accept",
            EvidenceRef("artifact", "evidence/review.json", "0" * 64),
            adapter=adapter,
        )
