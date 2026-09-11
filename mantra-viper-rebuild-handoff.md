# MANTRA and VIPER: model rebuild handoff

## Objective and checkout identity

Rebuild the two MANTRA models described in the architecture papers: the Hopfield predictor reporting PearsonDelta 0.5861640938949398 (résumé shorthand ~0.58), and the selected single-query MIL predictor reporting 0.6025499488874759 (~0.602). Reconstruct preprocessing and training as well as inference. Use VIPER for experiment declarations, execution, measurements, and verification; MANTRA owns the model and biological transformations.

The verified MANTRA checkout is `/Users/machina/Developer/ChatGPT/mantra`, revision `6916d01404ecebe4ee21b29ca74724a8a8ced7c2`. The earlier location `/Users/machina/Developer/mantra` no longer exists. Another directory, `/Users/machina/Developer/mantra_local`, exists; it was not selected for this source map.

VIPER is `/Users/machina/Developer/ChatGPT/viper`, revision `178653de710763d1f9d171b77d8eade89e498b10`. Its package metadata identifies distribution `viper-provenance`, version `0.1.0a3`, imported as `viper`. Recheck both working trees before edits. MANTRA currently has modifications and type changes under historical `.envs/.../share/terminfo`; preserve them.

This handoff locates source and stored specifications. It does not report a fresh training run or numerical reproduction. The short papers describe architecture; exact reproduction must retain the recorded row memberships, normalization populations, seeds, and data identities even though those details were omitted from the résumé.

## Start here


| Location | Purpose |
|---|---|
| [AGENTS.md](/Users/machina/Developer/ChatGPT/mantra/AGENTS.md) | Repository instructions; also inspect any narrower instructions before changes. |
| [experiments/v1953_direct_mil_simplified_scorer_promotion/specs/promotion.yaml](/Users/machina/Developer/ChatGPT/mantra/experiments/v1953_direct_mil_simplified_scorer_promotion/specs/promotion.yaml) | Selected MIL checkpoint, expected result, hashes, and promotion target. |
| [reinstantiation/APPLICATION_VERIFICATION.json](/Users/machina/Developer/ChatGPT/mantra/reinstantiation/APPLICATION_VERIFICATION.json) | Exact saved-model replay command, environment, input hashes, and expected outputs. |
| [reinstantiation/README.md](/Users/machina/Developer/ChatGPT/mantra/reinstantiation/README.md) | Restoration overview and archived environment route. |
| [experiments/v1938_sota_clean_repro/README.md](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/README.md) | Maintained model implementation organization. |
| [experiments/v1938_sota_clean_repro/JOURNAL.md](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/JOURNAL.md) | Hopfield raw-gene readout result and experiment history; search 0.586164 and RAW_GENE_READOUT_TUNING_RESULTS. |

The two explanatory papers are [Hopfield](/Users/machina/Documents/MANTRA/mantra-architecture.pdf) and [MIL](/Users/machina/Documents/MANTRA/mantra-mil-architecture.pdf), with editable [Hopfield LaTeX](/Users/machina/Documents/MANTRA/mantra-architecture.tex) and [MIL LaTeX](/Users/machina/Documents/MANTRA/mantra-mil-architecture.tex). Their GitHub citations pin the MANTRA revision above.

## Model identities: avoid mixing configurations

**Hopfield:** biological descriptors, predicted control state, and response-group summaries form a 187-dimensional encoder input. The MLP maps 187 → 384 → 384 → 128 with SiLU, LayerNorm, and normalized output. Training matches response-derived donor distributions with KL divergence, plus an active response-bank KL objective weighted 0.8. The cited configuration uses teacher temperature 0.043 and embedding temperature 0.041; selected raw-gene retrieval uses 0.055. Its final values are full observed 5,000-gene response profiles, followed by a predicted shift from matched controls to the global-control reference. Do not substitute coefficient decoding for this final raw-gene readout.

