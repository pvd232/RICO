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

**Plan:** [plan.toml](../plans/mantra-hopfield-reconstruction/H1-PB-01/plan.toml)

**Current receipt:** [receipt](../evidence/mantra-rebuild/bootstrap.json)

<details>
<summary>Implementation and gate details</summary>

**Candidate files:** [contracts/mantra-hopfield-reconstruction.toml](../plans/mantra-hopfield-reconstruction/H1-PB-01/add/contracts/mantra-hopfield-reconstruction.toml) · [contracts/mantra-hopfield-reconstruction.md](../plans/mantra-hopfield-reconstruction/H1-PB-01/add/contracts/mantra-hopfield-reconstruction.md) · [checklists/mantra-rebuild-phase-1.toml](../plans/mantra-hopfield-reconstruction/H1-PB-01/add/checklists/mantra-rebuild-phase-1.toml) · [checklists/mantra-rebuild-phase-1.md](../plans/mantra-hopfield-reconstruction/H1-PB-01/add/checklists/mantra-rebuild-phase-1.md) · [tests/phase1/__init__.py](../plans/mantra-hopfield-reconstruction/H1-PB-01/add/tests/phase1/__init__.py) · [tests/phase1/test_hopfield_contract.py](../plans/mantra-hopfield-reconstruction/H1-PB-01/add/tests/phase1/test_hopfield_contract.py) · [docs/checklists/mantra-rebuild.md](../plans/mantra-hopfield-reconstruction/H1-PB-01/replace/docs/checklists/mantra-rebuild.md)

**Implementation roots:** [contracts](.) · [checklists](../checklists) · [docs/checklists](../docs/checklists)

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

**Next action:** No lifecycle action is required for accepted bootstrap history.

<a id="h1-pb-02"></a>

#### <nobr><code>H1-PB-02</code></nobr>

**Status:** drafting

**Requirement contribution:** Make the existing Hopfield loader reject disagreement among feature, coefficient-target, and truth perturbation order before training or prediction.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H1-PB-01</code></nobr>

**Next action:** Run the current PairBlock plan.

<a id="h1-pb-03"></a>

#### <nobr><code>H1-PB-03</code></nobr>

**Status:** waiting

**Requirement contribution:** Rebuild the selected preprocessing artifacts in producer order and compare their perturbation rows, gene columns, shapes, dtypes, normalization population, and numerical values with the historical artifacts.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H1-PB-02</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="h1-pb-04"></a>

#### <nobr><code>H1-PB-04</code></nobr>

**Status:** waiting

**Requirement contribution:** Train and select the historical Hopfield encoder through an identity-bound VIPER run.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H1-PB-03</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="h1-pb-05"></a>

#### <nobr><code>H1-PB-05</code></nobr>

**Status:** waiting

**Requirement contribution:** Rebuild raw-gene retrieval and reference correction and prove exact final output parity.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H1-PB-04</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="h1-pb-06"></a>

#### <nobr><code>H1-PB-06</code></nobr>

**Status:** waiting

**Requirement contribution:** Register the complete Phase 1 provenance graph and close the reconstruction checklist.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H1-PB-05</code></nobr>

**Next action:** Wait for the declared dependencies.


### Requirements

| Requirement | Claim | Progress | Verifiers | PairBlocks |
|---|---|---|---|---|
| <nobr><code>H1-REQ-01</code></nobr> | Phase 1 must begin from the selected Phase 0 Hopfield encoder SHA-256 2433527c3b23b66a16cedc0f7bc43867e4298af4d7a0733b202a8018ba876610, prediction SHA-256 d7180c4669a11b0b2fb184814aafb48ebafe75b02e4bd07998c337aa64dc59b7, and hold PearsonDelta 0.5861640938949398. | complete | <nobr><code>H1-VR-01</code></nobr> | <nobr><code>H1-PB-01</code></nobr> |
| <nobr><code>H1-REQ-02</code></nobr> | Before training or prediction, the selected Hopfield path must reject disagreement among the ordered perturbation labels for descriptor features, coefficient targets, and fit or tune truth rows; reconstructed preprocessing outputs must retain the selected gene order, shapes, dtypes, and fit plus tune normalization population. | in_progress | <nobr><code>H1-VR-02</code></nobr>, <nobr><code>H1-VR-03</code></nobr> | <nobr><code>H1-PB-02</code></nobr>, <nobr><code>H1-PB-03</code></nobr> |
| <nobr><code>H1-REQ-03</code></nobr> | Matched controls, control programs, response representations, biological descriptors, coefficient targets, and reference shifts must be rebuilt in dependency order and compared with their historical artifacts. | planned | <nobr><code>H1-VR-03</code></nobr> | <nobr><code>H1-PB-03</code></nobr> |
| <nobr><code>H1-REQ-04</code></nobr> | The 187 to 384 to 384 to 128 Hopfield encoder must be trained under the selected historical objectives and retain its checkpoints, logs, selection decision, and VIPER run. | planned | <nobr><code>H1-VR-04</code></nobr> | <nobr><code>H1-PB-04</code></nobr> |
| <nobr><code>H1-REQ-05</code></nobr> | Raw-gene retrieval at temperature 0.055 and reference correction must reproduce the selected prediction file byte for byte and the hold PearsonDelta exactly. | planned | <nobr><code>H1-VR-05</code></nobr> | <nobr><code>H1-PB-05</code></nobr> |
| <nobr><code>H1-REQ-06</code></nobr> | Every accepted Phase 1 producer, input, output, comparison, and implementation commit must remain reachable through retained VIPER and contract-protocol evidence. | planned | <nobr><code>H1-VR-06</code></nobr> | <nobr><code>H1-PB-06</code></nobr> |

