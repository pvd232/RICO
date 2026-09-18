"""Declare download-rooted K562 control residual and cNMF program builds."""

from viper.authoring import StageInputDraft, experiment, replicate, stage, variant
from viper.benchmark import RunArtifactDraft
from viper.outputs import StageOutputs, output

from rico.artifact_loaders.path_file import load as load_path
from rico.config import ControlProgramBankConfig, ControlResidualsConfig
from rico.stages.k562.control_programs import (
    control_program_bank,
    control_residuals,
)


def declare_control_program_bank_experiment(
    *,
    slim_atlas: RunArtifactDraft,
    control_program_panel: RunArtifactDraft,
):
    """Declare source-closed residualization followed by the accepted cNMF fit."""
    residual_stage = stage(
        control_residuals,
        stage_id="build_control_residuals",
        config=ControlResidualsConfig(),
        inputs={
            "slim_atlas": slim_atlas,
            "control_program_panel": control_program_panel,
        },
        outputs=StageOutputs.model_validate(
            {
                "control_residuals": output(
                    path="programs/control_residuals.npz",
                    loader=load_path,
                    data_role="training",
                ),
                "control_residuals_metadata": output(
                    path="programs/control_residuals.json",
                    loader=load_path,
                    data_role="training",
                ),
            }
        ),
        input_roots="download",
    )
    bank_stage = _declare_control_program_bank_stage(
        control_residuals=residual_stage.outputs["control_residuals"],
        control_residuals_metadata=residual_stage.outputs["control_residuals_metadata"],
        control_program_panel=control_program_panel,
    )
    return experiment(
        experiment_id="k562_control_program_bank",
        variants=(
            variant(
                "canonical",
                stages=(residual_stage, bank_stage),
                estimator=bank_stage.outputs["control_program_bank"],
            ),
        ),
        replicates=(replicate(seed=0),),
    )


def declare_control_program_bank_materialization_experiment(
    *,
    control_residuals: RunArtifactDraft,
    control_residuals_metadata: RunArtifactDraft,
    control_program_panel: RunArtifactDraft,
):
    """Fit cNMF from the accepted residual artifact without rebuilding it."""
    bank_stage = _declare_control_program_bank_stage(
        control_residuals=control_residuals,
        control_residuals_metadata=control_residuals_metadata,
        control_program_panel=control_program_panel,
    )
    return experiment(
        experiment_id="k562_control_program_bank_materialization",
        variants=(
            variant(
                "canonical",
                stages=(bank_stage,),
                estimator=bank_stage.outputs["control_program_bank"],
            ),
        ),
        replicates=(replicate(seed=0),),
    )


def _declare_control_program_bank_stage(
    *,
    control_residuals: StageInputDraft,
    control_residuals_metadata: StageInputDraft,
    control_program_panel: RunArtifactDraft,
):
    """Declare the shared download-rooted cNMF Build stage."""
    return stage(
        control_program_bank,
        stage_id="build_control_program_bank",
        config=ControlProgramBankConfig(),
        inputs={
            "control_residuals": control_residuals,
            "control_residuals_metadata": control_residuals_metadata,
            "control_program_panel": control_program_panel,
        },
        outputs=StageOutputs.model_validate(
            {
                "control_program_bank": output(
                    path="programs/control_program_bank.npz",
                    loader=load_path,
                    data_role="training",
                ),
                "control_program_bank_metadata": output(
                    path="programs/control_program_bank.json",
                    loader=load_path,
                    data_role="training",
                ),
            }
        ),
        input_roots="download",
    )
