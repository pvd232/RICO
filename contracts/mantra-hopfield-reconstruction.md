# MANTRA Hopfield Reconstruction

This contract rebuilds the selected Hopfield path from its preprocessing
inputs through encoder training, raw-gene retrieval, and reference correction.
Historical outputs are comparison references; no reconstruction stage may
consume them as model inputs.

The starting result is the Phase 0 replay: encoder SHA-256
`2433527c3b23b66a16cedc0f7bc43867e4298af4d7a0733b202a8018ba876610`,
prediction SHA-256
`d7180c4669a11b0b2fb184814aafb48ebafe75b02e4bd07998c337aa64dc59b7`
and hold `PearsonDelta` `0.5861640938949398`. The retained receipt is indexed
at `evidence/phase0/mantra/hopfield_output_parity_receipt.json`.

<!-- contract-protocol:generated:start -->
**In progress.** [Jump to current PairBlock](#h1-pb-02)

### PairBlocks

<a id="h1-pb-01"></a>

#### <nobr><code>H1-PB-01</code></nobr>

**Status:** bootstrap-complete

**Requirement contribution:** Install the typed Phase 1 contract and checklist workspace and bind them to the trusted Phase 0 Hopfield result.

**Plan:** [plan.toml](../plans/mantra-hopfield-reconstruction/H1-PB-01/plan.toml)

**Current receipt:** [receipt](../evidence/mantra-rebuild-phase-1/bootstrap.json)

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

**Requirement contribution:** Implement the row, gene, fitting-population, shape, dtype, and normalization identity boundary.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H1-PB-01</code></nobr>

**Next action:** Run the current PairBlock plan.

<a id="h1-pb-03"></a>

#### <nobr><code>H1-PB-03</code></nobr>

**Status:** waiting

**Requirement contribution:** Rebuild and compare the selected preprocessing artifacts in producer order.

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
| <nobr><code>H1-REQ-02</code></nobr> | Every reconstructed array must retain its row identities, gene axis, fitting population, shape, dtype, and normalization population. | in_progress | <nobr><code>H1-VR-02</code></nobr> | <nobr><code>H1-PB-02</code></nobr> |
| <nobr><code>H1-REQ-03</code></nobr> | Matched controls, control programs, response representations, biological descriptors, coefficient targets, and reference shifts must be rebuilt in dependency order and compared with their historical artifacts. | planned | <nobr><code>H1-VR-03</code></nobr> | <nobr><code>H1-PB-03</code></nobr> |
| <nobr><code>H1-REQ-04</code></nobr> | The 187 to 384 to 384 to 128 Hopfield encoder must be trained under the selected historical objectives and retain its checkpoints, logs, selection decision, and VIPER run. | planned | <nobr><code>H1-VR-04</code></nobr> | <nobr><code>H1-PB-04</code></nobr> |
| <nobr><code>H1-REQ-05</code></nobr> | Raw-gene retrieval at temperature 0.055 and reference correction must reproduce the selected prediction file byte for byte and the hold PearsonDelta exactly. | planned | <nobr><code>H1-VR-05</code></nobr> | <nobr><code>H1-PB-05</code></nobr> |
| <nobr><code>H1-REQ-06</code></nobr> | Every accepted Phase 1 producer, input, output, comparison, and implementation commit must remain reachable through retained VIPER and contract-protocol evidence. | planned | <nobr><code>H1-VR-06</code></nobr> | <nobr><code>H1-PB-06</code></nobr> |

### Verification rules

| Rule | Requirements | Acceptance conditions | Success case | Rejection cases |
|---|---|---|---|---|
| <nobr><code>H1-VR-01</code></nobr> | <nobr><code>H1-REQ-01</code></nobr> | The typed Phase 1 contract names the selected score and exact prediction digest, and the retained Phase 0 index resolves the replay receipt. | [HopfieldContractTests.test_names_selected_phase0_baseline](../tests/phase1/test_hopfield_contract.py) | [HopfieldContractTests.test_rejects_changed_prediction_identity](../tests/phase1/test_hopfield_contract.py) |
| <nobr><code>H1-VR-02</code></nobr> | <nobr><code>H1-REQ-02</code></nobr> | A changed row order, gene order, fitting population, shape, dtype, or normalization population fails before numerical comparison. | [test_accepts_exact_reconstruction_identities](../../mantra/src/mantra/rebuild/tests/test_hopfield_reconstruction_identity.py) | [test_rejects_changed_reconstruction_identity](../../mantra/src/mantra/rebuild/tests/test_hopfield_reconstruction_identity.py) |
| <nobr><code>H1-VR-03</code></nobr> | <nobr><code>H1-REQ-03</code></nobr> | Each preprocessing producer records its ordered inputs and emits an identity-bearing artifact whose arrays meet the approved comparison rule. | [test_rebuilds_selected_preprocessing_chain](../../mantra/src/mantra/rebuild/tests/test_hopfield_preprocessing.py) | [test_rejects_changed_preprocessing_array](../../mantra/src/mantra/rebuild/tests/test_hopfield_preprocessing.py) |
| <nobr><code>H1-VR-04</code></nobr> | <nobr><code>H1-REQ-04</code></nobr> | The training run uses the approved architecture, objective, seed, data identities, and selection rule and retains the selected checkpoint and logs. | [test_trains_selected_hopfield_encoder](../../mantra/src/mantra/rebuild/tests/test_hopfield_training.py) | [test_rejects_changed_training_contract](../../mantra/src/mantra/rebuild/tests/test_hopfield_training.py) |
| <nobr><code>H1-VR-05</code></nobr> | <nobr><code>H1-REQ-05</code></nobr> | The final gate requires equal prediction bytes and an exactly equal hold PearsonDelta of 0.5861640938949398. | [test_reproduces_selected_hopfield_output](../../mantra/src/mantra/rebuild/tests/test_hopfield_reconstruction.py) | [test_rejects_equal_score_with_changed_prediction_bytes](../../mantra/src/mantra/rebuild/tests/test_hopfield_reconstruction.py) |
| <nobr><code>H1-VR-06</code></nobr> | <nobr><code>H1-REQ-06</code></nobr> | The terminal registration resolves every accepted Phase 1 receipt, artifact, source commit, and producer edge from retained records. | [test_resolves_complete_phase1_provenance](../tests/phase1/test_hopfield_registration.py) | [test_rejects_severed_phase1_provenance](../tests/phase1/test_hopfield_registration.py) |
<!-- contract-protocol:generated:end -->

## Reconstruction order

1. Freeze row, gene, fitting-population, shape, dtype, and normalization
   identities.
2. Rebuild matched controls, control programs, response representations,
   biological descriptors, coefficient targets, and reference shifts.
3. Train and select the `187 → 384 → 384 → 128` encoder.
4. Run raw-gene retrieval at temperature `0.055`, apply reference correction,
   and require exact prediction-file and score parity.
5. Register the accepted producers and artifacts through VIPER.

Each implementation PairBlock receives its own plan only when work begins.
