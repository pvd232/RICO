"""Verify source-closed K562 control residuals and cNMF program fitting."""

import os
from pathlib import Path
import subprocess
import sys

import anndata as ad
import numpy as np
import pandas as pd
import pytest
import torch
from viper.artifacts import StageArtifactRef
from viper.authoring import BuildSpecDraft, run_artifact
from viper.references import LocalFileRef, ResolvedRunRef

from rico.cell_types.k562.control_programs import (
    CANONICAL_EXPRESSION_SURFACE,
    CANONICAL_TARGET_SUM,
    CONTROL_RESIDUAL_COVARIATES,
    ControlProgramBankMetadata,
    _zscore,
    array_sha256,
    build_control_program_bank,
    build_control_residuals,
    configure_cuda_determinism,
    fit_control_program_bank,
    fit_control_programs,
    reviewed_control_program_recipe,
    write_control_program_bank,
    write_control_residuals,
)
from rico.cell_types.k562.atlas import SlimAtlasMetadata
from rico.cell_types.k562.gene_panels import (
    ControlProgramPanel,
    ExcludedGene,
    GeneVariability,
    ordered_values_sha256,
)
from rico.config import ControlProgramBankConfig
from rico.plans.k562.control_programs import (
    declare_control_program_bank_experiment,
    declare_control_program_bank_materialization_experiment,
)


