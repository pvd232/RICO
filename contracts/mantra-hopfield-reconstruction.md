# MANTRA Hopfield Reconstruction

This contract rebuilds the selected Hopfield path from its preprocessing
inputs through encoder training, raw-gene retrieval, and reference correction.
Historical outputs serve only as comparison references; reconstruction stages
consume source inputs.

The starting result is the Phase 0 replay: encoder SHA-256
`2433527c3b23b66a16cedc0f7bc43867e4298af4d7a0733b202a8018ba876610`,
prediction SHA-256
`d7180c4669a11b0b2fb184814aafb48ebafe75b02e4bd07998c337aa64dc59b7`
and hold `PearsonDelta` `0.5861640938949398`. The retained receipt is indexed
at `archive/mantra-rebuild-phase-0/evidence/phase0/mantra/hopfield_output_parity_receipt.json`.

The historical Hopfield loader joins descriptor features, coefficient targets,
and truth values by row position. Their stored perturbation labels define what
each row means. The loader already compares feature and coefficient-target
labels; Phase 1 adds the missing comparison for the fit and tune truth labels
before rebuilding preprocessing or training the encoder.

<!-- contract-protocol:generated:start -->
**In progress.** [Jump to current PairBlock](#h1-pb-02)

**Checklist:** [MANTRA rebuild](../checklists/mantra-rebuild.md)

### PairBlocks

<a id="h1-pb-01"></a>

#### <nobr><code>H1-PB-01</code></nobr>

**Status:** bootstrap-complete

**Requirement contribution:** Install the typed Phase 1 contract and checklist workspace and bind them to the trusted Phase 0 Hopfield result.

**Review handoff**

**What changed**

- The MANTRA workspace now treats requirements as the checklist's long-term planning units and derives implementation ownership from PairBlocks.
- Phase 1 and Phase 2 now have producer-aligned requirements, verifiers, PairBlocks, and one preflighted plan for the first implementation change.
- The accepted Phase 0 result remains the immutable reconstruction oracle and is not executed again.

**Plan deviations:** The removed reverse requirement-to-PairBlock links made the old bootstrap package unreadable. This current-schema plan replaces that administrative boundary without rerunning Phase 0.

**Start work:** [Open current plan](../plans/mantra-hopfield-reconstruction/H1-PB-01/plan.toml)

**Review these files**

- [Complete requirement-first migration diff](../plans/mantra-hopfield-reconstruction/H1-PB-01/patches/requirement-first-contract.patch#L1)
- [Hopfield requirements and PairBlocks](mantra-hopfield-reconstruction.toml#L5)
- [MIL requirements and PairBlocks](mantra-mil-reconstruction.toml#L5)
- [Requirement-owned checklist phases](../checklists/mantra-rebuild.toml#L12)
- [Matrix execution rules](../docs/briefings/2026-09-15-mantra-phase-1-2-matrix-charter.md#L57)

**Evidence:** No passing gate receipt.

**Decision:** No lifecycle action is required for accepted bootstrap history.

<details>
<summary>Implementation details</summary>

**Plan:** [plan.toml](../plans/mantra-hopfield-reconstruction/H1-PB-01/plan.toml)

**Retained patch:** [patches/requirement-first-contract.patch](../plans/mantra-hopfield-reconstruction/H1-PB-01/patches/requirement-first-contract.patch)

**Implementation roots:** [contracts](.) · [checklists](../checklists) · [docs/briefings](../docs/briefings) · [plans](../plans)

**Test roots:** [tests/phase1](../tests/phase1)

**Dependencies:** None

**Gate steps:**

```bash
# typecheck
(cd . && pyright tests/phase1)
# test
(cd . && python3 -m unittest tests.phase1.test_hopfield_contract -q)
# documentation
(cd . && python3 /Users/machina/.agents/skills/code-documentation/scripts/check-schema-descriptions.py tests/phase1)
# lint
(cd . && ruff format --check tests/phase1)
# lint
(cd . && ruff check tests/phase1)
```

</details>

<a id="h1-pb-02"></a>

#### <nobr><code>H1-PB-02</code></nobr>

**Status:** drafting

**Requirement contribution:** Make the existing Hopfield loader reject disagreement among feature, coefficient-target, and truth perturbation order before training or prediction.

**Review handoff**

**What changed**

- The Hopfield loader now reads perturbation labels beside fit and tune truth rows and compares them with the feature order before using the numeric rows.
- The observing test reuses one complete fixture to prove matching labels succeed and either fit or tune disagreement fails.

**Plan deviations:** Everything went according to plan.

**Start work:** [Open current plan](../plans/mantra-hopfield-reconstruction/H1-PB-02/plan.toml)

**Review these files**

- [Complete H1-PB-02 diff](../plans/mantra-hopfield-reconstruction/H1-PB-02/patches/truth-perturbation-order.patch#L1)
- [Truth-surface loading and row-order join](../../mantra/experiments/v1938_sota_clean_repro/src/step01/hopfield/loader.py#L265)
- [Existing projected-feature acceptance fixture](../../mantra/experiments/v1938_sota_clean_repro/tests/step01/test_hopfield_direct_family_contract.py#L451)

**Evidence:** No passing gate receipt.

**Decision:** Run the current PairBlock plan.

<details>
<summary>Implementation details</summary>

**Plan:** [plan.toml](../plans/mantra-hopfield-reconstruction/H1-PB-02/plan.toml)

**Retained patch:** [patches/truth-perturbation-order.patch](../plans/mantra-hopfield-reconstruction/H1-PB-02/patches/truth-perturbation-order.patch)

**Implementation roots:** [experiments/v1938_sota_clean_repro/src/step01/hopfield](../../mantra/experiments/v1938_sota_clean_repro/src/step01/hopfield)

**Test roots:** [experiments/v1938_sota_clean_repro/tests/step01](../../mantra/experiments/v1938_sota_clean_repro/tests/step01)

**Dependencies:** <nobr><code>H1-PB-01</code></nobr>

**Gate steps:**

```bash
# typecheck
(cd . && pyright experiments/v1938_sota_clean_repro/src/step01/hopfield/loader.py experiments/v1938_sota_clean_repro/tests/step01/test_hopfield_direct_family_contract.py)
# test
(cd . && python3 -m pytest -q experiments/v1938_sota_clean_repro/tests/step01/test_hopfield_direct_family_contract.py -k truth_perturbation_order)
# documentation
(cd . && python3 /Users/machina/.agents/skills/code-documentation/scripts/check-schema-descriptions.py experiments/v1938_sota_clean_repro/src/step01/hopfield/loader.py experiments/v1938_sota_clean_repro/tests/step01/test_hopfield_direct_family_contract.py)
# lint
(cd . && ruff check experiments/v1938_sota_clean_repro/src/step01/hopfield/loader.py experiments/v1938_sota_clean_repro/tests/step01/test_hopfield_direct_family_contract.py)
# lint
(cd . && ruff format --check --range=263-335 experiments/v1938_sota_clean_repro/src/step01/hopfield/loader.py)
# lint
(cd . && ruff format --check --range=457-690 experiments/v1938_sota_clean_repro/tests/step01/test_hopfield_direct_family_contract.py)
```

</details>

<a id="h1-pb-03"></a>

#### <nobr><code>H1-PB-03</code></nobr>

**Status:** waiting

**Requirement contribution:** Rebuild and compare the selected descriptor-side Hopfield inputs.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H1-PB-02</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="h1-pb-04"></a>

#### <nobr><code>H1-PB-04</code></nobr>

**Status:** waiting

**Requirement contribution:** Rebuild and compare the selected target-side and response-transform Hopfield inputs.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H1-PB-03</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="h1-pb-05"></a>

#### <nobr><code>H1-PB-05</code></nobr>

**Status:** waiting

**Requirement contribution:** Assemble the rebuilt Hopfield model inputs and prove array and population parity.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H1-PB-04</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="h1-pb-06"></a>

#### <nobr><code>H1-PB-06</code></nobr>

**Status:** waiting

**Requirement contribution:** Train the selected Hopfield encoder and reproduce its retained weights and selection record.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H1-PB-05</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="h1-pb-07"></a>

#### <nobr><code>H1-PB-07</code></nobr>

**Status:** waiting

**Requirement contribution:** Run raw-gene retrieval and reference correction and prove exact final output parity.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H1-PB-06</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="h1-pb-08"></a>

#### <nobr><code>H1-PB-08</code></nobr>

**Status:** waiting

**Requirement contribution:** Resolve the complete Phase 1 producer and evidence graph and close Hopfield reconstruction.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H1-PB-07</code></nobr>

**Next action:** Wait for the declared dependencies.


### Requirements

| Requirement | Claim | Progress | Verifiers | PairBlocks |
|---|---|---|---|---|
| <nobr><code>H1-REQ-01</code></nobr> | Phase 1 must begin from the selected Phase 0 Hopfield encoder SHA-256 2433527c3b23b66a16cedc0f7bc43867e4298af4d7a0733b202a8018ba876610, prediction SHA-256 d7180c4669a11b0b2fb184814aafb48ebafe75b02e4bd07998c337aa64dc59b7, and hold PearsonDelta 0.5861640938949398. | complete | <nobr><code>H1-VR-01</code></nobr> | <nobr><code>H1-PB-01</code></nobr> |
| <nobr><code>H1-REQ-02</code></nobr> | Before any numerical comparison, training, or prediction, the selected Hopfield path must reject disagreement among the ordered perturbation labels for descriptor features, coefficient targets, and fit or tune truth rows. | in_progress | <nobr><code>H1-VR-02</code></nobr> | <nobr><code>H1-PB-02</code></nobr> |
| <nobr><code>H1-REQ-03</code></nobr> | The selected matched-control, control-program, core83, response40, family64, and gene-shift inputs must be rebuilt from their approved producers and match the retained historical files by keys, perturbation order, gene order, shape, dtype, and values. | planned | <nobr><code>H1-VR-03</code></nobr> | <nobr><code>H1-PB-03</code></nobr> |
| <nobr><code>H1-REQ-04</code></nobr> | The selected coefficient targets, fit and tune truth rows, response-block contract, response rotation, and response-similarity graph must be rebuilt from their approved producers and match the retained historical files by keys, row and column order, shape, dtype, and values. | planned | <nobr><code>H1-VR-04</code></nobr> | <nobr><code>H1-PB-04</code></nobr> |
| <nobr><code>H1-REQ-05</code></nobr> | The Hopfield loader must assemble the rebuilt inputs with the selected gene order, shapes, dtypes, and fit plus tune normalization population and reproduce every retained model input array. | planned | <nobr><code>H1-VR-05</code></nobr> | <nobr><code>H1-PB-05</code></nobr> |
| <nobr><code>H1-REQ-06</code></nobr> | The 187 to 384 to 384 to 128 Hopfield encoder must be trained under the selected historical objectives and seed and reproduce the retained weights while recording checkpoints, logs, selection scores, and the VIPER run. | planned | <nobr><code>H1-VR-06</code></nobr> | <nobr><code>H1-PB-06</code></nobr> |
| <nobr><code>H1-REQ-07</code></nobr> | Raw-gene retrieval from fit memory at temperature 0.055 and reference correction must reproduce prediction SHA-256 d7180c4669a11b0b2fb184814aafb48ebafe75b02e4bd07998c337aa64dc59b7 byte for byte and hold PearsonDelta 0.5861640938949398 exactly. | planned | <nobr><code>H1-VR-07</code></nobr> | <nobr><code>H1-PB-07</code></nobr> |
| <nobr><code>H1-REQ-08</code></nobr> | Every accepted Phase 1 producer, input, output, comparison, and implementation commit must remain reachable through retained VIPER and contract-protocol evidence. | planned | <nobr><code>H1-VR-08</code></nobr> | <nobr><code>H1-PB-08</code></nobr> |

### Verification rules

| Rule | Requirements | Acceptance conditions | Success case | Rejection cases |
|---|---|---|---|---|
| <nobr><code>H1-VR-01</code></nobr> | <nobr><code>H1-REQ-01</code></nobr> | The typed Phase 1 contract names the selected score and exact prediction digest, and the retained Phase 0 index resolves the replay receipt. | [HopfieldContractTests.test_names_selected_phase0_baseline](../tests/phase1/test_hopfield_contract.py) | [HopfieldContractTests.test_rejects_changed_prediction_identity](../tests/phase1/test_hopfield_contract.py) |
| <nobr><code>H1-VR-02</code></nobr> | <nobr><code>H1-REQ-02</code></nobr> | The existing Hopfield loader accepts equal feature, coefficient-target, and truth perturbation labels and rejects a truth surface whose fit or tune labels are reordered. | [test_accepts_matching_truth_perturbation_order](../../mantra/experiments/v1938_sota_clean_repro/tests/step01/test_hopfield_direct_family_contract.py) | [test_rejects_truth_perturbation_order_mismatch](../../mantra/experiments/v1938_sota_clean_repro/tests/step01/test_hopfield_direct_family_contract.py) |
| <nobr><code>H1-VR-03</code></nobr> | <nobr><code>H1-REQ-03</code></nobr> | Each rebuilt descriptor-side input has the same NPZ keys, ordered perturbations and genes, shapes, dtypes, and arrays as its retained historical counterpart. | [test_rebuilds_selected_descriptor_inputs](../../mantra/src/mantra/rebuild/tests/test_hopfield_preprocessing.py) | [test_rejects_changed_descriptor_input](../../mantra/src/mantra/rebuild/tests/test_hopfield_preprocessing.py) |
| <nobr><code>H1-VR-04</code></nobr> | <nobr><code>H1-REQ-04</code></nobr> | Each rebuilt target-side input has the same NPZ or JSON keys, ordered rows and columns, shapes, dtypes, and values as its retained historical counterpart. | [test_rebuilds_selected_target_inputs](../../mantra/src/mantra/rebuild/tests/test_hopfield_preprocessing.py) | [test_rejects_changed_target_input](../../mantra/src/mantra/rebuild/tests/test_hopfield_preprocessing.py) |
| <nobr><code>H1-VR-05</code></nobr> | <nobr><code>H1-REQ-05</code></nobr> | The assembled model inputs reproduce every retained array and use fit plus tune rows for configured normalization and training populations. | [test_rebuilds_selected_model_inputs](../../mantra/src/mantra/rebuild/tests/test_hopfield_preprocessing.py) | [test_rejects_changed_model_input_or_population](../../mantra/src/mantra/rebuild/tests/test_hopfield_preprocessing.py) |
| <nobr><code>H1-VR-06</code></nobr> | <nobr><code>H1-REQ-06</code></nobr> | The training run uses the approved architecture, objectives, seed, data identities, and selection rule and reproduces the retained encoder weights with complete logs and checkpoints. | [test_trains_selected_hopfield_encoder](../../mantra/src/mantra/rebuild/tests/test_hopfield_training.py) | [test_rejects_changed_training_contract](../../mantra/src/mantra/rebuild/tests/test_hopfield_training.py) |
| <nobr><code>H1-VR-07</code></nobr> | <nobr><code>H1-REQ-07</code></nobr> | The final gate requires equal prediction bytes and an exactly equal hold PearsonDelta of 0.5861640938949398. | [test_reproduces_selected_hopfield_output](../../mantra/src/mantra/rebuild/tests/test_hopfield_reconstruction.py) | [test_rejects_equal_score_with_changed_prediction_bytes](../../mantra/src/mantra/rebuild/tests/test_hopfield_reconstruction.py) |
| <nobr><code>H1-VR-08</code></nobr> | <nobr><code>H1-REQ-08</code></nobr> | The terminal registration resolves every accepted Phase 1 receipt, artifact, source commit, and producer edge from retained records. | [test_resolves_complete_phase1_provenance](../tests/phase1/test_hopfield_registration.py) | [test_rejects_severed_phase1_provenance](../tests/phase1/test_hopfield_registration.py) |
<!-- contract-protocol:generated:end -->

## Reconstruction order

1. Reject disagreement among the feature, coefficient-target, and truth
   perturbation order before training or prediction.
2. Rebuild matched controls, control programs, response representations,
   biological descriptors, coefficient targets, and reference shifts.
   Compare their perturbation rows, gene columns, shapes, dtypes,
   normalization population, and numerical values with the historical
   artifacts.
3. Train and select the `187 → 384 → 384 → 128` encoder.
4. Run raw-gene retrieval at temperature `0.055`, apply reference correction,
   and require exact prediction-file and score parity.
5. Register the accepted producers and artifacts through VIPER.

Each implementation PairBlock receives its own plan only when work begins.
