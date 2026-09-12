"""Run one validated proposal gate, retain its receipt, and update its status."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .checklist_profile import (
    DEFAULT_MASTER_CHECKLIST_VALIDATOR,
    PairBlockGateError,
    compile_normalized_manifest,
    load_proposal_contract,
    parse_pair_block_rows,
    validate_normalized_manifest,
    validate_traceability,
)
from .execution_identity import (
    capture_execution_identity,
    compare_execution_identities,
    sha256_bytes,
)
from .profile import MANTRA_PHASE0_PROFILE, ChecklistProfile

_PASSED = re.compile(r"(?m)(\d+) passed(?:,| in )")


def _described(description: str):
    """Attach machine-readable meaning to one persisted dataclass field."""

    return field(metadata={"description": description})


@dataclass(frozen=True, slots=True)
class GateReceipt:
    """Persist one proposal-gate attempt and its controlled status outcome."""

    schema_version: int = _described("Version of the persisted receipt shape.")
    pair_block_id: str = _described("PairBlock whose declared proposal gate ran.")
    result: str = _described("Gate outcome: passed, failed, or invalidated.")
    status_before: str = _described("Authoritative lifecycle status before execution.")
    status_after: str = _described("Lifecycle status written or preserved by the runner.")
    started_at: str = _described("UTC timestamp immediately before command execution.")
    finished_at: str = _described("UTC timestamp immediately after command execution.")
    checklist_path: str = _described("Repository-relative authoritative checklist path.")
    checklist_written_sha256: str = _described(
        "Digest of the checklist bytes the runner preserved or wrote."
    )
    contract_path: str = _described("Repository-relative governing contract path.")
    command: str = _described("Exact contract-declared shell command that ran.")
    command_sha256: str = _described("Digest of the executed command text.")
    exit_code: int = _described("Process exit code returned by the gate command.")
    stdout: str = _described("Complete standard output from the gate command.")
    stderr: str = _described("Complete standard error from the gate command.")
    output_sha256: str = _described(
        "Digest of stdout, a NUL separator, and stderr."
    )
    master_validator_path: str = _described(
        "Absolute path of the inherited master-checklist validator."
    )
    identity_before: dict[str, object] = field(
        metadata={
            "description": "Git and file identities captured before execution."
        }
    )
    identity_after: dict[str, object] = field(
        metadata={
            "description": "Git and file identities captured after execution."
        }
    )
    identity_drift: dict[str, dict[str, object]] = field(
        metadata={
            "description": "Before and after values for changed identities."
        }
    )
    normalized_manifest: dict[str, object] = field(
        metadata={
            "description": "Validated schema-version-2 checklist manifest."
        }
    )
    normalized_manifest_sha256: str = _described(
        "Digest of the normalized manifest's canonical JSON form."
    )


def _split_row(line: str) -> list[str]:
    """Split one PairBlock table row for its controlled two-cell update."""

    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _replace_status_row(
    checklist_text: str,
    *,
    line_index: int,
    gate: str,
    status: str,
) -> str:
    """Return checklist text with one gate cell and one status cell replaced."""

    lines = checklist_text.splitlines()
    cells = _split_row(lines[line_index])
    cells[1] = gate
    cells[2] = status
    lines[line_index] = "| " + " | ".join(cells) + " |"
    suffix = "\n" if checklist_text.endswith("\n") else ""
    return "\n".join(lines) + suffix


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
    profile: ChecklistProfile = MANTRA_PHASE0_PROFILE,
) -> Path:
    """Execute one eligible proposal gate and persist its evidence and status."""

    repository = repository.resolve()
    if not profile.accepts_pair_block_id(pair_block_id):
        raise PairBlockGateError(f"invalid PairBlock ID: {pair_block_id}")

    checklist_path = repository / profile.checklist_path
    checklist_before = checklist_path.read_bytes()
    checklist_text = checklist_before.decode("utf-8")
    rows, manifest = validate_traceability(
        repository,
        validator_path=validator_path,
        profile=profile,
    )
    try:
        row = rows[pair_block_id]
    except KeyError as error:
        raise PairBlockGateError(f"unknown PairBlock: {pair_block_id}") from error
    if not row.proposed_code.startswith(profile.proposed_code_link_prefix):
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

    proposal = load_proposal_contract(repository, checklist_path, row, profile)
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
        relative_receipt = os.path.relpath(receipt_path, checklist_path.parent)
        gate_cell = (
            f"Passed: `{passed.group(1)}` tests "
            f"([receipt]({Path(relative_receipt).as_posix()}))"
        )
        checklist_after = _replace_status_row(
            checklist_text,
            line_index=row.line_index,
            gate=gate_cell,
            status=status_after,
        ).encode("utf-8")
        projected_text = checklist_after.decode("utf-8")
        projected_rows = parse_pair_block_rows(projected_text, profile)
        manifest_after = compile_normalized_manifest(
            repository,
            projected_text,
            projected_rows,
            profile,
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
        validate_traceability(
            repository,
            validator_path=resolved_validator,
            profile=profile,
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
        profile=MANTRA_PHASE0_PROFILE,
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    print(receipt_path)
    return 0 if receipt["result"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
