"""Validate manifest-native PairBlock receipts against their authorities.

Gate declarations, lifecycle policy, stored output, and repository ownership
define the values a successful receipt may claim. This module parses the full
receipt shape and recomputes those relationships before a receipt can derive a
PairBlock state.
"""

from __future__ import annotations

import json
import re
import shlex
import subprocess
from dataclasses import asdict, fields
from datetime import datetime, timezone
from pathlib import Path

from .checklist_profile import DEFAULT_MASTER_CHECKLIST_VALIDATOR
from .declaration_manifest import PairBlock, ProjectDeclarations
from .execution_identity import ExecutionIdentity, sha256_bytes, sha256_file
from .profile import ChecklistProfile, PairBlockGateError, is_evidence_kind

_HEX_SHA256 = re.compile(r"[0-9a-f]{64}")
_GIT_OBJECT_ID = re.compile(r"[0-9a-f]{40,64}")
_GATE_FIELDS = frozenset(
    {
        "schema_version",
        "pair_block_id",
        "result",
        "status_before",
        "status_after",
        "started_at",
        "finished_at",
        "checklist_path",
        "checklist_written_sha256",
        "contract_path",
        "command",
        "command_sha256",
        "exit_code",
        "stdout",
        "stderr",
        "output_sha256",
        "master_validator_path",
        "identity_before",
        "identity_after",
        "identity_drift",
        "normalized_manifest",
        "normalized_manifest_sha256",
        "declaration_sha256",
        "pair_block_fingerprint",
        "structured_gate",
    }
)
_LIFECYCLE_FIELDS = frozenset(
    {
        "schema_version",
        "pair_block_id",
        "event",
        "result",
        "status_before",
        "status_after",
        "recorded_at",
        "repository_head",
        "checklist_before_sha256",
        "checklist_written_sha256",
        "evidence",
        "declaration_sha256",
        "pair_block_fingerprint",
        "declaration_repository_head",
        "implementation_repository_head",
    }
)


def _fail(path: Path, detail: str) -> PairBlockGateError:
    """Create one path-specific receipt validation error."""

    return PairBlockGateError(f"native receipt {detail}: {path}")


def _require_sha256(value: object, path: Path, field: str) -> str:
    """Return one lowercase SHA-256 string or reject the receipt."""

    if not isinstance(value, str) or _HEX_SHA256.fullmatch(value) is None:
        raise _fail(path, f"has invalid {field}")
    return value


def _canonical_gate_bytes(block: PairBlock) -> bytes:
    """Serialize the declared gate exactly as the controller hashes it."""

    return json.dumps(
        asdict(block.gate), sort_keys=True, separators=(",", ":")
    ).encode()


def _require_utc_time(value: object, path: Path, field: str) -> datetime:
    """Return one timezone-aware UTC timestamp from a receipt field."""

    if not isinstance(value, str):
        raise _fail(path, f"has invalid {field}")
    try:
        timestamp = datetime.fromisoformat(value)
    except ValueError as error:
        raise _fail(path, f"has invalid {field}") from error
    if timestamp.tzinfo is None or timestamp.utcoffset() != timezone.utc.utcoffset(
        None
    ):
        raise _fail(path, f"has non-UTC {field}")
    return timestamp


def _require_git_commit(repository: Path, value: object, path: Path, field: str) -> str:
    """Return one object ID that resolves to a commit in the named repository."""

    if not isinstance(value, str) or _GIT_OBJECT_ID.fullmatch(value) is None:
        raise _fail(path, f"has invalid {field}")
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{value}^{{commit}}"],
        cwd=repository,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        raise _fail(path, f"has unknown {field}")
    return value


def _expected_source_paths(
    repository: Path,
    owner: Path,
    block: PairBlock,
    profile: ChecklistProfile,
) -> dict[str, Path]:
    """Return the exact source keys and paths captured by the native gate."""

    declaration_path = repository / profile.require_declaration_path()
    paths = (
        declaration_path,
        *(owner / item for item in (*block.source_paths, *block.test_paths)),
    )
    return {
        (
            item.relative_to(repository).as_posix()
            if item.is_relative_to(repository)
            else item.as_posix()
        ): item
        for item in paths
    }