**MIL:** selected seed 123460; one student query; teacher bags of up to 192 cells, each with 210 matched-response coefficients and 19 control activities. Teacher conditioning adds a 123-dimensional descriptor after projection, uses four-head self-attention, and attention-pools to a normalized 128-dimensional key. The student learns one 128-dimensional query from biological inputs. Teacher training combines coefficient and decoded-gene MSE; student training combines embedding MSE and retrieved-coefficient MSE. The selected setup uses 48 teacher epochs, 96 student epochs, learning rates 0.001, and student retrieval temperature 0.06; inspect seed offsets and checkpoint-selection settings in the resolved configuration and trainer.

MIL inference uses query/key similarity divided by 0.10 plus biological-family similarity weighted 12. It reads all 1,427 donor entries. Direct control-similarity weight is zero, but control information still enters the teacher and final correction. Donor coefficients undergo covariance shrinkage with ridge 1 and a 0.30 blend with four teacher-nearest neighbors. Final prediction decodes coefficients, adds a ridge residual correction (246 inputs, penalty 1400, scale 0.58), shifts to the global-control reference, and applies per-gene slopes (ridge 10, clipped to [0.75, 1.35]).

Two easy configuration traps:

- The historical resolved training YAML contains `proto_count: 11`; `run_causal_reconstruction.py` overrides it to **1** and constructs a single-query student. The selected build report confirms one slot. Reading YAML alone gives the wrong architecture.
- `memory_rank: 192` remains in the scorer configuration, but `memory_transform: ridge_whiten` uses covariance shrinkage. It is not a rank-192 PCA truncation. Several other generic scorer fields are inactive in direct-MIL mode.

The encoder's training is supervised metric learning with soft response-similarity targets. Do not label it OpenAI CLIP: the inspected Hopfield trainer uses one shared encoder and KL distribution matching, rather than paired modality encoders trained with the CLIP objective.

## Shared preprocessing: expression to model inputs

Preserve perturbation IDs, gene ordering, cell membership, decoder orientation, normalization statistics, and response reference at every handoff. Shape agreement alone cannot establish equivalent inputs.

| Location | Purpose |
|---|---|
| [experiments/v1931_sota_freeze/src/step00_inputs/stage04_control_programs.py](/Users/machina/Developer/ChatGPT/mantra/experiments/v1931_sota_freeze/src/step00_inputs/stage04_control_programs.py) | Historical control-program construction: adjusted expression and consensus NMF. |
| [experiments/v1931_sota_freeze/src/step00_inputs/stage06_control_state.py](/Users/machina/Developer/ChatGPT/mantra/experiments/v1931_sota_freeze/src/step00_inputs/stage06_control_state.py) | Control-program projection; inspect project_control_programs. |
| [experiments/v1889_strict_source_only_step01_full_chain/src/step01_hopfield/response_programs/perturbation_mean_cell_svd.py](/Users/machina/Developer/ChatGPT/mantra/experiments/v1889_strict_source_only_step01_full_chain/src/step01_hopfield/response_programs/perturbation_mean_cell_svd.py) | Historical matching, response dictionary fitting, coefficient projection, and rotation. |
| [experiments/v1938_sota_clean_repro/src/step00/](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/src/step00) | Maintained input builders. Relevant packages: control_programs, cellwise_response_basis, cellwise_direct_response, direct_response_basis, family64, ctrl19, core83, response_block(s), gene_shift, assembly, pipeline. |
| [experiments/v1938_sota_clean_repro/specs/step00/](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/specs/step00) | Builder configurations; follow refs and source inputs rather than using defaults from unrelated experiments. |
| [experiments/v1938_sota_clean_repro/specs/paths/family64_source_paths.yaml](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/specs/paths/family64_source_paths.yaml) | Exact biological-prior source bindings. |
| [experiments/v1938_sota_clean_repro/specs/step00/build_family64.yaml](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/specs/step00/build_family64.yaml) | Selected prior blocks, penalties, and projection dimensions. |
| [experiments/v1938_sota_clean_repro/src/step00/family64/builder.py](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/src/step00/family64/builder.py) | Grouped ridge from biological priors to response coefficients; compressed biological descriptor. |
| [experiments/v1938_sota_clean_repro/scripts/archive/run_ctrl19_hold_proxy_apples_to_apples.py](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/scripts/archive/run_ctrl19_hold_proxy_apples_to_apples.py) | Historical control-state prediction; build_exact_decoder_prediction. |
| [experiments/v1938_sota_clean_repro/src/step00/core83/transforms.py](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/src/step00/core83/transforms.py) | 19 control activities plus 64 coordinates of predicted control coefficients. |
| [experiments/v1938_sota_clean_repro/src/step00/response_block/transforms.py](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/src/step00/response_block/transforms.py) | Signed coefficient occupancies and descriptor-neighbor prediction of response summaries. |
| [experiments/v1938_sota_clean_repro/src/step00/gene_shift/transforms.py](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/src/step00/gene_shift/transforms.py) | Predicted control-reference shift in gene space. |
| [experiments/v1938_sota_clean_repro/scripts/README.md](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/scripts/README.md) | Builder entry-point index; inspect the script associated with each selected YAML. |

