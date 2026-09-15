"""Verify the complete MANTRA optimization migration inventory."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
import tomllib

from tools.validate_mantra_optimization_inventory import (
    EXPECTED_OPERATIONS,
    load_and_validate,
    validate_inventory,
)

ROOT = Path(__file__).parents[2]
INVENTORY = ROOT / "docs/briefings/mantra-optimization-inventory.toml"
MANTRA = Path("/Users/machina/Developer/ChatGPT/mantra")


def test_inventory_covers_every_accelerated_operation() -> None:
    """Require every approved operation and every migration decision."""
    load_and_validate(INVENTORY, MANTRA, ROOT / "contracts")
    payload = tomllib.loads(INVENTORY.read_text(encoding="utf-8"))
    assert {operation["id"] for operation in payload["operations"]} == set(
        EXPECTED_OPERATIONS
    )


@pytest.mark.parametrize(
    "missing",
    ["historical_owners", "modular_owner", "verifier_id", "consumers"],
)
def test_rejects_missing_owner_gate_or_consumer(missing: str) -> None:
    """Reject omission of each ownership, gate, and consumer boundary."""
    payload = tomllib.loads(INVENTORY.read_text(encoding="utf-8"))
    candidate = deepcopy(payload)
    candidate["operations"][0].pop(missing)
    with pytest.raises(ValueError, match="fields are incomplete"):
        validate_inventory(candidate, MANTRA, ROOT / "contracts")
