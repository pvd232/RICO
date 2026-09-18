# MANTRA MIL Reconstruction

This contract rebuilds the selected standalone MIL path from its own historical
inputs through teacher and student training, retrieval, correction, and final
output parity.

The selected Phase 0 result is the v1952 seed-123460 `without_control` run with
hold `PearsonDelta` `0.6025499488874759`.

<!-- contract-protocol:generated:start -->
**In progress.** [Jump to current PairBlock](#m2-pb-01)

**Checklist:** [MANTRA rebuild](../checklists/mantra-rebuild.md)

### PairBlocks

<a id="m2-pb-01"></a>

#### <nobr><code>M2-PB-01</code></nobr>

**Status:** drafting

**Requirement contribution:** Bind the MIL rebuild to its standalone historical inputs and active single-query architecture.

**Plan:** None

**Current receipt:** None

**Dependencies:** None

**Next action:** Run the current PairBlock plan.

<a id="m2-pb-02"></a>

#### <nobr><code>M2-PB-02</code></nobr>

**Status:** waiting

**Requirement contribution:** Freeze the MIL input ledger and restore the exact historical training bundle, bags, priors, and conditioning arrays.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>M2-PB-01</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="m2-pb-03"></a>

#### <nobr><code>M2-PB-03</code></nobr>

**Status:** waiting

**Requirement contribution:** Train the selected teacher and single-query student and reproduce the retained MIL identity vectors.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>M2-PB-02</code></nobr>, <nobr><code>E0-PB-10</code></nobr>, <nobr><code>E0-PB-12</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="m2-pb-04"></a>

#### <nobr><code>M2-PB-04</code></nobr>

**Status:** waiting

**Requirement contribution:** Rebuild Step02 retrieval and smoothing and prove its prediction, weight, and score parity.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>M2-PB-03</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="m2-pb-05"></a>

#### <nobr><code>M2-PB-05</code></nobr>

**Status:** waiting

**Requirement contribution:** Rebuild Step03 correction and calibration and prove exact final MIL parity.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>M2-PB-04</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="m2-pb-06"></a>

#### <nobr><code>M2-PB-06</code></nobr>

**Status:** waiting

**Requirement contribution:** Resolve the complete Phase 2 producer and evidence graph and close MIL reconstruction.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>M2-PB-05</code></nobr>

**Next action:** Wait for the declared dependencies.


### Requirements

| Requirement | Claim | Progress | Verifiers | PairBlocks |
|---|---|---|---|---|
| <nobr><code>M2-REQ-01</code></nobr> | The standalone MIL rebuild must use the selected v1952 seed-123460 without_control inputs, create one student query, exclude the dormant proto_count 11 setting from the active architecture, and consume no Hopfield output. | in_progress | <nobr><code>M2-VR-01</code></nobr> | <nobr><code>M2-PB-01</code></nobr> |
| <nobr><code>M2-REQ-02</code></nobr> | Before replay training, one complete MIL input ledger must name every selected descriptor row, coefficient and gene target, control shift, cell-program projection, matched cell program, teacher bag, attention prior, and conditioning array, together with its retained digest, producing script or record, and restore route. Restoring that ledger must reproduce every historical input without rerunning upstream producers, and every standardized descriptor must retain the exact reference population used to fit its column means and standard deviations. | planned | <nobr><code>M2-VR-02</code></nobr> | <nobr><code>M2-PB-02</code></nobr> |
| <nobr><code>M2-REQ-03</code></nobr> | The teacher, donor embeddings, and single-query student must be rebuilt in producer order and reproduce the retained MIL identity vectors; every selection score and checkpoint decision must be emitted to stdout and the primary experiment log and retained through VIPER. | planned | <nobr><code>M2-VR-03</code></nobr> | <nobr><code>M2-PB-03</code></nobr> |
| <nobr><code>M2-REQ-04</code></nobr> | The selected Step02 memory construction must reproduce the fitted column moments, ridge-whitened covariance shrinkage, teacher-neighbor smoothing, and retrieval path before reproducing prediction SHA-256 c0011d71436c540bde8dd00f9e2f8ac8fb46aa787161460a1aefce5f0f1277be, weight SHA-256 8290145991446afd9f45c3f3be1ad7fe95518dfe6f75e1e950b86a2b84c323ab, and hold PearsonDelta 0.5924883417873266. | planned | <nobr><code>M2-VR-04</code></nobr> | <nobr><code>M2-PB-04</code></nobr> |
| <nobr><code>M2-REQ-05</code></nobr> | The selected Step03 residual correction, reference shift, and per-gene calibration must reproduce prediction SHA-256 e39230c8c17954602a2c3dbfc26ed4759922be36bdabc6b27ffb96204a07f7fd, weight SHA-256 372e4409468d7d0441383833601d2a008ab24fd309ae4cd6fb2ebaa36e1dd3f0, and hold PearsonDelta 0.6025499488874759. | planned | <nobr><code>M2-VR-05</code></nobr> | <nobr><code>M2-PB-05</code></nobr> |
| <nobr><code>M2-REQ-06</code></nobr> | Every accepted Phase 2 producer, input, output, comparison, checkpoint, and implementation commit must remain reachable through retained VIPER and contract-protocol evidence. | planned | <nobr><code>M2-VR-06</code></nobr> | <nobr><code>M2-PB-06</code></nobr> |

### Verification rules

| Rule | Requirements | Acceptance conditions | Success case | Rejection cases |
|---|---|---|---|---|
| <nobr><code>M2-VR-01</code></nobr> | <nobr><code>M2-REQ-01</code></nobr> | The selected MIL configuration resolves the standalone historical inputs, creates one student query, ignores proto_count 11, and has no dependency on a Hopfield output. | [test_accepts_selected_standalone_mil_configuration](../../mantra-rebuild/tests/test_mil_contract.py) | [test_rejects_hopfield_or_multi_query_dependency](../../mantra-rebuild/tests/test_mil_contract.py) |
| <nobr><code>M2-VR-02</code></nobr> | <nobr><code>M2-REQ-02</code></nobr> | The MIL input ledger resolves every retained file to its exact digest, producing script or record, and restore route; restoring it reproduces the historical keys, perturbation order, gene order, shapes, dtypes, and values, and the loader reports each descriptor's standardization reference rows together with the selected bag and conditioning rules. | [test_restores_selected_mil_inputs](../../mantra-rebuild/tests/test_mil_inputs.py) | [test_rejects_changed_mil_input_or_bag](../../mantra-rebuild/tests/test_mil_inputs.py) |
| <nobr><code>M2-VR-03</code></nobr> | <nobr><code>M2-REQ-03</code></nobr> | The approved MIL configuration reproduces the teacher and student arrays, checkpoints, selection records, and fixed MIL identity contract without loading hold targets during selection. | [test_rebuilds_selected_teacher_and_student](../../mantra-rebuild/tests/test_mil_training.py) | [test_rejects_changed_training_intermediate_or_hold_selection](../../mantra-rebuild/tests/test_mil_training.py) |
| <nobr><code>M2-VR-04</code></nobr> | <nobr><code>M2-REQ-04</code></nobr> | The Step02 fitted moments, ridge-whitened and neighbor-smoothed memory, output arrays, and weight arrays equal their retained historical counterparts and the hold PearsonDelta equals 0.5924883417873266. | [test_rebuilds_selected_step02](../../mantra-rebuild/tests/test_mil_reconstruction.py) | [test_rejects_changed_step02_output](../../mantra-rebuild/tests/test_mil_reconstruction.py) |
| <nobr><code>M2-VR-05</code></nobr> | <nobr><code>M2-REQ-05</code></nobr> | The Step03 output arrays and weight arrays equal their retained historical counterparts and the final hold PearsonDelta equals 0.6025499488874759. | [test_rebuilds_selected_step03](../../mantra-rebuild/tests/test_mil_reconstruction.py) | [test_rejects_equal_score_with_changed_step03_output](../../mantra-rebuild/tests/test_mil_reconstruction.py) |
| <nobr><code>M2-VR-06</code></nobr> | <nobr><code>M2-REQ-06</code></nobr> | The terminal registration resolves every accepted Phase 2 receipt, artifact, source commit, and producer edge from retained records. | [test_resolves_complete_mil_reconstruction](../tests/phase2/test_mil_registration.py) | [test_rejects_severed_phase2_provenance](../tests/phase2/test_mil_registration.py) |
<!-- contract-protocol:generated:end -->
