#!/usr/bin/env python3
"""Materialize one planned PairBlock over Git HEAD and run its declared gate.

The checker copies tracked baseline files into a temporary directory, overlays
the selected plan actions, and executes the gate there. The RICO working tree
remains unchanged, so a passing result proves the staged production candidates
work together before the user creates their active clones.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path

import tomllib


def main(argv: Sequence[str] | None = None) -> int:
    """Materialize the selected block and return its gate's exit status."""

    arguments = _parse_arguments(argv)
    plan_root = Path(__file__).resolve().parent
    repository = plan_root.parents[1]
    plan = _load_plan(plan_root / "plan.toml")
    block = _select_block(plan, arguments.pair_block_id)

    with tempfile.TemporaryDirectory(prefix="pairblock-plan-") as directory:
        candidate = Path(directory) / "RICO"
        _copy_tracked_baseline(repository, candidate)
        _overlay_actions(plan_root, candidate, block)
        os.symlink(repository / ".venv", candidate / ".venv")
        result = _run_gate(candidate, block)
    return result.returncode


def _parse_arguments(argv: Sequence[str] | None) -> argparse.Namespace:
    """Parse the one PairBlock identifier selected for materialization."""

    parser = argparse.ArgumentParser()
    parser.add_argument("pair_block_id", nargs="?", default="P0-PB-10K")
    return parser.parse_args(argv)


def _load_plan(path: Path) -> dict[str, object]:
    """Load the source-backed plan from its checked-in TOML file."""

    with path.open("rb") as stream:
        return tomllib.load(stream)


def _select_block(plan: Mapping[str, object], pair_block_id: str) -> dict[str, object]:
    """Return the unique planned block with the requested identifier."""

    blocks = plan.get("pair_blocks")
    if not isinstance(blocks, list):
        raise TypeError("plan pair_blocks must be a list")
    matches = [
        block
        for block in blocks
        if isinstance(block, dict) and block.get("id") == pair_block_id
    ]
    if len(matches) != 1:
        raise ValueError(f"plan must contain one PairBlock {pair_block_id}")
    return matches[0]


def _copy_tracked_baseline(repository: Path, destination: Path) -> None:
    """Copy every file owned by the current Git revision into a temporary root."""

    destination.mkdir(parents=True)
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repository,
        check=True,
        capture_output=True,
    )
    for encoded_path in result.stdout.split(b"\0"):
        if not encoded_path:
            continue
        relative_path = Path(encoded_path.decode())
        source = repository / relative_path
        target = destination / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def _overlay_actions(
    plan_root: Path,
    candidate: Path,
    block: Mapping[str, object],
) -> None:
    """Copy each declared candidate file to its production-relative target."""

    actions = block.get("actions")
    if not isinstance(actions, list) or not actions:
        raise ValueError("planned PairBlock must declare at least one action")
    for action in actions:
        if not isinstance(action, dict) or action.get("kind") != "add":
            raise ValueError("P0-PB-10K accepts only add actions")
        source_value = action.get("source")
        target_value = action.get("target")
        if not isinstance(source_value, str) or not isinstance(target_value, str):
            raise TypeError("plan action source and target must be strings")
        source = _contained_path(plan_root, source_value, "action source")
        target = _contained_path(candidate, target_value, "action target")
        if not source.is_file():
            raise ValueError(f"planned source is missing: {source_value}")
        if target.exists():
            raise ValueError(f"add target already exists: {target_value}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def _contained_path(root: Path, value: str, label: str) -> Path:
    """Resolve one relative path and require it to remain beneath its owner."""

    path = Path(value)
    resolved = (root / path).resolve()
    if path.is_absolute() or not resolved.is_relative_to(root.resolve()):
        raise ValueError(f"{label} must remain beneath {root}")
    return resolved


def _run_gate(
    candidate: Path,
    block: Mapping[str, object],
) -> subprocess.CompletedProcess[str]:
    """Execute the selected block's ordered gate commands in the candidate root."""

    gate = block.get("gate")
    if not isinstance(gate, list) or any(not isinstance(item, str) for item in gate):
        raise ValueError("planned PairBlock gate must be a string list")
    command = " && ".join(gate)
    return subprocess.run(
        ["/bin/zsh", "-e", "-c", command],
        cwd=candidate,
        check=False,
        text=True,
    )


if __name__ == "__main__":
    raise SystemExit(main())
