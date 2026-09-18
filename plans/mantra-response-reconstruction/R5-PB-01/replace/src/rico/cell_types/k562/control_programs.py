"""Build the K562 control-expression residuals and cNMF program bank."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
from typing import Any, cast
import zipfile

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sklearn.cluster import KMeans
import torch

from rico.cell_types.k562.gene_panels import (
    ControlProgramPanel,
    ordered_values_sha256,
)
from rico.cell_types.k562.atlas import (
    SlimAtlasMetadata,
    read_slim_atlas_metadata,
)
from rico.config import ControlProgramBankConfig
from rico.data.fast_h5ad import FastH5ADLoader

CONTROL_RESIDUAL_COVARIATES = ("mitopercent", "IEG_score")
CANONICAL_EXPRESSION_SURFACE = "log1p_cp10k"
CANONICAL_TARGET_SUM = 10_000.0
DEFAULT_DETERMINISTIC_CUBLAS_WORKSPACE = ":16:8"
DETERMINISTIC_CUBLAS_WORKSPACES = frozenset({":16:8", ":4096:8"})
MANTRA_REPOSITORY = "https://github.com/pvd232/MANTRA.git"
_CUDA_INITIALIZED_AT_MODULE_IMPORT = torch.cuda.is_initialized()
_CUBLAS_WORKSPACE_AT_MODULE_IMPORT = os.environ.get("CUBLAS_WORKSPACE_CONFIG")
if not _CUDA_INITIALIZED_AT_MODULE_IMPORT:
    os.environ.setdefault(
        "CUBLAS_WORKSPACE_CONFIG",
        DEFAULT_DETERMINISTIC_CUBLAS_WORKSPACE,
    )


class ControlProgramRecord(BaseModel):
    """Make persisted control-program records immutable and reject unknown fields."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ControlProgramProducerEvidence(ControlProgramRecord):
    """Identify one reviewed MANTRA source file and its owned operation."""

    repository: str = Field(description="Remote repository containing the producer.")
    commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    path: str = Field(description="Repository-relative producer source path.")
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    functions: tuple[str, ...] = Field(min_length=1)


class ControlProgramRecipe(ControlProgramRecord):
    """Bind residualization, NMF, and consensus to reviewed producer identities."""

    residualization: ControlProgramProducerEvidence
    factorization: ControlProgramProducerEvidence
    consensus: ControlProgramProducerEvidence


class ControlResidualsMetadata(ControlProgramRecord):
    """Bind one residual matrix to its fitted cells, genes, and covariates."""

    method: str = Field(description="Named expression residualization procedure.")
    control_label: str = Field(description="Label that selected fitted control cells.")
    control_cell_count: int = Field(gt=0, description="Fitted control-cell count.")
    control_gene_count: int = Field(gt=0, description="Fitted control-gene count.")
    control_cell_ids_sha256: str = Field(
        pattern=r"^[0-9a-f]{64}$",
        description="Digest of fitted control-cell identifiers in atlas order.",
    )
    control_gene_ids_sha256: str = Field(
        pattern=r"^[0-9a-f]{64}$",
        description="Digest of fitted control-gene identifiers in cNMF order.",
    )
    gene_ordering: str = Field(
        description="Rule that orders panel genes before residualization and cNMF."
    )
    covariates: tuple[str, ...] = Field(
        min_length=1,
        description="Ordered covariates regressed from control expression.",
    )
    immediate_early_genes_present: tuple[str, ...] = Field(
        description="Declared IEG symbols found and averaged in the slim atlas."
    )
    immediate_early_genes_missing: tuple[str, ...] = Field(
        description="Declared IEG symbols absent from the slim-atlas gene axis."
    )
    covariate_regression_includes_intercept: bool = Field(
        description="Whether the fitted covariate design includes an intercept column."
    )
    expression_shift_nonnegative: bool = Field(
        description="Whether each residual gene is shifted to a non-negative minimum."
    )
    residuals_sha256: str = Field(
        pattern=r"^[0-9a-f]{64}$",
        description="Digest of the adjusted and shifted control-expression matrix.",
    )
    regression_coefficients_sha256: str = Field(
        pattern=r"^[0-9a-f]{64}$",
        description="Digest of fitted covariate and intercept coefficients.",
    )
    gene_shifts_sha256: str = Field(
        pattern=r"^[0-9a-f]{64}$",
        description="Digest of per-gene shifts applied after residualization.",
    )

    @model_validator(mode="after")
    def validate_method(self) -> ControlResidualsMetadata:
        """Require the selected two-covariate, intercept-bearing residualization."""
        if self.covariates != CONTROL_RESIDUAL_COVARIATES:
            raise ValueError("control residuals require mitopercent and IEG_score")
        if not self.covariate_regression_includes_intercept:
            raise ValueError("control residualization must include an intercept")
        if not self.expression_shift_nonnegative:
            raise ValueError("control residuals must be shifted non-negative")
        if self.gene_ordering != "lexicographic Ensembl gene identifier":
            raise ValueError("control residual gene ordering is not the accepted rule")
        present = set(self.immediate_early_genes_present)
        missing = set(self.immediate_early_genes_missing)
        if present.intersection(missing):
            raise ValueError("an immediate-early gene cannot be present and missing")
        return self


