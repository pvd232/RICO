"""Run PairBlock gates and record evidence-backed lifecycle transitions."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import tempfile
from collections.abc import Sequence
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from itertools import pairwise
from pathlib import Path

from .checklist_profile import (
    DEFAULT_MASTER_CHECKLIST_VALIDATOR,
    MANTRA_PHASE0_ADAPTER,
    MarkdownChecklistAdapter,
    PairBlockGateError,
    PairBlockRow,
    validate_normalized_manifest,
)
from .execution_identity import (
    capture_execution_identity,
    compare_execution_identities,
    sha256_bytes,
)
from .profile import ChecklistProfile

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


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    """Identify one artifact, command, test, or external lifecycle observation.

    Attributes:
        kind: Global master-checklist evidence kind.
        target: File, command, test, or external result that was observed.
        revision: Commit, graph identity, or immutable revision of that result.
    """

    kind: str
    target: str
    revision: str

    def __post_init__(self) -> None:
        """Reject evidence that the global manifest cannot represent."""

        if self.kind not in {"artifact", "command", "external", "test"}:
            raise PairBlockGateError(f"invalid evidence kind: {self.kind}")
        if not self.target.strip() or not self.revision.strip():
            raise PairBlockGateError("evidence target and revision must not be empty")


@dataclass(frozen=True, slots=True)
class LifecycleReceipt:
    """Persist one accepted PairBlock lifecycle event and its predecessor.

    Attributes:
        schema_version: Version of this receipt structure.
        pair_block_id: PairBlock advanced by the event.
        event: Profile event applied to the previous status.
        result: ``applied`` or ``rejected``.
        status_before: Checklist status read before the event.
        status_after: Status selected by the lifecycle policy.
        recorded_at: UTC time at which the transition began.
        repository_head: RICO commit checked out for the transition.
        checklist_before_sha256: Digest of the checklist read by the controller.
        checklist_written_sha256: Digest of the projected checklist, if valid.
        evidence: Observation that authorizes this event.
        previous_receipt: Receipt linked by the previous status row, if any.
    """

    schema_version: int
    pair_block_id: str
    event: str
    result: str
    status_before: str
    status_after: str
    recorded_at: str
    repository_head: str
    checklist_before_sha256: str
    checklist_written_sha256: str | None
    evidence: EvidenceRef
    previous_receipt: str | None


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


def _reject_nested_conda_run(command: str) -> None:
    """Reject a Conda-owned gate that would invoke another ``conda run``.

    A proposal command owns its declared environment. Starting this controller
    inside a different non-base Conda environment can cause a nested
    ``conda run`` to reuse the controller interpreter instead of the declared
    target. Refusing that launch preserves the proposal's runtime boundary.
    """

    active_environment = os.environ.get("CONDA_DEFAULT_ENV")
    if not active_environment or active_environment == "base":
        return
    tokens = shlex.split(command)
    invokes_conda_run = any(
        Path(executable).name == "conda" and operation == "run"
        for executable, operation in pairwise(tokens)
    )
    if invokes_conda_run:
        raise PairBlockGateError(
            "gate controller must run outside a non-base Conda environment "
            f"before executing a declared conda run; active={active_environment}"
        )


def _require_resolved_dependencies(
    row: PairBlockRow,
    rows: dict[str, PairBlockRow],
    profile: ChecklistProfile,
) -> None:
    """Require every declared predecessor to permit dependent work."""

    for dependency in row.dependencies:
        dependency_status = rows[dependency].status
        if dependency_status not in profile.lifecycle.resolved_dependency_states:
            raise PairBlockGateError(
                f"{row.pair_block_id} dependency {dependency} is not resolved: "
                f"{dependency_status}"
            )


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
    _require_resolved_dependencies(row, rows, profile)
    if row.status not in profile.lifecycle.proposal_gate_states:
        raise PairBlockGateError(f"proposal gate cannot run from status: {row.status}")

    proposal = adapter.load_proposal_contract(repository, checklist_path, row)
    _reject_nested_conda_run(proposal.command)
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
        ["/bin/zsh", "-c", proposal.command],
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
            repository,
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


def advance_pairblock(
    repository: Path,
    pair_block_id: str,
    event: str,
    evidence: EvidenceRef,
    *,
    now: datetime | None = None,
    validator_path: Path = DEFAULT_MASTER_CHECKLIST_VALIDATOR,
    adapter: MarkdownChecklistAdapter = MANTRA_PHASE0_ADAPTER,
) -> Path:
    """Apply one legal lifecycle event and render every derived status."""

    repository = repository.resolve()
    profile = adapter.profile
    checklist_path = repository / profile.checklist_path
    checklist_before = checklist_path.read_bytes()
    checklist_text = checklist_before.decode("utf-8")
    rows, _ = adapter.validate_traceability(
        repository,
        validator_path=validator_path,
    )
    try:
        row = rows[pair_block_id]
    except KeyError as error:
        raise PairBlockGateError(f"unknown PairBlock: {pair_block_id}") from error
    non_code_events = {
        profile.lifecycle.non_code_review_event,
        profile.lifecycle.non_code_complete_event,
    }
    if event in non_code_events:
        if adapter.has_proposed_code(row):
            raise PairBlockGateError(
                f"{pair_block_id} has runnable proposed code; run its gate"
            )
        if evidence.kind != "external":
            raise PairBlockGateError(
                f"{event} requires external review evidence"
            )
        if event == profile.lifecycle.non_code_review_event:
            _require_resolved_dependencies(row, rows, profile)
    try:
        status_after = profile.lifecycle.advance(row.status, event)
    except ValueError as error:
        raise PairBlockGateError(str(error)) from error

    recorded = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    stamp = recorded.strftime("%Y%m%dT%H%M%S.%fZ")
    receipt_path = (
        repository
        / "evidence"
        / "pairblock-lifecycle"
        / pair_block_id.lower()
        / f"{stamp}-{event}.json"
    )
    if receipt_path.exists():
        raise PairBlockGateError(f"receipt already exists: {receipt_path}")
    relative_receipt = Path(
        os.path.relpath(receipt_path, checklist_path.parent)
    ).as_posix()
    repository_head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    receipt = LifecycleReceipt(
        schema_version=1,
        pair_block_id=pair_block_id,
        event=event,
        result="applied",
        status_before=row.status,
        status_after=status_after,
        recorded_at=recorded.isoformat(),
        repository_head=repository_head,
        checklist_before_sha256=sha256_bytes(checklist_before),
        checklist_written_sha256=None,
        evidence=evidence,
        previous_receipt=adapter.current_receipt(row),
    )
    _atomic_write(
        receipt_path,
        (json.dumps(asdict(receipt), indent=2, sort_keys=True) + "\n").encode(),
    )

    try:
        checklist_after = adapter.render_transition(
            repository,
            checklist_text,
            row,
            receipt_path=relative_receipt,
            status=status_after,
        )
        projected_text = checklist_after.decode("utf-8")
        projected_rows = adapter.parse_pair_block_rows(projected_text)
        projected_manifest = adapter.compile_normalized_manifest(
            repository,
            projected_text,
            projected_rows,
        )
        validate_normalized_manifest(
            repository,
            projected_manifest,
            validator_path.resolve(),
        )
    except Exception:
        rejected = replace(receipt, result="rejected")
        _atomic_write(
            receipt_path,
            (json.dumps(asdict(rejected), indent=2, sort_keys=True) + "\n").encode(),
        )
        raise

    receipt = replace(
        receipt,
        checklist_written_sha256=sha256_bytes(checklist_after),
    )
    _atomic_write(
        receipt_path,
        (json.dumps(asdict(receipt), indent=2, sort_keys=True) + "\n").encode(),
    )
    _atomic_write(checklist_path, checklist_after)
    adapter.validate_traceability(
        repository,
        validator_path=validator_path,
    )
    return receipt_path


def main(argv: Sequence[str] | None = None) -> int:
    """Run a proposal gate or record one later lifecycle transition."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument(
        "--master-validator",
        type=Path,
        default=DEFAULT_MASTER_CHECKLIST_VALIDATOR,
    )
    commands = parser.add_subparsers(dest="operation", required=True)
    gate = commands.add_parser("gate")
    gate.add_argument("pair_block_id")
    advance = commands.add_parser("advance")
    advance.add_argument("pair_block_id")
    advance.add_argument(
        "event",
        choices=MANTRA_PHASE0_ADAPTER.profile.lifecycle.transition_events,
    )
    advance.add_argument("--evidence-kind", required=True)
    advance.add_argument("--evidence-target", required=True)
    advance.add_argument("--evidence-revision", required=True)
    arguments = parser.parse_args(argv)
    if arguments.operation == "gate":
        receipt_path = run_gate(
            arguments.repository,
            arguments.pair_block_id,
            validator_path=arguments.master_validator,
        )
    else:
        receipt_path = advance_pairblock(
            arguments.repository,
            arguments.pair_block_id,
            arguments.event,
            EvidenceRef(
                kind=arguments.evidence_kind,
                target=arguments.evidence_target,
                revision=arguments.evidence_revision,
            ),
            validator_path=arguments.master_validator,
        )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    print(receipt_path)
    return 0 if receipt["result"] in {"applied", "passed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
