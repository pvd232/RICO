"""Execute PairBlock gates and maintain their evidence-backed state machines.

This module joins typed declarations or legacy Markdown records to commands,
receipts, rendered views, and the global checklist validator. It is the only
writer for PairBlock gate and lifecycle receipts. Project syntax remains in the
profile and legacy adapter; declaration parsing and Markdown presentation
remain in their dedicated modules.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from itertools import pairwise
from pathlib import Path

from .checklist_profile import (
    DEFAULT_MASTER_CHECKLIST_VALIDATOR,
    MANTRA_PHASE0_ADAPTER,
    EvidenceRecord,
    GateRecord,
    MarkdownChecklistAdapter,
    NormalizedManifest,
    PairBlockRow,
    validate_normalized_manifest,
)
from .declaration_manifest import (
    DeclarationChange,
    GateCommand,
    ProjectDeclarations,
    compare_declarations,
    declarations_from_payload,
    empty_declarations,
    load_declarations,
)
from .execution_identity import (
    capture_execution_identity,
    compare_execution_identities,
    sha256_bytes,
    sha256_file,
)
from .markdown_renderer import PairBlockView, render_markdown
from .profile import (
    EVIDENCE_KINDS,
    ChecklistProfile,
    EvidenceKind,
    PairBlockGateError,
    is_evidence_kind,
)
from .projection_transaction import (
    apply_projection,
    atomic_write,
    pending_projections,
    prepare_projection,
)
from .receipt_validation import (
    validate_native_gate_receipt,
    validate_native_lifecycle_receipt,
)

_PASSED = re.compile(r"(?m)(\d+) passed(?:,| in )")
_REVISION_RECEIPT_FIELDS = frozenset(
    {
        "schema_version",
        "event",
        "result",
        "recorded_at",
        "before_sha256",
        "after_sha256",
        "records",
        "affected_pair_blocks",
        "approval",
        "superseded_receipt_heads",
        "previous_receipt",
        "accepted_manifest",
        "reviewed_plan",
        "reviewed_plan_sha256",
    }
)
_REVISION_PLAN_FIELDS = frozenset(
    {
        "schema_version",
        "created_at",
        "before_sha256",
        "after_sha256",
        "records",
        "affected_pair_blocks",
        "previous_receipt",
        "candidate_manifest",
    }
)


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
        declaration_sha256: Accepted declaration manifest digest for a native block.
        pair_block_fingerprint: Native block contract fingerprint.
        previous_receipt: Previous native receipt in the block's chain.
        structured_gate: Repository, working directory, argument vector, and
            environment executed for a native block.
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
    normalized_manifest: NormalizedManifest
    normalized_manifest_sha256: str
    declaration_sha256: str | None = None
    pair_block_fingerprint: str | None = None
    previous_receipt: str | None = None
    structured_gate: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    """Identify one artifact, command, test, or external lifecycle observation.

    Attributes:
        kind: Global master-checklist evidence kind.
        target: File, command, test, or external result that was observed.
        revision: Commit, graph identity, or immutable revision of that result.
    """

    kind: EvidenceKind
    target: str
    revision: str

    def __post_init__(self) -> None:
        """Require evidence that the global manifest can represent."""

        if not is_evidence_kind(self.kind):
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
        certification_reason: Explanation of the historical-chain defect that
            authorizes certification for one named legacy block.
        declaration_sha256: Accepted declaration manifest digest for a native block.
        pair_block_fingerprint: Native block contract fingerprint.
        declaration_repository_head: Commit that owns the declaration state.
        implementation_repository_head: Commit that owns the block's source.
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
    certification_reason: str | None = None
    declaration_sha256: str | None = None
    pair_block_fingerprint: str | None = None
    declaration_repository_head: str | None = None
    implementation_repository_head: str | None = None


def _lifecycle_receipt_bytes(receipt: LifecycleReceipt) -> bytes:
    """Serialize a lifecycle receipt while preserving the version-1 field set."""

    payload = asdict(receipt)
    if receipt.certification_reason is None:
        payload.pop("certification_reason")
    if receipt.declaration_sha256 is None:
        payload.pop("declaration_sha256")
    if receipt.pair_block_fingerprint is None:
        payload.pop("pair_block_fingerprint")
    if receipt.declaration_repository_head is None:
        payload.pop("declaration_repository_head")
    if receipt.implementation_repository_head is None:
        payload.pop("implementation_repository_head")
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()


def _gate_receipt_bytes(receipt: GateReceipt) -> bytes:
    """Serialize a gate receipt without native-only null fields."""

    payload = asdict(receipt)
    for field in (
        "declaration_sha256",
        "pair_block_fingerprint",
        "previous_receipt",
        "structured_gate",
    ):
        if payload[field] is None:
            payload.pop(field)
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()


def _reject_nested_conda_run(command: str) -> None:
    """Reject a Conda-owned gate that would invoke another ``conda run``.

    A proposal command owns its declared environment. Starting this controller
    inside a different non-base Conda environment can cause a nested
    ``conda run`` to reuse the controller interpreter in place of the declared
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


def _require_certification_artifact(
    repository: Path,
    evidence: EvidenceRef,
    profile: ChecklistProfile,
) -> None:
    """Require the profile's terminal artifact and its exact byte identity."""

    target = Path(evidence.target)
    if target != profile.require_legacy_certification_artifact():
        raise PairBlockGateError(
            "legacy certification must use the configured terminal artifact"
        )
    if target.is_absolute() or ".." in target.parts:
        raise PairBlockGateError(
            "legacy certification artifact must be repository-relative"
        )
    resolved = (repository / target).resolve()
    if not resolved.is_relative_to(repository) or not resolved.is_file():
        raise PairBlockGateError("legacy certification artifact is missing")
    if sha256_file(resolved) != evidence.revision:
        raise PairBlockGateError("legacy certification artifact digest differs")


def _require_native_lifecycle_evidence(
    repository: Path,
    event: str,
    evidence: EvidenceRef,
    profile: ChecklistProfile,
) -> None:
    """Verify that one lifecycle observation satisfies its event policy.

    External approval remains a reference to the user-review system. Artifact
    evidence names a repository-contained file and uses the file's SHA-256 as
    its revision. This makes acceptance and registration depend on retained
    bytes rather than an arbitrary label.
    """

    try:
        required_kind = profile.lifecycle.required_evidence_kind(event)
    except ValueError as error:
        raise PairBlockGateError(str(error)) from error
    if evidence.kind != required_kind:
        raise PairBlockGateError(
            f"{event} requires {required_kind} evidence; received {evidence.kind}"
        )
    if required_kind != "artifact":
        return
    target = Path(evidence.target)
    if target.is_absolute() or ".." in target.parts:
        raise PairBlockGateError("lifecycle artifact must be repository-relative")
    resolved = (repository / target).resolve()
    if not resolved.is_relative_to(repository) or not resolved.is_file():
        raise PairBlockGateError("lifecycle artifact is missing")
    if sha256_file(resolved) != evidence.revision:
        raise PairBlockGateError("lifecycle artifact digest differs")