class ControlProgramBankMetadata(ControlProgramRecord):
    """Bind one stable cNMF bank to its algorithm, axes, and realized rank."""

    method: str = Field(description="Named factorization and consensus procedure.")
    producer_recipe: ControlProgramRecipe = Field(
        description="Reviewed MANTRA source identities for every hand-ported operation."
    )
    control_cell_count: int = Field(
        gt=0,
        description="Control cells supplied to every parallel NMF restart.",
    )
    control_gene_count: int = Field(
        gt=0,
        description="Control-panel genes represented by each program column.",
    )
    nominal_rank: int = Field(
        gt=0,
        description="Programs fitted independently in each NMF restart.",
    )
    realized_rank: int = Field(
        gt=0,
        description="Consensus programs retained after run-coverage filtering.",
    )
    restarts: int = Field(
        gt=1,
        description="Parallel NMF initializations contributing candidate programs.",
    )
    max_iterations: int = Field(
        gt=0,
        description="Maximum multiplicative-update iterations allowed.",
    )
    completed_iterations: int = Field(
        gt=0,
        description="Multiplicative-update iterations executed before termination.",
    )
    random_seed: int = Field(
        ge=0,
        description="Shared NMF initialization and consensus KMeans seed.",
    )
    program_regularization: float = Field(
        ge=0.0,
        description="Regularization applied to NMF program loadings.",
    )
    usage_regularization: float = Field(
        ge=0.0,
        description="Regularization applied to cell-specific NMF usages.",
    )
    l1_ratio: float = Field(
        ge=0.0,
        le=1.0,
        description="Fraction of each NMF penalty assigned to L1 shrinkage.",
    )
    minimum_run_coverage: float = Field(
        gt=0.0,
        le=1.0,
        description="Minimum restart fraction required to retain a consensus program.",
    )
    factorization_backend: str = Field(
        description="Backend that fitted parallel NMF factors."
    )
    consensus_backend: str = Field(
        description="Backend that clustered normalized candidate programs."
    )
    consensus_initializations: int = Field(
        gt=0,
        description="Independent seeded KMeans starts used for consensus.",
    )
    control_cell_ids_sha256: str = Field(
        pattern=r"^[0-9a-f]{64}$",
        description="Digest of the fitted control-cell axis.",
    )
    control_gene_ids_sha256: str = Field(
        pattern=r"^[0-9a-f]{64}$",
        description="Digest of the fitted control-gene axis.",
    )
    programs_sha256: str = Field(
        pattern=r"^[0-9a-f]{64}$",
        description="Digest of the retained gene-by-program consensus matrix.",
    )
    programs_all_sha256: str = Field(
        pattern=r"^[0-9a-f]{64}$",
        description="Digest of normalized candidates from every NMF restart.",
    )
    cluster_assignments_sha256: str = Field(
        pattern=r"^[0-9a-f]{64}$",
        description="Digest of each candidate program's consensus-cluster assignment.",
    )
    reconstruction_coefficients_sha256: str = Field(
        pattern=r"^[0-9a-f]{64}$",
        description=(
            "Digest of control-cell nonnegative coefficients against the final "
            "consensus bank."
        ),
    )
    reconstruction_rmse_sha256: str = Field(
        pattern=r"^[0-9a-f]{64}$",
        description="Digest of per-control-cell final consensus reconstruction RMSE.",
    )
    mean_reconstruction_rmse: float = Field(
        ge=0.0,
        description="Mean final consensus reconstruction RMSE across control cells.",
    )
    maximum_reconstruction_rmse: float = Field(
        ge=0.0,
        description="Maximum final consensus reconstruction RMSE across control cells.",
    )
    run_coverage: tuple[float, ...] = Field(
        description="Restart coverage for every nominal consensus cluster."
    )

    @model_validator(mode="after")
    def validate_bank(self) -> ControlProgramBankMetadata:
        """Bind the realized rank to the declared stability-filtering result."""
        if len(self.run_coverage) != self.nominal_rank:
            raise ValueError("run coverage does not match the nominal rank")
        stable_count = sum(
            coverage >= self.minimum_run_coverage for coverage in self.run_coverage
        )
        if stable_count != self.realized_rank:
            raise ValueError("realized rank differs from stable run coverage")
        if self.factorization_backend != "gpu":
            raise ValueError("accepted control-program factorization requires GPU")
        if self.consensus_backend != "cpu":
            raise ValueError("accepted control-program consensus requires CPU")
        return self


