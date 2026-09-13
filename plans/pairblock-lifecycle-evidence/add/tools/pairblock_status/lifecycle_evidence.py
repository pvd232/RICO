"""Define exact evidence references for native PairBlock lifecycle events.

The module converts JSON-compatible mappings into one of three transition
types. It validates the reference syntax and event-to-evidence relationship.
The controller remains responsible for opening each referenced record and
checking its relationship to the active PairBlock and implementation commit.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Literal, NewType

Sha256 = NewType("Sha256", str)
CodexTaskId = NewType("CodexTaskId", str)
CodexMessageId = NewType("CodexMessageId", str)

_SHA256 = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True, slots=True)
class RepositoryRecordRef:
    """Identify one immutable record stored beneath the RICO repository root.

    Attributes:
        path: POSIX path from the RICO repository root to the record.
        sha256: Lowercase SHA-256 digest of the record's bytes.
    """

    path: PurePosixPath
    sha256: Sha256

    def __post_init__(self) -> None:
        """Reject paths outside the repository and malformed byte identities."""

        if not isinstance(self.path, PurePosixPath):
            raise TypeError("record path must be a PurePosixPath")
        if (
            self.path.is_absolute()
            or self.path == PurePosixPath(".")
            or ".." in self.path.parts
        ):
            raise ValueError("record path must stay beneath the repo root")
        if not isinstance(self.sha256, str) or _SHA256.fullmatch(self.sha256) is None:
            raise ValueError("record sha256 must contain 64 lowercase hex characters")


@dataclass(frozen=True, slots=True)
class UserApprovalRef:
    """Identify the Codex task message cited for one approval transition.

    Attributes:
        task_id: Codex task containing the user's approval message.
        message_id: Message within that task cited by the lifecycle receipt.
        kind: Serialized discriminator for user-approval evidence.
    """

    task_id: CodexTaskId
    message_id: CodexMessageId
    kind: Literal["user_approval"] = field(default="user_approval", init=False)

    def __post_init__(self) -> None:
        """Require both external identifiers used to locate the approval."""

        if not isinstance(self.task_id, str) or not isinstance(self.message_id, str):
            raise TypeError("approval task_id and message_id must be strings")
        if not self.task_id.strip() or not self.message_id.strip():
            raise ValueError("approval task_id and message_id must not be empty")
        if (
            self.task_id.strip() != self.task_id
            or self.message_id.strip() != self.message_id
        ):
            raise ValueError("approval task_id and message_id must be canonical")


@dataclass(frozen=True, slots=True)
class ImplementationReviewRef:
    """Identify the retained code-review record used by an accept transition.

    Attributes:
        receipt: Path and byte identity of the implementation-review record.
        kind: Serialized discriminator for implementation-review evidence.
    """

    receipt: RepositoryRecordRef
    kind: Literal["implementation_review"] = field(
        default="implementation_review",
        init=False,
    )

    def __post_init__(self) -> None:
        """Require the immutable record identity consumed by review validation."""

        if not isinstance(self.receipt, RepositoryRecordRef):
            raise TypeError("implementation review receipt must be RepositoryRecordRef")


@dataclass(frozen=True, slots=True)
class ViperRegistrationRef:
    """Identify the retained VIPER record used by a register transition.

    Attributes:
        receipt: Path and byte identity of the PairBlock registration record.
        kind: Serialized discriminator for VIPER-registration evidence.
    """

    receipt: RepositoryRecordRef
    kind: Literal["viper_registration"] = field(
        default="viper_registration",
        init=False,
    )

    def __post_init__(self) -> None:
        """Require the immutable record identity consumed by VIPER validation."""

        if not isinstance(self.receipt, RepositoryRecordRef):
            raise TypeError("VIPER registration receipt must be RepositoryRecordRef")


type LifecycleEvidenceRef = (
    UserApprovalRef | ImplementationReviewRef | ViperRegistrationRef
)


@dataclass(frozen=True, slots=True)
class ApprovalTransition:
    """Pair an approve event with the only evidence type that can authorize it.

    Attributes:
        evidence: Codex task message cited as the user's approval.
        event: Serialized discriminator for the approve transition.
    """

    evidence: UserApprovalRef
    event: Literal["approve"] = field(default="approve", init=False)

    def __post_init__(self) -> None:
        """Reject direct construction with another event's evidence type."""

        if not isinstance(self.evidence, UserApprovalRef):
            raise TypeError("approve requires UserApprovalRef")


@dataclass(frozen=True, slots=True)
class AcceptanceTransition:
    """Pair an accept event with the implementation review that authorizes it.

    Attributes:
        evidence: Retained review record for the accepted implementation.
        event: Serialized discriminator for the accept transition.
    """

    evidence: ImplementationReviewRef
    event: Literal["accept"] = field(default="accept", init=False)

    def __post_init__(self) -> None:
        """Reject direct construction with another event's evidence type."""

        if not isinstance(self.evidence, ImplementationReviewRef):
            raise TypeError("accept requires ImplementationReviewRef")