Biological sources include CORUM complexes, protein-interaction features, directed regulatory-graph features, and functional annotations. Use the bound source files for exact membership. The historical MIL student augments the response-informed descriptor with raw interaction features; do not infer its input width from a directory named `family64`.

## Hopfield source and selected result

| Location | Purpose |
|---|---|
| [experiments/v1938_sota_clean_repro/src/step01/hopfield/encoder.py](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/src/step01/hopfield/encoder.py) | HopfieldEncoder network. |
| [experiments/v1938_sota_clean_repro/src/step01/hopfield/train.py](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/src/step01/hopfield/train.py) | Target distributions, masking, KL losses, response-bank supervision, optimizer, and checkpoint selection. |
| [experiments/v1938_sota_clean_repro/src/step01/hopfield/model.py](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/src/step01/hopfield/model.py) | Response-bank transforms and model operations. |
| [experiments/v1938_sota_clean_repro/src/step01/hopfield/](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/src/step01/hopfield) | Read config, loader, runner, and writer alongside the encoder. |
| [experiments/v1938_sota_clean_repro/runs/clean_shared_mil_proto_hyperparam_sweep_20260714T063000Z/base_step01/base_lr2e4/candidates/mixed_src_snk_ripple_raw_pen1_base_lr2e4/diagnostics/BASE_STEP01_RESULT_REPORT.json](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/runs/clean_shared_mil_proto_hyperparam_sweep_20260714T063000Z/base_step01/base_lr2e4/candidates/mixed_src_snk_ripple_raw_pen1_base_lr2e4/diagnostics/BASE_STEP01_RESULT_REPORT.json) | Saved encoder configuration used in the architecture trace. |
| [experiments/v1938_sota_clean_repro/runs/matrix_fit_only_bold_step02_20260715T083000Z/scripts/run_raw_gene_readout_tuning.py](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/runs/matrix_fit_only_bold_step02_20260715T083000Z/scripts/run_raw_gene_readout_tuning.py) | Selected final readout; predict_raw_gene_readout. |
| [experiments/v1938_sota_clean_repro/runs/matrix_fit_only_bold_step02_20260715T083000Z/diagnostics/RAW_GENE_READOUT_TUNING_RESULTS.json](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/runs/matrix_fit_only_bold_step02_20260715T083000Z/diagnostics/RAW_GENE_READOUT_TUNING_RESULTS.json) | Readout search results: locate the selected temperature and score, then follow its checkpoint binding. |

Do not treat the Hopfield checkpoints referenced by the MIL full-stack configuration as automatically identifying this 0.586 raw-gene model. The generic MIL runtime carries base/projected Step01 bindings even when direct-MIL is the selected estimator.

## MIL training, retrieval, and correction