@dataclass(frozen=True, slots=True)
class AcceptedDeclarations:
    """Identify the declaration snapshot approved for execution.

    Attributes:
        declarations: Exact accepted typed records.
        receipt_path: Repository-relative revision-chain head.
        affected_pair_blocks: Blocks reopened by that accepted revision.
    """

    declarations: ProjectDeclarations
    receipt_path: str | None
    affected_pair_blocks: tuple[str, ...] = ()


def _current_declarations(
    repository: Path, profile: ChecklistProfile
) -> ProjectDeclarations:
    """Load the working declaration manifest configured by the profile."""

    if profile.declaration_path is None:
        return empty_declarations()
    return load_declarations(repository / profile.declaration_path, profile)


def _accepted_declarations(
    repository: Path, profile: ChecklistProfile
) -> AcceptedDeclarations:
    """Load the unique head of the accepted declaration revision chain."""

    directory = repository / "evidence" / "declaration-revisions"
    if not directory.is_dir():
        return AcceptedDeclarations(empty_declarations(), None)
    receipts = _load_applied_revision_receipts(repository, directory)
    if not receipts:
        return AcceptedDeclarations(empty_declarations(), None)
    head = _unique_revision_head(repository, profile, receipts)
    return _accepted_snapshot(repository, profile, head, receipts[head])


def _load_applied_revision_receipts(
    repository: Path, directory: Path
) -> dict[str, dict[str, object]]:
    """Load structurally valid applied revision receipts by relative path."""

    receipts: dict[str, dict[str, object]] = {}
    for path in sorted(directory.glob("*.json")):
        try:
            receipt = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise PairBlockGateError(
                f"invalid declaration revision receipt: {path}"
            ) from error
        if not isinstance(receipt, dict) or receipt.get("result") != "applied":
            continue
        _validate_revision_receipt_envelope(repository, path, receipt)
        relative = path.relative_to(repository).as_posix()
        receipts[relative] = receipt
    return receipts