@dataclass(frozen=True)
class ControlResiduals:
    """Carry one validated residualization result between pure functions."""

    residuals: np.ndarray
    cell_ids: np.ndarray
    gene_ids: np.ndarray
    regression_coefficients: np.ndarray
    gene_shifts: np.ndarray
    metadata: ControlResidualsMetadata


@dataclass(frozen=True)
class ControlProgramFit:
    """Carry deterministic cNMF arrays before persistence."""

    programs: np.ndarray
    programs_all: np.ndarray
    cluster_assignments: np.ndarray
    run_coverage: np.ndarray
    completed_iterations: int


@dataclass(frozen=True)
class ControlProgramBankFit(ControlProgramFit):
    """Add final-bank coefficients and diagnostics to one cNMF fit."""

    reconstruction_coefficients: np.ndarray
    reconstruction_rmse: np.ndarray


def configure_cuda_determinism(seed: int) -> None:
    """Apply the pinned MANTRA CUDA seed and deterministic backend settings."""
    observed_workspace = os.environ.get("CUBLAS_WORKSPACE_CONFIG")
    if observed_workspace not in DETERMINISTIC_CUBLAS_WORKSPACES:
        raise RuntimeError(
            "CUBLAS_WORKSPACE_CONFIG must select a deterministic cuBLAS workspace "
            "before CUDA initialization"
        )
    if (
        _CUDA_INITIALIZED_AT_MODULE_IMPORT
        and _CUBLAS_WORKSPACE_AT_MODULE_IMPORT not in DETERMINISTIC_CUBLAS_WORKSPACES
    ):
        raise RuntimeError(
            "CUDA was initialized before the deterministic cuBLAS workspace was selected"
        )
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False


def reviewed_control_program_recipe() -> ControlProgramRecipe:
    """Return the three immutable MANTRA authorities for the accepted port."""
    return ControlProgramRecipe(
        residualization=ControlProgramProducerEvidence(
            repository=MANTRA_REPOSITORY,
            commit="83af6df07a3958307b33bcd80b93592e80acbe51",
            path="src/mantra/sota/programs/discovery/run_programs_state.py",
            sha256="aca6f052762c5e244a4405b6efbc328618e2eba786212aa6b99af39848428af2",
            functions=("_compute_module_score", "_zscore", "regress_out_covariates"),
        ),
        factorization=ControlProgramProducerEvidence(
            repository=MANTRA_REPOSITORY,
            commit="6bedf04247d76738ff57ff51153166bde9757c10",
            path="SOTA/sota7/src/mantra_sota7/program_discovery/nmf_torch_batched.py",
            sha256="d99feb5ab66dbe59edfa36c1bf1130c1037df5741412d65d01a4b64620b7b35b",
            functions=("nmf_torch_batched",),
        ),
        consensus=ControlProgramProducerEvidence(
            repository=MANTRA_REPOSITORY,
            commit="6bedf04247d76738ff57ff51153166bde9757c10",
            path="SOTA/sota7/src/mantra_sota7/program_discovery/kmeans_gpu.py",
            sha256="897bbe8e2468b1ae3149885625314f450b43424706d296fffb27c57d437025c5",
            functions=("stability_kmeans_labels_centers",),
        ),
    )