@dataclass(frozen=True, slots=True)
class RegistrationTransition:
    """Pair a register event with the VIPER record that authorizes completion.
    Attributes:
        evidence: Retained record that binds VIPER verification to the PairBlock.
        event: Serialized discriminator for the register transition.
    """

    evidence: ViperRegistrationRef
    event: Literal["register"] = field(default="register", init=False)

    def __post_init__(self) -> None:
        """Reject direct construction with another event's evidence type."""

        if not isinstance(self.evidence, ViperRegistrationRef):
            raise TypeError("register requires ViperRegistrationRef")


type NativeLifecycleTransition = (
    ApprovalTransition | AcceptanceTransition | RegistrationTransition
)


def parse_lifecycle_transition(value: object) -> NativeLifecycleTransition:
    """Parse one exact event-specific transition from JSON-compatible data."""

    transition = _require_mapping(value, "transition")
    _require_exact_fields(transition, {"event", "evidence"}, "transition")
    event = _require_string(transition["event"], "transition.event")
    evidence = _require_mapping(transition["evidence"], "transition.evidence")

    if event == "approve":
        return ApprovalTransition(_parse_user_approval(evidence))
    if event == "accept":
        return AcceptanceTransition(_parse_implementation_review(evidence))
    if event == "register":
        return RegistrationTransition(_parse_viper_registration(evidence))
    raise ValueError(f"unsupported native lifecycle event: {event}")


def lifecycle_transition_mapping(
    transition: NativeLifecycleTransition,
) -> dict[str, object]:
    """Return the canonical JSON-compatible mapping for one transition."""

    if isinstance(transition, ApprovalTransition):
        evidence: dict[str, object] = {
            "kind": transition.evidence.kind,
            "task_id": transition.evidence.task_id,
            "message_id": transition.evidence.message_id,
        }
    else:
        evidence = {
            "kind": transition.evidence.kind,
            "receipt": _repository_record_mapping(transition.evidence.receipt),
        }
    return {"event": transition.event, "evidence": evidence}


def _parse_user_approval(value: Mapping[str, object]) -> UserApprovalRef:
    """Parse one user-approval reference with its exact persisted fields."""

    _require_kind(value.get("kind"), "user_approval")
    _require_exact_fields(
        value,
        {"kind", "task_id", "message_id"},
        "user approval evidence",
    )
    return UserApprovalRef(
        task_id=CodexTaskId(_require_string(value["task_id"], "task_id")),
        message_id=CodexMessageId(_require_string(value["message_id"], "message_id")),
    )


def _parse_implementation_review(
    value: Mapping[str, object],
) -> ImplementationReviewRef:
    """Parse one implementation-review reference and its nested record identity."""

    _require_kind(value.get("kind"), "implementation_review")
    _require_exact_fields(
        value,
        {"kind", "receipt"},
        "implementation review evidence",
    )
    return ImplementationReviewRef(receipt=_parse_repository_record(value["receipt"]))


def _parse_viper_registration(
    value: Mapping[str, object],
) -> ViperRegistrationRef:
    """Parse one VIPER-registration reference and its nested record identity."""

    _require_kind(value.get("kind"), "viper_registration")
    _require_exact_fields(
        value,
        {"kind", "receipt"},
        "VIPER registration evidence",
    )
    return ViperRegistrationRef(receipt=_parse_repository_record(value["receipt"]))


def _parse_repository_record(value: object) -> RepositoryRecordRef:
    """Parse one repository-relative record path and byte identity."""

    record = _require_mapping(value, "repository record")
    _require_exact_fields(record, {"path", "sha256"}, "repository record")
    path = _require_string(record["path"], "repository record path")
    sha256 = _require_string(record["sha256"], "repository record sha256")
    parsed_path = PurePosixPath(path)
    if parsed_path.as_posix() != path:
        raise ValueError("repository record path must use canonical POSIX syntax")
    return RepositoryRecordRef(parsed_path, Sha256(sha256))


def _repository_record_mapping(reference: RepositoryRecordRef) -> dict[str, str]:
    """Return one record reference in its persisted JSON shape."""

    return {"path": reference.path.as_posix(), "sha256": reference.sha256}


def _require_mapping(value: object, label: str) -> Mapping[str, object]:
    """Return a string-keyed mapping or reject the named persisted object."""

    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise ValueError(f"{label} must be a string-keyed mapping")
    return value


def _require_exact_fields(
    value: Mapping[str, object],
    expected: set[str],
    label: str,
) -> None:
    """Reject missing or unknown fields in one persisted object."""

    if set(value) != expected:
        raise ValueError(f"{label} fields differ: expected {sorted(expected)}")


def _require_string(value: object, label: str) -> str:
    """Return one nonempty string or reject the named field."""

    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")
    return value


def _require_kind(value: object, expected: str) -> None:
    """Require the discriminator selected by the enclosing lifecycle event."""

    if value != expected:
        raise ValueError(f"evidence kind must be {expected}")
