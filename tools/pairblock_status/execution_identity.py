"""Capture the Git and file identities that delimit one proposal-gate run."""

from __future__ import annotations

import hashlib
import subprocess
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ExecutionIdentity:
    """Persist the repository and file identities at one gate boundary.

    Attributes:
        git_head: Commit checked out when the identity was captured.
        git_status_sha256: Digest of Git's NUL-delimited porcelain status,
            including untracked paths.
        git_diff_sha256: Digest of the binary diff between the worktree and
            ``HEAD``.
        checklist_sha256: Digest of the authoritative checklist bytes.
        contract_sha256: Digest of the governing contract bytes.
        source_sha256: Proposed repository paths mapped to their byte digests.
        master_validator_sha256: Digest of the inherited checklist validator.
        implementation_repository: Absolute path of the repository that owns
            the executed implementation.
        implementation_git_head: Owner commit checked out at capture time.
        implementation_git_status_sha256: Digest of the owner's porcelain
            status, including untracked paths.
        implementation_git_diff_sha256: Digest of the owner's binary diff.
    """

    git_head: str
    git_status_sha256: str
    git_diff_sha256: str
    checklist_sha256: str
    contract_sha256: str
    source_sha256: dict[str, str]
    master_validator_sha256: str
    implementation_repository: str
    implementation_git_head: str
    implementation_git_status_sha256: str
    implementation_git_diff_sha256: str


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
    implementation_repository: Path | None = None,
) -> ExecutionIdentity:
    """Capture controller and implementation repository identities.

    ``repository`` owns the declarations and rendered views.
    ``implementation_repository`` owns the command and proposed source. The
    two arguments may identify the same Git checkout.
    """

    owner = (implementation_repository or repository).resolve()

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
            (
                path.relative_to(repository).as_posix()
                if path.is_relative_to(repository)
                else path.as_posix()
            ): sha256_file(path)
            for path in source_paths
        },
        master_validator_sha256=sha256_file(validator_path),
        implementation_repository=owner.as_posix(),
        implementation_git_head=_git_output(owner, ["rev-parse", "HEAD"])
        .decode()
        .strip(),
        implementation_git_status_sha256=sha256_bytes(
            _git_output(
                owner,
                ["status", "--porcelain=v1", "-z", "--untracked-files=all"],
            )
        ),
        implementation_git_diff_sha256=sha256_bytes(
            _git_output(owner, ["diff", "--binary", "HEAD"])
        ),
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
