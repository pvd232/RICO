"""Contract tests for strict Phase 0 restoration bindings."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

from mantra.rebuild.restoration import (
    HuggingFaceArchiveMember,
    RestorationBinding,
    RestorationBindingError,
    RestoredFileIdentity,
    load_restoration_bindings,
    validate_restoration_bindings,
)

DIGEST = "a" * 64
REVISION = "b" * 40
DESTINATION = "experiments/example/input.npz"
ALLOWED_ARCHIVES = {"sota_reproducer"}


def valid_binding() -> RestorationBinding:
    """Build one binding that satisfies every local field invariant."""

    identity = RestoredFileIdentity(byte_count=123, sha256=DIGEST)
    return RestorationBinding(
        destination=DESTINATION,
        source=HuggingFaceArchiveMember(
            repo_id="pvd232/k562-gwps-raw-v18",
            control_revision=REVISION,
            archive_id="sota_reproducer",
            member=f"objects/sha256/{DIGEST[:2]}/{DIGEST}",
        ),
        expected=identity,
    )


@pytest.mark.parametrize(
    "destination",
    ["/tmp/input.npz", "../input.npz", "experiments//input.npz"],
)
def test_destination_cannot_escape_or_change_form(destination: str) -> None:
    """Reject destinations outside normalized MANTRA-relative paths."""

    with pytest.raises(RestorationBindingError):
        replace(valid_binding(), destination=destination)


def test_negative_byte_count_is_rejected() -> None:
    """Reject a file identity with a negative byte count."""

    with pytest.raises(RestorationBindingError):
        RestoredFileIdentity(byte_count=-1, sha256=DIGEST)


@pytest.mark.parametrize("digest", ["A" * 64, "a" * 63, "not-a-digest"])
def test_malformed_digest_is_rejected(digest: str) -> None:
    """Reject digests outside lowercase SHA-256 form."""

    with pytest.raises(RestorationBindingError):
        RestoredFileIdentity(byte_count=1, sha256=digest)


def test_member_must_match_content_identity() -> None:
    """Require the archive member name to encode the expected digest."""

    binding = valid_binding()
    bad_source = replace(binding.source, member="objects/sha256/aa/wrong")
    with pytest.raises(RestorationBindingError):
        replace(binding, source=bad_source)


@pytest.mark.parametrize(
    ("field", "value"),
    [("source", {}), ("expected", {})],
)
def test_binding_rejects_invalid_nested_type(field: str, value: object) -> None:
    """Keep invalid nested values inside the binding error boundary."""

    with pytest.raises(RestorationBindingError, match=rf"^{field} must be"):
        replace(valid_binding(), **{field: value})


def test_duplicate_destination_is_rejected() -> None:
    """Reject two bindings for the same canonical destination."""

    binding = valid_binding()
    with pytest.raises(RestorationBindingError):
        validate_restoration_bindings(
            [binding, binding],
            required_restorations={DESTINATION: binding.expected},
            allowed_archive_ids=ALLOWED_ARCHIVES,
        )


def test_missing_and_unexpected_destinations_are_rejected() -> None:
    """Require exact coverage of the approved missing-file set."""

    binding = valid_binding()
    with pytest.raises(RestorationBindingError):
        validate_restoration_bindings(
            [binding],
            required_restorations={
                "experiments/another/input.npz": binding.expected
            },
            allowed_archive_ids=ALLOWED_ARCHIVES,
        )


def test_bindings_must_be_ordered() -> None:
    """Require deterministic destination order in the persisted binding set."""

    first = valid_binding()
    second = replace(first, destination="experiments/z/input.npz")
    with pytest.raises(RestorationBindingError):
        validate_restoration_bindings(
            [second, first],
            required_restorations={
                first.destination: first.expected,
                second.destination: second.expected,
            },
            allowed_archive_ids=ALLOWED_ARCHIVES,
        )


def test_unknown_archive_is_rejected() -> None:
    """Reject an archive absent from the signed control package."""

    binding = valid_binding()
    with pytest.raises(RestorationBindingError):
        validate_restoration_bindings(
            [binding],
            required_restorations={DESTINATION: binding.expected},
            allowed_archive_ids={"historical_and_shared_experiments"},
        )


def test_valid_binding_set_is_returned_unchanged() -> None:
    """Accept one ordered binding covering the approved restoration set."""

    binding = valid_binding()
    assert validate_restoration_bindings(
        [binding],
        required_restorations={DESTINATION: binding.expected},
        allowed_archive_ids=ALLOWED_ARCHIVES,
    ) == (binding,)


def test_loader_rejects_unknown_fields(tmp_path) -> None:
    """Reject persisted binding objects with undeclared fields."""

    binding = valid_binding()
    payload = {
        "destination": binding.destination,
        "source": {
            "repo_id": binding.source.repo_id,
            "control_revision": binding.source.control_revision,
            "archive_id": binding.source.archive_id,
            "member": binding.source.member,
        },
        "expected": {
            "byte_count": binding.expected.byte_count,
            "sha256": binding.expected.sha256,
        },
        "status": "invented",
    }
    path = tmp_path / "bindings.json"
    path.write_text(json.dumps([payload]), encoding="utf-8")

    with pytest.raises(RestorationBindingError):
        load_restoration_bindings(path)


def test_incomplete_source_identity_is_rejected() -> None:
    """Reject a source identity missing its archive identifier."""

    binding = valid_binding()
    with pytest.raises(RestorationBindingError):
        HuggingFaceArchiveMember.from_mapping(
            {
                "repo_id": binding.source.repo_id,
                "control_revision": binding.source.control_revision,
                "member": binding.source.member,
            }
        )