def array_sha256(value: np.ndarray) -> str:
    """Digest an array together with its dtype and shape."""
    array = np.ascontiguousarray(value)
    digest = hashlib.sha256()
    digest.update(array.dtype.str.encode())
    digest.update(json.dumps(array.shape, separators=(",", ":")).encode())
    digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def build_control_residuals(
    slim_h5ad: Path,
    panel: ControlProgramPanel,
    *,
    control_label: str = "non-targeting",
) -> ControlResiduals:
    """Residualize selected log1p control expression against mito and IEG scores."""
    if control_label != panel.control_label:
        raise ValueError("configured control label differs from the typed panel")
    atlas_metadata = read_slim_atlas_metadata(slim_h5ad)
    with FastH5ADLoader(slim_h5ad) as atlas:
        _validate_slim_atlas(atlas, atlas_metadata)
        required_obs = {"gene", "mitopercent"}
        missing_obs = required_obs.difference(atlas.obs_keys)
        if missing_obs:
            raise ValueError(
                f"slim atlas lacks required obs fields: {sorted(missing_obs)}"
            )
        if "gene_name" not in atlas.var_keys:
            raise ValueError("slim atlas lacks var['gene_name']")

        labels = atlas.read_obs_column("gene").astype(str)
        control_rows = np.flatnonzero(labels == control_label).astype(np.int64)
        if control_rows.size != panel.fitted_cell_count:
            raise ValueError(
                "slim-atlas control-cell count differs from the control panel"
            )
        cell_ids = atlas.obs_names[control_rows].astype(str)
        cell_digest = ordered_values_sha256(tuple(cell_ids.tolist()))
        if cell_digest != panel.fitted_cell_ids_sha256:
            raise ValueError("slim-atlas control-cell order differs from the panel")

        # The accepted MANTRA builder sorted the supplied gene list before
        # matrix extraction. The typed panel still owns membership.
        control_gene_ids = tuple(sorted(panel.selected_gene_ids))
        selected = atlas.read_selected(
            row_idx=control_rows,
            gene_ids=control_gene_ids,
        )
        if selected.missing_gene_ids:
            raise ValueError(
                f"slim atlas lacks control-panel genes: {selected.missing_gene_ids[:8]}"
            )
        expression = np.asarray(selected.values, dtype=np.float32, order="C")

        symbols = atlas.read_var_column("gene_name").astype(str)
        symbol_to_indices: dict[str, list[int]] = {}
        for index, symbol in enumerate(symbols.tolist()):
            symbol_to_indices.setdefault(symbol, []).append(index)
        duplicated_iegs = tuple(
            symbol
            for symbol in panel.immediate_early_genes
            if len(symbol_to_indices.get(symbol, ())) > 1
        )
        if duplicated_iegs:
            raise ValueError(
                "slim atlas has ambiguous immediate-early-gene symbols: "
                f"{duplicated_iegs}"
            )
        present_iegs = tuple(
            symbol
            for symbol in panel.immediate_early_genes
            if len(symbol_to_indices.get(symbol, ())) == 1
        )
        missing_iegs = tuple(
            symbol
            for symbol in panel.immediate_early_genes
            if symbol not in present_iegs
        )
        if not present_iegs:
            raise ValueError("slim atlas contains none of the declared IEG symbols")
        ieg_columns = np.asarray(
            [symbol_to_indices[symbol][0] for symbol in present_iegs],
            dtype=np.int64,
        )
        ieg_score = (
            atlas.read_X_rows_cols(
                row_idx=control_rows,
                col_idx=ieg_columns,
            )
            .astype(np.float32)
            .mean(axis=1)
        )
        mito = atlas.read_obs_column("mitopercent")[control_rows].astype(np.float32)

    covariates = np.stack((_zscore(mito), _zscore(ieg_score)), axis=1)
    design = np.concatenate(
        (covariates, np.ones((covariates.shape[0], 1), dtype=np.float32)),
        axis=1,
    )
    coefficients = np.linalg.pinv(design.T @ design).astype(np.float32) @ (
        design.T @ expression
    )
    residuals = np.nan_to_num(
        expression - design @ coefficients,
        nan=0.0,
        posinf=0.0,
        neginf=0.0,
    ).astype(np.float32)
    minimum = residuals.min(axis=0)
    shifts = np.where(minimum < 0.0, -minimum, 0.0).astype(np.float32)
    residuals = np.asarray(residuals + shifts, dtype=np.float32, order="C")
    if not np.isfinite(residuals).all() or (residuals < 0.0).any():
        raise ValueError("control residuals must be finite and non-negative")

    gene_ids = np.asarray(control_gene_ids, dtype=str)
    metadata = ControlResidualsMetadata(
        method="linear_covariate_residuals_with_gene_shift",
        control_label=control_label,
        control_cell_count=int(control_rows.size),
        control_gene_count=int(gene_ids.size),
        control_cell_ids_sha256=cell_digest,
        control_gene_ids_sha256=ordered_values_sha256(control_gene_ids),
        gene_ordering="lexicographic Ensembl gene identifier",
        covariates=CONTROL_RESIDUAL_COVARIATES,
        immediate_early_genes_present=present_iegs,
        immediate_early_genes_missing=missing_iegs,
        covariate_regression_includes_intercept=True,
        expression_shift_nonnegative=True,
        residuals_sha256=array_sha256(residuals),
        regression_coefficients_sha256=array_sha256(coefficients),
        gene_shifts_sha256=array_sha256(shifts),
    )
    return ControlResiduals(
        residuals=residuals,
        cell_ids=cell_ids,
        gene_ids=gene_ids,
        regression_coefficients=coefficients,
        gene_shifts=shifts,
        metadata=metadata,
    )


