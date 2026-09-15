# MANTRA MIL Reconstruction

This contract rebuilds the selected standalone MIL path from its own historical
inputs through teacher and student training, retrieval, correction, and final
output parity.

The selected Phase 0 result is the v1952 seed-123460 `without_control` run with
hold `PearsonDelta` `0.6025499488874759`.

<!-- contract-protocol:generated:start -->
**Planned.** [Jump to current PairBlock](#m2-pb-01)

**Checklist:** [MANTRA rebuild](../checklists/mantra-rebuild.md)

### PairBlocks

<a id="m2-pb-01"></a>

#### <nobr><code>M2-PB-01</code></nobr>

**Status:** waiting

**Requirement contribution:** Bind the MIL rebuild to its standalone historical inputs and active single-query architecture.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H1-PB-06</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="m2-pb-02"></a>

#### <nobr><code>M2-PB-02</code></nobr>

**Status:** waiting

**Requirement contribution:** Rebuild teacher bags, conditioning, teacher training, donor embeddings, and single-query student training with retained selection evidence.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>M2-PB-01</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="m2-pb-03"></a>

#### <nobr><code>M2-PB-03</code></nobr>

**Status:** waiting

**Requirement contribution:** Rebuild retrieval and every downstream correction and compare each intermediate before final scoring.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>M2-PB-02</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="m2-pb-04"></a>

#### <nobr><code>M2-PB-04</code></nobr>

**Status:** waiting

**Requirement contribution:** Verify final MIL parity and retain the complete accepted execution through VIPER and contract evidence.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>M2-PB-03</code></nobr>

**Next action:** Wait for the declared dependencies.


### Requirements

| Requirement | Claim | Progress | Verifiers | PairBlocks |
|---|---|---|---|---|
| <nobr><code>M2-REQ-01</code></nobr> | The standalone MIL rebuild must use the selected v1952 seed-123460 without_control inputs, create one student query, exclude the dormant proto_count 11 setting from the active architecture, and consume no Hopfield output. | planned | <nobr><code>M2-VR-01</code></nobr> | <nobr><code>M2-PB-01</code></nobr> |
| <nobr><code>M2-REQ-02</code></nobr> | Teacher bags and conditioning, the teacher, donor embeddings, and the single-query student must be rebuilt in producer order; every selection score and checkpoint decision must be emitted to stdout and the primary experiment log and retained through VIPER. | planned | <nobr><code>M2-VR-02</code></nobr> | <nobr><code>M2-PB-02</code></nobr> |
| <nobr><code>M2-REQ-03</code></nobr> | Covariance shrinkage, teacher-neighbor smoothing, retrieval, residual correction, reference shift, and per-gene calibration must be rebuilt and compared with their historical intermediates before final evaluation. | planned | <nobr><code>M2-VR-03</code></nobr> | <nobr><code>M2-PB-03</code></nobr> |
| <nobr><code>M2-REQ-04</code></nobr> | The rebuilt MIL path must reproduce hold PearsonDelta 0.6025499488874759 and the approved prediction identities or numerical tolerances, with every accepted producer, artifact, comparison, checkpoint, and implementation commit reachable through retained VIPER and contract evidence. | planned | <nobr><code>M2-VR-04</code></nobr> | <nobr><code>M2-PB-04</code></nobr> |

### Verification rules

| Rule | Requirements | Acceptance conditions | Success case | Rejection cases |
|---|---|---|---|---|
| <nobr><code>M2-VR-01</code></nobr> | <nobr><code>M2-REQ-01</code></nobr> | The selected MIL configuration resolves the standalone historical inputs, creates one student query, ignores proto_count 11, and has no dependency on a Hopfield output. | [test_accepts_selected_standalone_mil_configuration](../../mantra/src/mantra/rebuild/tests/test_mil_contract.py) | [test_rejects_hopfield_or_multi_query_dependency](../../mantra/src/mantra/rebuild/tests/test_mil_contract.py) |
| <nobr><code>M2-VR-02</code></nobr> | <nobr><code>M2-REQ-02</code></nobr> | The teacher and student training chain reproduces the approved intermediate arrays and retains every selection score and checkpoint decision. | [test_rebuilds_selected_teacher_and_student](../../mantra/src/mantra/rebuild/tests/test_mil_training.py) | [test_rejects_changed_training_intermediate](../../mantra/src/mantra/rebuild/tests/test_mil_training.py) |
| <nobr><code>M2-VR-03</code></nobr> | <nobr><code>M2-REQ-03</code></nobr> | Each retrieval and correction intermediate matches its approved identity or numerical tolerance before the final prediction is scored. | [test_rebuilds_selected_retrieval_and_correction](../../mantra/src/mantra/rebuild/tests/test_mil_reconstruction.py) | [test_rejects_changed_correction_intermediate](../../mantra/src/mantra/rebuild/tests/test_mil_reconstruction.py) |
| <nobr><code>M2-VR-04</code></nobr> | <nobr><code>M2-REQ-04</code></nobr> | The final prediction and hold PearsonDelta match the approved Phase 0 MIL result, and retained evidence resolves the complete accepted execution. | [test_resolves_complete_mil_reconstruction](../tests/phase2/test_mil_registration.py) | [test_rejects_changed_or_unregistered_mil_result](../tests/phase2/test_mil_registration.py) |
<!-- contract-protocol:generated:end -->