| Location | Purpose |
|---|---|
| [experiments/v1951_direct_mil_causal_reconstruction/scripts/run_causal_reconstruction.py](/Users/machina/Developer/ChatGPT/mantra/experiments/v1951_direct_mil_causal_reconstruction/scripts/run_causal_reconstruction.py) | Training owner; inspect train_variant, replace_training_memory, and the single-query overrides. |
| [experiments/v1951_direct_mil_causal_reconstruction/specs/resolved/transformed_training_memory.yaml](/Users/machina/Developer/ChatGPT/mantra/experiments/v1951_direct_mil_causal_reconstruction/specs/resolved/transformed_training_memory.yaml) | Resolved training inputs and settings; apply runner overrides. |
| [experiments/v1952_direct_mil_control_term_ablation/scripts/run_control_term_multiseed.py](/Users/machina/Developer/ChatGPT/mantra/experiments/v1952_direct_mil_control_term_ablation/scripts/run_control_term_multiseed.py) | Reconstructs the selected seed under the no-control scorer; follow its calls into v1951. |
| [experiments/v1952_direct_mil_control_term_ablation/specs/control_term_ablation.yaml](/Users/machina/Developer/ChatGPT/mantra/experiments/v1952_direct_mil_control_term_ablation/specs/control_term_ablation.yaml) | Seed/scorer experiment specification. |
| [experiments/v1952_direct_mil_control_term_ablation/diagnostics/seed_123460/build_report.json](/Users/machina/Developer/ChatGPT/mantra/experiments/v1952_direct_mil_control_term_ablation/diagnostics/seed_123460/build_report.json) | Selected model dimensions, seed, and recorded scorer behavior. |
| [experiments/v1938_sota_clean_repro/src/step02/mil_proto/loader.py](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/src/step02/mil_proto/loader.py) | build_bags: projected treated coefficients minus barycentric control coefficients, concatenated with control activities. |
| [experiments/v1938_sota_clean_repro/src/step02/mil_proto/models.py](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/src/step02/mil_proto/models.py) | MILTeacher and MILPrototypeStudent. |
| [experiments/v1938_sota_clean_repro/src/step02/mil_proto/spec.py](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/src/step02/mil_proto/spec.py) | Resolves active model/loss policies. |
| [experiments/v1938_sota_clean_repro/src/step02/mil_proto/prepare.py](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/src/step02/mil_proto/prepare.py) | Builds tensors and training bundles. |
| [experiments/v1938_sota_clean_repro/src/step02/mil_proto/train.py](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/src/step02/mil_proto/train.py) | Teacher and student optimization. |
| [experiments/v1938_sota_clean_repro/src/step02/mil_proto/objective.py](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/src/step02/mil_proto/objective.py) | Active coefficient-reconstruction and embedding-alignment losses. |
| [experiments/v1938_sota_clean_repro/src/step02/state.py](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/src/step02/state.py) | ridge_whiten_shrink_memory, smooth_memory_by_teacher_neighbors, build_slot_logits. |
| [experiments/v1938_sota_clean_repro/src/step02/proposal.py](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/src/step02/proposal.py) | Donor aggregation and direct coefficient prediction. |
| [experiments/v1938_sota_clean_repro/src/step02/mil_proto/direct_step03.py](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/src/step02/mil_proto/direct_step03.py) | fit_direct_step03_artifacts and apply_fixed_gene_slope. |
| [experiments/v1938_sota_clean_repro/src/step03/ridge.py](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/src/step03/ridge.py) | Residual ridge fitting, shrinkage, and reference shift. |
| [experiments/v1953_direct_mil_simplified_scorer_promotion/specs/runtime/full_stack.yaml](/Users/machina/Developer/ChatGPT/mantra/experiments/v1953_direct_mil_simplified_scorer_promotion/specs/runtime/full_stack.yaml) | Exact checkpoint and runtime bindings. |
| [experiments/v1953_direct_mil_simplified_scorer_promotion/specs/runtime/step02.yaml](/Users/machina/Developer/ChatGPT/mantra/experiments/v1953_direct_mil_simplified_scorer_promotion/specs/runtime/step02.yaml) | Selected inference scorer. |
| [experiments/v1953_direct_mil_simplified_scorer_promotion/specs/runtime/step03.yaml](/Users/machina/Developer/ChatGPT/mantra/experiments/v1953_direct_mil_simplified_scorer_promotion/specs/runtime/step03.yaml) | Selected correction and gene calibration. |
| [experiments/v1953_direct_mil_simplified_scorer_promotion/specs/runtime/step02_input_contract.yaml](/Users/machina/Developer/ChatGPT/mantra/experiments/v1953_direct_mil_simplified_scorer_promotion/specs/runtime/step02_input_contract.yaml) | Explicit feature, response, decoder-related, and cellwise input paths. |
| [experiments/v1953_direct_mil_simplified_scorer_promotion/scripts/run_result.py](/Users/machina/Developer/ChatGPT/mantra/experiments/v1953_direct_mil_simplified_scorer_promotion/scripts/run_result.py) | Saved-checkpoint replay entry point; not a complete from-scratch trainer. |
| [experiments/v1938_sota_clean_repro/src/runtime/pipeline.py](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/src/runtime/pipeline.py) | Maintained full-stack orchestration. |
| [src/mantra/eval/eval.py](/Users/machina/Developer/ChatGPT/mantra/src/mantra/eval/eval.py) | pearson_delta; preserve the original metric definition. |

