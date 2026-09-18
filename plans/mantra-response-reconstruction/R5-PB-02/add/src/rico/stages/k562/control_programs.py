"""Expose K562 control residualization as a VIPER Build stage."""

from viper.stages import build

from rico.cell_types.k562.control_programs import (
    build_control_residuals,
    write_control_residuals,
)
from rico.cell_types.k562.gene_panels import ControlProgramPanel
from rico.config import ControlResidualsConfig


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
