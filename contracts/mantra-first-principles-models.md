# MANTRA First-Principles Models

This contract rebuilds the shared perturbation representations, Hopfield, and
MIL as explicit VIPER stages. A finite manifest names the approved identity,
per-prior PCA, per-prior MLP, fusion, grouped-ridge, and direct-to-Hopfield
paths. It also rebuilds the auxiliary MLP that predicts held-out `ctrl19` rows
without using held-out response truth and reproduces the historical 40-value
response-block feature from rebuilt block definitions. Fit rows use direct
response coefficients; tune and held-out rows use fit-only retrieval.

Each variant receives its own immutable input bundle. Model construction,
training, inference, diagnostics, and canonical `PearsonDelta` evaluation remain
separate stages, and the selected GPU vectorizations must survive the rewrite.
Before variant training, a controlled substitution ladder replaces each shared
historical producer in both retained model paths one at a time. Hopfield starts
from the frozen MIL-stack bridge; MIL starts from its retained parity result.
The next ladder replaces one legacy model component at a time with its modular
owner. Each step holds every non-target source, configuration, and artifact
digest fixed and preserves the corresponding frozen prediction and score.

The final pre-graph benchmark compares every declared Hopfield variant and the
rebuilt MIL result with the Phase 1 and Phase 2 parity results on one frozen
evaluation surface. Matrix execution stops after that evidence is registered
and before the graph encoder begins.