def _require_identity(
    value: object,
    path: Path,
    field: str,
    repository: Path,
    owner: Path,
    expected_sources: dict[str, Path],
    validator_path: Path,
) -> dict[str, object]:
    """Validate one complete execution identity and its owner repository."""

    expected = {item.name for item in fields(ExecutionIdentity)}
    if not isinstance(value, dict) or set(value) != expected:
        raise _fail(path, f"has invalid {field} fields")
    if value["implementation_repository"] != owner.as_posix():
        raise _fail(path, f"has wrong {field} implementation repository")
    _require_git_commit(repository, value["git_head"], path, f"{field}.git_head")
    _require_git_commit(
        repository=owner,
        value=value["implementation_git_head"],
        path=path,
        field=f"{field}.implementation_git_head",
    )
    for name in expected - {
        "source_sha256",
        "implementation_repository",
        "git_head",
        "implementation_git_head",
    }:
        _require_sha256(value[name], path, f"{field}.{name}")
    source = value["source_sha256"]
    if not isinstance(source, dict) or set(source) != set(expected_sources):
        raise _fail(path, f"has invalid {field}.source_sha256")
    if any(
        _HEX_SHA256.fullmatch(str(source[name])) is None for name in expected_sources
    ):
        raise _fail(path, f"has invalid {field}.source_sha256")
    if value["master_validator_sha256"] != sha256_file(validator_path):
        raise _fail(path, f"has changed {field}.master_validator_sha256")
    return value


def _identity_drift(
    before: dict[str, object], after: dict[str, object]
) -> dict[str, dict[str, object]]:
    """Recompute the changed fields between two stored identities."""

    return {
        name: {"before": before[name], "after": after[name]}
        for name in before
        if before[name] != after[name]
    }


def validate_native_gate_receipt(
    repository: Path,
    path: Path,
    receipt: dict[str, object],
    block: PairBlock,
    declarations: ProjectDeclarations,
    profile: ChecklistProfile,
    accepted_declaration_sha256s: frozenset[str],
) -> None:
    """Verify every authoritative field in one successful gate receipt."""

    fields_present = set(receipt)
    if receipt.get("previous_receipt") is not None:
        expected_fields = _GATE_FIELDS | {"previous_receipt"}
    else:
        expected_fields = _GATE_FIELDS
    if fields_present != expected_fields:
        raise _fail(path, "fields differ")
    if (
        receipt.get("schema_version") != 3
        or receipt.get("result") != "passed"
        or receipt.get("pair_block_id") != block.id
        or receipt.get("exit_code") != 0
        or receipt.get("status_after") != profile.lifecycle.review_status
    ):
        raise _fail(path, "gate envelope differs")
    started = _require_utc_time(receipt.get("started_at"), path, "started_at")
    finished = _require_utc_time(receipt.get("finished_at"), path, "finished_at")
    if finished < started:
        raise _fail(path, "gate time order differs")
    if (
        receipt.get("checklist_path") != profile.checklist_path.as_posix()
        or receipt.get("contract_path") != profile.contract_path.as_posix()
    ):
        raise _fail(path, "document paths differ")
    if receipt.get("declaration_sha256") not in accepted_declaration_sha256s:
        raise _fail(path, "declaration digest differs")
    if receipt.get("pair_block_fingerprint") != declarations.pair_block_fingerprint(
        block.id
    ):
        raise _fail(path, "PairBlock fingerprint differs")

    declared_gate = {
        "repository": block.gate.repository,
        "working_directory": block.gate.working_directory,
        "argv": list(block.gate.argv),
        "environment": dict(block.gate.environment),
    }
    if receipt.get("structured_gate") != declared_gate:
        raise _fail(path, "structured gate differs")
    if receipt.get("command") != shlex.join(block.gate.argv):
        raise _fail(path, "command differs")
    if receipt.get("command_sha256") != sha256_bytes(_canonical_gate_bytes(block)):
        raise _fail(path, "command digest differs")

    stdout = receipt.get("stdout")
    stderr = receipt.get("stderr")
    if not isinstance(stdout, str) or not isinstance(stderr, str):
        raise _fail(path, "output fields differ")
    output = stdout.encode() + b"\0" + stderr.encode()
    if receipt.get("output_sha256") != sha256_bytes(output):
        raise _fail(path, "output digest differs")

    owner = (repository / dict(profile.repository_roots)[block.repository]).resolve()
    expected_sources = _expected_source_paths(repository, owner, block, profile)
    validator_path = DEFAULT_MASTER_CHECKLIST_VALIDATOR.resolve()
    if receipt.get("master_validator_path") != validator_path.as_posix():
        raise _fail(path, "master validator path differs")
    before = _require_identity(
        receipt.get("identity_before"),
        path,
        "identity_before",
        repository,
        owner,
        expected_sources,
        validator_path,
    )
    after = _require_identity(
        receipt.get("identity_after"),
        path,
        "identity_after",
        repository,
        owner,
        expected_sources,
        validator_path,
    )
    drift = _identity_drift(before, after)
    if receipt.get("identity_drift") != drift or drift:
        raise _fail(path, "execution identity drift differs")

    manifest = receipt.get("normalized_manifest")
    if not isinstance(manifest, dict):
        raise _fail(path, "normalized manifest is missing")
    manifest_digest = sha256_bytes(
        (json.dumps(manifest, sort_keys=True) + "\n").encode()
    )
    if receipt.get("normalized_manifest_sha256") != manifest_digest:
        raise _fail(path, "normalized manifest digest differs")


