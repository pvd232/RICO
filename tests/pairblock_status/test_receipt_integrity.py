"""Verify native receipt fields and implementation-repository identities."""

from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Callable
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

NOW = datetime(2026, 9, 13, 14, 0, tzinfo=timezone.utc)
PASSING_COMMAND = (
    "python -c 'print(\"2 passed in 0.01s\")' "
    "tools/pairblock_status/checklist_profile.py "
    "tests/pairblock_status/test_pairblock_controller.py"
)


def _accept(
    repository: Path,
    profile: ChecklistProfile,
) -> MarkdownChecklistAdapter:
    """Accept fixture declarations and return their configured adapter."""

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
    return adapter


@pytest.mark.parametrize(
    ("field", "replacement", "message"),
    [
        ("command", "never executed", "command differs"),
        ("command_sha256", "0" * 64, "command digest differs"),
        ("output_sha256", "0" * 64, "output digest differs"),
        ("declaration_sha256", "0" * 64, "declaration digest differs"),
        ("identity_before", {}, "identity_before fields"),
    ],
)
def test_tampered_gate_receipt_cannot_authorize_approval(
    repository_factory: RepositoryFactory,
    declaration_profile: ChecklistProfile,
    field: str,
    replacement: object,
    message: str,
) -> None:
    """Reject each stored claim after its authoritative value changes."""

    repository = repository_factory(command=PASSING_COMMAND)
    adapter = _accept(repository, declaration_profile)
    receipt_path = run_gate(
        repository, "PB-NATIVE", now=NOW + timedelta(seconds=1), adapter=adapter
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt[field] = replacement
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    with pytest.raises(PairBlockGateError, match=message):
        advance_pairblock(
            repository,
            "PB-NATIVE",
            "approve",
            EvidenceRef("external", "review", "message"),
            adapter=adapter,
        )


def _replace_both_identity_fields(
    receipt: dict[str, object], field: str, value: object
) -> None:
    """Set one identity field to the same forged value on both snapshots."""

    for identity_name in ("identity_before", "identity_after"):
        identity = receipt[identity_name]
        assert isinstance(identity, dict)
        identity[field] = value


def _replace_both_source_maps(receipt: dict[str, object]) -> None:
    """Replace both captured source maps with malformed digests."""

    for identity_name in ("identity_before", "identity_after"):
        identity = receipt[identity_name]
        assert isinstance(identity, dict)
        sources = identity["source_sha256"]
        assert isinstance(sources, dict)
        identity["source_sha256"] = {name: "not-a-digest" for name in sources}


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda receipt: receipt.__setitem__("unexpected", True),
            "fields differ",
        ),
        (
            lambda receipt: _replace_both_identity_fields(
                receipt, "git_head", "0" * 40
            ),
            "unknown identity_before.git_head",
        ),
        (_replace_both_source_maps, "invalid identity_before.source_sha256"),
        (
            lambda receipt: receipt.__setitem__("master_validator_path", "/bin/true"),
            "master validator path differs",
        ),
    ],
)
def test_nested_gate_receipt_tampering_cannot_authorize_approval(
    repository_factory: RepositoryFactory,
    declaration_profile: ChecklistProfile,
    mutate: Callable[[dict[str, object]], None],
    message: str,
) -> None:
    """Reject coordinated edits that preserve the receipt's internal equality."""

    repository = repository_factory(command=PASSING_COMMAND)
    adapter = _accept(repository, declaration_profile)
    receipt_path = run_gate(
        repository, "PB-NATIVE", now=NOW + timedelta(seconds=1), adapter=adapter
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    mutate(receipt)
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    with pytest.raises(PairBlockGateError, match=message):
        advance_pairblock(
            repository,
            "PB-NATIVE",
            "approve",
            EvidenceRef("external", "review", "message"),
            adapter=adapter,
        )


def test_cross_repository_gate_records_implementation_owner(
    repository_factory: RepositoryFactory,
    declaration_profile: ChecklistProfile,
) -> None:
    """Distinguish the declaration checkout from the source checkout."""

    repository = repository_factory(command=PASSING_COMMAND)
    owner = repository.parent / "owner"
    owner.mkdir()
    for relative in (
        Path("tools/pairblock_status/checklist_profile.py"),
        Path("tests/pairblock_status/test_pairblock_controller.py"),
    ):
        source = Path(__file__).parents[2] / relative
        target = owner / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    subprocess.run(["git", "init", "-q"], cwd=owner, check=True)
    subprocess.run(["git", "add", "."], cwd=owner, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-qm",
            "fixture",
        ],
        cwd=owner,
        check=True,
    )
    manifest = repository / "declarations.toml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            'repository = "test"', 'repository = "owner"'
        ),
        encoding="utf-8",
    )
    profile = replace(
        declaration_profile,
        repository_roots=(("owner", Path("../owner")),),
    )
    adapter = _accept(repository, profile)

    receipt_path = run_gate(
        repository, "PB-NATIVE", now=NOW + timedelta(seconds=1), adapter=adapter
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert (
        receipt["identity_before"]["git_head"]
        == subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )
    assert (
        receipt["identity_before"]["implementation_git_head"]
        == subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=owner,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )
    assert receipt["identity_before"]["implementation_repository"] == owner.as_posix()