def fit_control_programs(
    residuals: np.ndarray,
    *,
    components: int,
    restarts: int,
    max_iterations: int,
    tolerance: float,
    random_seed: int,
    program_regularization: float,
    usage_regularization: float,
    l1_ratio: float,
    consensus_initializations: int,
    minimum_run_coverage: float,
    device: str,
    compile_updates: bool,
) -> ControlProgramFit:
    """Fit GPU-resident batched NMF and deterministic CPU consensus KMeans."""
    values = np.asarray(residuals, dtype=np.float32, order="C")
    if values.ndim != 2 or min(values.shape) < 2:
        raise ValueError("control residuals must be a two-dimensional matrix")
    if not np.isfinite(values).all() or (values < 0.0).any():
        raise ValueError("control residuals must be finite and non-negative")
    configure_cuda_determinism(random_seed)
    if device.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for the accepted control-program build")
    value_tensor = torch.from_numpy(values).to(device=device, dtype=torch.float32)
    cells, genes = values.shape
    usages = (
        torch.abs(
            torch.randn(
                restarts,
                cells,
                components,
                device=device,
                dtype=torch.float32,
            )
        )
        * 0.1
    )
    programs = (
        torch.abs(
            torch.randn(
                restarts,
                components,
                genes,
                device=device,
                dtype=torch.float32,
            )
        )
        * 0.1
    )
    l1_usage = usage_regularization * l1_ratio
    l2_usage = usage_regularization * (1.0 - l1_ratio)
    l1_program = program_regularization * l1_ratio
    l2_program = program_regularization * (1.0 - l1_ratio)
    step_programs = (
        torch.compile(_update_programs) if compile_updates else _update_programs
    )
    step_usages = torch.compile(_update_usages) if compile_updates else _update_usages
    completed_iterations = 0
    epsilon = 1.0e-9
    for iteration in range(max_iterations):
        programs = step_programs(
            programs,
            usages,
            value_tensor,
            epsilon,
            l1_program,
            l2_program,
        )
        usages = step_usages(
            usages,
            programs,
            value_tensor,
            epsilon,
            l1_usage,
            l2_usage,
        )
        programs = torch.nan_to_num(programs, nan=0.0, posinf=0.0, neginf=0.0)
        usages = torch.nan_to_num(usages, nan=0.0, posinf=0.0, neginf=0.0)
        programs.clamp_(min=epsilon, max=1.0e4)
        usages.clamp_(min=epsilon, max=1.0e4)
        completed_iterations = iteration + 1
        if iteration % 10 == 0 or iteration == max_iterations - 1:
            error = _root_mean_square_error(value_tensor, usages, programs)
            if float(error.mean().item()) < tolerance:
                break

    program_array = programs.detach().cpu().numpy().astype(np.float32, copy=False)
    norms = np.linalg.norm(program_array, axis=2, keepdims=True) + 1.0e-8
    programs_all = (program_array / norms).reshape(
        restarts * components,
        genes,
    )
    consensus = KMeans(
        n_clusters=components,
        random_state=random_seed,
        n_init=cast(Any, consensus_initializations),
        max_iter=300,
        tol=1.0e-4,
        algorithm="lloyd",
    ).fit(np.asarray(programs_all, dtype=np.float32, order="C"))
    labels = np.asarray(consensus.labels_, dtype=np.int32)
    centers = np.asarray(consensus.cluster_centers_, dtype=np.float32)
    coverage = np.zeros(components, dtype=np.float32)
    for restart in range(restarts):
        present = np.unique(labels[restart * components : (restart + 1) * components])
        coverage[present] += 1.0
    coverage /= float(restarts)
    stable = coverage >= minimum_run_coverage
    return ControlProgramFit(
        programs=np.clip(centers[stable].T, 0.0, None).astype(np.float32),
        programs_all=np.asarray(programs_all, dtype=np.float32),
        cluster_assignments=labels,
        run_coverage=coverage,
        completed_iterations=completed_iterations,
    )


