"""Validate and resolve MANTRA restoration bindings.

The historical archive module authenticates the release pointer and control
files before this module runs. This module does not repeat that cryptographic
work. It joins a required MANTRA destination to the authenticated filesystem
manifest, follows any repository-internal symlink, and joins the resulting
file identity to one authenticated object-manifest row.
"""

from __future__ import annotations

import json
import posixpath
import re
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_REPO_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*$")
_ARCHIVE_ID = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


class RestorationBindingError(ValueError):
    """A restoration record does not satisfy the Phase 0 contract."""


def _require_string(value: object, field: str) -> str:
    """Return a non-empty string or reject the named field."""

    if not isinstance(value, str) or not value:
        raise RestorationBindingError(f"{field} must be a non-empty string")
    return value


def _require_mapping(value: object, field: str) -> Mapping[str, Any]:
    """Return a mapping or reject the named field."""

    if not isinstance(value, Mapping):
        raise RestorationBindingError(f"{field} must be an object")
    return value


def _require_sequence(value: object, field: str) -> Sequence[object]:
    """Return a non-string sequence or reject the named field."""

    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise RestorationBindingError(f"{field} must be an array")
    return value


def _require_integer(value: object, field: str) -> int:
    """Return a non-negative integer or reject the named field."""

    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RestorationBindingError(f"{field} must be a non-negative integer")
    return value


def _require_exact_fields(
    value: Mapping[str, Any],
    expected: set[str],
    context: str,
) -> None:
    """Reject missing or unknown fields in one serialized binding object."""

    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        raise RestorationBindingError(
            f"{context} fields differ: missing={missing}, unknown={unknown}"
        )


def _validate_relative_path(value: object, field: str) -> str:
    """Return one normalized repository-relative POSIX path."""

    text = _require_string(value, field)
    path = PurePosixPath(text)
    if (
        path.is_absolute()
        or text != path.as_posix()
        or path == PurePosixPath(".")
        or ".." in path.parts
        or "\\" in text
    ):
        raise RestorationBindingError(
            f"{field} must be a normalized repository-relative POSIX path"
        )
    return text


def _require_commit(value: object, field: str) -> str:
    """Return one lowercase Git commit hash."""

    text = _require_string(value, field)
    if not _COMMIT.fullmatch(text):
        raise RestorationBindingError(
            f"{field} must be a lowercase 40-character commit hash"
        )
    return text


def _require_sha256(value: object, field: str) -> str:
    """Return one lowercase SHA-256 digest."""

    text = _require_string(value, field)
    if not _SHA256.fullmatch(text):
        raise RestorationBindingError(
            f"{field} must be 64 lowercase hexadecimal characters"
        )
    return text


@dataclass(frozen=True, slots=True)
class HuggingFaceArchiveMember:
    """One content-addressed member of a signed Hugging Face archive."""

    repo_id: str
    control_revision: str
    archive_id: str
    member: str

    def __post_init__(self) -> None:
        """Validate the signed archive-member identity."""

        if not _REPO_ID.fullmatch(_require_string(self.repo_id, "repo_id")):
            raise RestorationBindingError("repo_id must have namespace/name form")
        _require_commit(self.control_revision, "control_revision")
        if not _ARCHIVE_ID.fullmatch(_require_string(self.archive_id, "archive_id")):
            raise RestorationBindingError("archive_id has an invalid form")
        _validate_relative_path(self.member, "member")

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, Any],
    ) -> HuggingFaceArchiveMember:
        """Build one archive-member identity from an exact mapping."""

        _require_exact_fields(
            value,
            {"repo_id", "control_revision", "archive_id", "member"},
            "source",
        )
        return cls(
            repo_id=value["repo_id"],
            control_revision=value["control_revision"],
            archive_id=value["archive_id"],
            member=value["member"],
        )


@dataclass(frozen=True, slots=True)
class RestoredFileIdentity:
    """Expected byte identity of one restored file."""

    byte_count: int
    sha256: str

    def __post_init__(self) -> None:
        """Validate the expected byte count and digest."""

        _require_integer(self.byte_count, "byte_count")
        _require_sha256(self.sha256, "sha256")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> RestoredFileIdentity:
        """Build one expected file identity from an exact mapping."""

        _require_exact_fields(value, {"byte_count", "sha256"}, "expected")
        return cls(
            byte_count=value["byte_count"],
            sha256=value["sha256"],
        )


