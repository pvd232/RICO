"""Verify dependency state across legacy and manifest-native declarations."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest
from conftest import TEST_ADAPTER, RepositoryFactory

from tools.pairblock_status.execution_identity import sha256_file
from tools.pairblock_status.pairblock_controller import (
    EvidenceRef,
    accept_declaration_revision,
    render_views,
    run_gate,
    write_declaration_revision_plan,
)
from tools.pairblock_status.profile import ChecklistProfile, PairBlockGateError

NOW = datetime(2026, 9, 13, 15, 0, tzinfo=timezone.utc)
PASSING_COMMAND = (
    "python -c 'print(\"2 passed in 0.01s\")' "
    "tools/pairblock_status/checklist_profile.py "
    "tests/pairblock_status/test_pairblock_controller.py"
)


def test_native_block_waits_for_unresolved_legacy_dependency(
    repository_factory: RepositoryFactory,
    declaration_profile: ChecklistProfile,
) -> None:
    """Render and enforce one unresolved dependency from the legacy checklist."""

    repository = repository_factory(command=PASSING_COMMAND, status="Review")
    manifest = repository / "declarations.toml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            'depends_on = []\nsection = "0A"',
            'depends_on = ["PB-GATE"]\nsection = "0A"',
        ),
        encoding="utf-8",
    )
    adapter = replace(TEST_ADAPTER, profile=declaration_profile)
    plan = write_declaration_revision_plan(repository, now=NOW, adapter=adapter)
    accept_declaration_revision(
        repository,
        EvidenceRef("external", "review", "message"),
        plan_path=plan,
        plan_sha256=sha256_file(plan),
        now=NOW,
        adapter=adapter,
    )

    checklist = (repository / declaration_profile.checklist_path).read_text(
        encoding="utf-8"
    )
    assert "| `PB-NATIVE` | Waiting for PB-GATE |" in checklist
    with pytest.raises(PairBlockGateError, match="cannot run.*Waiting for PB-GATE"):
        run_gate(repository, "PB-NATIVE", adapter=adapter)

    checklist_path = repository / declaration_profile.checklist_path
    checklist_path.write_text(
        checklist.replace("Waiting for PB-GATE", "Drafting"),
        encoding="utf-8",
    )
    render_views(repository, adapter=adapter)
    assert "| `PB-NATIVE` | Waiting for PB-GATE |" in checklist_path.read_text(
        encoding="utf-8"
    )
