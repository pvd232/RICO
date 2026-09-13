"""Verify idempotent recovery of interrupted projection transactions."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.pairblock_status import projection_transaction


@pytest.mark.parametrize("failed_write", [1, 2, 3])
def test_prepared_projection_recovers_after_each_target_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failed_write: int,
) -> None:
    """Resume after either document write or the receipt commit write."""

    repository = tmp_path / "repository"
    repository.mkdir()
    receipt = repository / "evidence/receipts/result.json"
    contract = repository / "docs/contract.md"
    checklist = repository / "docs/checklist.md"
    journal = projection_transaction.prepare_projection(
        repository,
        "transition",
        receipt_path=receipt,
        receipt=b'{"result": "applied"}\n',
        documents={contract: b"contract\n", checklist: b"checklist\n"},
    )
    original = projection_transaction.atomic_write
    writes = 0

    def interrupt(path: Path, content: bytes) -> None:
        """Raise at one selected persistent write boundary."""

        nonlocal writes
        writes += 1
        if writes == failed_write:
            raise OSError("injected interruption")
        original(path, content)

    monkeypatch.setattr(projection_transaction, "atomic_write", interrupt)
    with pytest.raises(OSError, match="interruption"):
        projection_transaction.apply_projection(
            repository, journal, validate_documents=lambda: None
        )

    monkeypatch.setattr(projection_transaction, "atomic_write", original)
    recovered = projection_transaction.apply_projection(
        repository, journal, validate_documents=lambda: None
    )

    assert recovered == receipt
    assert receipt.read_bytes() == b'{"result": "applied"}\n'
    assert contract.read_bytes() == b"contract\n"
    assert checklist.read_bytes() == b"checklist\n"
    assert not journal.exists()


def test_projection_validation_failure_does_not_publish_receipt(
    tmp_path: Path,
) -> None:
    """Keep the receipt absent until the rendered documents pass validation."""

    repository = tmp_path / "repository"
    repository.mkdir()
    receipt = repository / "evidence/receipts/result.json"
    contract = repository / "docs/contract.md"
    journal = projection_transaction.prepare_projection(
        repository,
        "transition",
        receipt_path=receipt,
        receipt=b'{"result": "applied"}\n',
        documents={contract: b"contract\n"},
    )

    def reject_projection() -> None:
        """Represent a semantic validator rejecting the rendered documents."""

        raise ValueError("invalid projection")

    with pytest.raises(ValueError, match="invalid projection"):
        projection_transaction.apply_projection(
            repository,
            journal,
            validate_documents=reject_projection,
        )

    assert contract.read_bytes() == b"contract\n"
    assert not receipt.exists()
    assert journal.exists()
