#!/usr/bin/env python3
"""Materialize one planned PairBlock over its Git baseline and run its gate.

The checker extracts the plan's immutable baseline into a temporary directory,
overlays the selected actions, and executes the gate there. The RICO working
tree remains unchanged, and later production edits cannot change the candidate
under test.
"""

from __future__ import annotations

import argparse
import io
import os
import shutil
import subprocess
import tarfile
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
    _validate_plan_identity(plan, plan_root, repository)
    block = _select_block(plan, arguments.pair_block_id)
    baseline = _require_string(plan, "baseline")

    with tempfile.TemporaryDirectory(prefix="pairblock-plan-") as directory:
        candidate = Path(directory) / "RICO"
        _copy_tracked_baseline(repository, candidate, baseline)
        _overlay_actions(plan_root, candidate, block)
        os.symlink(repository / ".venv", candidate / ".venv")
        result = _run_gate(candidate, block)
    return result.returncode


def _parse_arguments(argv: Sequence[str] | None) -> argparse.Namespace:
    """Parse the one PairBlock identifier selected for materialization."""

    parser = argparse.ArgumentParser()
    parser.add_argument("pair_block_id")
    return parser.parse_args(argv)


def _load_plan(path: Path) -> dict[str, object]:
    """Load the source-backed plan from its checked-in TOML file."""

    with path.open("rb") as stream:
        return tomllib.load(stream)


def _validate_plan_identity(
    plan: Mapping[str, object],
    plan_root: Path,
    repository: Path,
) -> None:
    """Require the package directory, contract ID, and contract path to agree."""

    if plan.get("schema_version") != 1:
        raise ValueError("plan schema_version must be 1")
    contract_id = _require_string(plan, "contract_id")
    if plan_root.name != contract_id:
        raise ValueError("plan directory must equal contract_id")
    contract_path = Path(_require_string(plan, "contract_path"))
    if contract_path.stem != contract_id:
        raise ValueError("contract filename stem must equal contract_id")
    contract = _contained_path(repository, contract_path.as_posix(), "contract path")
    if not contract.is_file():
        raise ValueError("contract path must name an existing file")


def _require_string(plan: Mapping[str, object], field: str) -> str:
    """Return one required nonempty plan string."""

    value = plan.get(field)
    if not isinstance(value, str) or not value or value.strip() != value:
        raise TypeError(f"plan {field} must be a nonempty string")
    return value


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


def _copy_tracked_baseline(
    repository: Path,
    destination: Path,
    baseline: str,
) -> None:
    """Extract the plan's immutable Git baseline into a temporary root."""

    destination.mkdir(parents=True)
    result = subprocess.run(
        ["git", "archive", "--format=tar", baseline],
        cwd=repository,
        check=True,
        capture_output=True,
    )
    with tarfile.open(fileobj=io.BytesIO(result.stdout), mode="r:") as archive:
        archive.extractall(destination, filter="data")


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
        if not isinstance(action, dict):
            raise TypeError("plan action must be a mapping")
        kind = action.get("kind")
        if kind not in {"add", "replace"}:
            raise ValueError("plan action kind must be add or replace")
        source_value = action.get("source")
        target_value = action.get("target")
        if not isinstance(source_value, str) or not isinstance(target_value, str):
            raise TypeError("plan action source and target must be strings")
        source = _contained_path(plan_root, source_value, "action source")
        target = _contained_path(candidate, target_value, "action target")
        if not source.is_file():
            raise ValueError(f"planned source is missing: {source_value}")
        if kind == "add" and target.exists():
            raise ValueError(f"add target already exists: {target_value}")
        if kind == "replace" and not target.is_file():
            raise ValueError(f"replace target is missing: {target_value}")
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
