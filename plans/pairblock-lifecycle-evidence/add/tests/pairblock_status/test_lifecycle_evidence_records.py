"""Verify exact parsing of event-specific native lifecycle evidence."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import cast

import pytest

from tools.pairblock_status.lifecycle_evidence import (
    AcceptanceTransition,
    ApprovalTransition,
    CodexMessageId,
    CodexTaskId,
    ImplementationReviewRef,
    RegistrationTransition,
    RepositoryRecordRef,
    Sha256,
    UserApprovalRef,
    ViperRegistrationRef,
    lifecycle_transition_mapping,
    parse_lifecycle_transition,
)

DIGEST = Sha256("a" * 64)
RECORD = RepositoryRecordRef(PurePosixPath("evidence/record.json"), DIGEST)


@pytest.mark.parametrize(
    "transition",
    [
        ApprovalTransition(
            UserApprovalRef(
                task_id=CodexTaskId("task-123"),
                message_id=CodexMessageId("msg_456"),
            )
        ),
        AcceptanceTransition(ImplementationReviewRef(RECORD)),
        RegistrationTransition(ViperRegistrationRef(RECORD)),
    ],
)
def test_transition_round_trip_preserves_event_specific_type(
    transition: ApprovalTransition | AcceptanceTransition | RegistrationTransition,
) -> None:
    """Round-trip each event without losing its evidence discriminator."""

    serialized = lifecycle_transition_mapping(transition)

    assert parse_lifecycle_transition(serialized) == transition


@pytest.mark.parametrize(
    ("event", "kind"),
    [
        ("approve", "implementation_review"),
        ("accept", "viper_registration"),
        ("register", "implementation_review"),
    ],
)
def test_event_rejects_another_event_evidence_type(event: str, kind: str) -> None:
    """Reject a valid evidence shape when its discriminator belongs elsewhere."""

    serialized = {
        "event": event,
        "evidence": {
            "kind": kind,
            "receipt": {
                "path": "evidence/record.json",
                "sha256": "a" * 64,
            },
        },
    }

    with pytest.raises(ValueError, match="evidence kind"):
        parse_lifecycle_transition(serialized)


def test_transition_constructor_rejects_another_event_evidence_type() -> None:
    """Enforce the evidence relationship even when a caller bypasses parsing."""

    wrong_evidence = cast(UserApprovalRef, ImplementationReviewRef(RECORD))

    with pytest.raises(TypeError, match="approve requires UserApprovalRef"):
        ApprovalTransition(wrong_evidence)


def test_record_constructor_rejects_untyped_runtime_values() -> None:
    """Reject caller-supplied values that bypass the parser's type narrowing."""

    wrong_path = cast(PurePosixPath, "evidence/record.json")
    wrong_digest = cast(Sha256, True)

    with pytest.raises(TypeError, match="PurePosixPath"):
        RepositoryRecordRef(wrong_path, DIGEST)
    with pytest.raises(ValueError, match="64 lowercase hex"):
        RepositoryRecordRef(PurePosixPath("evidence/record.json"), wrong_digest)


def test_typed_evidence_rejects_an_untyped_record_reference() -> None:
    """Reject direct evidence construction that bypasses record parsing."""

    wrong_record = cast(RepositoryRecordRef, "evidence/record.json")

    with pytest.raises(TypeError, match="implementation review receipt"):
        ImplementationReviewRef(wrong_record)
    with pytest.raises(TypeError, match="VIPER registration receipt"):
        ViperRegistrationRef(wrong_record)


def test_user_approval_requires_canonical_external_identifiers() -> None:
    """Reject approval identifiers whose whitespace changes their identity."""

    with pytest.raises(ValueError, match="canonical"):
        UserApprovalRef(CodexTaskId(" task-123"), CodexMessageId("msg_456"))


@pytest.mark.parametrize(
    "serialized",
    [
        {
            "event": "approve",
            "evidence": {
                "kind": "user_approval",
                "task_id": "task-123",
                "message_id": "msg_456",
                "extra": True,
            },
        },
        {
            "event": "accept",
            "evidence": {
                "kind": "implementation_review",
                "receipt": "evidence/review.json",
            },
        },
        {
            "event": "register",
            "evidence": {
                "kind": "viper_registration",
                "receipt": {
                    "path": "evidence/registration.json",
                    "sha256": True,
                },
            },
        },
        {
            "event": "accept",
            "evidence": {
                "kind": "implementation_review",
                "receipt": {
                    "path": "evidence//review.json",
                    "sha256": "a" * 64,
                },
            },
        },
    ],
)
def test_parser_rejects_unknown_fields_and_invalid_nested_values(
    serialized: object,
) -> None:
    """Reject evidence that cannot satisfy its exact persisted schema."""

    with pytest.raises(ValueError):
        parse_lifecycle_transition(serialized)


@pytest.mark.parametrize(
    "path",
    [
        PurePosixPath("/tmp/record.json"),
        PurePosixPath("../record.json"),
        PurePosixPath("."),
    ],
)
def test_repository_record_stays_beneath_repository_root(
    path: PurePosixPath,
) -> None:
    """Reject paths that fail to identify one repository-owned record."""

    with pytest.raises(ValueError, match="repository root"):
        RepositoryRecordRef(path, DIGEST)


@pytest.mark.parametrize("sha256", ["A" * 64, "a" * 63, "not-a-digest"])
def test_repository_record_requires_exact_sha256(sha256: str) -> None:
    """Reject malformed digests before a record can authorize a transition."""

    with pytest.raises(ValueError, match="64 lowercase hex"):
        RepositoryRecordRef(
            PurePosixPath("evidence/record.json"),
            Sha256(sha256),
        )