def _write_slim_atlas(path: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Write one small log1p atlas with controls, treated cells, and two IEGs."""
    rng = np.random.default_rng(41)
    cell_ids = tuple(f"cell-{index}" for index in range(10))
    gene_ids = tuple(f"ENSG{index:011d}" for index in range(7))
    expression = np.log1p(rng.poisson(10, size=(10, 7))).astype(np.float32)
    atlas = ad.AnnData(
        X=expression,
        obs=pd.DataFrame(
            {
                "gene": ["non-targeting"] * 8 + ["PERT1"] * 2,
                "mitopercent": np.linspace(1.0, 10.0, 10, dtype=np.float32),
            },
            index=pd.Index(cell_ids, name="cell_barcode"),
        ),
        var=pd.DataFrame(
            {"gene_name": ["A", "B", "C", "D", "E", "IEG1", "IEG2"]},
            index=pd.Index(gene_ids, name="gene_id"),
        ),
    )
    atlas.uns["rico_slim_atlas"] = SlimAtlasMetadata(
        expression_surface=CANONICAL_EXPRESSION_SURFACE,
        target_sum=CANONICAL_TARGET_SUM,
        source_cell_count=len(cell_ids),
        selected_cell_count=len(cell_ids),
        gene_count=len(gene_ids),
        selected_cell_ids_sha256=ordered_values_sha256(cell_ids),
        gene_ids_sha256=ordered_values_sha256(gene_ids),
    ).model_dump(mode="json")
    atlas.write_h5ad(path)
    return cell_ids, gene_ids


def _panel(cell_ids: tuple[str, ...], gene_ids: tuple[str, ...]) -> ControlProgramPanel:
    """Build one valid typed panel aligned to the synthetic atlas."""
    selected = gene_ids[:5]
    symbols = ("A", "B", "C", "D", "E")
    return ControlProgramPanel(
        method="scanpy.pp.highly_variable_genes",
        flavor="seurat_v3",
        scanpy_version="test",
        span=0.3,
        control_label="non-targeting",
        fitted_cell_count=8,
        fitted_cell_ids_sha256=ordered_values_sha256(cell_ids[:8]),
        source_gene_count=7,
        eligible_gene_count=5,
        selected_gene_count=5,
        source_gene_ids_sha256=ordered_values_sha256(gene_ids),
        immediate_early_genes=("IEG1", "IEG2"),
        excluded_genes=(
            ExcludedGene(
                gene_id=gene_ids[5],
                symbol="IEG1",
                source_index=5,
                reasons=("core_immediate_early",),
            ),
            ExcludedGene(
                gene_id=gene_ids[6],
                symbol="IEG2",
                source_index=6,
                reasons=("core_immediate_early",),
            ),
        ),
        variability=tuple(
            GeneVariability(
                gene_id=gene_id,
                symbol=symbol,
                source_index=index,
                mean=float(index + 1),
                variance=float(index + 2),
                normalized_variance=float(5 - index),
                rank=index,
            )
            for index, (gene_id, symbol) in enumerate(
                zip(selected, symbols, strict=True)
            )
        ),
        selected_gene_ids=selected,
        selected_gene_symbols=symbols,
        selected_gene_ids_sha256=ordered_values_sha256(selected),
    )


def _run_ref(tmp_path: Path, marker: str) -> ResolvedRunRef:
    """Return one deterministic completed-run reference for plan tests."""
    return ResolvedRunRef(
        sha256=marker * 64,
        bytes=1,
        stored_at=LocalFileRef(
            workspace=tmp_path.resolve(),
            store_id="b" * 32,
            commit="c" * 64,
            path=f"experiments/{marker}/runs/canonical/run/resolved.yaml",
        ),
    )


def test_builds_deterministic_nonnegative_control_residuals(tmp_path: Path) -> None:
    """Use the typed panel and exact two covariates to prepare cNMF input."""
    atlas = tmp_path / "slim.h5ad"
    cell_ids, gene_ids = _write_slim_atlas(atlas)
    panel = _panel(cell_ids, gene_ids)

    first = build_control_residuals(atlas, panel)
    second = build_control_residuals(atlas, panel)

    assert first.residuals.shape == (8, 5)
    assert np.all(first.residuals >= 0.0)
    assert first.metadata.covariates == CONTROL_RESIDUAL_COVARIATES
    assert first.metadata.immediate_early_genes_present == ("IEG1", "IEG2")
    assert tuple(first.gene_ids.tolist()) == tuple(sorted(panel.selected_gene_ids))
    np.testing.assert_array_equal(first.residuals, second.residuals)

    first_npz = tmp_path / "first.npz"
    second_npz = tmp_path / "second.npz"
    write_control_residuals(first_npz, tmp_path / "first.json", first)
    write_control_residuals(second_npz, tmp_path / "second.json", second)
    assert first_npz.read_bytes() == second_npz.read_bytes()


def test_covariate_zscore_matches_pinned_nan_policy() -> None:
    """Fill NaNs with the finite mean before applying the pinned population scale."""
    values = np.asarray([1.0, np.nan, 5.0], dtype=np.float32)
    expected_filled = np.asarray([1.0, 3.0, 5.0], dtype=np.float32)
    expected = (
        (expected_filled - np.nanmean(values)) / (np.nanstd(expected_filled) + 1.0e-9)
    ).astype(np.float32)

    np.testing.assert_array_equal(_zscore(values), expected)


def test_rejects_a_control_panel_from_a_different_cell_axis(tmp_path: Path) -> None:
    """Prevent a panel fitted on different controls from entering residualization."""
    atlas = tmp_path / "slim.h5ad"
    cell_ids, gene_ids = _write_slim_atlas(atlas)
    panel = _panel(cell_ids, gene_ids).model_copy(
        update={"fitted_cell_ids_sha256": "0" * 64}
    )

    with pytest.raises(ValueError, match="control-cell order"):
        build_control_residuals(atlas, panel)


@pytest.mark.parametrize(
    ("metadata_update", "message"),
    (
        ({"expression_surface": "raw_counts"}, "log1p_cp10k"),
        ({"target_sum": 1_000.0}, "10,000-count"),
        ({"selected_cell_ids_sha256": "0" * 64}, "cell axis"),
        ({"gene_ids_sha256": "0" * 64}, "gene axis"),
    ),
)
def test_rejects_a_noncanonical_or_misaligned_slim_atlas(
    tmp_path: Path,
    metadata_update: dict[str, object],
    message: str,
) -> None:
    """Reject changed normalization metadata or either altered canonical axis."""
    atlas_path = tmp_path / "slim.h5ad"
    cell_ids, gene_ids = _write_slim_atlas(atlas_path)
    atlas = ad.read_h5ad(atlas_path)
    metadata = SlimAtlasMetadata.model_validate(dict(atlas.uns["rico_slim_atlas"]))
    atlas.uns["rico_slim_atlas"] = metadata.model_copy(
        update=metadata_update
    ).model_dump(mode="json")
    atlas.write_h5ad(atlas_path)

    with pytest.raises(ValueError, match=message):
        build_control_residuals(atlas_path, _panel(cell_ids, gene_ids))


def test_bank_rejects_residuals_bound_to_a_different_panel(tmp_path: Path) -> None:
    """Reject a residual artifact whose fitted cells differ from its panel input."""
    atlas = tmp_path / "slim.h5ad"
    cell_ids, gene_ids = _write_slim_atlas(atlas)
    panel = _panel(cell_ids, gene_ids)
    residuals = build_control_residuals(atlas, panel)
    residual_path = tmp_path / "residuals.npz"
    residual_metadata = tmp_path / "residuals.json"
    write_control_residuals(residual_path, residual_metadata, residuals)
    changed_panel = panel.model_copy(update={"fitted_cell_ids_sha256": "0" * 64})
    changed_panel_path = tmp_path / "changed-panel.json"
    changed_panel_path.write_text(changed_panel.model_dump_json())

    with pytest.raises(ValueError, match="typed panel"):
        build_control_program_bank(
            residual_path,
            residual_metadata,
            changed_panel_path,
            ControlProgramBankConfig(
                nominal_components=3,
                expected_realized_components=3,
                restarts=4,
                max_iterations=5,
                compile_updates=False,
            ),
            device="cpu",
        )


def test_cpu_kernel_repeats_and_persists_the_same_cnmf_result(
    tmp_path: Path,
) -> None:
    """Repeat the cNMF kernel and retain final coefficients and diagnostics."""
    residuals = np.abs(
        np.random.default_rng(7).normal(size=(32, 10)).astype(np.float32)
    )
    config = ControlProgramBankConfig(
        nominal_components=3,
        expected_realized_components=3,
        restarts=4,
        max_iterations=30,
        tolerance=1.0e-12,
        random_seed=9,
        program_regularization=0.1,
        usage_regularization=0.0,
        l1_ratio=1.0,
        consensus_initializations=3,
        minimum_run_coverage=0.25,
        compile_updates=False,
    )

    first = fit_control_program_bank(residuals, config, device="cpu")
    second = fit_control_program_bank(residuals, config, device="cpu")

    np.testing.assert_array_equal(first.programs, second.programs)
    np.testing.assert_array_equal(first.programs_all, second.programs_all)
    np.testing.assert_array_equal(
        first.cluster_assignments,
        second.cluster_assignments,
    )
    assert first.programs.shape[0] == residuals.shape[1]
    assert first.programs_all.shape == (12, residuals.shape[1])
    assert first.reconstruction_coefficients.shape == (
        residuals.shape[0],
        first.programs.shape[1],
    )
    assert first.reconstruction_rmse.shape == (residuals.shape[0],)
    assert np.isfinite(first.reconstruction_coefficients).all()
    assert np.all(first.reconstruction_coefficients >= 0.0)
    assert np.isfinite(first.reconstruction_rmse).all()

    metadata = ControlProgramBankMetadata(
        method="gpu_batched_cnmf_cpu_consensus",
        producer_recipe=reviewed_control_program_recipe(),
        control_cell_count=residuals.shape[0],
        control_gene_count=residuals.shape[1],
        nominal_rank=3,
        realized_rank=first.programs.shape[1],
        restarts=4,
        max_iterations=30,
        completed_iterations=first.completed_iterations,
        random_seed=9,
        program_regularization=0.1,
        usage_regularization=0.0,
        l1_ratio=1.0,
        minimum_run_coverage=0.25,
        factorization_backend="gpu",
        consensus_backend="cpu",
        consensus_initializations=3,
        control_cell_ids_sha256="1" * 64,
        control_gene_ids_sha256="2" * 64,
        programs_sha256=array_sha256(first.programs),
        programs_all_sha256=array_sha256(first.programs_all),
        cluster_assignments_sha256=array_sha256(first.cluster_assignments),
        reconstruction_coefficients_sha256=array_sha256(
            first.reconstruction_coefficients
        ),
        reconstruction_rmse_sha256=array_sha256(first.reconstruction_rmse),
        mean_reconstruction_rmse=float(first.reconstruction_rmse.mean()),
        maximum_reconstruction_rmse=float(first.reconstruction_rmse.max()),
        run_coverage=tuple(float(value) for value in first.run_coverage),
    )
    bank_path = tmp_path / "bank.npz"
    metadata_path = tmp_path / "bank.json"
    write_control_program_bank(
        bank_path,
        metadata_path,
        first,
        np.asarray([f"cell-{index}" for index in range(residuals.shape[0])]),
        np.asarray([f"gene-{index}" for index in range(residuals.shape[1])]),
        metadata,
    )

    with np.load(bank_path, allow_pickle=False) as archive:
        np.testing.assert_array_equal(
            archive["reconstruction_coefficients"],
            first.reconstruction_coefficients,
        )
        np.testing.assert_array_equal(
            archive["reconstruction_rmse"], first.reconstruction_rmse
        )
    persisted = ControlProgramBankMetadata.model_validate_json(
        metadata_path.read_text()
    )
    assert persisted.reconstruction_coefficients_sha256 == array_sha256(
        first.reconstruction_coefficients
    )
    assert persisted.reconstruction_rmse_sha256 == array_sha256(
        first.reconstruction_rmse
    )


def test_port_matches_the_pinned_mantra_authority_fixture() -> None:
    """Match arrays generated directly by the reviewed MANTRA NMF and CPU consensus."""
    values = np.abs(np.random.default_rng(7).normal(size=(8, 6)).astype(np.float32))
    fit = fit_control_programs(
        values,
        components=2,
        restarts=3,
        max_iterations=5,
        tolerance=1.0e-12,
        random_seed=11,
        program_regularization=0.2,
        usage_regularization=0.0,
        l1_ratio=1.0,
        consensus_initializations=3,
        minimum_run_coverage=0.5,
        device="cpu",
        compile_updates=False,
    )

    expected = {
        "programs": (
            (6, 2),
            np.dtype("float32"),
            "353d56d0a49ea43ef12a2d70b59dacc6cf4d909843c07495b7fc0d6122ffc580",
        ),
        "programs_all": (
            (6, 6),
            np.dtype("float32"),
            "bd1309fa55cc189bc9073b30f02cd9226e6abde43b835d750b4c7bb51ca2eb64",
        ),
        "cluster_assignments": (
            (6,),
            np.dtype("int32"),
            "184c33919fc0d31a149843dab7c86d8843fe5fb50461700b6539b246dac8c32d",
        ),
        "run_coverage": (
            (2,),
            np.dtype("float32"),
            "a4c4be6797d0486771e8c5a9d75b625a112f9c61b10b7466869b53adfc68da6d",
        ),
    }
    for name, (shape, dtype, digest) in expected.items():
        observed = getattr(fit, name)
        assert observed.shape == shape
        assert observed.dtype == dtype
        assert array_sha256(observed) == digest
    assert fit.completed_iterations == 5


def test_control_program_recipe_pins_each_hand_ported_authority() -> None:
    """Retain exact repository revisions and source bytes for the three operations."""
    recipe = reviewed_control_program_recipe()

    assert recipe.residualization.functions == (
        "_compute_module_score",
        "_zscore",
        "regress_out_covariates",
    )
    assert recipe.factorization.sha256 == (
        "d99feb5ab66dbe59edfa36c1bf1130c1037df5741412d65d01a4b64620b7b35b"
    )
    assert recipe.consensus.functions == ("stability_kmeans_labels_centers",)


def test_configures_the_pinned_deterministic_torch_context() -> None:
    """Apply the source-owned CUDA determinism policy before factorization."""
    configure_cuda_determinism(17)

    assert os.environ["CUBLAS_WORKSPACE_CONFIG"] == ":16:8"
    assert torch.are_deterministic_algorithms_enabled()
    assert not torch.backends.cuda.matmul.allow_tf32
    assert not torch.backends.cudnn.allow_tf32
    assert not torch.backends.cudnn.benchmark


def test_accepts_viper_deterministic_cublas_workspace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Accept VIPER's reproducible cuBLAS workspace before factorization."""
    monkeypatch.setenv("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

    configure_cuda_determinism(17)

    assert os.environ["CUBLAS_WORKSPACE_CONFIG"] == ":4096:8"


def test_fresh_import_selects_cublas_workspace_before_cuda_initialization() -> None:
    """A fresh worker selects the reviewed workspace without initializing CUDA."""
    script = """
import os
import rico.cell_types.k562.control_programs
import torch

assert os.environ["CUBLAS_WORKSPACE_CONFIG"] == ":16:8"
assert not torch.cuda.is_initialized()
"""
    subprocess.run([sys.executable, "-c", script], check=True)


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA is required")
def test_gpu_rejects_a_worker_initialized_without_the_reviewed_workspace() -> None:
    """Fail rather than claim determinism after an unsafe worker initialization."""
    script = """
import torch

warmup = torch.ones((2, 2), device="cuda")
torch.matmul(warmup, warmup)

from rico.cell_types.k562.control_programs import configure_cuda_determinism

try:
    configure_cuda_determinism(7)
except RuntimeError as error:
    assert "before CUDA initialization" in str(error) or "CUDA was initialized" in str(error)
else:
    raise AssertionError("unsafe reused CUDA worker was accepted")
"""
    environment = dict(os.environ)
    environment.pop("CUBLAS_WORKSPACE_CONFIG", None)
    subprocess.run([sys.executable, "-c", script], check=True, env=environment)


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA is required")
def test_gpu_compiled_path_emits_nineteen_programs_and_diagnostics() -> None:
    """Observe the bounded compiled-GPU success path required by R5-REQ-01."""
    values = np.abs(np.random.default_rng(19).normal(size=(32, 24)).astype(np.float32))
    fit = fit_control_program_bank(
        values,
        ControlProgramBankConfig(
            nominal_components=19,
            expected_realized_components=19,
            restarts=2,
            max_iterations=4,
            tolerance=1.0e-12,
            random_seed=9,
            program_regularization=10.0,
            usage_regularization=0.0,
            l1_ratio=1.0,
            consensus_initializations=2,
            minimum_run_coverage=0.5,
            compile_updates=True,
        ),
        device="cuda",
    )

    assert fit.programs.shape == (24, 19)
    assert fit.reconstruction_coefficients.shape == (32, 19)
    assert fit.reconstruction_rmse.shape == (32,)
    assert np.isfinite(fit.reconstruction_rmse).all()


def test_accepted_control_program_config_retains_nineteen_stable_programs() -> None:
    """Pin the accepted GPU fit and deterministic consensus configuration."""
    config = ControlProgramBankConfig()

    assert config.nominal_components == 30
    assert config.expected_realized_components == 19
    assert config.restarts == 12
    assert config.max_iterations == 500
    assert config.random_seed == 9
    assert config.program_regularization == 10.0
    assert config.usage_regularization == 0.0
    assert config.l1_ratio == 1.0
    assert config.minimum_run_coverage == 0.7
    assert config.factorization_backend == "gpu"
    assert config.consensus_backend == "cpu"
    assert config.consensus_initializations == 10


def test_control_program_plan_requires_download_root_closure(tmp_path: Path) -> None:
    """Require both input-producing runs and both Builds to close at Downloads."""
    slim_atlas = run_artifact(
        _run_ref(tmp_path, "a"),
        StageArtifactRef(stage_id="build_slim_atlas", artifact_name="slim_atlas"),
        path="inputs/atlas/slim.h5ad",
        data_role="training",
    )
    panel = run_artifact(
        _run_ref(tmp_path, "b"),
        StageArtifactRef(
            stage_id="build_control_program_panel",
            artifact_name="control_program_panel",
        ),
        path="inputs/programs/control_program_panel.json",
        data_role="training",
    )

    selected = declare_control_program_bank_experiment(
        slim_atlas=slim_atlas,
        control_program_panel=panel,
    ).variants["canonical"]

    assert tuple(selected.stages) == (
        "build_control_residuals",
        "build_control_program_bank",
    )
    residual_stage = selected.stages["build_control_residuals"]
    bank_stage = selected.stages["build_control_program_bank"]
    assert isinstance(residual_stage.spec, BuildSpecDraft)
    assert isinstance(bank_stage.spec, BuildSpecDraft)
    assert residual_stage.spec.input_roots == "download"
    assert bank_stage.spec.input_roots == "download"
    assert selected.estimator.output_name == "control_program_bank"


def test_program_bank_materialization_does_not_rebuild_residuals(
    tmp_path: Path,
) -> None:
    """Consume the accepted residual receipt in the only cNMF stage."""
    residual_run = _run_ref(tmp_path, "c")
    residuals = run_artifact(
        residual_run,
        StageArtifactRef(
            stage_id="build_control_residuals",
            artifact_name="control_residuals",
        ),
        path="inputs/programs/control_residuals.npz",
        data_role="training",
    )
    metadata = run_artifact(
        residual_run,
        StageArtifactRef(
            stage_id="build_control_residuals",
            artifact_name="control_residuals_metadata",
        ),
        path="inputs/programs/control_residuals.json",
        data_role="training",
    )
    panel = run_artifact(
        _run_ref(tmp_path, "d"),
        StageArtifactRef(
            stage_id="build_control_program_panel",
            artifact_name="control_program_panel",
        ),
        path="inputs/programs/control_program_panel.json",
        data_role="training",
    )

    selected = declare_control_program_bank_materialization_experiment(
        control_residuals=residuals,
        control_residuals_metadata=metadata,
        control_program_panel=panel,
    ).variants["canonical"]

    assert tuple(selected.stages) == ("build_control_program_bank",)
    bank_stage = selected.stages["build_control_program_bank"]
    assert isinstance(bank_stage.spec, BuildSpecDraft)
    assert bank_stage.spec.input_roots == "download"
    assert selected.estimator.output_name == "control_program_bank"
