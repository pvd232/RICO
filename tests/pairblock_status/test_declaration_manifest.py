"""Verify typed declaration parsing, joins, fingerprints, and revisions."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

from tools.pairblock_status.checklist_profile import PairBlockGateError
from tools.pairblock_status.declaration_manifest import (
    ProjectDeclarations,
    compare_declarations,
    load_declarations,
)
from tools.pairblock_status.profile import ChecklistProfile

FIXTURE_ROOT = Path(__file__).parent / "fixtures/minimal_profile"


def _load(repository: Path, profile: ChecklistProfile) -> ProjectDeclarations:
    """Load the valid fixture declaration."""

    return load_declarations(repository / "declarations.toml", profile)


def _write_manifest(tmp_path: Path, edit) -> Path:
    """Copy the fixture repository and apply one textual manifest edit."""

    repository = tmp_path / "repository"
    shutil.copytree(FIXTURE_ROOT, repository)
    for relative in (
        Path("tools/pairblock_status/checklist_profile.py"),
        Path("tests/pairblock_status/test_pairblock_controller.py"),
    ):
        source = Path(__file__).parents[2] / relative
        destination = repository / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    path = repository / "declarations.toml"
    original = path.read_text(encoding="utf-8")
    path.write_text(edit(original), encoding="utf-8")
    return path


def _remove_verifier(text: str) -> str:
    """Remove the fixture verifier while retaining its empty collection key."""

    text = text.replace(
        "schema_version = 1\n", "schema_version = 1\nverifiers = []\n", 1
    )
    return text.replace(
        '[[verifiers]]\nid = "VR-NATIVE"\nrequirement_ids = ["REQ-NATIVE"]\nconditions = ["The declared test command passes."]\nsuccess_case = "The receipt records the passing command."\nrejection_cases = ["The command fails."]\n\n',
        "",
    )


def test_manifest_loads_typed_records_and_stable_fingerprint(
    repository_factory: Callable[..., Path],
    declaration_profile: ChecklistProfile,
) -> None:
    """Load every typed record and bind its complete contract closure."""

    declarations = _load(repository_factory(command="true"), declaration_profile)

    assert tuple(declarations.requirements_by_id) == ("REQ-NATIVE",)
    assert tuple(declarations.verifiers_by_id) == ("VR-NATIVE",)
    assert tuple(declarations.pair_blocks_by_id) == ("PB-NATIVE",)
    assert len(declarations.sha256) == 64
    assert len(declarations.pair_block_fingerprint("PB-NATIVE")) == 64


@pytest.mark.parametrize(
    ("edit", "message"),
    [
        (
            lambda text: text.replace(
                'claim = "The proposal gate retains its result."',
                'claim = "The proposal gate retains its result."\nextra = true',
            ),
            "unknown fields",
        ),
        (
            lambda text: text.replace(
                'verifier_ids = ["VR-NATIVE"]', 'verifier_ids = ["VR-MISSING"]'
            ),
            "unknown IDs",
        ),
        (
            lambda text: text.replace(
                'depends_on = []\nsection = "0A"',
                'depends_on = ["PB-NATIVE"]\nsection = "0A"',
            ),
            "dependency cycle",
        ),
        (
            lambda text: text.replace(
                'test_paths = ["tests/pairblock_status/test_pairblock_controller.py"]',
                'test_paths = ["tools/pairblock_status/checklist_profile.py"]',
            ),
            "source and test roles",
        ),
        (
            lambda text: text.replace(
                'repository = "test"\nsource_paths',
                'repository = "unknown"\nsource_paths',
                1,
            ),
            "unknown repository",
        ),
        (
            lambda text: text.replace(
                'source_paths = ["tools/pairblock_status/checklist_profile.py"]',
                'source_paths = ["../escape.py"]',
            ),
            "repository-relative path",
        ),
    ],
)
def test_manifest_rejects_severed_or_ambiguous_records(
    tmp_path: Path,
    declaration_profile: ChecklistProfile,
    edit,
    message: str,
) -> None:
    """Reject malformed ownership before a gate can execute."""

    path = _write_manifest(tmp_path, edit)

    with pytest.raises(PairBlockGateError, match=message):
        load_declarations(path, declaration_profile)


def test_changed_verifier_reopens_owner_and_dependents(
    repository_factory: Callable[..., Path],
    declaration_profile: ChecklistProfile,
) -> None:
    """Propagate a verifier change through PairBlock reverse dependencies."""

    accepted = _load(repository_factory(command="true"), declaration_profile)
    requirement = accepted.requirements[0]
    verifier = replace(accepted.verifiers[0], conditions=("A stronger condition.",))
    dependent = replace(
        accepted.pair_blocks[0],
        id="PB-DEPENDENCY",
        requirement_ids=(requirement.id,),
        depends_on=("PB-NATIVE",),
    )
    candidate = replace(
        accepted,
        requirements=(
            replace(requirement, pair_block_ids=("PB-NATIVE", "PB-DEPENDENCY")),
        ),
        verifiers=(verifier,),
        pair_blocks=(*accepted.pair_blocks, dependent),
    )

    change = compare_declarations(accepted, candidate)

    assert change.affected_pair_blocks == ("PB-DEPENDENCY", "PB-NATIVE")
    assert any(record.record == "verifier:VR-NATIVE" for record in change.records)


def test_changed_requirement_reopens_requirement_dependents(
    repository_factory: Callable[..., Path],
    declaration_profile: ChecklistProfile,
) -> None:
    """Propagate a requirement change without a parallel PairBlock dependency."""

    fixture = _load(repository_factory(command="true"), declaration_profile)
    requirement = fixture.requirements[0]
    verifier = fixture.verifiers[0]
    block = fixture.pair_blocks[0]
    upstream = replace(
        requirement,
        id="REQ-UPSTREAM",
        verifier_ids=("VR-UPSTREAM",),
        pair_block_ids=("PB-UPSTREAM",),
    )
    dependent = replace(
        requirement,
        id="REQ-DEPENDENT",
        depends_on=("REQ-UPSTREAM",),
        verifier_ids=("VR-DEPENDENT",),
        pair_block_ids=("PB-DEPENDENT",),
    )
    accepted = replace(
        fixture,
        requirements=(upstream, dependent),
        verifiers=(
            replace(verifier, id="VR-UPSTREAM", requirement_ids=("REQ-UPSTREAM",)),
            replace(verifier, id="VR-DEPENDENT", requirement_ids=("REQ-DEPENDENT",)),
        ),
        pair_blocks=(
            replace(block, id="PB-UPSTREAM", requirement_ids=("REQ-UPSTREAM",)),
            replace(block, id="PB-DEPENDENT", requirement_ids=("REQ-DEPENDENT",)),
        ),
    )
    candidate = replace(
        accepted,
        requirements=(replace(upstream, claim="Changed upstream claim."), dependent),
    )

    change = compare_declarations(accepted, candidate)

    assert change.affected_pair_blocks == ("PB-DEPENDENT", "PB-UPSTREAM")


def test_unrelated_declaration_change_preserves_receipts(
    repository_factory: Callable[..., Path],
    declaration_profile: ChecklistProfile,
) -> None:
    """Exclude a PairBlock whose declaration closure did not change."""

    accepted = _load(repository_factory(command="true"), declaration_profile)
    candidate = replace(
        accepted,
        requirements=(replace(accepted.requirements[0], claim="Changed claim."),),
    )

    change = compare_declarations(accepted, candidate)

    assert change.affected_pair_blocks == ("PB-NATIVE",)


def test_referenced_record_removal_is_rejected(
    tmp_path: Path, declaration_profile: ChecklistProfile
) -> None:
    """Reject removal of a verifier still named by its requirement."""

    path = _write_manifest(tmp_path, _remove_verifier)

    with pytest.raises(PairBlockGateError, match="unknown IDs"):
        load_declarations(path, declaration_profile)
