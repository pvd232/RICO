"""Verify deterministic human views generated from typed declarations."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from tools.pairblock_status.checklist_profile import PairBlockGateError
from tools.pairblock_status.declaration_manifest import load_declarations
from tools.pairblock_status.markdown_renderer import PairBlockView, render_markdown
from tools.pairblock_status.profile import ChecklistProfile


def _render(
    repository: Path,
    profile: ChecklistProfile,
    *,
    status: str = "Drafting",
    receipt: str | None = None,
    check: bool = False,
):
    """Render the fixture declaration through its configured documents."""

    declarations = load_declarations(repository / "declarations.toml", profile)
    return render_markdown(
        repository,
        declarations,
        {"PB-NATIVE": PairBlockView(status, receipt)},
        profile,
        check=check,
    )


def test_equal_inputs_render_equal_bytes(
    repository_factory: Callable[..., Path], declaration_profile: ChecklistProfile
) -> None:
    """Produce byte-identical documents from equal structured inputs."""

    repository = repository_factory(command="true")

    first = _render(repository, declaration_profile)
    second = _render(repository, declaration_profile)

    assert first == second
    assert b"#### Manifest-native block PB-NATIVE" in first.contract
    assert b"[checklist_profile.py]" in first.contract
    assert b"python -c 'print('" in first.contract
    assert b"| `PB-NATIVE` | Drafting |" in first.checklist


def test_receipt_transition_updates_every_displayed_status(
    repository_factory: Callable[..., Path], declaration_profile: ChecklistProfile
) -> None:
    """Render one receipt-derived status and its direct receipt links."""

    repository = repository_factory(command="true")
    rendered = _render(
        repository,
        declaration_profile,
        status="Review",
        receipt="evidence/pairblock-gates/pb-gate/pass.json",
    )

    assert b"**Status:** Review" in rendered.contract
    assert b"| `PB-NATIVE` | Review |" in rendered.checklist
    assert b"pass.json" in rendered.contract
    assert b"pass.json" in rendered.checklist
    assert b"advance PB-NATIVE approve" in rendered.contract


def test_manual_generated_region_edit_fails_check_mode(
    repository_factory: Callable[..., Path], declaration_profile: ChecklistProfile
) -> None:
    """Reject hand-edited bytes inside a generated document region."""

    repository = repository_factory(command="true")
    rendered = _render(repository, declaration_profile)
    contract = repository / declaration_profile.contract_path
    checklist = repository / declaration_profile.checklist_path
    contract.write_bytes(rendered.contract.replace(b"Drafting", b"Complete"))
    checklist.write_bytes(rendered.checklist)

    with pytest.raises(PairBlockGateError, match="differs from declarations"):
        _render(repository, declaration_profile, check=True)


def test_missing_generated_region_is_rejected(
    repository_factory: Callable[..., Path], declaration_profile: ChecklistProfile
) -> None:
    """Require one guarded region in each generated document."""

    repository = repository_factory(command="true")
    contract = repository / declaration_profile.contract_path
    contract.write_text("# Contract\n", encoding="utf-8")

    with pytest.raises(PairBlockGateError, match="needs one"):
        _render(repository, declaration_profile)


def test_links_escape_markdown_controls_and_commands_name_repository(
    repository_factory: Callable[..., Path], declaration_profile: ChecklistProfile
) -> None:
    """Render copyable commands and unambiguous unusual path destinations."""

    repository = repository_factory(command="true")
    manifest = repository / "declarations.toml"
    unusual = "tools/pairblock_status/example (a)#b|c.py"
    target = repository / unusual
    target.write_text("VALUE = 1\n", encoding="utf-8")
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            'source_paths = ["tools/pairblock_status/checklist_profile.py"]',
            f'source_paths = ["{unusual}"]',
        ),
        encoding="utf-8",
    )

    rendered = _render(repository, declaration_profile)

    assert b"example%20%28a%29%23b%7Cc.py" in rendered.contract
    repository_command = f"cd {repository.resolve().as_posix()}".encode()
    assert rendered.contract.count(repository_command) == 2