## Restoration and dependency closure

A Git checkout is not a complete training dataset. The signed reinstantiation materials identify archived project files and the historical runtime. Start by checking local availability and identities against the manifests. For every loaded NPZ/H5AD/checkpoint, identify its producer and raw-source dependencies; otherwise a checkpoint replay can be mistaken for a full rebuild.

| Location | Purpose |
|---|---|
| [reinstantiation/REINSTANTIATION_ROOT_RELEASE.json](/Users/machina/Developer/ChatGPT/mantra/reinstantiation/REINSTANTIATION_ROOT_RELEASE.json) | Pinned archive/runtime/control release pointers. |
| [reinstantiation/FILEMAP.md](/Users/machina/Developer/ChatGPT/mantra/reinstantiation/FILEMAP.md) | Restoration file index. |
| [reinstantiation/DEPLOYMENT_STACK_REFERENCE.md](/Users/machina/Developer/ChatGPT/mantra/reinstantiation/DEPLOYMENT_STACK_REFERENCE.md) | Historical machine and runtime stack. |
| [reinstantiation/GCE_HOST_PROFILE.json](/Users/machina/Developer/ChatGPT/mantra/reinstantiation/GCE_HOST_PROFILE.json) | Machine, GPU, OS, and runtime facts. |
| [reinstantiation/bootstrap_gce_reinstantiation.sh](/Users/machina/Developer/ChatGPT/mantra/reinstantiation/bootstrap_gce_reinstantiation.sh) | Restores archives/environment and runs application verification; this script provisions cloud resources. |
| [archive_pointers/](/Users/machina/Developer/ChatGPT/mantra/archive_pointers) | Additional archived-artifact pointers. |
| [pyproject.toml](/Users/machina/Developer/ChatGPT/mantra/pyproject.toml) | Current project metadata requires Python >=3.13,<3.14; do not assume this reconstructs the historical numerical environment. |

The saved application command is `{runtime_root}/bin/python experiments/v1953_direct_mil_simplified_scorer_promotion/scripts/run_result.py`, from the repository root, with `CUBLAS_WORKSPACE_CONFIG=:4096:8` and `PYTHONPATH={repository_root}:{repository_root}/src`. Resolve `{runtime_root}` from the restored environment. The historical README's `/home/machina/MANTRA` is a deployment location, not the local macOS checkout.

Running the replay can write to a fixed historical run directory; inspect output handling before launching. Provisioning is not part of this handoff. The earlier ephemeral Spot-host authorization concerned GPU acceptance, not an unrestricted rebuild allocation.

### Availability of application inputs

The table below checks file existence only. It does not hash files or prove that all training inputs are present. The application verification JSON owns expected hashes and output checks.

