"""Own the typed declarations that replace executable Markdown metadata.

This module parses project TOML into immutable requirement, verifier, and
PairBlock records. It validates their references and repository paths, computes
stable record and PairBlock identities, and derives the exact impact of a
candidate revision. Lifecycle state and human Markdown rendering belong to the
controller and renderer modules.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict, deque
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import tomllib

from .profile import (
    ChecklistProfile,
    EvidenceKind,
    PairBlockGateError,
    is_evidence_kind,
)

_RECORD_KINDS = ("requirement", "verifier", "pair_block")
_ENVIRONMENT_KEY = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class GateReference:
    """Name the global checklist gate that closes one requirement.

    Attributes:
        kind: Global gate category consumed by the checklist validator.
        target: Verifier ID or external target selected by the requirement.
    """

    kind: EvidenceKind
    target: str


@dataclass(frozen=True, slots=True)
class GateCommand:
    """Describe one executable gate without shell parsing.

    Attributes:
        repository: Profile repository ID that owns the command.
        working_directory: Owning-repository-relative process directory.
        argv: Argument vector passed directly to the child process.
        environment: Environment variables added to the child process.
    """

    repository: str
    working_directory: str
    argv: tuple[str, ...]
    environment: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class Requirement:
    """Represent one contract claim and its implementation owners.

    Attributes:
        id: Stable requirement identifier.
        claim: Human statement that the implementation must satisfy.
        phase: Numeric global-checklist phase.
        order: Requirement position within its phase.
        depends_on: Requirement IDs that must precede this record.
        gate: Global checklist observation that decides completion.
        verifier_ids: Verifiers that define the acceptance boundary.
        pair_block_ids: PairBlocks that implement this requirement.
    """

    id: str
    claim: str
    phase: int
    order: int
    depends_on: tuple[str, ...]
    gate: GateReference
    verifier_ids: tuple[str, ...]
    pair_block_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Verifier:
    """Represent the observations that decide one or more requirements.

    Attributes:
        id: Stable verifier identifier.
        requirement_ids: Requirements decided by this verifier.
        conditions: Independently observable acceptance conditions.
        success_case: Smallest scenario that must pass.
        rejection_cases: Counterexamples that must fail.
    """

    id: str
    requirement_ids: tuple[str, ...]
    conditions: tuple[str, ...]
    success_case: str
    rejection_cases: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PairBlock:
    """Represent one bounded implementation and its executable gate.

    Attributes:
        id: Stable PairBlock identifier.
        requirement_ids: Requirements implemented by the block.
        depends_on: PairBlocks that must reach a resolved state first.
        section: Global-checklist scheduling section.
        repository: Profile repository ID that owns the implementation.
        source_paths: Owning-repository-relative implementation files.
        test_paths: Owning-repository-relative observing tests.
        gate: Directly executable focused gate.
    """

    id: str
    requirement_ids: tuple[str, ...]
    depends_on: tuple[str, ...]
    section: str
    repository: str
    source_paths: tuple[str, ...]
    test_paths: tuple[str, ...]
    gate: GateCommand


@dataclass(frozen=True, slots=True)
class ProjectDeclarations:
    """Own every manifest-native contract record for one checklist.

    Attributes:
        schema_version: Version of the typed declaration format.
        requirements: Contract claims ordered by their manifest positions.
        verifiers: Acceptance boundaries referenced by requirements.
        pair_blocks: Implementations referenced by requirements.
    """

    schema_version: int
    requirements: tuple[Requirement, ...]
    verifiers: tuple[Verifier, ...]
    pair_blocks: tuple[PairBlock, ...]

    @property
    def requirements_by_id(self) -> dict[str, Requirement]:
        """Return requirements keyed by their stable identifiers."""

        return {record.id: record for record in self.requirements}

    @property
    def verifiers_by_id(self) -> dict[str, Verifier]:
        """Return verifiers keyed by their stable identifiers."""

        return {record.id: record for record in self.verifiers}

    @property
    def pair_blocks_by_id(self) -> dict[str, PairBlock]:
        """Return PairBlocks keyed by their stable identifiers."""

        return {record.id: record for record in self.pair_blocks}

    def canonical_payload(self) -> dict[str, object]:
        """Return the order-independent serialized declaration payload."""

        return {
            "schema_version": self.schema_version,
            "requirements": [
                _record_payload(record)
                for record in sorted(self.requirements, key=lambda item: item.id)
            ],
            "verifiers": [
                _record_payload(record)
                for record in sorted(self.verifiers, key=lambda item: item.id)
            ],
            "pair_blocks": [
                _record_payload(record)
                for record in sorted(self.pair_blocks, key=lambda item: item.id)
            ],
        }

    @property
    def sha256(self) -> str:
        """Return the digest of the canonical declaration payload."""

        return _digest(self.canonical_payload())

    def record_digests(self) -> dict[str, str]:
        """Return one canonical digest for every declared record."""

        records: dict[str, object] = {}
        for kind, values in (
            ("requirement", self.requirements),
            ("verifier", self.verifiers),
            ("pair_block", self.pair_blocks),
        ):
            for record in values:
                records[f"{kind}:{record.id}"] = _record_payload(record)
        return {key: _digest(value) for key, value in sorted(records.items())}

    def pair_block_fingerprint(self, pair_block_id: str) -> str:
        """Hash every declaration whose change can invalidate one PairBlock.

        The fingerprint includes the block and its transitive block
        dependencies, their requirements and transitive requirement
        dependencies, and every verifier selected by those requirements.
        Lifecycle receipts store this value so a later declaration revision
        cannot reuse evidence collected for an older contract.
        """

        blocks = self.pair_blocks_by_id
        requirements = self.requirements_by_id
        verifiers = self.verifiers_by_id
        try:
            root = blocks[pair_block_id]
        except KeyError as error:
            raise PairBlockGateError(
                f"unknown manifest PairBlock: {pair_block_id}"
            ) from error

        block_ids = _transitive_dependencies(pair_block_id, blocks)
        requirement_ids = {
            requirement_id
            for block_id in block_ids
            for requirement_id in blocks[block_id].requirement_ids
        }
        requirement_ids.update(root.requirement_ids)
        pending_requirements = list(requirement_ids)
        while pending_requirements:
            requirement_id = pending_requirements.pop()
            for dependency in requirements[requirement_id].depends_on:
                if dependency in requirements and dependency not in requirement_ids:
                    requirement_ids.add(dependency)
                    pending_requirements.append(dependency)
        verifier_ids = {
            verifier_id
            for requirement_id in requirement_ids
            for verifier_id in requirements[requirement_id].verifier_ids
        }
        payload = {
            "pair_blocks": [
                _record_payload(blocks[block_id]) for block_id in sorted(block_ids)
            ],
            "requirements": [
                _record_payload(requirements[record_id])
                for record_id in sorted(requirement_ids)
            ],
            "verifiers": [
                _record_payload(verifiers[record_id])
                for record_id in sorted(verifier_ids)
            ],
        }
        return _digest(payload)


@dataclass(frozen=True, slots=True)
class RecordChange:
    """Identify one added, changed, or removed declaration record.

    Attributes:
        record: Record kind and stable ID joined by a colon.
        before_sha256: Prior digest, or ``None`` for an added record.
        after_sha256: Candidate digest, or ``None`` for a removed record.
    """

    record: str
    before_sha256: str | None
    after_sha256: str | None


@dataclass(frozen=True, slots=True)
class DeclarationChange:
    """Describe one candidate declaration revision and its affected blocks.

    Attributes:
        before_sha256: Digest of the accepted declaration manifest.
        after_sha256: Digest of the working declaration manifest.
        records: Added, changed, and removed record identities.
        affected_pair_blocks: Direct and reverse-dependent PairBlocks reopened
            by the change.
    """

    before_sha256: str
    after_sha256: str
    records: tuple[RecordChange, ...]
    affected_pair_blocks: tuple[str, ...]

    @property
    def changed(self) -> bool:
        """Return whether the candidate differs from the accepted declaration."""

        return self.before_sha256 != self.after_sha256


def _require_exact_fields(
    value: Mapping[str, Any], required: set[str], label: str
) -> None:
    """Reject missing and unknown mapping fields."""

    missing = required - value.keys()
    extra = value.keys() - required
    if missing:
        raise PairBlockGateError(f"{label} missing fields: {sorted(missing)}")
    if extra:
        raise PairBlockGateError(f"{label} unknown fields: {sorted(extra)}")


def _require_text(value: Any, label: str) -> str:
    """Return one non-empty string."""

    if not isinstance(value, str) or not value.strip():
        raise PairBlockGateError(f"{label} must be a non-empty string")
    return value


def _require_integer(value: Any, label: str) -> int:
    """Return one non-negative integer distinct from Boolean values."""

    if type(value) is not int or value < 0:
        raise PairBlockGateError(f"{label} must be a non-negative integer")
    return value


def _require_schema_version(value: Any, label: str) -> int:
    """Return the only declaration schema version this loader implements."""

    version = _require_integer(value, label)
    if version != _SCHEMA_VERSION:
        raise PairBlockGateError(f"{label} must equal {_SCHEMA_VERSION}")
    return version


def _require_string_list(
    value: Any, label: str, *, nonempty: bool = False
) -> tuple[str, ...]:
    """Return a duplicate-free tuple of non-empty strings."""

    if not isinstance(value, list):
        raise PairBlockGateError(f"{label} must be an array")
    values = tuple(_require_text(item, f"{label} item") for item in value)
    if nonempty and not values:
        raise PairBlockGateError(f"{label} must not be empty")
    if len(values) != len(set(values)):
        raise PairBlockGateError(f"{label} contains duplicates")
    return values


def _require_repo_path(value: Any, label: str) -> str:
    """Return one normalized repository-relative POSIX path."""

    text = _require_text(value, label)
    path = PurePosixPath(text)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != text:
        raise PairBlockGateError(
            f"{label} must be a normalized repository-relative path"
        )
    return text


def _require_records(value: Any, label: str) -> list[Mapping[str, Any]]:
    """Return one TOML array containing mapping records."""

    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise PairBlockGateError(f"{label} must be an array of tables")
    return value


def _parse_gate_reference(value: Any, label: str) -> GateReference:
    """Parse one global checklist gate reference."""

    if not isinstance(value, dict):
        raise PairBlockGateError(f"{label} must be a table")
    _require_exact_fields(value, {"kind", "target"}, label)
    kind = _require_text(value["kind"], f"{label}.kind")
    if not is_evidence_kind(kind):
        raise PairBlockGateError(f"{label}.kind is invalid: {kind}")
    return GateReference(
        kind=kind, target=_require_text(value["target"], f"{label}.target")
    )


def _parse_gate_command(value: Any, label: str) -> GateCommand:
    """Parse one directly executable gate command."""

    if not isinstance(value, dict):
        raise PairBlockGateError(f"{label} must be a table")
    _require_exact_fields(
        value,
        {"repository", "working_directory", "argv", "environment"},
        label,
    )
    environment = value["environment"]
    if not isinstance(environment, dict):
        raise PairBlockGateError(f"{label}.environment must be a table")
    parsed_environment = tuple(
        sorted(
            (
                _require_text(key, f"{label}.environment key"),
                _require_text(item, f"{label}.environment.{key}"),
            )
            for key, item in environment.items()
        )
    )
    invalid_keys = [
        key for key, _ in parsed_environment if _ENVIRONMENT_KEY.fullmatch(key) is None
    ]
    if invalid_keys:
        raise PairBlockGateError(
            f"{label}.environment has invalid keys: {invalid_keys}"
        )
    return GateCommand(
        repository=_require_text(value["repository"], f"{label}.repository"),
        working_directory=_require_repo_path(
            value["working_directory"], f"{label}.working_directory"
        ),
        argv=_require_string_list(value["argv"], f"{label}.argv", nonempty=True),
        environment=parsed_environment,
    )


def _parse_requirement(value: Mapping[str, Any], index: int) -> Requirement:
    """Parse one requirement table."""

    label = f"requirements[{index}]"
    _require_exact_fields(
        value,
        {
            "id",
            "claim",
            "phase",
            "order",
            "depends_on",
            "gate",
            "verifier_ids",
            "pair_block_ids",
        },
        label,
    )
    return Requirement(
        id=_require_text(value["id"], f"{label}.id"),
        claim=_require_text(value["claim"], f"{label}.claim"),
        phase=_require_integer(value["phase"], f"{label}.phase"),
        order=_require_integer(value["order"], f"{label}.order"),
        depends_on=_require_string_list(value["depends_on"], f"{label}.depends_on"),
        gate=_parse_gate_reference(value["gate"], f"{label}.gate"),
        verifier_ids=_require_string_list(
            value["verifier_ids"], f"{label}.verifier_ids", nonempty=True
        ),
        pair_block_ids=_require_string_list(
            value["pair_block_ids"], f"{label}.pair_block_ids", nonempty=True
        ),
    )


def _parse_verifier(value: Mapping[str, Any], index: int) -> Verifier:
    """Parse one verifier table."""

    label = f"verifiers[{index}]"
    _require_exact_fields(
        value,
        {"id", "requirement_ids", "conditions", "success_case", "rejection_cases"},
        label,
    )
    return Verifier(
        id=_require_text(value["id"], f"{label}.id"),
        requirement_ids=_require_string_list(
            value["requirement_ids"], f"{label}.requirement_ids", nonempty=True
        ),
        conditions=_require_string_list(
            value["conditions"], f"{label}.conditions", nonempty=True
        ),
        success_case=_require_text(value["success_case"], f"{label}.success_case"),
        rejection_cases=_require_string_list(
            value["rejection_cases"], f"{label}.rejection_cases", nonempty=True
        ),
    )


def _parse_pair_block(value: Mapping[str, Any], index: int) -> PairBlock:
    """Parse one PairBlock table."""

    label = f"pair_blocks[{index}]"
    _require_exact_fields(
        value,
        {
            "id",
            "requirement_ids",
            "depends_on",
            "section",
            "repository",
            "source_paths",
            "test_paths",
            "gate",
        },
        label,
    )
    source_paths = tuple(
        _require_repo_path(item, f"{label}.source_paths item")
        for item in _require_string_list(
            value["source_paths"], f"{label}.source_paths", nonempty=True
        )
    )
    test_paths = tuple(
        _require_repo_path(item, f"{label}.test_paths item")
        for item in _require_string_list(
            value["test_paths"], f"{label}.test_paths", nonempty=True
        )
    )
    if set(source_paths) & set(test_paths):
        raise PairBlockGateError(f"{label} assigns one path to source and test roles")
    return PairBlock(
        id=_require_text(value["id"], f"{label}.id"),
        requirement_ids=_require_string_list(
            value["requirement_ids"], f"{label}.requirement_ids", nonempty=True
        ),
        depends_on=_require_string_list(value["depends_on"], f"{label}.depends_on"),
        section=_require_text(value["section"], f"{label}.section"),
        repository=_require_text(value["repository"], f"{label}.repository"),
        source_paths=source_paths,
        test_paths=test_paths,
        gate=_parse_gate_command(value["gate"], f"{label}.gate"),
    )


def load_declarations(path: Path, profile: ChecklistProfile) -> ProjectDeclarations:
    """Load and validate one typed project declaration manifest."""

    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise PairBlockGateError(
            f"cannot load declaration manifest: {error}"
        ) from error
    _require_exact_fields(raw, {"schema_version", *_plural_record_kinds()}, str(path))
    schema_version = _require_schema_version(
        raw["schema_version"], "declaration.schema_version"
    )
    declarations = ProjectDeclarations(
        schema_version=schema_version,
        requirements=tuple(
            _parse_requirement(value, index)
            for index, value in enumerate(
                _require_records(raw["requirements"], "requirements")
            )
        ),
        verifiers=tuple(
            _parse_verifier(value, index)
            for index, value in enumerate(
                _require_records(raw["verifiers"], "verifiers")
            )
        ),
        pair_blocks=tuple(
            _parse_pair_block(value, index)
            for index, value in enumerate(
                _require_records(raw["pair_blocks"], "pair_blocks")
            )
        ),
    )
    _validate_declarations(
        declarations,
        _repository_from_declaration_path(path, profile),
        profile,
    )
    return declarations


def declarations_from_payload(
    payload: Mapping[str, Any], profile: ChecklistProfile, repository: Path
) -> ProjectDeclarations:
    """Rebuild an accepted declaration snapshot from a revision receipt."""

    _require_exact_fields(
        payload, {"schema_version", *_plural_record_kinds()}, "snapshot"
    )
    declarations = ProjectDeclarations(
        schema_version=_require_schema_version(
            payload["schema_version"], "snapshot.schema_version"
        ),
        requirements=tuple(
            _parse_requirement(value, index)
            for index, value in enumerate(
                _require_records(payload["requirements"], "requirements")
            )
        ),
        verifiers=tuple(
            _parse_verifier(value, index)
            for index, value in enumerate(
                _require_records(payload["verifiers"], "verifiers")
            )
        ),
        pair_blocks=tuple(
            _parse_pair_block(value, index)
            for index, value in enumerate(
                _require_records(payload["pair_blocks"], "pair_blocks")
            )
        ),
    )
    _validate_declarations(
        declarations, repository.resolve(), profile, require_files=False
    )
    return declarations


def compare_declarations(
    accepted: ProjectDeclarations, candidate: ProjectDeclarations
) -> DeclarationChange:
    """Derive changed records and every PairBlock invalidated by those changes.

    Record digests establish the direct differences. Reverse requirement and
    PairBlock dependency edges extend those differences to consumers whose
    prior lifecycle evidence is no longer current.
    """

    before = accepted.record_digests()
    after = candidate.record_digests()
    records = tuple(
        RecordChange(key, before.get(key), after.get(key))
        for key in sorted(before.keys() | after.keys())
        if before.get(key) != after.get(key)
    )
    changed_keys = {record.record for record in records}
    affected = _directly_affected_blocks(accepted, candidate, changed_keys)
    all_blocks = {**accepted.pair_blocks_by_id, **candidate.pair_blocks_by_id}
    reverse_dependencies: dict[str, set[str]] = defaultdict(set)
    for block in all_blocks.values():
        for dependency in block.depends_on:
            reverse_dependencies[dependency].add(block.id)
    queue = deque(affected)
    while queue:
        for dependent in reverse_dependencies[queue.popleft()]:
            if dependent not in affected:
                affected.add(dependent)
                queue.append(dependent)
    return DeclarationChange(
        before_sha256=accepted.sha256,
        after_sha256=candidate.sha256,
        records=records,
        affected_pair_blocks=tuple(sorted(affected)),
    )


def empty_declarations() -> ProjectDeclarations:
    """Return the accepted bootstrap state before the first native record."""

    return ProjectDeclarations(1, (), (), ())


def _repository_from_declaration_path(path: Path, profile: ChecklistProfile) -> Path:
    """Resolve the checklist repository from its configured manifest path."""

    if profile.declaration_path is None:
        raise PairBlockGateError("profile has no declaration_path")
    resolved = path.resolve()
    if tuple(resolved.parts[-len(profile.declaration_path.parts) :]) != tuple(
        profile.declaration_path.parts
    ):
        raise PairBlockGateError(
            f"declaration path must end with {profile.declaration_path.as_posix()}"
        )
    repository = resolved
    for _ in profile.declaration_path.parts:
        repository = repository.parent
    return repository


def _plural_record_kinds() -> set[str]:
    """Return TOML collection keys for every record category."""

    return {f"{kind}s" for kind in _RECORD_KINDS}


def _record_payload(record: Requirement | Verifier | PairBlock) -> dict[str, object]:
    """Return a canonical JSON-compatible record mapping."""

    payload = asdict(record)
    if isinstance(record, PairBlock):
        payload["gate"]["environment"] = dict(record.gate.environment)
    return payload


def _canonical_bytes(value: object) -> bytes:
    """Serialize one value with stable key and collection ordering."""

    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: object) -> str:
    """Return the SHA-256 of one canonical JSON value."""

    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _require_unique_ids(
    records: Sequence[Requirement | Verifier | PairBlock], label: str
) -> None:
    """Reject duplicate IDs within one record category."""

    values = [record.id for record in records]
    if len(values) != len(set(values)):
        raise PairBlockGateError(f"duplicate {label} ID")


def _require_known(values: Iterable[str], known: set[str], label: str) -> None:
    """Reject a reference to an absent declaration record."""

    missing = sorted(set(values) - known)
    if missing:
        raise PairBlockGateError(f"{label} references unknown IDs: {missing}")


def _require_acyclic(edges: Mapping[str, Sequence[str]], label: str) -> None:
    """Reject a cycle in one declaration dependency graph."""

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        """Visit one dependency and reject its first back edge."""

        if node in visiting:
            raise PairBlockGateError(f"{label} dependency cycle includes {node}")
        if node in visited:
            return
        visiting.add(node)
        for dependency in edges[node]:
            visit(dependency)
        visiting.remove(node)
        visited.add(node)

    for node in edges:
        visit(node)


def _validate_declarations(
    declarations: ProjectDeclarations,
    repository: Path,
    profile: ChecklistProfile,
    *,
    require_files: bool = True,
) -> None:
    """Validate identifiers, joins, graphs, repositories, and owned paths."""

    _validate_record_identities(declarations, profile)
    _validate_record_references(declarations)
    _validate_dependency_graphs(declarations)
    _validate_ownership_joins(declarations)
    _validate_repository_paths(
        declarations,
        repository,
        profile,
        require_files=require_files,
    )


def _validate_record_identities(
    declarations: ProjectDeclarations, profile: ChecklistProfile
) -> None:
    """Validate category uniqueness, ID syntax, and requirement positions."""

    _require_unique_ids(declarations.requirements, "requirement")
    _require_unique_ids(declarations.verifiers, "verifier")
    _require_unique_ids(declarations.pair_blocks, "PairBlock")
    requirement_ids = set(declarations.requirements_by_id)
    verifier_ids = set(declarations.verifiers_by_id)
    pair_block_ids = set(declarations.pair_blocks_by_id)
    all_ids = requirement_ids | verifier_ids | pair_block_ids
    if len(all_ids) != len(requirement_ids) + len(verifier_ids) + len(pair_block_ids):
        raise PairBlockGateError(
            "declaration IDs must be unique across record categories"
        )

    positions = [(record.phase, record.order) for record in declarations.requirements]
    if len(positions) != len(set(positions)):
        raise PairBlockGateError("requirement phase and order positions must be unique")
    for requirement in declarations.requirements:
        if not profile.accepts_requirement_id(requirement.id):
            raise PairBlockGateError(f"invalid requirement ID: {requirement.id}")
    for block in declarations.pair_blocks:
        if not profile.accepts_pair_block_id(block.id):
            raise PairBlockGateError(f"invalid PairBlock ID: {block.id}")


def _validate_record_references(declarations: ProjectDeclarations) -> None:
    """Require each ownership reference to name a typed record."""

    requirement_ids = set(declarations.requirements_by_id)
    verifier_ids = set(declarations.verifiers_by_id)
    pair_block_ids = set(declarations.pair_blocks_by_id)
    for requirement in declarations.requirements:
        _require_known(requirement.verifier_ids, verifier_ids, requirement.id)
        _require_known(requirement.pair_block_ids, pair_block_ids, requirement.id)
    for verifier in declarations.verifiers:
        _require_known(verifier.requirement_ids, requirement_ids, verifier.id)
    for block in declarations.pair_blocks:
        _require_known(block.requirement_ids, requirement_ids, block.id)


def _validate_dependency_graphs(declarations: ProjectDeclarations) -> None:
    """Require acyclic dependencies within each typed record category."""

    requirement_ids = set(declarations.requirements_by_id)
    pair_block_ids = set(declarations.pair_blocks_by_id)
    _require_acyclic(
        {
            record.id: tuple(
                dependency
                for dependency in record.depends_on
                if dependency in requirement_ids
            )
            for record in declarations.requirements
        },
        "requirement",
    )
    _require_acyclic(
        {
            record.id: tuple(
                dependency
                for dependency in record.depends_on
                if dependency in pair_block_ids
            )
            for record in declarations.pair_blocks
        },
        "PairBlock",
    )


def _validate_ownership_joins(declarations: ProjectDeclarations) -> None:
    """Require both sides of each ownership relationship to agree."""

    _validate_requirement_owners(declarations)
    _validate_owner_requirements(declarations)


def _validate_requirement_owners(declarations: ProjectDeclarations) -> None:
    """Require each requirement's named owners to point back to it."""

    for requirement in declarations.requirements:
        for verifier_id in requirement.verifier_ids:
            if (
                requirement.id
                not in declarations.verifiers_by_id[verifier_id].requirement_ids
            ):
                raise PairBlockGateError(
                    f"{requirement.id} and {verifier_id} disagree on ownership"
                )
        for pair_block_id in requirement.pair_block_ids:
            if (
                requirement.id
                not in declarations.pair_blocks_by_id[pair_block_id].requirement_ids
            ):
                raise PairBlockGateError(
                    f"{requirement.id} and {pair_block_id} disagree on ownership"
                )


