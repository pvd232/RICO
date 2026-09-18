"""Verify deterministic K562 control-expression residualization."""

from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import pytest

from rico.cell_types.k562.control_programs import (
    CANONICAL_EXPRESSION_SURFACE,
    CANONICAL_TARGET_SUM,
    CONTROL_RESIDUAL_COVARIATES,
    _zscore,
    build_control_residuals,
    write_control_residuals,
)
from rico.cell_types.k562.atlas import SlimAtlasMetadata
from rico.cell_types.k562.gene_panels import (
    ControlProgramPanel,
    ExcludedGene,
    GeneVariability,
    ordered_values_sha256,
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