| Bound input | Present locally |
|---|---|
| `experiments/v1953_direct_mil_simplified_scorer_promotion/scripts/run_result.py` | yes |
| `experiments/v1953_direct_mil_simplified_scorer_promotion/specs/runtime/full_stack.yaml` | yes |
| `experiments/v1953_direct_mil_simplified_scorer_promotion/specs/runtime/benchmark_reference.yaml` | yes |
| `experiments/v1953_direct_mil_simplified_scorer_promotion/specs/runtime/step02.yaml` | yes |
| `experiments/v1953_direct_mil_simplified_scorer_promotion/specs/runtime/step03.yaml` | yes |
| `experiments/v1953_direct_mil_simplified_scorer_promotion/specs/runtime/step02_input_contract.yaml` | yes |
| `experiments/v1938_sota_clean_repro/src/runtime/config.py` | yes |
| `experiments/v1938_sota_clean_repro/src/runtime/pipeline.py` | yes |
| `experiments/v1938_sota_clean_repro/src/step02/runner.py` | yes |
| `experiments/v1938_sota_clean_repro/src/step02/state.py` | yes |
| `experiments/v1938_sota_clean_repro/src/step02/proposal.py` | yes |
| `experiments/v1938_sota_clean_repro/src/step02/mil_proto/direct_step03.py` | yes |
| `experiments/v1938_sota_clean_repro/src/step03/runner.py` | yes |
| `src/mantra/eval/eval.py` | yes |
| `experiments/v1952_direct_mil_control_term_ablation/runs/control_ablation_seed_123460/checkpoints/transformed_training_memory/derived/mil_proto/mil_proto_identity_vectors.npz` | NO |
| `experiments/v1938_sota_clean_repro/runs/checkpoint_bootstrap_20260713T030000Z/base_step01/candidates/mixed_src_snk_ripple_raw_pen1_directw2p0_local/diagnostics/BASE_STEP01_RESULT_REPORT.json` | yes |
| `experiments/v1938_sota_clean_repro/runs/checkpoint_bootstrap_20260713T030000Z/base_step01/diagnostics/BASE_STEP01_RETRAIN_PARITY.json` | yes |
| `experiments/v1938_sota_clean_repro/runs/checkpoint_bootstrap_20260713T030000Z/base_step01/candidates/mixed_src_snk_ripple_raw_pen1_directw2p0_local/checkpoints/mean/HOPFIELD_PREDICTIONS.npz` | NO |
| `experiments/v1938_sota_clean_repro/runs/checkpoint_bootstrap_20260713T030000Z/projected_step01/diagnostics/PROJECTED_STEP01_RESULT_REPORT.json` | yes |
| `experiments/v1938_sota_clean_repro/runs/checkpoint_bootstrap_20260713T030000Z/projected_step01/candidates/aggregate_proto64_scale2p8_temp0p095/checkpoints/mean/HOPFIELD_PREDICTIONS.npz` | NO |


### Historical training dependencies

The v1952 specification inherits these earlier owners and artifacts. Recover missing dependencies before treating its training runner as self-contained.

| Location | Present locally |
|---|---|
| [experiments/v1951_direct_mil_causal_reconstruction/specs/causal_reconstruction.yaml](/Users/machina/Developer/ChatGPT/mantra/experiments/v1951_direct_mil_causal_reconstruction/specs/causal_reconstruction.yaml) | yes |
| [experiments/v1938_sota_clean_repro/runs/matrix_fit_only_bold_step02_20260715T083000Z/student_prior_response_gcn_direct_coeff_mil_probe/scripts/run_student_prior_response_gcn_direct_coeff_mil_probe.py](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/runs/matrix_fit_only_bold_step02_20260715T083000Z/student_prior_response_gcn_direct_coeff_mil_probe/scripts/run_student_prior_response_gcn_direct_coeff_mil_probe.py) | NO; restore or rebuild |
| [experiments/v1938_sota_clean_repro/runs/matrix_fit_only_bold_step02_20260715T083000Z/teacher_feature_direct_coeff_mil_probe/scripts/score_direct_coeff_independent.py](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/runs/matrix_fit_only_bold_step02_20260715T083000Z/teacher_feature_direct_coeff_mil_probe/scripts/score_direct_coeff_independent.py) | NO; restore or rebuild |
| [experiments/v1938_sota_clean_repro/runs/matrix_fit_only_bold_step02_20260715T083000Z/student_prior_response_gcn_direct_coeff_mil_probe/input_builds/family64_raw_interaction/inputs/student_features/features.npz](/Users/machina/Developer/ChatGPT/mantra/experiments/v1938_sota_clean_repro/runs/matrix_fit_only_bold_step02_20260715T083000Z/student_prior_response_gcn_direct_coeff_mil_probe/input_builds/family64_raw_interaction/inputs/student_features/features.npz) | NO; restore or rebuild |

## VIPER: public interfaces and implementation owners

VIPER should wrap explicit MANTRA stages and artifacts; it does not supply MANTRA's model architecture. Prefer complete Python declarations, with each input and output introduced at its point of use. Public package imports come from their defining modules; `viper.__init__` is intentionally minimal.