def _validate_owner_requirements(declarations: ProjectDeclarations) -> None:
    """Require each verifier and PairBlock requirement to point back to it."""

    for verifier in declarations.verifiers:
        for requirement_id in verifier.requirement_ids:
            if (
                verifier.id
                not in declarations.requirements_by_id[requirement_id].verifier_ids
            ):
                raise PairBlockGateError(
                    f"{verifier.id} and {requirement_id} disagree on ownership"
                )
    for block in declarations.pair_blocks:
        for requirement_id in block.requirement_ids:
            if (
                block.id
                not in declarations.requirements_by_id[requirement_id].pair_block_ids
            ):
                raise PairBlockGateError(
                    f"{block.id} and {requirement_id} disagree on ownership"
                )


def _validate_repository_paths(
    declarations: ProjectDeclarations,
    repository: Path,
    profile: ChecklistProfile,
    *,
    require_files: bool,
) -> None:
    """Resolve every code and gate path inside its named repository."""

    roots = dict(profile.repository_roots)
    for block in declarations.pair_blocks:
        if block.repository not in roots:
            raise PairBlockGateError(
                f"{block.id} uses unknown repository: {block.repository}"
            )
        if block.gate.repository != block.repository:
            raise PairBlockGateError(
                f"{block.id} gate repository differs from its code owner"
            )
        owner = (repository / roots[block.repository]).resolve()
        for relative in (
            *block.source_paths,
            *block.test_paths,
            block.gate.working_directory,
        ):
            resolved = (owner / relative).resolve()
            if not resolved.is_relative_to(owner):
                raise PairBlockGateError(
                    f"{block.id} path escapes repository: {relative}"
                )
        if require_files:
            if not (owner / block.gate.working_directory).is_dir():
                raise PairBlockGateError(
                    f"{block.id} working directory does not exist: "
                    f"{block.gate.working_directory}"
                )
            for relative in (*block.source_paths, *block.test_paths):
                if not (owner / relative).is_file():
                    raise PairBlockGateError(
                        f"{block.id} path does not exist: {relative}"
                    )