def fit_control_program_bank(
    residuals: np.ndarray,
    config: ControlProgramBankConfig,
    *,
    device: str,
) -> ControlProgramBankFit:
    """Fit cNMF and diagnose the final bank on its control-cell training matrix."""
    fit = fit_control_programs(
        residuals,
        components=config.nominal_components,
        restarts=config.restarts,
        max_iterations=config.max_iterations,
        tolerance=config.tolerance,
        random_seed=config.random_seed,
        program_regularization=config.program_regularization,
        usage_regularization=config.usage_regularization,
        l1_ratio=config.l1_ratio,
        consensus_initializations=config.consensus_initializations,
        minimum_run_coverage=config.minimum_run_coverage,
        device=device,
        compile_updates=config.compile_updates,
    )
    values = torch.from_numpy(np.asarray(residuals, dtype=np.float32, order="C")).to(
        device=device, dtype=torch.float32
    )
    reconstruction_coefficients, reconstruction_rmse = _fit_consensus_reconstruction(
        values,
        fit.programs,
        max_iterations=config.max_iterations,
        epsilon=1.0e-9,
    )
    return ControlProgramBankFit(
        programs=fit.programs,
        programs_all=fit.programs_all,
        cluster_assignments=fit.cluster_assignments,
        run_coverage=fit.run_coverage,
        completed_iterations=fit.completed_iterations,
        reconstruction_coefficients=reconstruction_coefficients,
        reconstruction_rmse=reconstruction_rmse,
    )


def build_control_program_bank(
    residuals_path: Path,
    residuals_metadata_path: Path,
    panel_path: Path,
    config: ControlProgramBankConfig,
    *,
    device: str = "cuda",
) -> tuple[
    ControlProgramBankFit,
    np.ndarray,
    np.ndarray,
    ControlProgramBankMetadata,
]:
    """Validate residual inputs, run accepted cNMF, and bind the stable bank."""
    residual_metadata = ControlResidualsMetadata.model_validate_json(
        residuals_metadata_path.read_text()
    )
    panel = ControlProgramPanel.model_validate_json(panel_path.read_text())
    with np.load(residuals_path, allow_pickle=False) as archive:
        required = {
            "residuals",
            "cell_ids",
            "gene_ids",
            "regression_coefficients",
            "gene_shifts",
        }
        if set(archive.files) != required:
            raise ValueError("control residual archive has an unexpected schema")
        residuals = np.asarray(archive["residuals"], dtype=np.float32)
        cell_ids = np.asarray(archive["cell_ids"]).astype(str)
        gene_ids = np.asarray(archive["gene_ids"]).astype(str)
        coefficients = np.asarray(archive["regression_coefficients"], dtype=np.float32)
        shifts = np.asarray(archive["gene_shifts"], dtype=np.float32)
    _validate_residual_archive(
        residuals,
        cell_ids,
        gene_ids,
        coefficients,
        shifts,
        residual_metadata,
        panel,
    )
    fit = fit_control_program_bank(
        residuals,
        config,
        device=device,
    )
    realized_rank = int(fit.programs.shape[1])
    if realized_rank != config.expected_realized_components:
        raise ValueError(
            "control-program realized rank differs from the accepted baseline: "
            f"{realized_rank} != {config.expected_realized_components}"
        )
    metadata = ControlProgramBankMetadata(
        method="gpu_batched_cnmf_cpu_consensus",
        producer_recipe=reviewed_control_program_recipe(),
        control_cell_count=int(residuals.shape[0]),
        control_gene_count=int(residuals.shape[1]),
        nominal_rank=config.nominal_components,
        realized_rank=realized_rank,
        restarts=config.restarts,
        max_iterations=config.max_iterations,
        completed_iterations=fit.completed_iterations,
        random_seed=config.random_seed,
        program_regularization=config.program_regularization,
        usage_regularization=config.usage_regularization,
        l1_ratio=config.l1_ratio,
        minimum_run_coverage=config.minimum_run_coverage,
        factorization_backend=config.factorization_backend,
        consensus_backend=config.consensus_backend,
        consensus_initializations=config.consensus_initializations,
        control_cell_ids_sha256=residual_metadata.control_cell_ids_sha256,
        control_gene_ids_sha256=residual_metadata.control_gene_ids_sha256,
        programs_sha256=array_sha256(fit.programs),
        programs_all_sha256=array_sha256(fit.programs_all),
        cluster_assignments_sha256=array_sha256(fit.cluster_assignments),
        reconstruction_coefficients_sha256=array_sha256(
            fit.reconstruction_coefficients
        ),
        reconstruction_rmse_sha256=array_sha256(fit.reconstruction_rmse),
        mean_reconstruction_rmse=float(fit.reconstruction_rmse.mean()),
        maximum_reconstruction_rmse=float(fit.reconstruction_rmse.max()),
        run_coverage=tuple(float(value) for value in fit.run_coverage),
    )
    return fit, cell_ids, gene_ids, metadata