| Location | Purpose |
|---|---|
| [README.md](/Users/machina/Developer/ChatGPT/viper/README.md) | Complete CPU Python workflow. |
| [examples/cpu_quickstart.py](/Users/machina/Developer/ChatGPT/viper/examples/cpu_quickstart.py) | End-to-end stage, metric, plan, execution, and verification example. |
| [examples/stages.py](/Users/machina/Developer/ChatGPT/viper/examples/stages.py) | Composed stage declarations. |
| [examples/variants.py](/Users/machina/Developer/ChatGPT/viper/examples/variants.py) | Variants and replicates. |
| [examples/execution_policies.py](/Users/machina/Developer/ChatGPT/viper/examples/execution_policies.py) | Execution policy examples. |
| [examples/recovery.py](/Users/machina/Developer/ChatGPT/viper/examples/recovery.py) | Recovery and restoration examples. |
| [docs/reference/api.md](/Users/machina/Developer/ChatGPT/viper/docs/reference/api.md) | Authoritative public import map. |
| [docs/how-to/inputs.md](/Users/machina/Developer/ChatGPT/viper/docs/how-to/inputs.md) | Input roles and dependencies. |
| [docs/how-to/stages.md](/Users/machina/Developer/ChatGPT/viper/docs/how-to/stages.md) | StageContext and stage composition. |
| [docs/how-to/metrics-and-benchmarks.md](/Users/machina/Developer/ChatGPT/viper/docs/how-to/metrics-and-benchmarks.md) | MetricContext, saved-artifact metrics, and comparisons. |
| [docs/how-to/execution.md](/Users/machina/Developer/ChatGPT/viper/docs/how-to/execution.md) | Run execution. |
| [docs/explanation/guarantees.md](/Users/machina/Developer/ChatGPT/viper/docs/explanation/guarantees.md) | What saved-run verification establishes; output-byte equality is a separate comparison. |
| [src/viper/authoring.py](/Users/machina/Developer/ChatGPT/viper/src/viper/authoring.py) | experiment, stage, input, variant, replicate, plan declarations. |
| [src/viper/stages.py](/Users/machina/Developer/ChatGPT/viper/src/viper/stages.py) | StageContext and decorators. |
| [src/viper/config.py](/Users/machina/Developer/ChatGPT/viper/src/viper/config.py) | Typed stage and metric configuration. |
| [src/viper/outputs.py](/Users/machina/Developer/ChatGPT/viper/src/viper/outputs.py) | Declared output objects. |
| [src/viper/metrics.py](/Users/machina/Developer/ChatGPT/viper/src/viper/metrics.py) | Metric declaration, recording, and measurement types. |
| [src/viper/repository.py](/Users/machina/Developer/ChatGPT/viper/src/viper/repository.py) | Public source discovery: read_source. |
| [src/viper/runtime.py](/Users/machina/Developer/ChatGPT/viper/src/viper/runtime.py) | Environment and reproducibility configuration. |
| [src/viper/randomness.py](/Users/machina/Developer/ChatGPT/viper/src/viper/randomness.py) | RNG capture and seed handling. |
| [src/viper/resume.py](/Users/machina/Developer/ChatGPT/viper/src/viper/resume.py) | Checkpoint/resume state. |
| [src/viper/execution/__init__.py](/Users/machina/Developer/ChatGPT/viper/src/viper/execution/__init__.py) | Public execution entry points. |
| [src/viper/execution/results.py](/Users/machina/Developer/ChatGPT/viper/src/viper/execution/results.py) | Execution result types. |
| [src/viper/verification.py](/Users/machina/Developer/ChatGPT/viper/src/viper/verification.py) | Saved-run verification. |
| [src/viper/_verification/](/Users/machina/Developer/ChatGPT/viper/src/viper/_verification) | Internal artifact, runtime, measurement, and lineage checks. |
| [docs/reference/agents.md](/Users/machina/Developer/ChatGPT/viper/docs/reference/agents.md) | MCP discovery, access modes, and operations. |
| [src/viper/mcp.py](/Users/machina/Developer/ChatGPT/viper/src/viper/mcp.py) | Machine-facing server. |
| [src/viper/api.py](/Users/machina/Developer/ChatGPT/viper/src/viper/api.py) | Structured request/response operations. |
| [llms.txt](/Users/machina/Developer/ChatGPT/viper/llms.txt) | Agent documentation index. |
| [CONTRIBUTING.md](/Users/machina/Developer/ChatGPT/viper/CONTRIBUTING.md) | Use the project-local .venv for VIPER development. |
| [pyproject.toml](/Users/machina/Developer/ChatGPT/viper/pyproject.toml) | Distribution name, dependencies, and optional MCP/test extras. |