def _transitive_dependencies(
    pair_block_id: str, blocks: Mapping[str, PairBlock]
) -> set[str]:
    """Return one PairBlock and every declaration predecessor it names."""

    discovered: set[str] = set()
    pending = [pair_block_id]
    while pending:
        current = pending.pop()
        if current in discovered:
            continue
        discovered.add(current)
        pending.extend(
            dependency
            for dependency in blocks[current].depends_on
            if dependency in blocks
        )
    return discovered


def _directly_affected_blocks(
    accepted: ProjectDeclarations,
    candidate: ProjectDeclarations,
    changed_keys: set[str],
) -> set[str]:
    """Map changed records through requirement dependencies to their owners."""

    affected = {
        key.removeprefix("pair_block:")
        for key in changed_keys
        if key.startswith("pair_block:")
    }
    for declarations in (accepted, candidate):
        requirement_ids = {
            requirement.id
            for requirement in declarations.requirements
            if f"requirement:{requirement.id}" in changed_keys
        }
        for verifier in declarations.verifiers:
            if f"verifier:{verifier.id}" in changed_keys:
                requirement_ids.update(verifier.requirement_ids)
        reverse_dependencies: dict[str, set[str]] = defaultdict(set)
        for requirement in declarations.requirements:
            for dependency in requirement.depends_on:
                reverse_dependencies[dependency].add(requirement.id)
        pending = deque(requirement_ids)
        while pending:
            for dependent in reverse_dependencies[pending.popleft()]:
                if dependent not in requirement_ids:
                    requirement_ids.add(dependent)
                    pending.append(dependent)
        for requirement_id in requirement_ids:
            requirement = declarations.requirements_by_id.get(requirement_id)
            if requirement is not None:
                affected.update(requirement.pair_block_ids)
    return affected
