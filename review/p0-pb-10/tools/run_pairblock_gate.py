"""Run one validated proposal gate, retain its receipt, and update its status."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .checklist_profile import (
    DEFAULT_MASTER_CHECKLIST_VALIDATOR,
    MANTRA_PHASE0_ADAPTER,
    MarkdownChecklistAdapter,
    PairBlockGateError,
    validate_normalized_manifest,
)
from .execution_identity import (
    capture_execution_identity,
    compare_execution_identities,
    sha256_bytes,
)

_PASSED = re.compile(r"(?m)(\d+) passed(?:,| in )")


@dataclass(frozen=True, slots=True)
class GateReceipt:
    """Persist one proposal-gate attempt and its controlled status outcome.

    Attributes:
        schema_version: Version of the persisted receipt structure.
        pair_block_id: PairBlock whose declared proposal gate ran.
        result: Gate outcome: ``passed``, ``failed``, or ``invalidated``.
        status_before: Authoritative lifecycle status before execution.
        status_after: Lifecycle status written or preserved by the runner.
        started_at: UTC timestamp immediately before command execution.
        finished_at: UTC timestamp immediately after command execution.
        checklist_path: Repository-relative authoritative checklist path.
        checklist_written_sha256: Digest of the checklist bytes preserved or
            written by the runner.
        contract_path: Repository-relative governing contract path.
        command: Exact contract-declared shell command that ran.
        command_sha256: Digest of the executed command text.
        exit_code: Process exit code returned by the gate command.
        stdout: Complete standard output from the gate command.
        stderr: Complete standard error from the gate command.
        output_sha256: Digest of stdout, a NUL separator, and stderr.
        master_validator_path: Absolute inherited-validator path.
        identity_before: Git and file identities captured before execution.
        identity_after: Git and file identities captured after execution.
        identity_drift: Before and after values for changed identities.
        normalized_manifest: Validated schema-version-2 checklist manifest.
        normalized_manifest_sha256: Digest of the manifest's canonical JSON.
    """

    schema_version: int
    pair_block_id: str
    result: str
    status_before: str
    status_after: str
    started_at: str
    finished_at: str
    checklist_path: str
    checklist_written_sha256: str
    contract_path: str
    command: str
    command_sha256: str
    exit_code: int
    stdout: str
    stderr: str
    output_sha256: str
    master_validator_path: str
    identity_before: dict[str, object]
    identity_after: dict[str, object]
    identity_drift: dict[str, dict[str, object]]
    normalized_manifest: dict[str, object]
    normalized_manifest_sha256: str


def _atomic_write(path: Path, content: bytes) -> None:
    """Replace one file after flushing a same-directory temporary file."""

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    finally:
        temporary = Path(temporary_name)
        if temporary.exists():
            temporary.unlink()


def run_gate(
    repository: Path,
    pair_block_id: str,
    *,
    now: datetime | None = None,
    validator_path: Path = DEFAULT_MASTER_CHECKLIST_VALIDATOR,
    adapter: MarkdownChecklistAdapter = MANTRA_PHASE0_ADAPTER,
) -> Path:
    """Execute one eligible proposal gate and persist its evidence and status."""

    repository = repository.resolve()
    profile = adapter.profile
    if not profile.accepts_pair_block_id(pair_block_id):
        raise PairBlockGateError(f"invalid PairBlock ID: {pair_block_id}")

    checklist_path = repository / profile.checklist_path
    checklist_before = checklist_path.read_bytes()
    checklist_text = checklist_before.decode("utf-8")
    rows, manifest = adapter.validate_traceability(
        repository,
        validator_path=validator_path,
    )
    try:
        row = rows[pair_block_id]
    except KeyError as error:
        raise PairBlockGateError(f"unknown PairBlock: {pair_block_id}") from error
    if not adapter.has_proposed_code(row):
        raise PairBlockGateError(f"{pair_block_id} has no proposed code")
    for dependency in row.dependencies:
        dependency_status = rows[dependency].status
        if dependency_status not in profile.lifecycle.resolved_dependency_states:
            raise PairBlockGateError(
                f"{pair_block_id} dependency {dependency} is not resolved: "
                f"{dependency_status}"
            )
    if row.status not in profile.lifecycle.proposal_gate_states:
        raise PairBlockGateError(f"proposal gate cannot run from status: {row.status}")

    proposal = adapter.load_proposal_contract(repository, checklist_path, row)
    resolved_validator = validator_path.resolve()
    identity_before = capture_execution_identity(
        repository,
        checklist_path=checklist_path,
        contract_path=proposal.path,
        source_paths=proposal.source_paths,
        validator_path=resolved_validator,
    )
    started = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    completed = subprocess.run(
        ["/bin/zsh", "-lc", proposal.command],
        cwd=repository,
        check=False,
        capture_output=True,
        text=True,
    )
    finished = datetime.now(timezone.utc) if now is None else started
    identity_after = capture_execution_identity(
        repository,
        checklist_path=checklist_path,
        contract_path=proposal.path,
        source_paths=proposal.source_paths,
        validator_path=resolved_validator,
    )
    drift = compare_execution_identities(identity_before, identity_after)

    if completed.returncode != 0:
        result = "failed"
    elif drift:
        result = "invalidated"
    else:
        result = "passed"
    status_after = profile.lifecycle.review_status if result == "passed" else row.status

    stamp = started.strftime("%Y%m%dT%H%M%S.%fZ")
    receipt_path = (
        repository
        / "evidence"
        / "pairblock-gates"
        / pair_block_id.lower()
        / f"{stamp}.json"
    )
    if receipt_path.exists():
        raise PairBlockGateError(f"receipt already exists: {receipt_path}")

    checklist_after = checklist_before
    manifest_after = manifest
    if result == "passed":
        passed = _PASSED.search(completed.stdout + completed.stderr)
        if passed is None:
            raise PairBlockGateError("passing gate output lacks a pytest pass count")
        relative_receipt = Path(
            os.path.relpath(receipt_path, checklist_path.parent)
        ).as_posix()
        checklist_after = adapter.record_gate_result(
            checklist_text,
            row,
            test_count=int(passed.group(1)),
            receipt_path=relative_receipt,
            status=status_after,
        )
        projected_text = checklist_after.decode("utf-8")
        projected_rows = adapter.parse_pair_block_rows(projected_text)
        manifest_after = adapter.compile_normalized_manifest(
            repository,
            projected_text,
            projected_rows,
        )
        validate_normalized_manifest(
            repository,
            manifest_after,
            resolved_validator,
        )

    combined_output = completed.stdout.encode() + b"\0" + completed.stderr.encode()
    receipt = GateReceipt(
        schema_version=2,
        pair_block_id=pair_block_id,
        result=result,
        status_before=row.status,
        status_after=status_after,
        started_at=started.isoformat(),
        finished_at=finished.isoformat(),
        checklist_path=profile.checklist_path.as_posix(),
        checklist_written_sha256=sha256_bytes(checklist_after),
        contract_path=proposal.path.relative_to(repository).as_posix(),
        command=proposal.command,
        command_sha256=sha256_bytes(proposal.command.encode()),
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        output_sha256=sha256_bytes(combined_output),
        master_validator_path=str(resolved_validator),
        identity_before=asdict(identity_before),
        identity_after=asdict(identity_after),
        identity_drift=drift,
        normalized_manifest=manifest_after,
        normalized_manifest_sha256=sha256_bytes(
            (json.dumps(manifest_after, sort_keys=True) + "\n").encode()
        ),
    )

    # A finalized receipt may exist without a checklist link after interruption;
    # the receipt's checklist digest makes that state detectable and recoverable.
    _atomic_write(
        receipt_path,
        (json.dumps(asdict(receipt), indent=2, sort_keys=True) + "\n").encode(),
    )
    if result == "passed":
        _atomic_write(checklist_path, checklist_after)
        adapter.validate_traceability(
            repository,
            validator_path=resolved_validator,
        )
    return receipt_path


def main(argv: Sequence[str] | None = None) -> int:
    """Parse the CLI request and return success only for a passing gate."""

    parser = argparse.ArgumentParser()
    parser.add_argument("pair_block_id")
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument(
        "--master-validator",
        type=Path,
        default=DEFAULT_MASTER_CHECKLIST_VALIDATOR,
    )
    arguments = parser.parse_args(argv)
    receipt_path = run_gate(
        arguments.repository,
        arguments.pair_block_id,
        validator_path=arguments.master_validator,
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    print(receipt_path)
    return 0 if receipt["result"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