@dataclass(frozen=True, slots=True)
class RestorationBinding:
    """Archive source and verified destination for one required MANTRA file."""

    destination: str
    source: HuggingFaceArchiveMember
    expected: RestoredFileIdentity

    def __post_init__(self) -> None:
        """Validate the destination and its content-addressed member."""

        _validate_relative_path(self.destination, "destination")
        if not isinstance(self.source, HuggingFaceArchiveMember):
            raise RestorationBindingError("source must be a HuggingFaceArchiveMember")
        if not isinstance(self.expected, RestoredFileIdentity):
            raise RestorationBindingError("expected must be a RestoredFileIdentity")
        required_member = (
            f"objects/sha256/{self.expected.sha256[:2]}/{self.expected.sha256}"
        )
        if self.source.member != required_member:
            raise RestorationBindingError(
                f"member must equal the content-addressed path {required_member}"
            )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> RestorationBinding:
        """Build one restoration binding from an exact mapping."""

        _require_exact_fields(
            value,
            {"destination", "source", "expected"},
            "binding",
        )
        source = value["source"]
        expected = value["expected"]
        if not isinstance(source, Mapping):
            raise RestorationBindingError("source must be an object")
        if not isinstance(expected, Mapping):
            raise RestorationBindingError("expected must be an object")
        return cls(
            destination=value["destination"],
            source=HuggingFaceArchiveMember.from_mapping(source),
            expected=RestoredFileIdentity.from_mapping(expected),
        )


