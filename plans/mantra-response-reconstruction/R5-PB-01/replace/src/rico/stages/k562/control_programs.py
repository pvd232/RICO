"""Expose K562 control residualization and cNMF as VIPER Build stages."""

from viper.stages import build

from rico.cell_types.k562.control_programs import (
    build_control_program_bank,
    build_control_residuals,
    write_control_program_bank,
    write_control_residuals,
)
from rico.cell_types.k562.gene_panels import ControlProgramPanel
from rico.config import ControlProgramBankConfig, ControlResidualsConfig


@build(config=ControlResidualsConfig)
def control_residuals(context) -> None:
    """Build covariate-adjusted control expression from the canonical slim atlas."""
    panel = ControlProgramPanel.model_validate_json(
        context.inputs["control_program_panel"].read_text()
    )
    result = build_control_residuals(
        context.inputs["slim_atlas"],
        panel,
        control_label=context.config.control_label,
    )
    write_control_residuals(
        context.outputs["control_residuals"],
        context.outputs["control_residuals_metadata"],
        result,
    )


@build(config=ControlProgramBankConfig)
def control_program_bank(context) -> None:
    """Fit the accepted GPU cNMF bank and retain all stable programs."""
    fit, cell_ids, gene_ids, metadata = build_control_program_bank(
        context.inputs["control_residuals"],
        context.inputs["control_residuals_metadata"],
        context.inputs["control_program_panel"],
        context.config,
        device="cuda",
    )
    write_control_program_bank(
        context.outputs["control_program_bank"],
        context.outputs["control_program_bank_metadata"],
        fit,
        cell_ids,
        gene_ids,
        metadata,
    )
