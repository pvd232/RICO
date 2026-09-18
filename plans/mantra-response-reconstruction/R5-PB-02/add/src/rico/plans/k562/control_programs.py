"""Declare the download-rooted K562 control-residual build."""

from viper.authoring import experiment, replicate, stage, variant
from viper.benchmark import RunArtifactDraft
from viper.outputs import StageOutputs, output

from rico.artifact_loaders.path_file import load as load_path
from rico.config import ControlResidualsConfig
from rico.stages.k562.control_programs import control_residuals


def declare_control_residuals_experiment(
    *,
    slim_atlas: RunArtifactDraft,
    control_program_panel: RunArtifactDraft,
):
    """Declare source-closed residualization of canonical control cells."""
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
    return experiment(
        experiment_id="k562_control_residuals",
        variants=(
            variant(
                "canonical",
                stages=(residual_stage,),
                estimator=residual_stage.outputs["control_residuals"],
            ),
        ),
        replicates=(replicate(seed=0),),
    )
