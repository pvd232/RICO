"""Contract tests for Phase 0 restoration capacity receipts."""

from __future__ import annotations

from dataclasses import replace

import pytest

from mantra.rebuild.capacity import CapacityPlan, CapacityReceipt


def plan() -> CapacityPlan:
    """Build a plan whose five terms sum to twenty bytes."""

    return CapacityPlan(
        compressed_cache_bytes=4,
        canonical_bytes=3,
        viper_bytes=2,
        temporary_bytes=1,
        reserved_bytes=10,
    )


def test_required_bytes_sum_every_storage_role() -> None:
    """Include every storage role in the required-space total."""

    assert plan().required_bytes == 20


def test_capacity_passes_at_exact_boundary() -> None:
    """Accept free space equal to the required-space total."""

    receipt = CapacityReceipt(
        filesystem_path="/mantra",
        free_bytes=20,
        plan=plan(),
    )
    assert receipt.passed


def test_capacity_fails_below_boundary() -> None:
    """Reject free space below the required-space total."""

    receipt = CapacityReceipt(
        filesystem_path="/mantra",
        free_bytes=19,
        plan=plan(),
    )
    assert not receipt.passed


@pytest.mark.parametrize(
    "field",
    [
        "compressed_cache_bytes",
        "canonical_bytes",
        "viper_bytes",
        "temporary_bytes",
        "reserved_bytes",
    ],
)
def test_negative_storage_term_is_rejected(field: str) -> None:
    """Reject a negative value for each storage role."""

    with pytest.raises(ValueError):
        replace(plan(), **{field: -1})


def test_receipt_exposes_every_contract_term() -> None:
    """Serialize every plan term, observed free space, total, and decision."""

    receipt = CapacityReceipt(
        filesystem_path="/mantra",
        free_bytes=21,
        plan=plan(),
    )
    assert receipt.to_dict() == {
        "filesystem_path": "/mantra",
        "free_bytes": 21,
        "compressed_cache_bytes": 4,
        "canonical_bytes": 3,
        "viper_bytes": 2,
        "temporary_bytes": 1,
        "reserved_bytes": 10,
        "required_bytes": 20,
        "passed": True,
    }