### Verification rules

| Rule | Requirements | Acceptance conditions | Success case | Rejection cases |
|---|---|---|---|---|
| <nobr><code>H1-VR-01</code></nobr> | <nobr><code>H1-REQ-01</code></nobr> | The typed Phase 1 contract names the selected score and exact prediction digest, and the retained Phase 0 index resolves the replay receipt. | [HopfieldContractTests.test_names_selected_phase0_baseline](../tests/phase1/test_hopfield_contract.py) | [HopfieldContractTests.test_rejects_changed_prediction_identity](../tests/phase1/test_hopfield_contract.py) |
| <nobr><code>H1-VR-02</code></nobr> | <nobr><code>H1-REQ-02</code></nobr> | The existing Hopfield loader accepts matching feature, coefficient-target, and truth perturbation order and rejects a truth surface whose fit or tune labels are reordered. | [test_projected_feature_spec_matches_projected_feature_bundle](../../mantra/experiments/v1938_sota_clean_repro/tests/step01/test_hopfield_direct_family_contract.py) | [test_rejects_truth_perturbation_order_mismatch](../../mantra/experiments/v1938_sota_clean_repro/tests/step01/test_hopfield_direct_family_contract.py) |
| <nobr><code>H1-VR-03</code></nobr> | <nobr><code>H1-REQ-02</code></nobr>, <nobr><code>H1-REQ-03</code></nobr> | Each rebuilt preprocessing artifact matches its historical perturbation rows, gene columns, shape, dtype, fit plus tune normalization population, and named numerical tolerance. | [test_rebuilds_selected_preprocessing_chain](../../mantra/src/mantra/rebuild/tests/test_hopfield_preprocessing.py) | [test_rejects_changed_preprocessing_array](../../mantra/src/mantra/rebuild/tests/test_hopfield_preprocessing.py) |
| <nobr><code>H1-VR-04</code></nobr> | <nobr><code>H1-REQ-04</code></nobr> | The training run uses the approved architecture, objective, seed, data identities, and selection rule and retains the selected checkpoint and logs. | [test_trains_selected_hopfield_encoder](../../mantra/src/mantra/rebuild/tests/test_hopfield_training.py) | [test_rejects_changed_training_contract](../../mantra/src/mantra/rebuild/tests/test_hopfield_training.py) |
| <nobr><code>H1-VR-05</code></nobr> | <nobr><code>H1-REQ-05</code></nobr> | The final gate requires equal prediction bytes and an exactly equal hold PearsonDelta of 0.5861640938949398. | [test_reproduces_selected_hopfield_output](../../mantra/src/mantra/rebuild/tests/test_hopfield_reconstruction.py) | [test_rejects_equal_score_with_changed_prediction_bytes](../../mantra/src/mantra/rebuild/tests/test_hopfield_reconstruction.py) |
| <nobr><code>H1-VR-06</code></nobr> | <nobr><code>H1-REQ-06</code></nobr> | The terminal registration resolves every accepted Phase 1 receipt, artifact, source commit, and producer edge from retained records. | [test_resolves_complete_phase1_provenance](../tests/phase1/test_hopfield_registration.py) | [test_rejects_severed_phase1_provenance](../tests/phase1/test_hopfield_registration.py) |
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