def write_control_residuals(
    destination: Path,
    metadata_destination: Path,
    result: ControlResiduals,
) -> None:
    """Persist one residualization result with deterministic NPZ bytes."""
    write_deterministic_npz(
        destination,
        residuals=result.residuals,
        cell_ids=result.cell_ids,
        gene_ids=result.gene_ids,
        regression_coefficients=result.regression_coefficients,
        gene_shifts=result.gene_shifts,
    )
    _write_record(metadata_destination, result.metadata)


def write_control_program_bank(
    destination: Path,
    metadata_destination: Path,
    fit: ControlProgramBankFit,
    cell_ids: np.ndarray,
    gene_ids: np.ndarray,
    metadata: ControlProgramBankMetadata,
) -> None:
    """Persist one role-named cNMF bank without dimension-specific aliases."""
    write_deterministic_npz(
        destination,
        programs=fit.programs,
        programs_all=fit.programs_all,
        cluster_assignments=fit.cluster_assignments,
        run_coverage=fit.run_coverage,
        reconstruction_coefficients=fit.reconstruction_coefficients,
        reconstruction_rmse=fit.reconstruction_rmse,
        cell_ids=cell_ids,
        gene_ids=gene_ids,
    )
    _write_record(metadata_destination, metadata)


def write_deterministic_npz(destination: Path, **arrays: np.ndarray) -> None:
    """Write sorted NumPy members with fixed ZIP metadata for stable bytes."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        destination,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for name in sorted(arrays):
            buffer = BytesIO()
            np.lib.format.write_array(
                buffer,
                np.asarray(arrays[name]),
                allow_pickle=False,
            )
            member = zipfile.ZipInfo(f"{name}.npy", date_time=(1980, 1, 1, 0, 0, 0))
            member.compress_type = zipfile.ZIP_DEFLATED
            member.external_attr = 0o600 << 16
            archive.writestr(
                member,
                buffer.getvalue(),
                compress_type=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            )


def _zscore(values: np.ndarray) -> np.ndarray:
    """Apply the exact population standardization used by the accepted builder."""
    array = np.asarray(values, dtype=np.float32).reshape(-1)
    mean = np.nanmean(array)
    filled = np.where(np.isnan(array), mean, array)
    standard_deviation = np.nanstd(filled) + 1.0e-9
    return ((filled - mean) / standard_deviation).astype(np.float32)


def _validate_slim_atlas(
    atlas: FastH5ADLoader,
    metadata: SlimAtlasMetadata,
) -> None:
    """Reject a noncanonical expression surface or an altered atlas axis."""
    if metadata.expression_surface != CANONICAL_EXPRESSION_SURFACE:
        raise ValueError("control residuals require the canonical log1p_cp10k surface")
    if metadata.target_sum != CANONICAL_TARGET_SUM:
        raise ValueError(
            "control residuals require a 10,000-count normalization target"
        )
    if atlas.n_obs != metadata.selected_cell_count:
        raise ValueError("slim-atlas cell count differs from its canonical metadata")
    if atlas.n_vars != metadata.gene_count:
        raise ValueError("slim-atlas gene count differs from its canonical metadata")
    cell_ids = tuple(str(value) for value in atlas.obs_names.tolist())
    gene_ids = tuple(str(value) for value in atlas.var_names.tolist())
    if ordered_values_sha256(cell_ids) != metadata.selected_cell_ids_sha256:
        raise ValueError("slim-atlas cell axis differs from its canonical metadata")
    if ordered_values_sha256(gene_ids) != metadata.gene_ids_sha256:
        raise ValueError("slim-atlas gene axis differs from its canonical metadata")


def _fit_consensus_reconstruction(
    values: torch.Tensor,
    programs: np.ndarray,
    *,
    max_iterations: int,
    epsilon: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Fit nonnegative control-cell coefficients against the final consensus bank."""
    program_tensor = torch.from_numpy(programs.T).to(
        device=values.device,
        dtype=torch.float32,
    )
    usages = torch.full(
        (1, values.shape[0], program_tensor.shape[0]),
        0.1,
        device=values.device,
        dtype=torch.float32,
    )
    batched_programs = program_tensor.unsqueeze(0)
    for _ in range(max_iterations):
        usages = _update_usages(
            usages,
            batched_programs,
            values,
            epsilon,
            0.0,
            0.0,
        )
        usages = torch.nan_to_num(usages, nan=0.0, posinf=0.0, neginf=0.0)
        usages.clamp_(min=epsilon, max=1.0e4)
    coefficients = usages[0]
    reconstructed = torch.matmul(coefficients, program_tensor)
    reconstruction_rmse = torch.sqrt(
        torch.mean(torch.square(values - reconstructed), dim=1)
    )
    return (
        coefficients.detach().cpu().numpy().astype(np.float32, copy=False),
        reconstruction_rmse.detach().cpu().numpy().astype(np.float32, copy=False),
    )