<!-- contract-protocol:generated:start -->
**Planned.** [Jump to current PairBlock](#b9-pb-01)

**Checklist:** [MANTRA rebuild](../checklists/mantra-rebuild.md)

### PairBlocks

<a id="b9-pb-01"></a>

#### <nobr><code>B9-PB-01</code></nobr>

**Status:** waiting

**Requirement contribution:** Benchmark every declared Hopfield variant and the rebuilt MIL model against the original Hopfield, Hopfield bridge, and original MIL baselines on one frozen evaluation surface.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H7-PB-05</code></nobr>, <nobr><code>M8-PB-06</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="b9-pb-02"></a>

#### <nobr><code>B9-PB-02</code></nobr>

**Status:** waiting

**Requirement contribution:** Close the complete pre-graph provenance graph and stop Matrix before graph-encoder execution.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>B9-PB-01</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="h7-pb-01"></a>

#### <nobr><code>H7-PB-01</code></nobr>

**Status:** waiting

**Requirement contribution:** Construct and persist the complete Hopfield encoder and memory layout as a replayable VIPER stage.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>S6-PB-09</code></nobr>, <nobr><code>E0-PB-09</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="h7-pb-02"></a>

#### <nobr><code>H7-PB-02</code></nobr>

**Status:** waiting

**Requirement contribution:** Train and select the first-principles Hopfield checkpoint without hold-response access.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H7-PB-01</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="h7-pb-03"></a>

#### <nobr><code>H7-PB-03</code></nobr>

**Status:** waiting

**Requirement contribution:** Run checkpoint-only Hopfield inference and retain ordered predictions.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H7-PB-02</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="h7-pb-04"></a>

#### <nobr><code>H7-PB-04</code></nobr>

**Status:** waiting

**Requirement contribution:** Run the Hopfield diagnostics from persisted inputs, checkpoint, and predictions without changing model state.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H7-PB-03</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="h7-pb-05"></a>

#### <nobr><code>H7-PB-05</code></nobr>

**Status:** waiting

**Requirement contribution:** Evaluate every rebuilt Hopfield variant through canonical PearsonDelta and compare it with the original and MIL-stack bridge baselines.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H7-PB-04</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="m8-pb-01"></a>

#### <nobr><code>M8-PB-01</code></nobr>

**Status:** waiting

**Requirement contribution:** Build and persist the complete ordered MIL bags as a replayable VIPER stage.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>S6-PB-09</code></nobr>, <nobr><code>E0-PB-10</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="m8-pb-02"></a>

#### <nobr><code>M8-PB-02</code></nobr>

**Status:** waiting

**Requirement contribution:** Construct and persist the initialized MIL teacher and student models as a replayable VIPER stage.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>M8-PB-01</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="m8-pb-03"></a>

#### <nobr><code>M8-PB-03</code></nobr>

**Status:** waiting

**Requirement contribution:** Train and select first-principles MIL teacher and student checkpoints without hold-response access.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>M8-PB-02</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="m8-pb-04"></a>

#### <nobr><code>M8-PB-04</code></nobr>

**Status:** waiting

**Requirement contribution:** Run checkpoint-only MIL inference and retain ordered predictions.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>M8-PB-03</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="m8-pb-05"></a>

#### <nobr><code>M8-PB-05</code></nobr>

**Status:** waiting

**Requirement contribution:** Run the MIL diagnostics from persisted bags, checkpoints, and predictions without changing model state.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>M8-PB-04</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="m8-pb-06"></a>

#### <nobr><code>M8-PB-06</code></nobr>

**Status:** waiting

**Requirement contribution:** Evaluate the rebuilt MIL model through canonical PearsonDelta and compare it with Phase 2.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>M8-PB-05</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="s6-pb-01"></a>

#### <nobr><code>S6-PB-01</code></nobr>

**Status:** waiting

**Requirement contribution:** Align every corrected prior and mask to one ordered perturbation-identity table.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>R5-PB-06</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="s6-pb-02"></a>

#### <nobr><code>S6-PB-02</code></nobr>

**Status:** waiting

**Requirement contribution:** Implement and retain the identity, per-prior PCA, and per-prior MLP transforms named by the variant manifest.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>S6-PB-01</code></nobr>, <nobr><code>E0-PB-11</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="s6-pb-03"></a>

#### <nobr><code>S6-PB-03</code></nobr>

**Status:** waiting

**Requirement contribution:** Implement and retain concatenation and learned-MLP fusion for the declared prior variants.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>S6-PB-02</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="s6-pb-04"></a>

#### <nobr><code>S6-PB-04</code></nobr>

**Status:** waiting

**Requirement contribution:** Execute only the declared grouped-ridge and direct-to-Hopfield representation paths.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>S6-PB-03</code></nobr>, <nobr><code>E0-PB-07</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="s6-pb-05"></a>

#### <nobr><code>S6-PB-05</code></nobr>

**Status:** waiting

**Requirement contribution:** Predict held-out ctrl19 rows through the retained auxiliary MLP and decoder without hold-response leakage.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>S6-PB-01</code></nobr>, <nobr><code>E0-PB-02</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="s6-pb-06"></a>

#### <nobr><code>S6-PB-06</code></nobr>

**Status:** waiting

**Requirement contribution:** Rebuild the split-aligned hard, soft-semantic, and spectral response-block features and prove parity without held-out response leakage.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>S6-PB-04</code></nobr>, <nobr><code>R5-PB-07</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="s6-pb-07"></a>

#### <nobr><code>S6-PB-07</code></nobr>

**Status:** waiting

**Requirement contribution:** Freeze one complete model-input bundle for each declared variant and require every model plan to name its exact bundle.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>S6-PB-05</code></nobr>, <nobr><code>S6-PB-06</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="s6-pb-08"></a>

#### <nobr><code>S6-PB-08</code></nobr>

**Status:** waiting

**Requirement contribution:** Replace each shared historical producer one at a time and preserve the Hopfield MIL-stack bridge and MIL parity baselines before variant training.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>S6-PB-07</code></nobr>, <nobr><code>E0-PB-08</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="s6-pb-09"></a>

#### <nobr><code>S6-PB-09</code></nobr>

**Status:** waiting

**Requirement contribution:** Replace one legacy Hopfield or MIL model component at a time with its modular owner while preserving the corresponding frozen model result.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>S6-PB-08</code></nobr>, <nobr><code>E0-PB-09</code></nobr>, <nobr><code>E0-PB-10</code></nobr>

**Next action:** Wait for the declared dependencies.


### Requirements

| Requirement | Claim | Progress | Verifiers | PairBlocks |
|---|---|---|---|---|
| <nobr><code>B9-REQ-01</code></nobr> | One benchmark stage must compare every declared Hopfield perturbation-representation variant and the rebuilt MIL result with the original Phase 1 Hopfield parity baseline, the H1-REQ-09 MIL-stack bridge baseline, and the Phase 2 MIL parity baseline on the same ordered perturbations, response genes, split membership, truth arrays, and canonical PearsonDelta implementation. | planned | <nobr><code>B9-VR-01</code></nobr> | <nobr><code>B9-PB-01</code></nobr> |
| <nobr><code>B9-REQ-02</code></nobr> | The pre-graph baseline must freeze the accepted identity table, canonical atlas, corrected priors, response targets, model inputs, weights, predictions, diagnostics, benchmark results, commits, and complete VIPER provenance without executing a graph-encoder PairBlock. | planned | <nobr><code>B9-VR-02</code></nobr> | <nobr><code>B9-PB-02</code></nobr> |
| <nobr><code>H7-REQ-01</code></nobr> | One Hopfield construction stage must build an encoder for each declared perturbation-representation variant and persist the exact bundle digest, complete architecture, initialized parameters, memory layout, input and output dimensions, and construction diagnostics consumed by training. | planned | <nobr><code>H7-VR-01</code></nobr> | <nobr><code>H7-PB-01</code></nobr> |
| <nobr><code>H7-REQ-02</code></nobr> | The Hopfield training stage must execute each declared perturbation-representation variant, exclude hold responses from fitting and selection, and retain its bundle digest, configuration, seed, checkpoints, epoch scores, selection decisions, logs, final weights, runtime, and peak GPU memory. | planned | <nobr><code>H7-VR-02</code></nobr> | <nobr><code>H7-PB-02</code></nobr> |
| <nobr><code>H7-REQ-03</code></nobr> | The Hopfield inference stage must load each accepted variant checkpoint and frozen input bundle, produce ordered fit, tune, and hold predictions without refitting, and retain the exact output arrays and identities. | planned | <nobr><code>H7-VR-03</code></nobr> | <nobr><code>H7-PB-03</code></nobr> |
| <nobr><code>H7-REQ-04</code></nobr> | One Hopfield diagnostic stage must read each variant's frozen inputs, accepted checkpoint, and persisted predictions and emit the declared retrieval, coefficient, response, split, runtime, memory, and failure diagnostics without fitting or changing model state. | planned | <nobr><code>H7-VR-04</code></nobr> | <nobr><code>H7-PB-04</code></nobr> |
| <nobr><code>H7-REQ-05</code></nobr> | The Hopfield evaluation stage must compute canonical PearsonDelta through src/mantra/eval/eval.py on the named GEARS response surface for every declared variant and compare each result with both the original Phase 1 parity baseline and the H1-REQ-09 MIL-stack bridge baseline. | planned | <nobr><code>H7-VR-05</code></nobr> | <nobr><code>H7-PB-05</code></nobr> |
| <nobr><code>M8-REQ-01</code></nobr> | One MIL bag-construction stage must build and persist the ordered bag membership, instances, masks, attention priors, conditioning values, and dimensions consumed by the MIL models from the shared model-input bundle. | planned | <nobr><code>M8-VR-01</code></nobr> | <nobr><code>M8-PB-01</code></nobr> |
| <nobr><code>M8-REQ-02</code></nobr> | One MIL construction stage must build the teacher and student models from the persisted bag schema and retain their complete architectures, initialized parameters, input and output dimensions, and construction diagnostics. | planned | <nobr><code>M8-VR-02</code></nobr> | <nobr><code>M8-PB-02</code></nobr> |
| <nobr><code>M8-REQ-03</code></nobr> | The MIL training stages must consume the persisted bags and model constructions, exclude hold responses from fitting and selection, and retain objective components, configuration, seeds, checkpoints, intermediary scores, decisions, logs, and final weights. | planned | <nobr><code>M8-VR-03</code></nobr> | <nobr><code>M8-PB-03</code></nobr> |
| <nobr><code>M8-REQ-04</code></nobr> | The MIL inference stage must load accepted teacher and student checkpoints plus the frozen input bundle, produce ordered fit, tune, and hold predictions without refitting, and retain the exact output arrays and identities. | planned | <nobr><code>M8-VR-04</code></nobr> | <nobr><code>M8-PB-04</code></nobr> |
| <nobr><code>M8-REQ-05</code></nobr> | One MIL diagnostic stage must read the frozen bags, accepted checkpoints, and persisted predictions and emit the declared attention, teacher-student, response, split, and failure diagnostics without fitting or changing model state. | planned | <nobr><code>M8-VR-05</code></nobr> | <nobr><code>M8-PB-05</code></nobr> |
| <nobr><code>M8-REQ-06</code></nobr> | The MIL evaluation stage must compute canonical PearsonDelta through src/mantra/eval/eval.py on the named GEARS response surface and compare the rebuilt result with the Phase 2 parity baseline. | planned | <nobr><code>M8-VR-06</code></nobr> | <nobr><code>M8-PB-06</code></nobr> |
| <nobr><code>S6-REQ-01</code></nobr> | One ordered perturbation-identity table must align every corrected prior modality and its observed-value mask to the canonical perturbation rows before any reduction, fusion, regression, or encoder consumes those values. | planned | <nobr><code>S6-VR-01</code></nobr> | <nobr><code>S6-PB-01</code></nobr> |
| <nobr><code>S6-REQ-02</code></nobr> | A versioned variant manifest must enumerate the allowed per-prior transforms: unreduced identity, fit-only PCA, and fit-only MLP. Each transform must retain its inputs, fitted state, ordered outputs, dimensions, missingness handling, and reconstruction or held-out diagnostic. | planned | <nobr><code>S6-VR-02</code></nobr> | <nobr><code>S6-PB-02</code></nobr> |
| <nobr><code>S6-REQ-03</code></nobr> | The variant manifest must define the selected fusion for each transformed prior set, including concatenation and a learned fusion MLP, and retain the modality order, masks, fitted parameters, output width, and validation diagnostic. | planned | <nobr><code>S6-VR-03</code></nobr> | <nobr><code>S6-PB-03</code></nobr> |
| <nobr><code>S6-REQ-04</code></nobr> | The variant manifest must explicitly route each fused or unfused prior representation either through fit-only grouped ridge regression or directly to the Hopfield encoder. It must include unreduced identity to grouped ridge, per-prior PCA to grouped ridge, per-prior MLP and fusion to grouped ridge, reduced or fused priors directly to Hopfield, and unreduced priors directly to Hopfield, and reject every unlisted composition. | planned | <nobr><code>S6-VR-04</code></nobr> | <nobr><code>S6-PB-04</code></nobr> |
| <nobr><code>S6-REQ-05</code></nobr> | One auxiliary MLP must predict a distribution over fitted control-state clusters for each held-out perturbation, decode that distribution into the 19-value ctrl19 vector, and retain the fitted MLP, cluster centers, decoder, inputs, predictions, and tune selection without reading held-out response truth. | planned | <nobr><code>S6-VR-05</code></nobr> | <nobr><code>S6-PB-05</code></nobr> |
| <nobr><code>S6-REQ-06</code></nobr> | Each retained historical 40-value response-block feature must be reproduced from the rebuilt block definitions and response coefficients: fit rows use their direct coefficients, tune and held-out rows use only fit rows through that model path's declared query features and retrieval rule, and the hard 16, soft semantic 16, and spectral 8 components must match the corresponding Phase 0 artifact. | planned | <nobr><code>S6-VR-06</code></nobr> | <nobr><code>S6-PB-06</code></nobr> |
| <nobr><code>S6-REQ-07</code></nobr> | One model-input bundle per declared perturbation-representation variant must bind that variant, predicted ctrl19 rows, derived core83 and declared PCA64 control features, parity-verified response-block rows, response-target bundle, canonical splits, normalization population, execution profile, and every fitted transform; each Hopfield or MIL plan must name exactly one bundle digest. | planned | <nobr><code>S6-VR-07</code></nobr> | <nobr><code>S6-PB-07</code></nobr> |
| <nobr><code>S6-REQ-08</code></nobr> | Before a prior-fusion variant may train, one controlled input-substitution ladder must start Hopfield from the H1-REQ-09 MIL-stack bridge baseline and MIL from the M2-REQ-06 parity baseline while replacing the canonical atlas, gene panels, control programs, response programs, response-block definitions, response-block rows, and corrected priors one producer at a time. Each step must hold every other artifact digest fixed, use one common rebuilt artifact reference in both model paths where the artifact is shared, and preserve the corresponding frozen baseline result. | planned | <nobr><code>S6-VR-08</code></nobr> | <nobr><code>S6-PB-08</code></nobr> |
| <nobr><code>S6-REQ-09</code></nobr> | After the input-substitution ladder passes, the legacy Hopfield and MIL execution scripts must be decomposed by replacing one orthogonal model component at a time with its modular owner. Each replacement must retain the target component's inputs, fitted state, outputs, and diagnostics, hold every non-target source, configuration, and artifact digest fixed, and preserve the Hopfield bridge or MIL parity prediction and score before the next component changes. | planned | <nobr><code>S6-VR-09</code></nobr> | <nobr><code>S6-PB-09</code></nobr> |

### Verification rules

| Rule | Requirements | Acceptance conditions | Success case | Rejection cases |
|---|---|---|---|---|
| <nobr><code>B9-VR-01</code></nobr> | <nobr><code>B9-REQ-01</code></nobr> | One command recomputes every declared Hopfield variant comparison plus the rebuilt MIL, original Hopfield, Hopfield bridge, and original MIL results through the canonical evaluator after proving equal axes, splits, and truth surfaces. | [test_compares_rebuilt_models_with_parity_baselines](../../mantra/src/mantra/rebuild/tests/test_pregraph_benchmark.py) | [test_rejects_cross_surface_model_comparison](../../mantra/src/mantra/rebuild/tests/test_pregraph_benchmark.py) |
| <nobr><code>B9-VR-02</code></nobr> | <nobr><code>B9-REQ-02</code></nobr> | The terminal evidence graph reaches every accepted pre-graph input, stage, output, comparison, and implementation commit, and contains no graph-encoder execution receipt. | [test_resolves_complete_pregraph_provenance](../tests/pregraph/test_pregraph_registration.py) | [test_rejects_severed_or_graph_encoder_evidence](../tests/pregraph/test_pregraph_registration.py) |
| <nobr><code>H7-VR-01</code></nobr> | <nobr><code>H7-REQ-01</code></nobr> | Construction reproduces the same initialized encoder and memory layout from the declared input bundle, architecture, and seed, and persists every value training reads. | [test_constructs_replayable_hopfield_encoder](../../mantra/src/mantra/rebuild/tests/test_hopfield_first_principles.py) | [test_rejects_hidden_hopfield_construction_state](../../mantra/src/mantra/rebuild/tests/test_hopfield_first_principles.py) |
| <nobr><code>H7-VR-02</code></nobr> | <nobr><code>H7-REQ-02</code></nobr> | Training reproduces from retained inputs and configuration, emits every checkpoint decision, and no fit or selection operation reads hold responses. | [test_trains_hopfield_without_hold_access](../../mantra/src/mantra/rebuild/tests/test_hopfield_first_principles.py) | [test_rejects_hopfield_hold_access_or_unlogged_selection](../../mantra/src/mantra/rebuild/tests/test_hopfield_first_principles.py) |
| <nobr><code>H7-VR-03</code></nobr> | <nobr><code>H7-REQ-03</code></nobr> | Inference is a pure checkpoint-and-input replay whose persisted predictions preserve all declared axes and splits. | [test_replays_hopfield_inference](../../mantra/src/mantra/rebuild/tests/test_hopfield_first_principles.py) | [test_rejects_hopfield_refit_or_prediction_reordering](../../mantra/src/mantra/rebuild/tests/test_hopfield_first_principles.py) |
| <nobr><code>H7-VR-04</code></nobr> | <nobr><code>H7-REQ-04</code></nobr> | Diagnostics replay from persisted inputs, checkpoint, and predictions, cover every declared split, and leave all input and model digests unchanged. | [test_runs_hopfield_diagnostics_without_refit](../../mantra/src/mantra/rebuild/tests/test_hopfield_first_principles.py) | [test_rejects_stateful_or_incomplete_hopfield_diagnostics](../../mantra/src/mantra/rebuild/tests/test_hopfield_first_principles.py) |
| <nobr><code>H7-VR-05</code></nobr> | <nobr><code>H7-REQ-05</code></nobr> | Evaluation uses the canonical evaluator and response surface and reports exact comparisons with the original Phase 1 prediction and score and the H1-REQ-09 bridge prediction and score. | [test_evaluates_hopfield_on_canonical_surface](../../mantra/src/mantra/rebuild/tests/test_hopfield_first_principles.py) | [test_rejects_shadow_metric_or_surface_substitution](../../mantra/src/mantra/rebuild/tests/test_hopfield_first_principles.py) |
| <nobr><code>M8-VR-01</code></nobr> | <nobr><code>M8-REQ-01</code></nobr> | Bag construction reproduces every ordered instance, membership, mask, prior, and conditioning value from the shared input bundle and persists every value the models read. | [test_builds_replayable_mil_bags](../../mantra/src/mantra/rebuild/tests/test_mil_first_principles.py) | [test_rejects_hidden_or_reordered_mil_bag_state](../../mantra/src/mantra/rebuild/tests/test_mil_first_principles.py) |
| <nobr><code>M8-VR-02</code></nobr> | <nobr><code>M8-REQ-02</code></nobr> | Construction reproduces the same initialized teacher and student from the declared bag schema, architecture, and seeds and persists every value training reads. | [test_constructs_replayable_mil_models](../../mantra/src/mantra/rebuild/tests/test_mil_first_principles.py) | [test_rejects_hidden_mil_model_state](../../mantra/src/mantra/rebuild/tests/test_mil_first_principles.py) |
| <nobr><code>M8-VR-03</code></nobr> | <nobr><code>M8-REQ-03</code></nobr> | Teacher and student training reproduce from retained inputs and configuration, emit every objective component and checkpoint decision, and use fit and tune responses for fitting and selection. | [test_trains_mil_without_hold_access](../../mantra/src/mantra/rebuild/tests/test_mil_first_principles.py) | [test_rejects_mil_hold_access_or_unlogged_selection](../../mantra/src/mantra/rebuild/tests/test_mil_first_principles.py) |
| <nobr><code>M8-VR-04</code></nobr> | <nobr><code>M8-REQ-04</code></nobr> | Inference is a pure checkpoint-and-input replay whose persisted predictions preserve all declared axes and splits. | [test_replays_mil_inference](../../mantra/src/mantra/rebuild/tests/test_mil_first_principles.py) | [test_rejects_mil_refit_or_prediction_reordering](../../mantra/src/mantra/rebuild/tests/test_mil_first_principles.py) |
| <nobr><code>M8-VR-05</code></nobr> | <nobr><code>M8-REQ-05</code></nobr> | Diagnostics replay from persisted bags, checkpoints, and predictions, cover every declared split, and leave all input and model digests unchanged. | [test_runs_mil_diagnostics_without_refit](../../mantra/src/mantra/rebuild/tests/test_mil_first_principles.py) | [test_rejects_stateful_or_incomplete_mil_diagnostics](../../mantra/src/mantra/rebuild/tests/test_mil_first_principles.py) |
| <nobr><code>M8-VR-06</code></nobr> | <nobr><code>M8-REQ-06</code></nobr> | Evaluation uses the canonical evaluator and response surface and reports the exact comparison with the Phase 2 prediction and score. | [test_evaluates_mil_on_canonical_surface](../../mantra/src/mantra/rebuild/tests/test_mil_first_principles.py) | [test_rejects_mil_shadow_metric_or_surface_substitution](../../mantra/src/mantra/rebuild/tests/test_mil_first_principles.py) |
| <nobr><code>S6-VR-01</code></nobr> | <nobr><code>S6-REQ-01</code></nobr> | Every corrected prior and mask resolves to the same canonical perturbation rows, observed zero remains distinct from missing data, and reordered, duplicated, absent, or extra rows fail. | [test_aligns_every_prior_to_canonical_perturbations](../../mantra/src/mantra/rebuild/tests/test_perturbation_identity_table.py) | [test_rejects_row_or_missingness_substitution](../../mantra/src/mantra/rebuild/tests/test_perturbation_identity_table.py) |
| <nobr><code>S6-VR-02</code></nobr> | <nobr><code>S6-REQ-02</code></nobr> | The manifest contains exactly the approved identity, PCA, and MLP transform kinds; each fitted transform uses only its declared training rows and reproduces ordered outputs and diagnostics. | [test_builds_declared_per_prior_transforms](../../mantra/src/mantra/rebuild/tests/test_prior_variants.py) | [test_rejects_unlisted_transform_or_hold_fit](../../mantra/src/mantra/rebuild/tests/test_prior_variants.py) |
| <nobr><code>S6-VR-03</code></nobr> | <nobr><code>S6-REQ-03</code></nobr> | Concatenation and learned-MLP fusion reproduce from retained modality order, masks, parameters, and widths, and fail when a modality or learned state is substituted. | [test_builds_declared_prior_fusions](../../mantra/src/mantra/rebuild/tests/test_prior_variants.py) | [test_rejects_changed_modality_order_or_fusion_state](../../mantra/src/mantra/rebuild/tests/test_prior_variants.py) |
| <nobr><code>S6-VR-04</code></nobr> | <nobr><code>S6-REQ-04</code></nobr> | Every minimum approved path executes from the same ordered priors, grouped ridge uses no hold target, direct paths bypass it completely, and the runner rejects any composition absent from the manifest. | [test_executes_every_approved_prior_to_hopfield_path](../../mantra/src/mantra/rebuild/tests/test_prior_encoder_variants.py) | [test_rejects_unlisted_variant_or_hidden_ridge_use](../../mantra/src/mantra/rebuild/tests/test_prior_encoder_variants.py) |
| <nobr><code>S6-VR-05</code></nobr> | <nobr><code>S6-REQ-05</code></nobr> | The MLP and decoder reproduce held-out ctrl19 predictions from retained fit and tune state, no hold response truth is loaded, and substituting cluster order, decoder, or prediction rows fails. | [test_predicts_heldout_ctrl19_without_hold_truth](../../mantra/src/mantra/rebuild/tests/test_ctrl19_holdout.py) | [test_rejects_hold_leakage_or_ctrl19_substitution](../../mantra/src/mantra/rebuild/tests/test_ctrl19_holdout.py) |
| <nobr><code>S6-VR-06</code></nobr> | <nobr><code>S6-REQ-06</code></nobr> | Each rebuilt model path preserves perturbation order and matches its Phase 0 hard 16, soft semantic 16, and spectral 8 rows; the shared fit and tune rows remain equal across the paths, each held-out proxy names its query-feature producer, and tune and held-out response truth is unavailable to those producers. | [test_rebuilds_response_block40_with_parity](../../mantra/src/mantra/rebuild/tests/test_response_block_features.py) | [test_rejects_response_block_drift_or_hold_leakage](../../mantra/src/mantra/rebuild/tests/test_response_block_features.py) |
| <nobr><code>S6-VR-07</code></nobr> | <nobr><code>S6-REQ-07</code></nobr> | Each plan resolves one complete bundle digest and rejects substituted variants, ctrl19 rows, core83 or PCA64 derivatives, response-block rows, splits, transforms, response columns, normalization populations, or execution profiles. | [test_binds_one_variant_and_input_bundle_for_both_models](../../mantra/src/mantra/rebuild/tests/test_model_input_bundle.py) | [test_rejects_mixed_or_substituted_model_inputs](../../mantra/src/mantra/rebuild/tests/test_model_input_bundle.py) |
| <nobr><code>S6-VR-08</code></nobr> | <nobr><code>S6-REQ-08</code></nobr> | The substitution ledger starts Hopfield from the frozen MIL-stack bridge and MIL from its retained parity bundle, changes exactly one producer reference per step, proves that every other digest stayed fixed, uses the same rebuilt reference for shared artifacts, and preserves each frozen prediction and score before any prior-fusion result is accepted. | [test_replaces_shared_producers_one_at_a_time_with_dual_model_parity](../../mantra/src/mantra/rebuild/tests/test_shared_input_substitution.py) | [test_rejects_multi_artifact_swap_split_shared_input_or_parity_loss](../../mantra/src/mantra/rebuild/tests/test_shared_input_substitution.py) |
| <nobr><code>S6-VR-09</code></nobr> | <nobr><code>S6-REQ-09</code></nobr> | Every ledger entry names one legacy component and one modular replacement, proves equal component inputs and fitted state, compares its outputs and diagnostics, holds every non-target source, configuration, and artifact digest fixed, preserves full GPU residency and the model's declared optimization granularity, and preserves the owning model's frozen prediction and score before another replacement is admitted. | [test_replaces_legacy_model_components_one_at_a_time](../../mantra/src/mantra/rebuild/tests/test_model_component_substitution.py) | [test_rejects_multi_component_change_hidden_state_or_baseline_drift](../../mantra/src/mantra/rebuild/tests/test_model_component_substitution.py) |
<!-- contract-protocol:generated:end -->
