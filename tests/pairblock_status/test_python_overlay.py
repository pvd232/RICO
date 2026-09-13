"""Tests for staged Python source overlays."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from tools.pairblock_status.python_overlay import run_overlay


def test_proposal_module_overrides_active_module(tmp_path: Path) -> None:
    """Import proposed bytes while retaining the active package structure."""

    active = tmp_path / "active"
    proposal = tmp_path / "proposal"
    (active / "example").mkdir(parents=True)
    (proposal / "example").mkdir(parents=True)
    (active / "example/__init__.py").write_text("", encoding="utf-8")
    (active / "example/value.py").write_text("VALUE = 'active'\n", encoding="utf-8")
    (proposal / "example/value.py").write_text("VALUE = 'proposal'\n", encoding="utf-8")

    result = run_overlay(
        active,
        proposal,
        (
            sys.executable,
            "-c",
            "from example.value import VALUE; assert VALUE == 'proposal'",
        ),
    )

    assert result == 0


@pytest.mark.parametrize("missing", ["active", "proposal"])
def test_requires_both_source_roots(tmp_path: Path, missing: str) -> None:
    """Reject an absent active or proposal source root."""

    active = tmp_path / "active"
    proposal = tmp_path / "proposal"
    active.mkdir()
    proposal.mkdir()
    (tmp_path / missing).rmdir()

    with pytest.raises(FileNotFoundError):
        run_overlay(active, proposal, (sys.executable, "-c", "pass"))
