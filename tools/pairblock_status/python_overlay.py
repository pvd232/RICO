"""Run a command with staged Python files overlaid on an active source tree."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
from collections.abc import Sequence
from pathlib import Path


def run_overlay(
    active_root: Path,
    proposal_root: Path,
    command: Sequence[str],
) -> int:
    """Copy both source trees into a temporary import root and run ``command``."""

    if not active_root.is_dir() or not proposal_root.is_dir():
        raise FileNotFoundError("active_root and proposal_root must be directories")
    if not command:
        raise ValueError("command must not be empty")
    with tempfile.TemporaryDirectory(prefix="pairblock-overlay-") as temporary:
        overlay = Path(temporary)
        shutil.copytree(active_root, overlay, dirs_exist_ok=True)
        shutil.copytree(proposal_root, overlay, dirs_exist_ok=True)
        environment = os.environ.copy()
        existing = environment.get("PYTHONPATH")
        environment["PYTHONPATH"] = (
            str(overlay) if not existing else f"{overlay}{os.pathsep}{existing}"
        )
        return subprocess.run(command, env=environment, check=False).returncode


def main(argv: Sequence[str] | None = None) -> int:
    """Parse the two source roots and execute the remaining command."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--active-root", type=Path, required=True)
    parser.add_argument("--proposal-root", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    arguments = parser.parse_args(argv)
    command = arguments.command
    if command[:1] == ["--"]:
        command = command[1:]
    return run_overlay(arguments.active_root, arguments.proposal_root, command)


if __name__ == "__main__":
    raise SystemExit(main())
