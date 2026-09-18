"""Build deterministic K562 control-expression residuals for cNMF."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from io import BytesIO
import json
from pathlib import Path
import zipfile

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator

from rico.cell_types.k562.atlas import SlimAtlasMetadata, read_slim_atlas_metadata
from rico.cell_types.k562.gene_panels import ControlProgramPanel, ordered_values_sha256
from rico.data.fast_h5ad import FastH5ADLoader

CONTROL_RESIDUAL_COVARIATES = ("mitopercent", "IEG_score")
CANONICAL_EXPRESSION_SURFACE = "log1p_cp10k"
CANONICAL_TARGET_SUM = 10_000.0


class ControlProgramRecord(BaseModel):
    """Make persisted control-program records immutable and reject unknown fields."""

    model_config = ConfigDict(extra="forbid", frozen=True)


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


@dataclass(frozen=True)
class ControlResiduals:
    """Carry one validated residualization result between pure functions."""

    residuals: np.ndarray
    cell_ids: np.ndarray
    gene_ids: np.ndarray
    regression_coefficients: np.ndarray
    gene_shifts: np.ndarray
    metadata: ControlResidualsMetadata


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


def _write_record(destination: Path, record: BaseModel) -> None:
    """Write one immutable JSON record."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(record.model_dump_json(indent=2) + "\n")