def _validate_revision_receipt_envelope(
    repository: Path,
    path: Path,
    receipt: dict[str, object],
) -> None:
    """Validate stored fields before a revision receipt enters the chain.

    The check enforces the receipt schema, a UTC timestamp, a nonempty external
    approval reference, and repository-contained superseded-receipt paths with
    matching PairBlock owners. The approval reference is a trust anchor; this
    repository validates its shape, while the named external review system
    authenticates the review event.
    """

    if set(receipt) != _REVISION_RECEIPT_FIELDS:
        raise PairBlockGateError(f"declaration revision receipt fields differ: {path}")
    if (
        receipt.get("schema_version") != 1
        or receipt.get("event") != "revise"
        or receipt.get("result") != "applied"
    ):
        raise PairBlockGateError(
            f"declaration revision receipt envelope differs: {path}"
        )
    recorded_at = receipt.get("recorded_at")
    if not isinstance(recorded_at, str):
        raise PairBlockGateError(f"declaration revision receipt lacks UTC time: {path}")
    try:
        timestamp = datetime.fromisoformat(recorded_at)
    except ValueError as error:
        raise PairBlockGateError(
            f"declaration revision receipt has invalid UTC time: {path}"
        ) from error
    if timestamp.tzinfo is None or timestamp.utcoffset() != timezone.utc.utcoffset(
        None
    ):
        raise PairBlockGateError(
            f"declaration revision receipt time is not UTC: {path}"
        )

    approval = receipt.get("approval")
    if not isinstance(approval, dict) or set(approval) != {
        "kind",
        "target",
        "revision",
    }:
        raise PairBlockGateError(f"declaration revision approval is malformed: {path}")
    if any(not isinstance(approval[field], str) for field in approval):
        raise PairBlockGateError(f"declaration revision approval is malformed: {path}")
    evidence = EvidenceRef(
        kind=approval["kind"],
        target=approval["target"],
        revision=approval["revision"],
    )
    if evidence.kind != "external":
        raise PairBlockGateError(
            f"declaration revision approval is not external: {path}"
        )

    reviewed_plan = receipt.get("reviewed_plan")
    reviewed_plan_sha256 = receipt.get("reviewed_plan_sha256")
    if not isinstance(reviewed_plan, str) or not isinstance(reviewed_plan_sha256, str):
        raise PairBlockGateError(f"declaration revision plan is malformed: {path}")
    plan_path = (repository / reviewed_plan).resolve()
    if (
        Path(reviewed_plan).is_absolute()
        or ".." in Path(reviewed_plan).parts
        or not plan_path.is_relative_to(repository)
        or not plan_path.is_file()
        or sha256_file(plan_path) != reviewed_plan_sha256
    ):
        raise PairBlockGateError(f"declaration revision plan differs: {path}")

    affected = receipt.get("affected_pair_blocks")
    superseded = receipt.get("superseded_receipt_heads")
    if not isinstance(affected, list) or any(
        not isinstance(item, str) for item in affected
    ):
        raise PairBlockGateError(f"declaration revision affected blocks differ: {path}")
    if not isinstance(superseded, dict) or any(
        not isinstance(block_id, str) or not isinstance(target, str)
        for block_id, target in superseded.items()
    ):
        raise PairBlockGateError(
            f"declaration revision superseded heads differ: {path}"
        )
    if not set(superseded) <= set(affected):
        raise PairBlockGateError(
            f"declaration revision supersedes unaffected blocks: {path}"
        )
    for block_id, target in superseded.items():
        target_path = (repository / target).resolve()
        if not target_path.is_relative_to(repository) or not target_path.is_file():
            raise PairBlockGateError(
                f"declaration revision superseded receipt is missing: {target}"
            )
        try:
            prior_receipt = json.loads(target_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise PairBlockGateError(
                f"declaration revision superseded receipt is invalid: {target}"
            ) from error
        if (
            not isinstance(prior_receipt, dict)
            or prior_receipt.get("pair_block_id") != block_id
        ):
            raise PairBlockGateError(
                f"declaration revision superseded receipt owner differs: {target}"
            )


def _unique_revision_head(
    repository: Path,
    profile: ChecklistProfile,
    receipts: dict[str, dict[str, object]],
) -> str:
    """Validate every applied revision from the unique head to the empty root.

    Each receipt must name its predecessor, join the predecessor's accepted
    digest, and reproduce its claimed change from the adjacent accepted
    manifests. Forks, cycles, missing predecessors, and disconnected receipts
    make the chain unusable.
    """

    referenced: set[str] = set()
    for receipt in receipts.values():
        previous = receipt.get("previous_receipt")
        if previous is not None and not isinstance(previous, str):
            raise PairBlockGateError("declaration revision predecessor must be a path")
        if isinstance(previous, str):
            referenced.add(previous)
    heads = set(receipts) - referenced
    if len(heads) != 1:
        raise PairBlockGateError("declaration revision receipts need one chain head")
    head = heads.pop()
    visited: set[str] = set()
    current = head
    while current is not None:
        if current in visited or current not in receipts:
            raise PairBlockGateError("declaration revision receipt chain is broken")
        visited.add(current)
        receipt = receipts[current]
        accepted = _accepted_snapshot(repository, profile, current, receipt)
        raw_previous = receipt.get("previous_receipt")
        if isinstance(raw_previous, str):
            if raw_previous not in receipts:
                raise PairBlockGateError("declaration revision receipt chain is broken")
            if receipt.get("before_sha256") != receipts[raw_previous].get(
                "after_sha256"
            ):
                raise PairBlockGateError("declaration revision digests do not join")
            previous = _accepted_snapshot(
                repository,
                profile,
                raw_previous,
                receipts[raw_previous],
            )
        else:
            previous = AcceptedDeclarations(empty_declarations(), None)
        _validate_revision_change(
            repository=repository,
            profile=profile,
            path=current,
            receipt=receipt,
            before=previous,
            after=accepted,
        )
        current = raw_previous if isinstance(raw_previous, str) else None
    if len(visited) != len(receipts):
        raise PairBlockGateError("declaration revision receipts form several chains")
    return head


def _validate_revision_change(
    *,
    repository: Path,
    profile: ChecklistProfile,
    path: str,
    receipt: dict[str, object],
    before: AcceptedDeclarations,
    after: AcceptedDeclarations,
) -> None:
    """Recompute every revision claim derived from two accepted manifests.

    The controller compares the stored manifest digests, record-level changes,
    reverse-dependent PairBlock closure, and superseded lifecycle heads with
    values derived from ``before`` and ``after``. A receipt may therefore carry
    these values as evidence, but cannot define them authoritatively.
    """

    change = compare_declarations(before.declarations, after.declarations)
    expected_records = [asdict(record) for record in change.records]
    if receipt.get("before_sha256") != change.before_sha256:
        raise PairBlockGateError(f"declaration revision before digest differs: {path}")
    if receipt.get("after_sha256") != change.after_sha256:
        raise PairBlockGateError(f"declaration revision after digest differs: {path}")
    if receipt.get("records") != expected_records:
        raise PairBlockGateError(f"declaration revision record changes differ: {path}")
    if receipt.get("affected_pair_blocks") != list(change.affected_pair_blocks):
        raise PairBlockGateError(f"declaration revision affected blocks differ: {path}")
    previous_blocks = before.declarations.pair_blocks_by_id
    expected_superseded: dict[str, str] = {}
    for pair_block_id in change.affected_pair_blocks:
        if pair_block_id not in previous_blocks:
            continue
        view = _native_view(
            repository,
            before.declarations,
            pair_block_id,
            profile,
        )
        if view.receipt is not None:
            expected_superseded[pair_block_id] = view.receipt
    if receipt.get("superseded_receipt_heads") != expected_superseded:
        raise PairBlockGateError(
            f"declaration revision superseded receipt heads differ: {path}"
        )
    reviewed_plan = receipt["reviewed_plan"]
    assert isinstance(reviewed_plan, str)
    plan = json.loads((repository / reviewed_plan).read_text(encoding="utf-8"))
    if (
        plan.get("before_sha256") != change.before_sha256
        or plan.get("after_sha256") != change.after_sha256
        or plan.get("records") != expected_records
        or plan.get("affected_pair_blocks") != list(change.affected_pair_blocks)
        or plan.get("candidate_manifest")
        != json.loads(
            json.dumps(after.declarations.canonical_payload(), sort_keys=True)
        )
    ):
        raise PairBlockGateError(f"declaration revision reviewed plan differs: {path}")


def _accepted_snapshot(
    repository: Path,
    profile: ChecklistProfile,
    head: str,
    receipt: dict[str, object],
) -> AcceptedDeclarations:
    """Parse one stored manifest and bind it to its receipt's digest and root."""

    previous = receipt.get("previous_receipt")
    snapshot = receipt.get("accepted_manifest")
    if not isinstance(snapshot, dict):
        raise PairBlockGateError(
            "declaration revision receipt lacks its accepted manifest"
        )
    declarations = declarations_from_payload(snapshot, profile, repository)
    if receipt.get("after_sha256") != declarations.sha256:
        raise PairBlockGateError("accepted declaration snapshot digest differs")
    if previous is None and receipt.get("before_sha256") != empty_declarations().sha256:
        raise PairBlockGateError("first declaration revision has the wrong predecessor")
    affected = receipt["affected_pair_blocks"]
    assert isinstance(affected, list)
    return AcceptedDeclarations(declarations, head, tuple(affected))


def _require_accepted_declarations(
    repository: Path, profile: ChecklistProfile
) -> ProjectDeclarations:
    """Reject execution while the working manifest differs from its approval."""

    current = _current_declarations(repository, profile)
    accepted = _accepted_declarations(repository, profile)
    if current.sha256 != accepted.declarations.sha256:
        raise PairBlockGateError(
            "working declarations differ from the accepted revision; record revise first"
        )
    return current


def _native_receipt_records(
    repository: Path,
    pair_block_id: str,
    declarations: ProjectDeclarations,
    profile: ChecklistProfile,
) -> dict[str, dict[str, object]]:
    """Load successful receipts bound to one current PairBlock fingerprint."""

    records: dict[str, dict[str, object]] = {}
    fingerprint = declarations.pair_block_fingerprint(pair_block_id)
    block = declarations.pair_blocks_by_id[pair_block_id]
    accepted_declaration_sha256s = frozenset(
        digest
        for receipt in _load_applied_revision_receipts(
            repository, repository / "evidence" / "declaration-revisions"
        ).values()
        if isinstance(digest := receipt.get("after_sha256"), str)
    )
    for category in ("pairblock-gates", "pairblock-lifecycle"):
        directory = repository / "evidence" / category / pair_block_id.lower()
        for path in sorted(directory.glob("*.json")) if directory.is_dir() else ():
            try:
                receipt = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                raise PairBlockGateError(f"invalid native receipt: {path}") from error
            if not isinstance(receipt, dict):
                raise PairBlockGateError(f"native receipt is not an object: {path}")
            expected_results = {"passed", "applied"}
            if (
                receipt.get("result") in expected_results
                and receipt.get("pair_block_id") == pair_block_id
                and receipt.get("pair_block_fingerprint") == fingerprint
            ):
                if category == "pairblock-gates":
                    validate_native_gate_receipt(
                        repository,
                        path,
                        receipt,
                        block,
                        declarations,
                        profile,
                        accepted_declaration_sha256s,
                    )
                else:
                    validate_native_lifecycle_receipt(
                        repository,
                        path,
                        receipt,
                        block,
                        declarations,
                        profile,
                        accepted_declaration_sha256s,
                    )
                records[path.relative_to(repository).as_posix()] = receipt
    return records


def _native_view(
    repository: Path,
    declarations: ProjectDeclarations,
    pair_block_id: str,
    profile: ChecklistProfile,
) -> PairBlockView:
    """Derive one native lifecycle state from its unique receipt-chain head."""

    records = _native_receipt_records(repository, pair_block_id, declarations, profile)
    if not records:
        return PairBlockView(profile.lifecycle.drafting_status)
    head = _unique_native_receipt_head(records, pair_block_id, profile)
    status = records[head].get("status_after")
    if not isinstance(status, str):
        raise PairBlockGateError(f"{pair_block_id} receipt lacks status_after")
    profile.lifecycle.normalize(status)
    return PairBlockView(status, head)


def _unique_native_receipt_head(
    records: dict[str, dict[str, object]],
    pair_block_id: str,
    profile: ChecklistProfile,
) -> str:
    """Validate one native receipt chain and return its unique head."""

    referenced = {
        previous
        for receipt in records.values()
        if isinstance((previous := receipt.get("previous_receipt")), str)
    }
    missing = referenced - records.keys()
    if missing:
        raise PairBlockGateError(
            f"{pair_block_id} receipt chain references missing receipts: {sorted(missing)}"
        )
    heads = set(records) - referenced
    if len(heads) != 1:
        raise PairBlockGateError(f"{pair_block_id} receipts need one chain head")
    head = heads.pop()
    visited: set[str] = set()
    current: str | None = head
    while current is not None:
        if current in visited:
            raise PairBlockGateError(f"{pair_block_id} receipt chain contains a cycle")
        visited.add(current)
        receipt = records[current]
        previous = receipt.get("previous_receipt")
        if isinstance(previous, str):
            prior = records[previous]
            if receipt.get("status_before") != prior.get("status_after"):
                raise PairBlockGateError(
                    f"{pair_block_id} receipt statuses do not join"
                )
            current = previous
        else:
            if receipt.get("status_before") != profile.lifecycle.drafting_status:
                raise PairBlockGateError(
                    f"{pair_block_id} receipt chain has no Drafting root"
                )
            current = None
    if len(visited) != len(records):
        raise PairBlockGateError(f"{pair_block_id} receipts form several chains")
    return head


def _native_views(
    repository: Path,
    declarations: ProjectDeclarations,
    profile: ChecklistProfile,
    dependency_statuses: Mapping[str, str] | None = None,
) -> dict[str, PairBlockView]:
    """Derive every manifest-native PairBlock view from receipts."""

    views = {
        pair_block.id: _native_view(
            repository,
            declarations,
            pair_block.id,
            profile,
        )
        for pair_block in declarations.pair_blocks
    }
    return _apply_waiting_states(
        declarations,
        views,
        profile,
        dependency_statuses,
    )


def _apply_waiting_states(
    declarations: ProjectDeclarations,
    views: dict[str, PairBlockView],
    profile: ChecklistProfile,
    dependency_statuses: Mapping[str, str] | None = None,
) -> dict[str, PairBlockView]:
    """Derive dependency-wait states for every receipt-free block."""

    result = dict(views)
    statuses = dict(dependency_statuses or {})
    statuses.update({key: view.status for key, view in result.items()})
    for pair_block in declarations.pair_blocks:
        if result[pair_block.id].receipt is not None:
            continue
        result[pair_block.id] = PairBlockView(profile.lifecycle.drafting_status)
        waiting_for = tuple(
            dependency
            for dependency in pair_block.depends_on
            if dependency in statuses
            and statuses[dependency] not in profile.lifecycle.resolved_dependency_states
        )
        if waiting_for:
            result[pair_block.id] = PairBlockView(
                f"{profile.lifecycle.waiting_prefix}{', '.join(waiting_for)}"
            )
    return result


def _validate_native_dependencies(
    declarations: ProjectDeclarations,
    legacy_rows: dict[str, PairBlockRow],
    legacy_requirement_ids: set[str],
) -> None:
    """Require unique ownership and resolvable cross-origin dependencies."""

    native_ids = set(declarations.pair_blocks_by_id)
    duplicate = native_ids & legacy_rows.keys()
    if duplicate:
        raise PairBlockGateError(
            f"PairBlock IDs have legacy and typed owners: {sorted(duplicate)}"
        )
    known_blocks = native_ids | legacy_rows.keys()
    missing_blocks = {
        dependency
        for block in declarations.pair_blocks
        for dependency in block.depends_on
        if dependency not in known_blocks
    }
    if missing_blocks:
        raise PairBlockGateError(
            f"manifest PairBlocks reference unknown dependencies: {sorted(missing_blocks)}"
        )
    native_requirement_ids = set(declarations.requirements_by_id)
    missing_requirements = {
        dependency
        for requirement in declarations.requirements
        for dependency in requirement.depends_on
        if dependency not in native_requirement_ids
        and dependency not in legacy_requirement_ids
    }
    if missing_requirements:
        raise PairBlockGateError(
            "manifest requirements reference unknown dependencies: "
            f"{sorted(missing_requirements)}"
        )


def _completion_evidence(
    repository: Path,
    view: PairBlockView,
    pending_receipts: Mapping[str, dict[str, object]] | None = None,
) -> list[EvidenceRecord]:
    """Return final lifecycle evidence for a completed native block."""

    if view.receipt is None:
        return []
    receipt = (pending_receipts or {}).get(view.receipt)
    if receipt is None:
        receipt = json.loads((repository / view.receipt).read_text(encoding="utf-8"))
    evidence = receipt.get("evidence")
    if not isinstance(evidence, dict):
        return []
    if set(evidence) != {"kind", "target", "revision"}:
        raise PairBlockGateError("native completion evidence has an invalid shape")
    kind = evidence["kind"]
    if not is_evidence_kind(kind):
        raise PairBlockGateError("native completion evidence has an invalid kind")
    return [
        EvidenceRecord(
            kind=kind,
            target=str(evidence["target"]),
            revision=str(evidence["revision"]),
        )
    ]


def _aggregate_state(states: Sequence[str]) -> str:
    """Return one global state for a collection of normalized states."""

    if states and all(state == "complete" for state in states):
        return "complete"
    if states and all(state == "planned" for state in states):
        return "planned"
    return "in_progress"


def _validate_hybrid_traceability(
    repository: Path,
    declarations: ProjectDeclarations,
    views: dict[str, PairBlockView],
    validator_path: Path,
    adapter: MarkdownChecklistAdapter,
    pending_receipts: Mapping[str, dict[str, object]] | None = None,
) -> tuple[dict[str, PairBlockRow], NormalizedManifest]:
    """Merge typed records with the preserved legacy normalized manifest."""

    profile = adapter.profile
    legacy_rows, manifest = adapter.validate_traceability(
        repository,
        validator_path=validator_path,
    )
    _validate_native_dependencies(
        declarations,
        legacy_rows,
        {str(record["requirement_id"]) for record in manifest["requirements"]},
    )
    render_markdown(
        repository,
        declarations,
        views,
        profile,
        check=True,
    )
    requirements = list(manifest["requirements"])
    pair_blocks = list(manifest["pair_blocks"])
    for block in declarations.pair_blocks:
        view = views[block.id]
        state = profile.lifecycle.normalize(view.status)
        pair_blocks.append(
            {
                "pair_block_id": block.id,
                "contract_id": profile.contract_id,
                "section": block.section,
                "requirement_ids": list(block.requirement_ids),
                "state": state,
                "gate": {"kind": "test", "target": shlex.join(block.gate.argv)},
                "completion_evidence": (
                    _completion_evidence(repository, view, pending_receipts)
                    if state == "complete"
                    else []
                ),
            }
        )
    for requirement in declarations.requirements:
        owners = [
            next(
                record
                for record in pair_blocks
                if record["pair_block_id"] == pair_block_id
            )
            for pair_block_id in requirement.pair_block_ids
        ]
        state = _aggregate_state([str(owner["state"]) for owner in owners])
        evidence = [item for owner in owners for item in owner["completion_evidence"]]
        requirements.append(
            {
                "requirement_id": requirement.id,
                "contract_id": profile.contract_id,
                "phase": requirement.phase,
                "order": requirement.order,
                "depends_on": list(requirement.depends_on),
                "state": state,
                "gate": GateRecord(
                    kind=requirement.gate.kind,
                    target=requirement.gate.target,
                ),
                "completion_evidence": evidence if state == "complete" else [],
            }
        )
    manifest["requirements"] = requirements
    manifest["pair_blocks"] = pair_blocks
    contract = manifest["contracts"][0]
    contract["requirement_ids"] = [
        *contract["requirement_ids"],
        *(record.id for record in declarations.requirements),
    ]
    contract["sha256"] = sha256_file(repository / profile.contract_path)
    contract["state"] = _aggregate_state(
        [str(record["state"]) for record in requirements + pair_blocks]
    )
    validate_normalized_manifest(repository, manifest, validator_path.resolve())
    return legacy_rows, manifest


def _write_rendered_documents(
    repository: Path,
    contract: bytes,
    checklist: bytes,
    profile: ChecklistProfile,
) -> None:
    """Atomically replace both human views from one rendered projection."""

    atomic_write(repository / profile.contract_path, contract)
    atomic_write(repository / profile.checklist_path, checklist)


def _commit_native_projection(
    repository: Path,
    transaction_id: str,
    *,
    receipt_path: Path,
    receipt: bytes,
    rendered_contract: bytes,
    rendered_checklist: bytes,
    profile: ChecklistProfile,
    validate_documents: Callable[[], object],
) -> Path:
    """Publish one receipt after its rendered documents pass validation."""

    journal = prepare_projection(
        repository,
        transaction_id,
        receipt_path=receipt_path,
        receipt=receipt,
        documents={
            repository / profile.contract_path: rendered_contract,
            repository / profile.checklist_path: rendered_checklist,
        },
    )
    return apply_projection(
        repository,
        journal,
        validate_documents=validate_documents,
        validate_committed=validate_documents,
    )


def _recover_native_projections(
    repository: Path,
    validator_path: Path,
    adapter: MarkdownChecklistAdapter,
) -> None:
    """Finish each prepared transition before reading authoritative state."""

    repository = repository.resolve()

    def validate_committed() -> None:
        """Validate the recovered receipt against both regenerated views."""

        declarations = _require_accepted_declarations(repository, adapter.profile)
        legacy_rows, _ = adapter.validate_traceability(
            repository,
            validator_path=validator_path,
        )
        views = _native_views(
            repository,
            declarations,
            adapter.profile,
            {key: row.status for key, row in legacy_rows.items()},
        )
        _validate_hybrid_traceability(
            repository, declarations, views, validator_path, adapter
        )

    for journal in pending_projections(repository):
        apply_projection(
            repository,
            journal,
            validate_documents=lambda: None,
            validate_committed=validate_committed,
        )


def _native_source_paths(
    repository: Path,
    declarations: ProjectDeclarations,
    pair_block_id: str,
    profile: ChecklistProfile,
) -> tuple[Path, ...]:
    """Resolve the declaration and implementation files bound by one gate."""

    block = declarations.pair_blocks_by_id[pair_block_id]
    owner = (repository / dict(profile.repository_roots)[block.repository]).resolve()
    declaration_path = repository / profile.require_declaration_path()
    return (
        declaration_path,
        *(owner / path for path in (*block.source_paths, *block.test_paths)),
    )


def _run_native_gate(
    repository: Path,
    pair_block_id: str,
    *,
    now: datetime | None,
    validator_path: Path,
    adapter: MarkdownChecklistAdapter,
) -> Path:
    """Execute one accepted manifest-native gate and render its new state."""

    profile = adapter.profile
    declarations = _require_accepted_declarations(repository, profile)
    legacy_rows, _ = adapter.validate_traceability(
        repository,
        validator_path=validator_path,
    )
    legacy_statuses = {key: row.status for key, row in legacy_rows.items()}
    views = _native_views(repository, declarations, profile, legacy_statuses)
    legacy_rows, manifest = _validate_hybrid_traceability(
        repository, declarations, views, validator_path, adapter
    )
    try:
        block = declarations.pair_blocks_by_id[pair_block_id]
    except KeyError as error:
        raise PairBlockGateError(f"unknown PairBlock: {pair_block_id}") from error
    view = views[pair_block_id]
    if view.status not in profile.lifecycle.proposal_gate_states:
        raise PairBlockGateError(f"proposal gate cannot run from status: {view.status}")
    all_statuses = {key: row.status for key, row in legacy_rows.items()}
    all_statuses.update({key: item.status for key, item in views.items()})
    for dependency in block.depends_on:
        if all_statuses[dependency] not in profile.lifecycle.resolved_dependency_states:
            raise PairBlockGateError(
                f"{pair_block_id} dependency {dependency} is not resolved: "
                f"{all_statuses[dependency]}"
            )

    owner = (repository / dict(profile.repository_roots)[block.repository]).resolve()
    working_directory = (owner / block.gate.working_directory).resolve()
    source_paths = _native_source_paths(
        repository, declarations, pair_block_id, profile
    )
    validator = validator_path.resolve()
    identity_before = capture_execution_identity(
        repository,
        checklist_path=repository / profile.checklist_path,
        contract_path=repository / profile.contract_path,
        source_paths=source_paths,
        validator_path=validator,
        implementation_repository=owner,
    )
    started = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    environment = os.environ.copy()
    environment.update(dict(block.gate.environment))
    completed = subprocess.run(
        block.gate.argv,
        cwd=working_directory,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    finished = datetime.now(timezone.utc) if now is None else started
    identity_after = capture_execution_identity(
        repository,
        checklist_path=repository / profile.checklist_path,
        contract_path=repository / profile.contract_path,
        source_paths=source_paths,
        validator_path=validator,
        implementation_repository=owner,
    )
    drift = compare_execution_identities(identity_before, identity_after)
    result = "passed" if completed.returncode == 0 and not drift else "failed"
    if completed.returncode == 0 and drift:
        result = "invalidated"
    status_after = (
        profile.lifecycle.review_status if result == "passed" else view.status
    )
    stamp = started.strftime("%Y%m%dT%H%M%S.%fZ")
    receipt_path = (
        repository
        / "evidence"
        / "pairblock-gates"
        / pair_block_id.lower()
        / f"{stamp}.json"
    )
    relative_receipt = receipt_path.relative_to(repository).as_posix()
    if receipt_path.exists():
        raise PairBlockGateError(f"receipt already exists: {receipt_path}")
    combined_output = completed.stdout.encode() + b"\0" + completed.stderr.encode()
    receipt = GateReceipt(
        schema_version=3,
        pair_block_id=pair_block_id,
        result=result,
        status_before=view.status,
        status_after=status_after,
        started_at=started.isoformat(),
        finished_at=finished.isoformat(),
        checklist_path=profile.checklist_path.as_posix(),
        checklist_written_sha256=sha256_file(repository / profile.checklist_path),
        contract_path=profile.contract_path.as_posix(),
        command=shlex.join(block.gate.argv),
        command_sha256=sha256_bytes(_canonical_gate_bytes(block.gate)),
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        output_sha256=sha256_bytes(combined_output),
        master_validator_path=str(validator),
        identity_before=asdict(identity_before),
        identity_after=asdict(identity_after),
        identity_drift=drift,
        normalized_manifest=manifest,
        normalized_manifest_sha256=sha256_bytes(
            (json.dumps(manifest, sort_keys=True) + "\n").encode()
        ),
        declaration_sha256=declarations.sha256,
        pair_block_fingerprint=declarations.pair_block_fingerprint(pair_block_id),
        previous_receipt=view.receipt,
        structured_gate={
            "repository": block.gate.repository,
            "working_directory": block.gate.working_directory,
            "argv": list(block.gate.argv),
            "environment": dict(block.gate.environment),
        },
    )
    if result != "passed":
        atomic_write(receipt_path, _gate_receipt_bytes(receipt))
        return receipt_path

    pass_count = _PASSED.search(completed.stdout + completed.stderr)
    if pass_count is None:
        raise PairBlockGateError("passing gate output lacks a pytest pass count")
    projected_views = dict(views)
    projected_views[pair_block_id] = PairBlockView(status_after, relative_receipt)
    projected_views = _apply_waiting_states(
        declarations,
        projected_views,
        profile,
        legacy_statuses,
    )
    rendered = render_markdown(repository, declarations, projected_views, profile)
    receipt = replace(
        receipt,
        checklist_written_sha256=sha256_bytes(rendered.checklist),
        normalized_manifest_sha256=sha256_bytes(
            (json.dumps(manifest, sort_keys=True) + "\n").encode()
        ),
    )
    return _commit_native_projection(
        repository,
        f"{stamp}-{pair_block_id.lower()}-gate",
        receipt_path=receipt_path,
        receipt=_gate_receipt_bytes(receipt),
        rendered_contract=rendered.contract,
        rendered_checklist=rendered.checklist,
        profile=profile,
        validate_documents=lambda: _validate_hybrid_traceability(
            repository, declarations, projected_views, validator, adapter
        ),
    )


def _canonical_gate_bytes(gate: GateCommand) -> bytes:
    """Serialize one structured gate for receipt identity."""

    return json.dumps(asdict(gate), sort_keys=True, separators=(",", ":")).encode()


def _advance_native_pairblock(
    repository: Path,
    pair_block_id: str,
    event: str,
    evidence: EvidenceRef,
    *,
    now: datetime | None,
    validator_path: Path,
    adapter: MarkdownChecklistAdapter,
) -> Path:
    """Record one native lifecycle transition and regenerate both views."""

    profile = adapter.profile
    declarations = _require_accepted_declarations(repository, profile)
    legacy_rows, _ = adapter.validate_traceability(
        repository,
        validator_path=validator_path,
    )
    legacy_statuses = {key: row.status for key, row in legacy_rows.items()}
    views = _native_views(repository, declarations, profile, legacy_statuses)
    _validate_hybrid_traceability(
        repository, declarations, views, validator_path, adapter
    )
    if pair_block_id not in declarations.pair_blocks_by_id:
        raise PairBlockGateError(f"unknown PairBlock: {pair_block_id}")
    view = views[pair_block_id]
    try:
        status_after = profile.lifecycle.advance(view.status, event)
    except ValueError as error:
        raise PairBlockGateError(str(error)) from error
    if event not in {item[0] for item in profile.lifecycle.transitions}:
        raise PairBlockGateError("manifest-native code uses the executable lifecycle")
    _require_native_lifecycle_evidence(repository, event, evidence, profile)
    recorded = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    receipt_path = (
        repository
        / "evidence"
        / "pairblock-lifecycle"
        / pair_block_id.lower()
        / f"{recorded.strftime('%Y%m%dT%H%M%S.%fZ')}-{event}.json"
    )
    relative_receipt = receipt_path.relative_to(repository).as_posix()
    if receipt_path.exists():
        raise PairBlockGateError(f"receipt already exists: {receipt_path}")
    checklist_path = repository / profile.checklist_path
    checklist_before = checklist_path.read_bytes()
    block = declarations.pair_blocks_by_id[pair_block_id]
    owner = (repository / dict(profile.repository_roots)[block.repository]).resolve()
    declaration_head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    implementation_head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=owner,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    receipt = LifecycleReceipt(
        schema_version=3,
        pair_block_id=pair_block_id,
        event=event,
        result="applied",
        status_before=view.status,
        status_after=status_after,
        recorded_at=recorded.isoformat(),
        repository_head=declaration_head,
        checklist_before_sha256=sha256_bytes(checklist_before),
        checklist_written_sha256="0" * 64,
        evidence=evidence,
        previous_receipt=view.receipt,
        declaration_sha256=declarations.sha256,
        pair_block_fingerprint=declarations.pair_block_fingerprint(pair_block_id),
        declaration_repository_head=declaration_head,
        implementation_repository_head=implementation_head,
    )
    projected_views = dict(views)
    projected_views[pair_block_id] = PairBlockView(status_after, relative_receipt)
    projected_views = _apply_waiting_states(
        declarations,
        projected_views,
        profile,
        legacy_statuses,
    )
    rendered = render_markdown(repository, declarations, projected_views, profile)
    receipt = replace(
        receipt,
        checklist_written_sha256=sha256_bytes(rendered.checklist),
    )
    pending_receipt = json.loads(_lifecycle_receipt_bytes(receipt))
    return _commit_native_projection(
        repository,
        f"{recorded.strftime('%Y%m%dT%H%M%S.%fZ')}-{pair_block_id.lower()}-{event}",
        receipt_path=receipt_path,
        receipt=_lifecycle_receipt_bytes(receipt),
        rendered_contract=rendered.contract,
        rendered_checklist=rendered.checklist,
        profile=profile,
        validate_documents=lambda: _validate_hybrid_traceability(
            repository,
            declarations,
            projected_views,
            validator_path,
            adapter,
            {relative_receipt: pending_receipt},
        ),
    )


def accept_declaration_revision(
    repository: Path,
    approval: EvidenceRef,
    *,
    plan_path: Path,
    plan_sha256: str,
    now: datetime | None = None,
    validator_path: Path = DEFAULT_MASTER_CHECKLIST_VALIDATOR,
    adapter: MarkdownChecklistAdapter = MANTRA_PHASE0_ADAPTER,
) -> Path:
    """Persist a reviewed manifest, verify its receipt, and reopen affected blocks.

    ``approval`` identifies the external user-review event that authorizes the
    candidate manifest. The controller recomputes the candidate's record
    changes and affected PairBlocks before writing the receipt, then reloads
    the complete revision chain before changing either rendered document.
    """

    if approval.kind != "external":
        raise PairBlockGateError("declaration revision requires external approval")
    repository = repository.resolve()
    profile = adapter.profile
    _recover_native_projections(repository, validator_path, adapter)
    candidate = _current_declarations(repository, profile)
    accepted = _accepted_declarations(repository, profile)
    change = compare_declarations(accepted.declarations, candidate)
    if not change.changed:
        raise PairBlockGateError(
            "working declarations already match the accepted revision"
        )
    reviewed_plan = plan_path.resolve()
    if not reviewed_plan.is_relative_to(repository) or not reviewed_plan.is_file():
        raise PairBlockGateError("reviewed declaration plan must be a repository file")
    if sha256_file(reviewed_plan) != plan_sha256:
        raise PairBlockGateError("reviewed declaration plan digest differs")
    try:
        plan = json.loads(reviewed_plan.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PairBlockGateError("reviewed declaration plan is invalid") from error
    if not isinstance(plan, dict) or set(plan) != _REVISION_PLAN_FIELDS:
        raise PairBlockGateError("reviewed declaration plan fields differ")
    expected_plan = {
        "schema_version": 1,
        "created_at": plan.get("created_at"),
        "before_sha256": change.before_sha256,
        "after_sha256": change.after_sha256,
        "records": [asdict(record) for record in change.records],
        "affected_pair_blocks": list(change.affected_pair_blocks),
        "previous_receipt": accepted.receipt_path,
        "candidate_manifest": json.loads(
            json.dumps(candidate.canonical_payload(), sort_keys=True)
        ),
    }
    if plan != expected_plan:
        raise PairBlockGateError("working declarations differ from the reviewed plan")
    legacy_rows, legacy_manifest = adapter.validate_traceability(
        repository,
        validator_path=validator_path,
    )
    _validate_native_dependencies(
        candidate,
        legacy_rows,
        {str(record["requirement_id"]) for record in legacy_manifest["requirements"]},
    )
    legacy_statuses = {key: row.status for key, row in legacy_rows.items()}
    previous_views = _native_views(
        repository,
        accepted.declarations,
        profile,
        legacy_statuses,
    )
    superseded = {
        pair_block_id: previous_views[pair_block_id].receipt
        for pair_block_id in change.affected_pair_blocks
        if pair_block_id in previous_views
        and previous_views[pair_block_id].receipt is not None
    }
    recorded = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    receipt_path = (
        repository
        / "evidence"
        / "declaration-revisions"
        / f"{recorded.strftime('%Y%m%dT%H%M%S.%fZ')}-revise.json"
    )
    receipt = {
        "schema_version": 1,
        "event": "revise",
        "result": "applied",
        "recorded_at": recorded.isoformat(),
        "before_sha256": change.before_sha256,
        "after_sha256": change.after_sha256,
        "records": [asdict(record) for record in change.records],
        "affected_pair_blocks": list(change.affected_pair_blocks),
        "approval": asdict(approval),
        "superseded_receipt_heads": superseded,
        "previous_receipt": accepted.receipt_path,
        "accepted_manifest": candidate.canonical_payload(),
        "reviewed_plan": reviewed_plan.relative_to(repository).as_posix(),
        "reviewed_plan_sha256": plan_sha256,
    }
    views = _apply_waiting_states(
        candidate,
        _native_views(repository, candidate, profile, legacy_statuses),
        profile,
        legacy_statuses,
    )
    rendered = render_markdown(repository, candidate, views, profile)
    return _commit_native_projection(
        repository,
        f"{recorded.strftime('%Y%m%dT%H%M%S.%fZ')}-declaration-revision",
        receipt_path=receipt_path,
        receipt=(json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode(),
        rendered_contract=rendered.contract,
        rendered_checklist=rendered.checklist,
        profile=profile,
        validate_documents=lambda: _validate_hybrid_traceability(
            repository, candidate, views, validator_path, adapter
        ),
    )


def plan_declaration_revision(
    repository: Path,
    *,
    validator_path: Path = DEFAULT_MASTER_CHECKLIST_VALIDATOR,
    adapter: MarkdownChecklistAdapter = MANTRA_PHASE0_ADAPTER,
) -> DeclarationChange:
    """Recompute the candidate change against the verified revision-chain head."""

    repository = repository.resolve()
    _recover_native_projections(repository, validator_path, adapter)
    candidate = _current_declarations(repository, adapter.profile)
    accepted = _accepted_declarations(repository, adapter.profile)
    legacy_rows, legacy_manifest = adapter.validate_traceability(
        repository,
        validator_path=validator_path,
    )
    _validate_native_dependencies(
        candidate,
        legacy_rows,
        {str(record["requirement_id"]) for record in legacy_manifest["requirements"]},
    )
    return compare_declarations(accepted.declarations, candidate)


def write_declaration_revision_plan(
    repository: Path,
    *,
    now: datetime | None = None,
    validator_path: Path = DEFAULT_MASTER_CHECKLIST_VALIDATOR,
    adapter: MarkdownChecklistAdapter = MANTRA_PHASE0_ADAPTER,
) -> Path:
    """Persist the exact candidate declaration change presented for review."""

    repository = repository.resolve()
    change = plan_declaration_revision(
        repository, validator_path=validator_path, adapter=adapter
    )
    if not change.changed:
        raise PairBlockGateError(
            "working declarations already match the accepted revision"
        )
    candidate = _current_declarations(repository, adapter.profile)
    accepted = _accepted_declarations(repository, adapter.profile)
    created = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    plan_path = (
        repository
        / "evidence"
        / "declaration-plans"
        / f"{created.strftime('%Y%m%dT%H%M%S.%fZ')}.json"
    )
    if plan_path.exists():
        raise PairBlockGateError(f"declaration plan already exists: {plan_path}")
    payload = {
        "schema_version": 1,
        "created_at": created.isoformat(),
        "before_sha256": change.before_sha256,
        "after_sha256": change.after_sha256,
        "records": [asdict(record) for record in change.records],
        "affected_pair_blocks": list(change.affected_pair_blocks),
        "previous_receipt": accepted.receipt_path,
        "candidate_manifest": candidate.canonical_payload(),
    }
    atomic_write(
        plan_path,
        (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode(),
    )
    return plan_path


def _run_markdown_gate(
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
        ["/bin/zsh", "-e", "-c", proposal.command],
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
    atomic_write(
        receipt_path,
        _gate_receipt_bytes(receipt),
    )
    if result == "passed":
        atomic_write(checklist_path, checklist_after)
        adapter.validate_traceability(
            repository,
            validator_path=resolved_validator,
        )
    return receipt_path


def run_gate(
    repository: Path,
    pair_block_id: str,
    *,
    now: datetime | None = None,
    validator_path: Path = DEFAULT_MASTER_CHECKLIST_VALIDATOR,
    adapter: MarkdownChecklistAdapter | None = None,
) -> Path:
    """Route one gate to its unique typed or legacy declaration owner."""

    repository = repository.resolve()
    selected_adapter = adapter or MANTRA_PHASE0_ADAPTER
    if selected_adapter.profile.declaration_path is not None:
        _recover_native_projections(repository, validator_path, selected_adapter)
    if selected_adapter.profile.declaration_path is None:
        return _run_markdown_gate(
            repository,
            pair_block_id,
            now=now,
            validator_path=validator_path,
            adapter=selected_adapter,
        )
    declarations = _require_accepted_declarations(repository, selected_adapter.profile)
    legacy_rows, legacy_manifest = selected_adapter.validate_traceability(
        repository,
        validator_path=validator_path,
    )
    _validate_native_dependencies(
        declarations,
        legacy_rows,
        {str(record["requirement_id"]) for record in legacy_manifest["requirements"]},
    )
    if pair_block_id in declarations.pair_blocks_by_id:
        return _run_native_gate(
            repository,
            pair_block_id,
            now=now,
            validator_path=validator_path,
            adapter=selected_adapter,
        )
    return _run_markdown_gate(
        repository,
        pair_block_id,
        now=now,
        validator_path=validator_path,
        adapter=selected_adapter,
    )


def _advance_markdown_pairblock(
    repository: Path,
    pair_block_id: str,
    event: str,
    evidence: EvidenceRef,
    *,
    certification_reason: str | None = None,
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
    is_legacy_certification = (
        profile.lifecycle.legacy_certification_event is not None
        and event == profile.lifecycle.legacy_certification_event
    )
    if is_legacy_certification:
        if pair_block_id not in profile.legacy_certifiable_pair_blocks:
            raise PairBlockGateError(
                f"{pair_block_id} is not approved for legacy certification"
            )
        if evidence.kind != "artifact":
            raise PairBlockGateError("legacy certification requires artifact evidence")
        if certification_reason is None or not certification_reason.strip():
            raise PairBlockGateError("legacy certification requires a reason")
        _require_certification_artifact(repository, evidence, profile)
    elif certification_reason is not None:
        raise PairBlockGateError(
            "certification reason is valid only for legacy certification"
        )
    if event in non_code_events:
        if adapter.has_proposed_code(row):
            raise PairBlockGateError(
                f"{pair_block_id} has runnable proposed code; run its gate"
            )
        if evidence.kind != "external":
            raise PairBlockGateError(f"{event} requires external review evidence")
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
        schema_version=2 if is_legacy_certification else 1,
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
        certification_reason=certification_reason,
    )
    atomic_write(
        receipt_path,
        _lifecycle_receipt_bytes(receipt),
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
        atomic_write(
            receipt_path,
            _lifecycle_receipt_bytes(rejected),
        )
        raise

    receipt = replace(
        receipt,
        checklist_written_sha256=sha256_bytes(checklist_after),
    )
    atomic_write(
        receipt_path,
        _lifecycle_receipt_bytes(receipt),
    )
    atomic_write(checklist_path, checklist_after)
    adapter.validate_traceability(
        repository,
        validator_path=validator_path,
    )
    return receipt_path


def advance_pairblock(
    repository: Path,
    pair_block_id: str,
    event: str,
    evidence: EvidenceRef,
    *,
    certification_reason: str | None = None,
    now: datetime | None = None,
    validator_path: Path = DEFAULT_MASTER_CHECKLIST_VALIDATOR,
    adapter: MarkdownChecklistAdapter | None = None,
) -> Path:
    """Route one lifecycle event to its unique declaration owner."""

    repository = repository.resolve()
    selected_adapter = adapter or MANTRA_PHASE0_ADAPTER
    if selected_adapter.profile.declaration_path is not None:
        _recover_native_projections(repository, validator_path, selected_adapter)
    if selected_adapter.profile.declaration_path is None:
        return _advance_markdown_pairblock(
            repository,
            pair_block_id,
            event,
            evidence,
            certification_reason=certification_reason,
            now=now,
            validator_path=validator_path,
            adapter=selected_adapter,
        )
    declarations = _require_accepted_declarations(repository, selected_adapter.profile)
    legacy_rows, legacy_manifest = selected_adapter.validate_traceability(
        repository,
        validator_path=validator_path,
    )
    _validate_native_dependencies(
        declarations,
        legacy_rows,
        {str(record["requirement_id"]) for record in legacy_manifest["requirements"]},
    )
    if pair_block_id in declarations.pair_blocks_by_id:
        if certification_reason is not None:
            raise PairBlockGateError(
                "certification reason is valid only for legacy certification"
            )
        return _advance_native_pairblock(
            repository,
            pair_block_id,
            event,
            evidence,
            now=now,
            validator_path=validator_path,
            adapter=selected_adapter,
        )
    return _advance_markdown_pairblock(
        repository,
        pair_block_id,
        event,
        evidence,
        certification_reason=certification_reason,
        now=now,
        validator_path=validator_path,
        adapter=selected_adapter,
    )


def render_views(
    repository: Path,
    *,
    validator_path: Path = DEFAULT_MASTER_CHECKLIST_VALIDATOR,
    adapter: MarkdownChecklistAdapter = MANTRA_PHASE0_ADAPTER,
) -> tuple[Path, Path]:
    """Regenerate both human views from accepted declarations and receipts."""

    repository = repository.resolve()
    _recover_native_projections(repository, validator_path, adapter)
    profile = adapter.profile
    declarations = _require_accepted_declarations(repository, profile)
    legacy_rows, _ = adapter.validate_traceability(
        repository,
        validator_path=validator_path,
    )
    views = _native_views(
        repository,
        declarations,
        profile,
        {key: row.status for key, row in legacy_rows.items()},
    )
    rendered = render_markdown(repository, declarations, views, profile)
    _write_rendered_documents(
        repository,
        rendered.contract,
        rendered.checklist,
        profile,
    )
    _validate_hybrid_traceability(
        repository,
        declarations,
        views,
        validator_path,
        adapter,
    )
    return repository / profile.contract_path, repository / profile.checklist_path


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
    advance.add_argument(
        "--evidence-kind", required=True, choices=sorted(EVIDENCE_KINDS)
    )
    advance.add_argument("--evidence-target", required=True)
    advance.add_argument("--evidence-revision", required=True)
    advance.add_argument("--certification-reason")
    revise = commands.add_parser("revise")
    revise.add_argument("--plan", type=Path, required=True)
    revise.add_argument("--plan-sha256", required=True)
    revise.add_argument("--approval-target", required=True)
    revise.add_argument("--approval-revision", required=True)
    commands.add_parser("plan-revision")
    commands.add_parser("render")
    arguments = parser.parse_args(argv)
    if arguments.operation == "plan-revision":
        plan_path = write_declaration_revision_plan(
            arguments.repository,
            validator_path=arguments.master_validator,
        )
        print(plan_path)
        print(sha256_file(plan_path))
        return 0
    if arguments.operation == "render":
        for path in render_views(
            arguments.repository,
            validator_path=arguments.master_validator,
        ):
            print(path)
        return 0
    if arguments.operation == "gate":
        receipt_path = run_gate(
            arguments.repository,
            arguments.pair_block_id,
            validator_path=arguments.master_validator,
        )
    elif arguments.operation == "advance":
        receipt_path = advance_pairblock(
            arguments.repository,
            arguments.pair_block_id,
            arguments.event,
            EvidenceRef(
                kind=arguments.evidence_kind,
                target=arguments.evidence_target,
                revision=arguments.evidence_revision,
            ),
            certification_reason=arguments.certification_reason,
            validator_path=arguments.master_validator,
        )
    else:
        receipt_path = accept_declaration_revision(
            arguments.repository,
            EvidenceRef(
                kind="external",
                target=arguments.approval_target,
                revision=arguments.approval_revision,
            ),
            plan_path=arguments.plan,
            plan_sha256=arguments.plan_sha256,
            validator_path=arguments.master_validator,
        )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    print(receipt_path)
    return 0 if receipt["result"] in {"applied", "passed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
