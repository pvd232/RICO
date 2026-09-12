"""Validated bindings from MANTRA paths to archived content objects."""

from __future__ import annotations

import json
import re
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_REPO_ID = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*$"
)
_ARCHIVE_ID = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


class RestorationBindingError(ValueError):
    """A restoration binding does not satisfy the Phase 0 contract."""


def _require_string(value: object, field: str) -> str:
    """Return a non-empty string or reject the named field."""

    if not isinstance(value, str) or not value:
        raise RestorationBindingError(f"{field} must be a non-empty string")
    return value


def _require_exact_fields(
    value: Mapping[str, Any],
    expected: set[str],
    context: str,
) -> None:
    """Reject missing or unknown fields in one serialized object."""

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
        if not _COMMIT.fullmatch(
            _require_string(self.control_revision, "control_revision")
        ):
            raise RestorationBindingError(
                "control_revision must be a lowercase 40-character commit hash"
            )
        if not _ARCHIVE_ID.fullmatch(
            _require_string(self.archive_id, "archive_id")
        ):
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

        if isinstance(self.byte_count, bool) or not isinstance(self.byte_count, int):
            raise RestorationBindingError("byte_count must be an integer")
        if self.byte_count < 0:
            raise RestorationBindingError("byte_count cannot be negative")
        if not _SHA256.fullmatch(_require_string(self.sha256, "sha256")):
            raise RestorationBindingError(
                "sha256 must be 64 lowercase hexadecimal characters"
            )

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
            raise RestorationBindingError(
                "source must be a HuggingFaceArchiveMember"
            )
        if not isinstance(self.expected, RestoredFileIdentity):
            raise RestorationBindingError(
                "expected must be a RestoredFileIdentity"
            )
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
