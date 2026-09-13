"""Define exact evidence references for native PairBlock lifecycle events.

Pydantic validates persisted mappings as one of three event-specific transition
types. The controller opens each referenced record and checks its relationship
to the active PairBlock and implementation commit.
"""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Annotated, Literal, NewType

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    TypeAdapter,
    field_validator,
)

Sha256 = NewType("Sha256", str)
CodexTaskId = NewType("CodexTaskId", str)
CodexMessageId = NewType("CodexMessageId", str)

_Sha256Field = Annotated[
    Sha256,
    StringConstraints(pattern=r"^[0-9a-f]{64}$"),
]


class EvidenceModel(BaseModel):
    """Reject unknown fields and mutation in every persisted evidence record."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class RepositoryRecordRef(EvidenceModel):
    """Identify one immutable record stored beneath the RICO repository root."""

    path: PurePosixPath = Field(
        description="POSIX path from the RICO repository root to the record."
    )
    sha256: _Sha256Field = Field(
        description="Lowercase SHA-256 digest of the record bytes."
    )

    @field_validator("path", mode="before")
    @classmethod
    def parse_canonical_path(cls, value: object) -> PurePosixPath:
        """Convert canonical persisted text into a repository-relative path."""

        if isinstance(value, PurePosixPath):
            return value
        if not isinstance(value, str):
            raise TypeError("record path must be a POSIX path")
        path = PurePosixPath(value)
        if path.as_posix() != value:
            raise ValueError("repository record path must use canonical POSIX syntax")
        return path

    @field_validator("path")
    @classmethod
    def require_repository_relative_path(
        cls,
        path: PurePosixPath,
    ) -> PurePosixPath:
        """Reject record paths that escape or identify the repository root."""

        if path.is_absolute() or path == PurePosixPath(".") or ".." in path.parts:
            raise ValueError("record path must stay beneath the repo root")
        return path


class UserApprovalRef(EvidenceModel):
    """Identify the Codex task message cited for one approval transition."""

    kind: Literal["user_approval"] = Field(
        description="Discriminator for evidence supplied by a user approval message.",
    )
    task_id: CodexTaskId = Field(
        description="Codex task containing the approval message."
    )
    message_id: CodexMessageId = Field(
        description="Message within the Codex task that records approval."
    )

    @field_validator("task_id", "message_id")
    @classmethod
    def require_canonical_identifier(cls, value: str) -> str:
        """Require a nonempty external identifier with no surrounding whitespace."""

        if not value or value.strip() != value:
            raise ValueError("approval identifiers must be nonempty and canonical")
        return value


class ImplementationReviewRef(EvidenceModel):
    """Identify the retained code-review record for an accept transition."""

    kind: Literal["implementation_review"] = Field(
        description="Discriminator for retained implementation-review evidence.",
    )
    receipt: RepositoryRecordRef = Field(
        description="Repository record containing the accepted implementation review."
    )


class ViperRegistrationRef(EvidenceModel):
    """Identify the retained VIPER record for a register transition."""

    kind: Literal["viper_registration"] = Field(
        description="Discriminator for retained VIPER-registration evidence.",
    )
    receipt: RepositoryRecordRef = Field(
        description="Repository record binding VIPER verification to the PairBlock."
    )


type LifecycleEvidenceRef = Annotated[
    UserApprovalRef | ImplementationReviewRef | ViperRegistrationRef,
    Field(discriminator="kind"),
]


class ApprovalTransition(EvidenceModel):
    """Pair an approve event with the user message that authorizes it."""

    event: Literal["approve"] = Field(
        description="Lifecycle event authorized by this transition.",
    )
    evidence: UserApprovalRef = Field(
        description="Codex task message cited as the user's approval."
    )


class AcceptanceTransition(EvidenceModel):
    """Pair an accept event with its retained implementation review."""

    event: Literal["accept"] = Field(
        description="Lifecycle event authorized by this transition.",
    )
    evidence: ImplementationReviewRef = Field(
        description="Retained review record for the accepted implementation."
    )


class RegistrationTransition(EvidenceModel):
    """Pair a register event with its retained VIPER record."""

    event: Literal["register"] = Field(
        description="Lifecycle event authorized by this transition.",
    )
    evidence: ViperRegistrationRef = Field(
        description="Retained VIPER record that authorizes completion."
    )


type NativeLifecycleTransition = Annotated[
    ApprovalTransition | AcceptanceTransition | RegistrationTransition,
    Field(discriminator="event"),
]

_TRANSITION_ADAPTER = TypeAdapter(NativeLifecycleTransition)


def parse_lifecycle_transition(value: object) -> NativeLifecycleTransition:
    """Validate a persisted mapping as one event-specific transition."""

    return _TRANSITION_ADAPTER.validate_python(value)


def lifecycle_transition_mapping(
    transition: NativeLifecycleTransition,
) -> dict[str, object]:
    """Return the canonical JSON-compatible mapping for one transition."""

    return transition.model_dump(mode="json")
