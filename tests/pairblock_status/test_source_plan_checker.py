"""Verify replay of the PairBlock lifecycle source plan."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_applied_source_plan_replays_from_its_declared_baseline() -> None:
    """Run the approved plan after its add targets exist in the live checkout."""

    repository = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [
            sys.executable,
            "plans/pairblock-lifecycle-evidence/check.py",
            "P0-PB-10K",
        ],
        cwd=repository,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