def load_restoration_bindings(path: Path) -> tuple[RestorationBinding, ...]:
    """Load strict binding records from one JSON array."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise RestorationBindingError("binding file must contain a JSON array")
    bindings = []
    for index, row in enumerate(payload):
        if not isinstance(row, Mapping):
            raise RestorationBindingError(f"binding {index} must be an object")
        bindings.append(RestorationBinding.from_mapping(row))
    return tuple(bindings)


def validate_restoration_bindings(
    bindings: Sequence[RestorationBinding],
    *,
    required_restorations: Mapping[str, RestoredFileIdentity],
    allowed_archive_ids: Collection[str],
) -> tuple[RestorationBinding, ...]:
    """Require one canonically ordered binding for every missing file in B."""

    destinations = [binding.destination for binding in bindings]
    if len(destinations) != len(set(destinations)):
        raise RestorationBindingError("binding destinations must be unique")
    if destinations != sorted(destinations):
        raise RestorationBindingError("bindings must be ordered by destination")

    required = set(required_restorations)
    observed = set(destinations)
    if observed != required:
        raise RestorationBindingError(
            "binding coverage differs: "
            f"missing={sorted(required - observed)}, "
            f"unexpected={sorted(observed - required)}"
        )

    for binding in bindings:
        if binding.source.archive_id not in allowed_archive_ids:
            raise RestorationBindingError(
                f"unknown archive_id {binding.source.archive_id}"
            )
        expected = required_restorations[binding.destination]
        if binding.expected != expected:
            raise RestorationBindingError(
                f"file identity differs for {binding.destination}"
            )

    return tuple(bindings)


def _index_filesystem_rows(
    filesystem_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Mapping[str, Any]]:
    """Index authenticated filesystem rows and reject duplicate paths."""

    indexed: dict[str, Mapping[str, Any]] = {}
    for position, row in enumerate(filesystem_rows):
        record = _require_mapping(row, f"filesystem_rows[{position}]")
        path = _validate_relative_path(
            record.get("path"), f"filesystem_rows[{position}].path"
        )
        if path in indexed:
            raise RestorationBindingError(f"duplicate filesystem path {path}")
        indexed[path] = record
    return indexed


def _declared_archive_ids(
    release: Mapping[str, Any],
    archive_index: Mapping[str, Any],
) -> tuple[str, str, frozenset[str]]:
    """Read repository and archive identities from authenticated controls."""

    if release.get("schema_version") != "mantra_reinstantiation_release.v1":
        raise RestorationBindingError("release schema_version is unsupported")
    if release.get("repo_type") != "dataset":
        raise RestorationBindingError("release repo_type must be dataset")
    repo_id = _require_string(release.get("repo_id"), "release.repo_id")
    if not _REPO_ID.fullmatch(repo_id):
        raise RestorationBindingError("release.repo_id must have namespace/name form")
    control_revision = _require_commit(
        release.get("control_revision"), "release.control_revision"
    )
    archive_revisions = _require_mapping(
        release.get("archive_data_revisions"), "release.archive_data_revisions"
    )

    if archive_index.get("schema_version") != "reinstantiation_archive_index.v1":
        raise RestorationBindingError("archive index schema_version is unsupported")
    archive_rows = _require_sequence(
        archive_index.get("archives"), "archive_index.archives"
    )
    archive_ids: set[str] = set()
    for position, archive_row in enumerate(archive_rows):
        record = _require_mapping(archive_row, f"archive_index.archives[{position}]")
        archive_id = _require_string(
            record.get("archive_id"),
            f"archive_index.archives[{position}].archive_id",
        )
        if not _ARCHIVE_ID.fullmatch(archive_id):
            raise RestorationBindingError(f"invalid archive_id {archive_id}")
        if archive_id in archive_ids:
            raise RestorationBindingError(f"duplicate archive_id {archive_id}")
        _require_commit(
            archive_revisions.get(archive_id),
            f"release.archive_data_revisions.{archive_id}",
        )
        archive_ids.add(archive_id)
    if set(archive_revisions) != archive_ids:
        raise RestorationBindingError(
            "release archive revisions differ from the archive index"
        )
    return repo_id, control_revision, frozenset(archive_ids)


def _repository_relative_symlink_target(
    *,
    link_path: str,
    target: object,
    archived_repository_root: PurePosixPath,
) -> str:
    """Resolve one archived symlink without allowing it to leave MANTRA."""

    target_text = _require_string(target, f"symlink target for {link_path}")
    if "\\" in target_text:
        raise RestorationBindingError(f"unsafe symlink target for {link_path}")
    target_path = PurePosixPath(target_text)
    if target_path.is_absolute():
        normalized = PurePosixPath(posixpath.normpath(target_text))
        try:
            relative = normalized.relative_to(archived_repository_root)
        except ValueError as error:
            raise RestorationBindingError(
                f"symlink target escapes archived MANTRA root: {link_path}"
            ) from error
        return _validate_relative_path(relative.as_posix(), "symlink target")

    combined = posixpath.normpath(
        (PurePosixPath(link_path).parent / target_path).as_posix()
    )
    return _validate_relative_path(combined, "symlink target")


def _resolve_file_row(
    *,
    destination: str,
    filesystem_by_path: Mapping[str, Mapping[str, Any]],
    archived_repository_root: PurePosixPath,
) -> Mapping[str, Any]:
    """Follow repository-internal symlinks to one authenticated file row."""

    current = destination
    visited: set[str] = set()
    while True:
        if current in visited:
            raise RestorationBindingError(f"symlink cycle reaches {current}")
        visited.add(current)
        row = filesystem_by_path.get(current)
        if row is None:
            raise RestorationBindingError(f"filesystem path is absent: {current}")
        entry_type = _require_string(
            row.get("entry_type"), f"filesystem entry_type for {current}"
        )
        if entry_type == "file":
            return row
        if entry_type != "symlink":
            raise RestorationBindingError(
                f"restoration destination does not resolve to a file: {current}"
            )
        current = _repository_relative_symlink_target(
            link_path=current,
            target=row.get("symlink_target"),
            archived_repository_root=archived_repository_root,
        )


def _index_object_rows(
    *,
    object_rows_by_archive: Mapping[str, Any],
    declared_archive_ids: Collection[str],
) -> dict[tuple[str, str], Mapping[str, Any]]:
    """Index authenticated object rows by owning archive and digest."""

    indexed: dict[tuple[str, str], Mapping[str, Any]] = {}
    for archive_id, object_rows in object_rows_by_archive.items():
        if not isinstance(archive_id, str):
            raise RestorationBindingError("object archive keys must be strings")
        if archive_id not in declared_archive_ids:
            raise RestorationBindingError(
                f"object manifest names undeclared archive {archive_id}"
            )
        records = _require_sequence(object_rows, f"object_rows_by_archive.{archive_id}")
        for position, object_row in enumerate(records):
            record = _require_mapping(
                object_row, f"object_rows_by_archive.{archive_id}[{position}]"
            )
            row_archive_id = _require_string(
                record.get("archive_id"),
                f"object row archive_id for {archive_id}[{position}]",
            )
            if row_archive_id != archive_id:
                raise RestorationBindingError(
                    f"object row belongs to {row_archive_id}, not {archive_id}"
                )
            digest = _require_sha256(
                record.get("sha256"),
                f"object row sha256 for {archive_id}[{position}]",
            )
            key = (archive_id, digest)
            if key in indexed:
                raise RestorationBindingError(
                    f"duplicate object {digest} in archive {archive_id}"
                )
            indexed[key] = record
    return indexed


def _binding_for_destination(
    *,
    destination: str,
    expected: RestoredFileIdentity,
    repo_id: str,
    control_revision: str,
    declared_archive_ids: Collection[str],
    filesystem_by_path: Mapping[str, Mapping[str, Any]],
    objects_by_archive_and_digest: Mapping[tuple[str, str], Mapping[str, Any]],
    archived_repository_root: PurePosixPath,
) -> RestorationBinding:
    """Join one required destination to its authenticated content object."""

    file_row = _resolve_file_row(
        destination=destination,
        filesystem_by_path=filesystem_by_path,
        archived_repository_root=archived_repository_root,
    )
    file_path = _require_string(file_row.get("path"), "file path")
    file_digest = _require_sha256(file_row.get("sha256"), f"sha256 for {file_path}")
    object_digest = _require_sha256(
        file_row.get("content_object_sha256"),
        f"content_object_sha256 for {file_path}",
    )
    if file_digest != object_digest or file_digest != expected.sha256:
        raise RestorationBindingError(f"file identity differs for {destination}")
    byte_count = _require_integer(
        file_row.get("size_bytes"), f"size_bytes for {file_path}"
    )
    if byte_count != expected.byte_count:
        raise RestorationBindingError(f"file byte count differs for {destination}")

    archive_id = _require_string(
        file_row.get("object_archive_id"), f"object_archive_id for {file_path}"
    )
    if archive_id not in declared_archive_ids:
        raise RestorationBindingError(f"undeclared object archive {archive_id}")
    object_row = objects_by_archive_and_digest.get((archive_id, object_digest))
    if object_row is None:
        raise RestorationBindingError(
            f"object {object_digest} is absent from archive {archive_id}"
        )
    if (
        _require_integer(
            object_row.get("size_bytes"), f"object size_bytes for {object_digest}"
        )
        != expected.byte_count
    ):
        raise RestorationBindingError(f"object byte count differs for {destination}")
    member = _validate_relative_path(
        object_row.get("tar_member"), f"tar_member for {object_digest}"
    )
    return RestorationBinding(
        destination=destination,
        source=HuggingFaceArchiveMember(
            repo_id=repo_id,
            control_revision=control_revision,
            archive_id=archive_id,
            member=member,
        ),
        expected=expected,
    )


def resolve_restoration_bindings_from_control_records(
    *,
    required_restorations: Mapping[str, RestoredFileIdentity],
    release: Mapping[str, Any],
    archive_index: Mapping[str, Any],
    filesystem_rows: Sequence[Mapping[str, Any]],
    object_rows_by_archive: Mapping[str, Sequence[Mapping[str, Any]]],
    archived_repository_root: str,
) -> tuple[RestorationBinding, ...]:
    """Resolve required files through authenticated control records.

    ``release``, ``archive_index``, ``filesystem_rows``, and every object row
    must come from control files authenticated by MANTRA's existing
    ``download_verified_control_package`` path or by an equivalent retained
    signature-and-checksum receipt. The function validates their joins; it
    does not claim to authenticate caller-supplied mappings.
    """

    required = _require_mapping(required_restorations, "required_restorations")
    release_record = _require_mapping(release, "release")
    archive_index_record = _require_mapping(archive_index, "archive_index")
    filesystem_records = _require_sequence(filesystem_rows, "filesystem_rows")
    object_records = _require_mapping(object_rows_by_archive, "object_rows_by_archive")
    validated_requirements: dict[str, RestoredFileIdentity] = {}
    for destination, expected in required.items():
        normalized_destination = _validate_relative_path(destination, "destination")
        if not isinstance(expected, RestoredFileIdentity):
            raise RestorationBindingError(
                f"required identity for {normalized_destination} "
                "must be a RestoredFileIdentity"
            )
        validated_requirements[normalized_destination] = expected

    root_text = _require_string(archived_repository_root, "archived_repository_root")
    root = PurePosixPath(root_text)
    if (
        not root.is_absolute()
        or root_text != root.as_posix()
        or root == PurePosixPath("/")
        or ".." in root.parts
    ):
        raise RestorationBindingError(
            "archived_repository_root must be a normalized absolute POSIX path"
        )

    repo_id, control_revision, declared_archive_ids = _declared_archive_ids(
        release_record, archive_index_record
    )
    filesystem_by_path = _index_filesystem_rows(filesystem_records)
    objects_by_archive_and_digest = _index_object_rows(
        object_rows_by_archive=object_records,
        declared_archive_ids=declared_archive_ids,
    )
    bindings = [
        _binding_for_destination(
            destination=destination,
            expected=expected,
            repo_id=repo_id,
            control_revision=control_revision,
            declared_archive_ids=declared_archive_ids,
            filesystem_by_path=filesystem_by_path,
            objects_by_archive_and_digest=objects_by_archive_and_digest,
            archived_repository_root=root,
        )
        for destination, expected in sorted(validated_requirements.items())
    ]
    return validate_restoration_bindings(
        bindings,
        required_restorations=validated_requirements,
        allowed_archive_ids=declared_archive_ids,
    )