def validate_native_lifecycle_receipt(
    repository: Path,
    path: Path,
    receipt: dict[str, object],
    block: PairBlock,
    declarations: ProjectDeclarations,
    profile: ChecklistProfile,
    accepted_declaration_sha256s: frozenset[str],
) -> None:
    """Verify one lifecycle transition and the evidence assigned to its event."""

    expected_fields = set(_LIFECYCLE_FIELDS)
    if receipt.get("previous_receipt") is not None:
        expected_fields.add("previous_receipt")
    if set(receipt) != expected_fields:
        raise _fail(path, "fields differ")
    event = receipt.get("event")
    before = receipt.get("status_before")
    after = receipt.get("status_after")
    if (
        receipt.get("schema_version") != 3
        or receipt.get("result") != "applied"
        or receipt.get("pair_block_id") != block.id
        or not isinstance(event, str)
        or not isinstance(before, str)
        or not isinstance(after, str)
    ):
        raise _fail(path, "lifecycle envelope differs")
    _require_utc_time(receipt.get("recorded_at"), path, "recorded_at")
    try:
        expected_after = profile.lifecycle.advance(before, event)
        expected_kind = profile.lifecycle.required_evidence_kind(event)
    except ValueError as error:
        raise _fail(path, "lifecycle transition is illegal") from error
    if after != expected_after:
        raise _fail(path, "lifecycle status differs")
    if receipt.get("declaration_sha256") not in accepted_declaration_sha256s:
        raise _fail(path, "declaration digest differs")
    if receipt.get("pair_block_fingerprint") != declarations.pair_block_fingerprint(
        block.id
    ):
        raise _fail(path, "PairBlock fingerprint differs")

    evidence = receipt.get("evidence")
    if not isinstance(evidence, dict) or set(evidence) != {
        "kind",
        "target",
        "revision",
    }:
        raise _fail(path, "lifecycle evidence fields differ")
    kind = evidence.get("kind")
    target = evidence.get("target")
    revision = evidence.get("revision")
    if (
        not is_evidence_kind(kind)
        or kind != expected_kind
        or not isinstance(target, str)
        or not target
        or not isinstance(revision, str)
        or not revision
    ):
        raise _fail(path, "lifecycle evidence differs")
    if kind == "artifact":
        artifact = (repository / target).resolve()
        if (
            Path(target).is_absolute()
            or ".." in Path(target).parts
            or not artifact.is_relative_to(repository)
            or not artifact.is_file()
            or sha256_file(artifact) != revision
        ):
            raise _fail(path, "lifecycle artifact differs")

    owner = (repository / dict(profile.repository_roots)[block.repository]).resolve()
    declaration_head = receipt.get("declaration_repository_head")
    implementation_head = receipt.get("implementation_repository_head")
    if (
        receipt.get("repository_head") != declaration_head
        or not isinstance(declaration_head, str)
        or not declaration_head
        or not isinstance(implementation_head, str)
        or not implementation_head
    ):
        raise _fail(path, "repository identities differ")
    _require_git_commit(
        repository, declaration_head, path, "declaration repository head"
    )
    _require_git_commit(
        owner, implementation_head, path, "implementation repository head"
    )
    if owner == repository and implementation_head != declaration_head:
        raise _fail(path, "single-repository identity differs")
    _require_sha256(
        receipt.get("checklist_before_sha256"), path, "checklist before digest"
    )
    _require_sha256(
        receipt.get("checklist_written_sha256"), path, "checklist written digest"
    )