### Proposed VIPER stage boundaries

These are rebuild design suggestions, not an existing port verified by this handoff:

1. Construct control programs, matched controls, the response dictionary, and cell/perturbation coefficients as named artifacts.
2. Build biological descriptors, predicted control state, response summaries, and reference shifts with saved fitted transforms.
3. Train the Hopfield encoder; separately perform its raw-gene retrieval evaluation.
4. Train the MIL teacher; save its weights and donor embeddings. Transform donor coefficients and train the student; save its weights and memory.
5. Fit the MIL correction and calibration, then evaluate both final predictors with the same explicit metric implementation.

Separate reusable fitted transforms from per-run predictions. Record raw-data identities and row ordering as well as numerical arrays. Use explicit data roles, and keep learned preprocessing scoped to the intended rows. Put seeds, loss weights, temperatures, dimensions, and decoder/memory identities in typed configuration rather than closures or undocumented defaults.

Start with `reproducible` execution, but verify that its applied runtime controls match the historical environment before making a byte-parity claim. `relaxed` allows nondeterministic execution; it is not proof that a later deterministic rerun will reproduce the same weights. Verify saved evidence and compare numerical outputs as separate checks.

### Tests to consult when implementing the port

| Location | Purpose |
|---|---|
| [tests/test_readme_workflow.py](/Users/machina/Developer/ChatGPT/viper/tests/test_readme_workflow.py) | Executable Python workflow. |
| [tests/test_workflow_documentation.py](/Users/machina/Developer/ChatGPT/viper/tests/test_workflow_documentation.py) | Documented multi-stage examples. |
| [tests/test_authoring.py](/Users/machina/Developer/ChatGPT/viper/tests/test_authoring.py) | Declaration behavior. |
| [tests/test_stage_invocation.py](/Users/machina/Developer/ChatGPT/viper/tests/test_stage_invocation.py) | Runtime stage invocation. |
| [tests/test_metric_interface.py](/Users/machina/Developer/ChatGPT/viper/tests/test_metric_interface.py) | Metric calling convention. |
| [tests/test_execution_policy_controls.py](/Users/machina/Developer/ChatGPT/viper/tests/test_execution_policy_controls.py) | Runtime policy settings. |
| [tests/test_execution_policy_acceptance.py](/Users/machina/Developer/ChatGPT/viper/tests/test_execution_policy_acceptance.py) | Policy acceptance. |
| [tests/test_verification_acceptance.py](/Users/machina/Developer/ChatGPT/viper/tests/test_verification_acceptance.py) | Saved evidence and tampering acceptance. |
| [tests/test_resume.py](/Users/machina/Developer/ChatGPT/viper/tests/test_resume.py) | Resume-state behavior. |
| [tests/test_mcp_transport.py](/Users/machina/Developer/ChatGPT/viper/tests/test_mcp_transport.py) | MCP protocol integration. |

## Rebuild completion criteria

First reproduce the saved MIL application from its bound artifacts and compare its results with APPLICATION_VERIFICATION.json. Then reconstruct preprocessing and retrain each model from the intended source inputs. Compare intermediate arrays, fitted transforms, weights, and final predictions to distinguish input drift from training or readout differences. Use the original score computation and keep any numerical tolerances explicit.

For Hopfield, retain the selected encoder configuration and raw-gene readout pairing. For MIL, retain the single-query override, transformed training memory, zero direct control term, and final calibration. Preserve all source and artifact hashes alongside the new run results.

This source map leaves exact raw-data closure, historical student-input width, full numerical environment compatibility, and fresh training parity for the rebuilding agent to verify. Those facts cannot be inferred from the résumé or from a passing saved-checkpoint replay.
