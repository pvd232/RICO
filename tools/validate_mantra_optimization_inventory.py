"""Validate the versioned MANTRA optimization migration inventory."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from pathlib import Path

import tomllib

EXPECTED_OPERATIONS = frozenset(
    {
        "cnmf_nmf",
        "consensus_kmeans",
        "fast_h5ad_read",
        "hopfield_training_retrieval",
        "low_rank_reduction",
        "mil_proposal_routing",
        "mil_training",
        "response_nnls",
        "ridge_regression",
        "sinkhorn_controls",
    }
)
REQUIRED_FIELDS = frozenset(
    {
        "id",
        "historical_owners",
        "modular_owner",
        "cpu_reference",
        "requirement_id",
        "pair_block_id",
        "verifier_id",
        "device_policy",
        "determinism_policy",
        "consumers",
    }
)


def _contract_ids(contracts: Path) -> tuple[set[str], set[str], set[str]]:
    """Collect requirement, PairBlock, and verifier IDs from contract packages."""
    requirements: set[str] = set()
    pair_blocks: set[str] = set()
    verifiers: set[str] = set()
    for path in contracts.glob("*.toml"):
        package = tomllib.loads(path.read_text(encoding="utf-8"))
        requirements.update(item["id"] for item in package.get("requirements", ()))
        pair_blocks.update(item["id"] for item in package.get("pair_blocks", ()))
        verifiers.update(item["id"] for item in package.get("verifiers", ()))
    return requirements, pair_blocks, verifiers


def validate_inventory(
    payload: Mapping[str, object], mantra_root: Path, contracts: Path
) -> None:
    """Reject incomplete operations and historical owners that cannot be opened."""
    if payload.get("schema_version") != 1:
        raise ValueError("inventory schema_version must equal 1")
    operations = payload.get("operations")
    if not isinstance(operations, list):
        raise TypeError("inventory operations must be an array")
    identifiers = tuple(
        operation.get("id") if isinstance(operation, dict) else None
        for operation in operations
    )
    if set(identifiers) != EXPECTED_OPERATIONS or len(identifiers) != len(
        EXPECTED_OPERATIONS
    ):
        raise ValueError("inventory operation set is incomplete or duplicated")
    requirement_ids, pair_block_ids, verifier_ids = _contract_ids(contracts)
    for operation in operations:
        if not isinstance(operation, dict) or set(operation) != REQUIRED_FIELDS:
            raise ValueError("inventory operation fields are incomplete")
        if any(not operation[field] for field in REQUIRED_FIELDS):
            raise ValueError("inventory operation fields must be nonempty")
        owners = operation["historical_owners"]
        if not isinstance(owners, list) or not all(
            isinstance(owner, str) and owner for owner in owners
        ):
            raise ValueError("historical owners must be nonempty strings")
        for owner in owners:
            path = mantra_root / owner.split(":", 1)[0]
            if not path.is_file():
                raise ValueError(f"historical owner is missing: {owner}")
        modular_owner = operation["modular_owner"]
        if not isinstance(modular_owner, str) or not modular_owner.startswith(
            ("src/rico/", "src/mantra/rebuild/")
        ):
            raise ValueError("modular owner must be a declared rebuild path")
        if operation["requirement_id"] not in requirement_ids:
            raise ValueError("inventory requirement is not declared")
        if operation["pair_block_id"] not in pair_block_ids:
            raise ValueError("inventory PairBlock is not declared")
        if operation["verifier_id"] not in verifier_ids:
            raise ValueError("inventory verifier is not declared")
        consumers = operation["consumers"]
        if not isinstance(consumers, list) or not set(consumers) <= pair_block_ids:
            raise ValueError("inventory consumer is not a declared PairBlock")


def load_and_validate(inventory: Path, mantra_root: Path, contracts: Path) -> None:
    """Load one TOML inventory and validate it against the MANTRA checkout."""
    validate_inventory(
        tomllib.loads(inventory.read_text(encoding="utf-8")), mantra_root, contracts
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Return success only when the command-line inventory is complete."""
    parser = argparse.ArgumentParser()
    parser.add_argument("inventory", type=Path)
    parser.add_argument("--mantra-root", type=Path, required=True)
    parser.add_argument("--contracts", type=Path, required=True)
    arguments = parser.parse_args(argv)
    load_and_validate(arguments.inventory, arguments.mantra_root, arguments.contracts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
