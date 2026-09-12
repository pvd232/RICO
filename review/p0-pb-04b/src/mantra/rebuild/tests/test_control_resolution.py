"""Contract tests for path resolution through authenticated archive controls."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

import pytest
from mantra.rebuild.restoration import (
    RestorationBindingError,
    RestoredFileIdentity,
    resolve_restoration_bindings_from_control_records,
)

REPO_ID = "pvd232/k562-gwps-raw-v18"
CONTROL_REVISION = "a" * 40
DATA_REVISION = "b" * 40
ARCHIVE_ID = "historical_and_shared_experiments"
ARCHIVED_ROOT = "/home/machina/MANTRA"
DIGEST = "c" * 64
BYTE_COUNT = 64_472_752
DESTINATION = "experiments/current/input.npz"
TARGET = "experiments/historical/input.npz"


def control_records() -> dict[str, object]:
    """Build the smallest internally linked authenticated-control fixture."""

    release = {
        "schema_version": "mantra_reinstantiation_release.v1",
        "repo_id": REPO_ID,
        "repo_type": "dataset",
        "control_revision": CONTROL_REVISION,
        "archive_data_revisions": {ARCHIVE_ID: DATA_REVISION},
    }
    archive_index = {
        "schema_version": "reinstantiation_archive_index.v1",
        "archives": [{"archive_id": ARCHIVE_ID}],
    }
    filesystem_rows = [
        {
            "path": DESTINATION,
            "entry_type": "symlink",
            "symlink_target": f"{ARCHIVED_ROOT}/{TARGET}",
        },
        {
            "path": TARGET,
            "entry_type": "file",
            "sha256": DIGEST,
            "content_object_sha256": DIGEST,
            "size_bytes": BYTE_COUNT,
            "object_archive_id": ARCHIVE_ID,
        },
    ]
    object_rows_by_archive = {
        ARCHIVE_ID: [
            {
                "archive_id": ARCHIVE_ID,
                "sha256": DIGEST,
                "size_bytes": BYTE_COUNT,
                "tar_member": f"objects/sha256/{DIGEST[:2]}/{DIGEST}",
            }
        ]
    }
    return {
        "release": release,
        "archive_index": archive_index,
        "filesystem_rows": filesystem_rows,
        "object_rows_by_archive": object_rows_by_archive,
    }


def resolve(records: dict[str, object] | None = None):
    """Resolve the approved destination with one optionally changed fixture."""

    controls = control_records() if records is None else records
    return resolve_restoration_bindings_from_control_records(
        required_restorations={
            DESTINATION: RestoredFileIdentity(
                byte_count=BYTE_COUNT,
                sha256=DIGEST,
            )
        },
        archived_repository_root=ARCHIVED_ROOT,
        **controls,
    )


def test_absolute_historical_symlink_resolves_to_owning_object_archive() -> None:
    """Preserve the requested destination while following its archived target."""

    binding = resolve()[0]

    assert binding.destination == DESTINATION
    assert binding.source.repo_id == REPO_ID
    assert binding.source.control_revision == CONTROL_REVISION
    assert binding.source.archive_id == ARCHIVE_ID
    assert binding.source.member == f"objects/sha256/{DIGEST[:2]}/{DIGEST}"
    assert binding.expected == RestoredFileIdentity(BYTE_COUNT, DIGEST)


def test_regular_file_uses_object_archive_not_path_archive() -> None:
    """Use object_archive_id when the path and object archives differ."""

    records = control_records()
    records["filesystem_rows"] = [
        {
            "path": DESTINATION,
            "entry_type": "file",
            "archive_id": "sota_reproducer",
            "sha256": DIGEST,
            "content_object_sha256": DIGEST,
            "size_bytes": BYTE_COUNT,
            "object_archive_id": ARCHIVE_ID,
        }
    ]

    assert resolve(records)[0].source.archive_id == ARCHIVE_ID


def test_relative_symlink_resolves_beneath_its_parent() -> None:
    """Resolve a normalized relative link inside the archived repository."""

    records = control_records()
    records["filesystem_rows"][0]["symlink_target"] = "../historical/input.npz"

    assert resolve(records)[0].expected.sha256 == DIGEST


def test_absent_destination_is_rejected() -> None:
    """Reject a required path omitted from the filesystem manifest."""

    records = control_records()
    records["filesystem_rows"] = records["filesystem_rows"][1:]

    with pytest.raises(RestorationBindingError, match="filesystem path is absent"):
        resolve(records)


def test_duplicate_filesystem_path_is_rejected() -> None:
    """Reject ambiguous path identity anywhere in the supplied manifest."""

    records = control_records()
    records["filesystem_rows"].append(deepcopy(records["filesystem_rows"][0]))

    with pytest.raises(RestorationBindingError, match="duplicate filesystem path"):
        resolve(records)


@pytest.mark.parametrize(
    "target",
    ["/home/machina/outside/input.npz", "../../outside/input.npz"],
)
def test_symlink_cannot_escape_archived_repository(target: str) -> None:
    """Reject absolute and relative links that leave archived MANTRA."""

    records = control_records()
    records["filesystem_rows"][0]["symlink_target"] = target

    with pytest.raises(RestorationBindingError):
        resolve(records)


def test_symlink_cycle_is_rejected() -> None:
    """Reject a link chain that returns to a previously visited path."""

    records = control_records()
    records["filesystem_rows"][1] = {
        "path": TARGET,
        "entry_type": "symlink",
        "symlink_target": f"{ARCHIVED_ROOT}/{DESTINATION}",
    }

    with pytest.raises(RestorationBindingError, match="symlink cycle"):
        resolve(records)


def test_missing_object_row_is_rejected() -> None:
    """Reject a file whose owning object manifest omits its digest."""

    records = control_records()
    records["object_rows_by_archive"][ARCHIVE_ID] = []

    with pytest.raises(RestorationBindingError, match="is absent from archive"):
        resolve(records)


def test_duplicate_object_row_is_rejected() -> None:
    """Reject ambiguous object identity inside one owning archive."""

    records = control_records()
    object_row = records["object_rows_by_archive"][ARCHIVE_ID][0]
    records["object_rows_by_archive"][ARCHIVE_ID].append(deepcopy(object_row))

    with pytest.raises(RestorationBindingError, match="duplicate object"):
        resolve(records)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("sha256", "d" * 64, "file identity differs"),
        ("content_object_sha256", "d" * 64, "file identity differs"),
        ("size_bytes", BYTE_COUNT + 1, "file byte count differs"),
    ],
)
def test_file_identity_must_match_required_identity(
    field: str,
    value: object,
    message: str,
) -> None:
    """Reject any filesystem identity field that differs from graph B."""

    records = control_records()
    records["filesystem_rows"][1][field] = value

    with pytest.raises(RestorationBindingError, match=message):
        resolve(records)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("size_bytes", BYTE_COUNT + 1, "object byte count differs"),
        ("tar_member", "objects/sha256/cc/wrong", "member must equal"),
    ],
)
def test_object_identity_must_match_file_identity(
    field: str,
    value: object,
    message: str,
) -> None:
    """Reject an object row that does not identify the required bytes."""

    records = control_records()
    records["object_rows_by_archive"][ARCHIVE_ID][0][field] = value

    with pytest.raises(RestorationBindingError, match=message):
        resolve(records)


def test_object_archive_must_be_declared() -> None:
    """Reject a filesystem row that names no signed archive-index entry."""

    records = control_records()
    records["filesystem_rows"][1]["object_archive_id"] = "unknown_archive"

    with pytest.raises(RestorationBindingError, match="undeclared object archive"):
        resolve(records)


def test_archive_index_rejects_duplicate_archive_ids() -> None:
    """Reject two signed archive rows that claim the same archive identity."""

    records = control_records()
    archive_row = records["archive_index"]["archives"][0]
    records["archive_index"]["archives"].append(deepcopy(archive_row))

    with pytest.raises(RestorationBindingError, match="duplicate archive_id"):
        resolve(records)


def test_release_and_archive_index_must_name_the_same_archives() -> None:
    """Reject a release whose data revisions do not close over the index."""

    records = control_records()
    records["release"]["archive_data_revisions"]["extra_archive"] = DATA_REVISION

    with pytest.raises(RestorationBindingError, match="revisions differ"):
        resolve(records)


def test_control_revision_must_be_a_commit() -> None:
    """Reject a release that cannot pin one authenticated control commit."""

    records = control_records()
    records["release"]["control_revision"] = "main"

    with pytest.raises(RestorationBindingError, match="40-character commit"):
        resolve(records)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("release", [], "release must be an object"),
        ("archive_index", [], "archive_index must be an object"),
        ("filesystem_rows", {}, "filesystem_rows must be an array"),
        ("object_rows_by_archive", [], "object_rows_by_archive must be an object"),
    ],
)
def test_public_control_inputs_stay_inside_contract_error_boundary(
    field: str,
    value: object,
    message: str,
) -> None:
    """Reject malformed nested controls with the declared exception type."""

    records = control_records()
    records[field] = value

    with pytest.raises(RestorationBindingError, match=message):
        resolve(records)


def test_required_identity_stays_inside_contract_error_boundary() -> None:
    """Reject a malformed required identity before reading its fields."""

    records = control_records()

    with pytest.raises(RestorationBindingError, match="RestoredFileIdentity"):
        resolve_restoration_bindings_from_control_records(
            required_restorations={DESTINATION: {}},
            archived_repository_root=ARCHIVED_ROOT,
            **records,
        )


def test_restored_identity_remains_immutable() -> None:
    """Keep the identity value immutable after resolution."""

    identity = resolve()[0].expected

    assert replace(identity, byte_count=identity.byte_count) == identity
    with pytest.raises(AttributeError):
        identity.byte_count = 0
