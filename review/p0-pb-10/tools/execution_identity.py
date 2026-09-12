"""Capture the Git and file identities that delimit one proposal-gate run."""

from __future__ import annotations

import hashlib
import subprocess
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ExecutionIdentity:
    """Persist the repository and file identities observed at one gate boundary."""

    git_head: str = field(
        metadata={"description": "Commit checked out when identity was captured."}
    )
    git_status_sha256: str = field(
        metadata={
            "description": (
                "Digest of Git's NUL-delimited status, including untracked paths."
            )
        }
    )
    git_diff_sha256: str = field(
        metadata={
            "description": "Digest of the binary diff between worktree and HEAD."
        }
    )
    checklist_sha256: str = field(
        metadata={"description": "Digest of the authoritative checklist bytes."}
    )
    contract_sha256: str = field(
        metadata={"description": "Digest of the governing contract bytes."}
    )
    source_sha256: dict[str, str] = field(
        metadata={
            "description": "Proposed repository paths mapped to their byte digests."
        }
    )
    master_validator_sha256: str = field(
        metadata={
            "description": "Digest of the global checklist validator used by the gate."
        }
    )


def sha256_bytes(value: bytes) -> str:
    """Return the lowercase SHA-256 digest of the supplied bytes."""

    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    """Return the lowercase SHA-256 digest of one file's bytes."""

    return sha256_bytes(path.read_bytes())


def _git_output(repository: Path, arguments: Sequence[str]) -> bytes:
    """Run one read-only Git query and return its exact standard output."""

    result = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
    )
    return result.stdout


def capture_execution_identity(
    repository: Path,
    *,
    checklist_path: Path,
    contract_path: Path,
    source_paths: Sequence[Path],
    validator_path: Path,
) -> ExecutionIdentity:
    """Capture every identity that must remain stable while a gate executes."""

    return ExecutionIdentity(
        git_head=_git_output(repository, ["rev-parse", "HEAD"]).decode().strip(),
        git_status_sha256=sha256_bytes(
            _git_output(
                repository,
                ["status", "--porcelain=v1", "-z", "--untracked-files=all"],
            )
        ),
        git_diff_sha256=sha256_bytes(
            _git_output(repository, ["diff", "--binary", "HEAD"])
        ),
        checklist_sha256=sha256_file(checklist_path),
        contract_sha256=sha256_file(contract_path),
        source_sha256={
            path.relative_to(repository).as_posix(): sha256_file(path)
            for path in source_paths
        },
        master_validator_sha256=sha256_file(validator_path),
    )


def compare_execution_identities(
    before: ExecutionIdentity,
    after: ExecutionIdentity,
) -> dict[str, dict[str, object]]:
    """Return every identity field that changed during gate execution."""

    before_values = asdict(before)
    after_values = asdict(after)
    return {
        name: {"before": before_values[name], "after": after_values[name]}
        for name in before_values
        if before_values[name] != after_values[name]
    }