def _update_programs(
    programs: torch.Tensor,
    usages: torch.Tensor,
    values: torch.Tensor,
    epsilon: float,
    l1_penalty: float,
    l2_penalty: float,
) -> torch.Tensor:
    """Apply one multiplicative update to all restart-specific programs."""
    transposed = usages.transpose(1, 2)
    numerator = torch.matmul(transposed, values.unsqueeze(0))
    denominator = torch.matmul(torch.matmul(transposed, usages), programs)
    return programs * (
        numerator / (denominator + l1_penalty + l2_penalty * programs + epsilon)
    )


def _update_usages(
    usages: torch.Tensor,
    programs: torch.Tensor,
    values: torch.Tensor,
    epsilon: float,
    l1_penalty: float,
    l2_penalty: float,
) -> torch.Tensor:
    """Apply one multiplicative update to all restart-specific cell usages."""
    transposed = programs.transpose(1, 2)
    numerator = torch.matmul(values.unsqueeze(0), transposed)
    denominator = torch.matmul(usages, torch.matmul(programs, transposed))
    return usages * (
        numerator / (denominator + l1_penalty + l2_penalty * usages + epsilon)
    )


def _root_mean_square_error(
    values: torch.Tensor,
    usages: torch.Tensor,
    programs: torch.Tensor,
) -> torch.Tensor:
    """Compute one reconstruction error per restart without a full 3D result."""
    errors = torch.zeros(
        usages.shape[0],
        device=programs.device,
        dtype=torch.float32,
    )
    for start in range(0, values.shape[0], 10_000):
        stop = min(start + 10_000, values.shape[0])
        difference = values[start:stop].unsqueeze(0) - torch.matmul(
            usages[:, start:stop], programs
        )
        errors += torch.sum(difference * difference, dim=(1, 2))
    return torch.sqrt(errors / values.numel())


def _validate_residual_archive(
    residuals: np.ndarray,
    cell_ids: np.ndarray,
    gene_ids: np.ndarray,
    coefficients: np.ndarray,
    shifts: np.ndarray,
    metadata: ControlResidualsMetadata,
    panel: ControlProgramPanel,
) -> None:
    """Reject altered residual arrays, axes, panel identity, or shapes."""
    if metadata.control_cell_count != panel.fitted_cell_count:
        raise ValueError("control residual cell count differs from the typed panel")
    if metadata.control_cell_ids_sha256 != panel.fitted_cell_ids_sha256:
        raise ValueError("control residual cell axis differs from the typed panel")
    if metadata.control_gene_count != panel.selected_gene_count:
        raise ValueError("control residual gene count differs from the typed panel")
    if residuals.shape != (metadata.control_cell_count, metadata.control_gene_count):
        raise ValueError("control residual shape differs from its metadata")
    if cell_ids.shape != (metadata.control_cell_count,):
        raise ValueError("control residual cell axis differs from its metadata")
    if gene_ids.shape != (metadata.control_gene_count,):
        raise ValueError("control residual gene axis differs from its metadata")
    if tuple(gene_ids.tolist()) != tuple(sorted(panel.selected_gene_ids)):
        raise ValueError("control residual gene axis differs from the typed panel")
    if (
        ordered_values_sha256(tuple(cell_ids.tolist()))
        != metadata.control_cell_ids_sha256
    ):
        raise ValueError("control residual cell-axis digest changed")
    if (
        ordered_values_sha256(tuple(gene_ids.tolist()))
        != metadata.control_gene_ids_sha256
    ):
        raise ValueError("control residual gene-axis digest changed")
    if array_sha256(residuals) != metadata.residuals_sha256:
        raise ValueError("control residual values changed")
    if array_sha256(coefficients) != metadata.regression_coefficients_sha256:
        raise ValueError("control regression coefficients changed")
    if array_sha256(shifts) != metadata.gene_shifts_sha256:
        raise ValueError("control gene shifts changed")


def _write_record(destination: Path, record: BaseModel) -> None:
    """Write one immutable JSON record."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(record.model_dump_json(indent=2) + "\n")
