"""Register and verify the frozen Phase 0 evidence set through VIPER."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from viper import execution
from viper.authoring import experiment, plan, replicate, stage, variant
from viper.benchmark import RunArtifactDraft
from viper.config import BuildConfig
from viper.outputs import StageOutputs, output
from viper.references import GitFileRef
from viper.repository import read_source
from viper.runtime import LocalEnvSpec, observe_python_env
from viper.stages import StageContext, build

from tools.artifact_loaders import load_json
from tools.freeze_phase0 import REQUIRED_EVIDENCE_ROLES, sha256_file

RESTORATION_BUNDLE_FILES = {
    "capacity_receipt": "capacity_receipt.json",
    "restoration_receipt": "disk_import_receipt.json",
}
DIRECT_EVIDENCE_ROLES = REQUIRED_EVIDENCE_ROLES - RESTORATION_BUNDLE_FILES.keys()
REQUIRED_STAGE_INPUTS = DIRECT_EVIDENCE_ROLES | {
    "index",
    "ledger",
    "restoration_evidence",
}
PRIOR_RUN_EVIDENCE_ROLES = frozenset(
    {
        "hopfield_replay_receipt",
        "mil_replay_receipt",
        "restoration_bindings",
        "restoration_evidence",
    }
)


class Phase0RegistrationError(RuntimeError):
    """Report disagreement between the index and a registered evidence input."""


def _identity(path: Path) -> dict[str, object]:
    """Return the byte count and SHA-256 observed for one evidence file."""

    return {"byte_count": path.stat().st_size, "sha256": sha256_file(path)}


def _evidence_path(context: StageContext[BuildConfig], role: str) -> Path:
    """Resolve one indexed role from a direct input or restoration bundle."""

    bundle_name = RESTORATION_BUNDLE_FILES.get(role)
    if bundle_name is not None:
        return context.inputs["restoration_evidence"] / bundle_name
    return context.inputs[role]


@build(config=BuildConfig)
def register_phase0(context: StageContext[BuildConfig]) -> None:
    """Verify every frozen identity and write the terminal Phase 0 receipt."""

    index = load_json(context.inputs["index"])
    if (
        not isinstance(index, dict)
        or index.get("schema_version") != "rico.phase0_evidence.v1"
    ):
        raise Phase0RegistrationError("Phase 0 index schema differs")
    evidence = index.get("evidence")
    ledger_identity = index.get("viper_usefulness_ledger")
    if not isinstance(evidence, dict) or set(evidence) != REQUIRED_EVIDENCE_ROLES:
        raise Phase0RegistrationError("Phase 0 evidence roles differ")
    if not isinstance(ledger_identity, dict):
        raise Phase0RegistrationError("VIPER usefulness ledger identity is absent")
    observed: dict[str, dict[str, object]] = {}
    for role in sorted(REQUIRED_EVIDENCE_ROLES):
        expected = evidence[role]
        if not isinstance(expected, dict):
            raise Phase0RegistrationError(f"Phase 0 evidence identity differs: {role}")
        path = _evidence_path(context, role)
        actual = _identity(path)
        if any(
            actual.get(field) != expected.get(field)
            for field in ("byte_count", "sha256")
        ):
            raise Phase0RegistrationError(f"Phase 0 evidence identity differs: {role}")
        observed[role] = actual
    actual_ledger = _identity(context.inputs["ledger"])
    if any(
        actual_ledger.get(field) != ledger_identity.get(field)
        for field in ("byte_count", "sha256")
    ):
        raise Phase0RegistrationError("VIPER usefulness ledger identity differs")
    receipt = {
        "schema_version": "rico.phase0_registration.v1",
        "evidence": observed,
        "index_sha256": sha256_file(context.inputs["index"]),
        "passed": True,
        "viper_usefulness_ledger": actual_ledger,
    }
    context.outputs["receipt"].write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build_phase0_registration_study(stage_inputs: Mapping[str, Any]):
    """Declare the terminal evidence-registration stage from named inputs."""

    if set(stage_inputs) != REQUIRED_STAGE_INPUTS:
        raise Phase0RegistrationError("registration stage inputs differ")
    disconnected = sorted(
        role
        for role in PRIOR_RUN_EVIDENCE_ROLES
        if not isinstance(stage_inputs[role], RunArtifactDraft)
    )
    if disconnected:
        raise Phase0RegistrationError(
            f"prior-run evidence inputs differ: {disconnected}"
        )
    registration = stage(
        register_phase0,
        stage_id="register",
        inputs=dict(stage_inputs),
        outputs=StageOutputs(
            receipt=output(
                path="phase0_registration_receipt.json",
                loader=load_json,
                data_role="benchmark",
            )
        ),
        file_access="declared",
    )
    return experiment(
        experiment_id="rico_mantra_phase0_evidence",
        variants=(
            variant(
                "complete",
                stages=(registration,),
                estimator=registration.outputs["receipt"],
            ),
        ),
        replicates=(replicate(seed=0),),
    )


def run_phase0_registration(
    repository_root: Path,
    stage_inputs: Mapping[str, Any],
    *,
    trusted_source_repositories: frozenset[str] = frozenset(),
):
    """Execute registration with explicit trust for prior-run source loaders."""

    source = read_source(repository_root)
    environment = LocalEnvSpec(
        lockfile=GitFileRef(
            repository=source.repository,
            commit=source.commit,
            path="requirements.txt",
        ),
        python_env=observe_python_env(),
    )
    return execution.run(
        plan(
            experiment=build_phase0_registration_study(stage_inputs),
            source=source,
            env=environment,
        ),
        repository_root=repository_root,
        trusted_source_repositories=trusted_source_repositories,
    )
