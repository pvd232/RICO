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

After both historical models reproduce their retained results, the legacy
Hopfield path receives the exact retained MIL descriptor bundle: the shared
83-value core block, the 144-value five-source family block, and its matching
40-value response proxy. That changes the encoder input width from 187 to 267.
The bridge run keeps the remaining legacy model and configuration fixed, then
freezes its checkpoint, predictions, score, inputs, runtime, and source commit.
The bridge result becomes the baseline for later one-at-a-time substitutions.
The original 64-value Hopfield result remains the historical replay baseline.

<!-- contract-protocol:generated:start -->
**In progress.** [Jump to current PairBlock](#h1-pb-05a)

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

**Status:** complete

**Requirement contribution:** Make the existing Hopfield loader reject disagreement among feature, coefficient-target, and truth perturbation order before training or prediction.

**Review handoff**

**What changed**

- The Hopfield loader now reads perturbation labels beside fit and tune truth rows and compares them with the feature order before using the numeric rows.
- The observing test reuses one complete fixture to prove matching labels succeed and either fit or tune disagreement fails.

**Plan deviations:** The first formatting check reached two untouched legacy lines. The gate now checks only the changed truth-reader range; no unrelated source was reformatted.

**Start review:** [Open tested GitHub comparison](https://github.com/pvd232/MANTRA/compare/181e29768320a0d8f809428655972431e957d1c5...a23bf766b70941afa7c8b0fdc64b7ca1326d461b)

**Review these files**

- [Complete H1-PB-02 diff](../plans/mantra-hopfield-reconstruction/H1-PB-02/patches/truth-perturbation-order.patch#L1)
- [Truth-surface loading and row-order join](../../mantra/experiments/v1938_sota_clean_repro/src/step01/hopfield/loader.py#L265)
- [Existing projected-feature acceptance fixture](../../mantra/experiments/v1938_sota_clean_repro/tests/step01/test_hopfield_direct_family_contract.py#L451)

**Evidence:** [Passing gate receipt](../evidence/mantra-rebuild/H1-PB-02/gate-review-02.json)

**Decision:** <nobr><code>H1-PB-02</code></nobr> is complete; no further decision is required.

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
(cd . && ruff format --check --range=263-286 experiments/v1938_sota_clean_repro/src/step01/hopfield/loader.py)
# lint
(cd . && ruff format --check --range=457-690 experiments/v1938_sota_clean_repro/tests/step01/test_hopfield_direct_family_contract.py)
```

</details>

<a id="h1-pb-03"></a>

#### <nobr><code>H1-PB-03</code></nobr>

**Status:** complete

**Requirement contribution:** Freeze the descriptor-input ledger and restore every exact historical file without rebuilding upstream producers.

**Review handoff**

**What changed**

- The existing Hopfield replay identities now form one descriptor-input ledger that also names each retained producer record and exact Git restore route.
- One production function restores core83, response40, family64, and gene-shift directly from the accepted commit, verifies their bytes, and never reruns the matched-control or control-program producers.
- The observing tests compare every restored NPZ key, ordered axis, shape, dtype, and value and reject changed restored bytes.

**Plan deviations:** CodeQL database creation scanned archived nested environments despite the requested src boundary, so Matrix stopped it after five minutes and used the contract-named H1-VR-03 observer. The reusable sparse-analysis defect remains separate from this replay-input guarantee.

**Start review:** [Open tested GitHub comparison](https://github.com/pvd232/MANTRA/compare/a23bf766b70941afa7c8b0fdc64b7ca1326d461b...144932a442d2176eb2d9379ef37364c2656d1ea3)

**Review these files**

- [Complete H1-PB-03 diff](../plans/mantra-hopfield-reconstruction/H1-PB-03/patches/descriptor-input-ledger.patch#L1)
- [Descriptor ledger and exact Git restoration](../../mantra/src/mantra/rebuild/hopfield_replay.py#L75)

**Evidence:** [Passing gate receipt](../evidence/mantra-rebuild/H1-PB-03/gate-review-01.json)

**Decision:** <nobr><code>H1-PB-03</code></nobr> is complete; no further decision is required.

<details>
<summary>Implementation details</summary>

**Plan:** [plan.toml](../plans/mantra-hopfield-reconstruction/H1-PB-03/plan.toml)

**Retained patch:** [patches/descriptor-input-ledger.patch](../plans/mantra-hopfield-reconstruction/H1-PB-03/patches/descriptor-input-ledger.patch)

**Implementation roots:** [src/mantra/rebuild](../../mantra/src/mantra/rebuild)

**Test roots:** [src/mantra/rebuild/tests](../../mantra/src/mantra/rebuild/tests)

**Dependencies:** <nobr><code>H1-PB-02</code></nobr>

**Gate steps:**

```bash
# typecheck
(cd . && pyright src/mantra/rebuild/hopfield_replay.py src/mantra/rebuild/tests/test_hopfield_preprocessing.py)
# test
(cd . && python3 -m pytest -q -p no:cacheprovider src/mantra/rebuild/tests/test_hopfield_preprocessing.py)
# documentation
(cd . && python3 /Users/machina/.agents/skills/code-documentation/scripts/check-schema-descriptions.py src/mantra/rebuild/hopfield_replay.py src/mantra/rebuild/tests/test_hopfield_preprocessing.py)
# lint
(cd . && ruff format --check src/mantra/rebuild/hopfield_replay.py src/mantra/rebuild/tests/test_hopfield_preprocessing.py)
# lint
(cd . && ruff check src/mantra/rebuild/hopfield_replay.py src/mantra/rebuild/tests/test_hopfield_preprocessing.py)
```

</details>

<a id="h1-pb-04"></a>

#### <nobr><code>H1-PB-04</code></nobr>

**Status:** complete

**Requirement contribution:** Freeze the target-input ledger and restore every exact historical target and response-transform file.

**Review handoff**

**What changed**

- One retained ledger now names the five historical coefficient-target, truth-surface, response-contract, response-rotation, and response-similarity files by exact digest and signed Hugging Face archive member.
- The Hopfield replay checks that every ledger identity matches the file identity consumed by training, then delegates restoration to MANTRA's existing authenticated archive reader.
- The focused observers prove exact target selection and reject a changed historical identity before any archive download begins.

**Plan deviations:** Matrix built the isolated candidate before persisting this plan. The candidate remained uncommitted, and this plan freezes its exact diff before the protocol gate. CodeQL used a sparse src-only Git snapshot to exclude archived experiments from graph construction.

**Start review:** [Open tested GitHub comparison](https://github.com/pvd232/MANTRA/compare/9638a876893493ef1955b01204158108c7ba068d...17f3a09bd1055c432e61ee03c196bb4819845195)

**Review these files**

- [Complete H1-PB-04 diff](../plans/mantra-hopfield-reconstruction/H1-PB-04/patches/target-input-ledger.patch#L1)
- [Target ledger and verified archive restoration](../../mantra/src/mantra/rebuild/hopfield_replay.py#L87)

**Evidence:** [Passing gate receipt](../evidence/mantra-rebuild/H1-PB-04/gate-review-03.json)

**Decision:** <nobr><code>H1-PB-04</code></nobr> is complete; no further decision is required.

<details>
<summary>Implementation details</summary>

**Plan:** [plan.toml](../plans/mantra-hopfield-reconstruction/H1-PB-04/plan.toml)

**Retained patch:** [patches/target-input-ledger.patch](../plans/mantra-hopfield-reconstruction/H1-PB-04/patches/target-input-ledger.patch)

**Implementation roots:** [src/mantra/rebuild](../../mantra/src/mantra/rebuild) · [cleanup](../../mantra/cleanup) · [experiments/v1938_sota_clean_repro/src](../../mantra/experiments/v1938_sota_clean_repro/src) · [experiments/v1938_sota_clean_repro/runs/matrix_fit_only_bold_step02_20260715T083000Z/scripts](../../mantra/experiments/v1938_sota_clean_repro/runs/matrix_fit_only_bold_step02_20260715T083000Z/scripts) · [pyproject.toml](../../mantra/pyproject.toml) · [pyrightconfig.json](../../mantra/pyrightconfig.json)

**Test roots:** [src/mantra/rebuild/tests](../../mantra/src/mantra/rebuild/tests) · [conftest.py](../../mantra/conftest.py)

**Dependencies:** <nobr><code>H1-PB-03</code></nobr>

**Gate steps:**

```bash
# typecheck
(cd . && pyright src/mantra/rebuild/hopfield_replay.py src/mantra/rebuild/tests/test_hopfield_preprocessing.py)
# test
(cd . && python3 -m pytest -q -p no:cacheprovider src/mantra/rebuild/tests/test_hopfield_preprocessing.py::test_restores_selected_target_inputs src/mantra/rebuild/tests/test_hopfield_preprocessing.py::test_rejects_changed_target_input)
# documentation
(cd . && python3 /Users/machina/.agents/skills/code-documentation/scripts/check-schema-descriptions.py src/mantra/rebuild/hopfield_replay.py src/mantra/rebuild/tests/test_hopfield_preprocessing.py)
# lint
(cd . && ruff format --check src/mantra/rebuild/hopfield_replay.py src/mantra/rebuild/tests/test_hopfield_preprocessing.py)
# lint
(cd . && ruff check src/mantra/rebuild/hopfield_replay.py src/mantra/rebuild/tests/test_hopfield_preprocessing.py)
```

</details>

<a id="h1-pb-05"></a>

#### <nobr><code>H1-PB-05</code></nobr>

**Status:** waiting

**Requirement contribution:** Assemble only the thirteen accepted Build outputs, connect them to Embed, Predict, and Evaluate as FutureInputRefs, and prove the final strict replay baseline.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H1-PB-05M</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="h1-pb-05a"></a>

#### <nobr><code>H1-PB-05A</code></nobr>

**Status:** drafting

**Requirement contribution:** Resolve the versioned source, build the Hopfield input contract, compare it with the retained file, apply the declared mismatch ladder, and retain the VIPER receipt.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H1-PB-07</code></nobr>

**Next action:** Run the current PairBlock plan.

<a id="h1-pb-05b"></a>

#### <nobr><code>H1-PB-05B</code></nobr>

**Status:** waiting

**Requirement contribution:** Resolve the versioned source, build the complete Hopfield stage configuration, compare it with the retained configuration, apply the declared mismatch ladder, and retain the VIPER receipt.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H1-PB-05A</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="h1-pb-05c"></a>

#### <nobr><code>H1-PB-05C</code></nobr>

**Status:** waiting

**Requirement contribution:** Download the true sources, build core83, compare it with the retained input, apply the declared mismatch ladder, and retain the VIPER receipt.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H1-PB-05B</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="h1-pb-05d"></a>

#### <nobr><code>H1-PB-05D</code></nobr>

**Status:** waiting

**Requirement contribution:** Download the true sources, build response40, compare it with the retained input, apply the declared mismatch ladder, and retain the VIPER receipt.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H1-PB-05C</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="h1-pb-05e"></a>

#### <nobr><code>H1-PB-05E</code></nobr>

**Status:** waiting

**Requirement contribution:** Download the true sources, build family64, compare it with the retained input, apply the declared mismatch ladder, and retain the VIPER receipt.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H1-PB-05D</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="h1-pb-05f"></a>

#### <nobr><code>H1-PB-05F</code></nobr>

**Status:** waiting

**Requirement contribution:** Download the true sources, build the gene-shift input, compare it with the retained input, apply the declared mismatch ladder, and retain the VIPER receipt.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H1-PB-05E</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="h1-pb-05g"></a>

#### <nobr><code>H1-PB-05G</code></nobr>

**Status:** waiting

**Requirement contribution:** Download the true sources, build the response-block definition, compare it with the retained input, apply the declared mismatch ladder, and retain the VIPER receipt.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H1-PB-05F</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="h1-pb-05h"></a>

#### <nobr><code>H1-PB-05H</code></nobr>

**Status:** waiting

**Requirement contribution:** Download the true sources, build the coefficient targets, compare them with the retained input, apply the declared mismatch ladder, and retain the VIPER receipt.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H1-PB-05G</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="h1-pb-05i"></a>

#### <nobr><code>H1-PB-05I</code></nobr>

**Status:** waiting

**Requirement contribution:** Download the true sources, build the fit and tune truth surface, compare it with the retained input, apply the declared mismatch ladder, and retain the VIPER receipt.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H1-PB-05H</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="h1-pb-05j"></a>

#### <nobr><code>H1-PB-05J</code></nobr>

**Status:** waiting

**Requirement contribution:** Download the true sources, build the hold truth surface, compare it with the retained input, apply the declared mismatch ladder, and retain the VIPER receipt.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H1-PB-05I</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="h1-pb-05k"></a>

#### <nobr><code>H1-PB-05K</code></nobr>

**Status:** waiting

**Requirement contribution:** Download the true sources, build the response-program contract, compare it with the retained input, apply the declared mismatch ladder, and retain the VIPER receipt.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H1-PB-05J</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="h1-pb-05l"></a>

#### <nobr><code>H1-PB-05L</code></nobr>

**Status:** waiting

**Requirement contribution:** Download the true sources, build the response-program rotation, compare it with the retained input, apply the declared mismatch ladder, and retain the VIPER receipt.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H1-PB-05K</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="h1-pb-05m"></a>

#### <nobr><code>H1-PB-05M</code></nobr>

**Status:** waiting

**Requirement contribution:** Download the true sources, build the response-similarity graph, compare it with the retained input, apply the declared mismatch ladder, and retain the VIPER receipt.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H1-PB-05L</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="h1-pb-06"></a>

#### <nobr><code>H1-PB-06</code></nobr>

**Status:** complete

**Requirement contribution:** Train the selected Hopfield encoder and reproduce its retained weights and selection record.

**Review handoff**

**What changed**

- The historical Hopfield encoder was retrained twice through strict VIPER under the declared Python 3.13, Torch 2.12.1, and CUDA 13 environment.
- Both runs emitted the same 1084512-byte encoder with SHA-256 af1f62c4c315c65e7379b97c57646b49b35c7f3fc3f69fcf6f94f0c8df276da9, which is now the modern replay baseline.
- The environment now declares zstandard because VIPER requires it to read the retained restoration archive.

**Plan deviations:** The archived encoder bytes did not reproduce under the modern runtime after the configuration was checked. Two independent strict VIPER runs produced the same modern bytes, so the declared fallback rule pinned that reproducible result without changing the model or inputs.

**Start review:** [Open tested GitHub comparison](https://github.com/pvd232/MANTRA/compare/0a12592c784bcb95c48b22da6b459b3c090f6d6f...abf965119c492ca167674d8564cbd4dbbf373de7)

**Review these files**

- [Complete H1-PB-06 diff](../plans/mantra-hopfield-reconstruction/H1-PB-06/patches/modern-encoder-baseline.patch#L1)
- [Modern encoder identity](../../mantra/src/mantra/rebuild/hopfield_replay.py#L78)

**Evidence:** [Passing gate receipt](../evidence/mantra-rebuild/H1-PB-06/gate-review-05.json)

**Decision:** <nobr><code>H1-PB-06</code></nobr> is complete; no further decision is required.

<details>
<summary>Implementation details</summary>

**Plan:** [plan.toml](../plans/mantra-hopfield-reconstruction/H1-PB-06/plan.toml)

**Retained patch:** [patches/modern-encoder-baseline.patch](../plans/mantra-hopfield-reconstruction/H1-PB-06/patches/modern-encoder-baseline.patch)

**Implementation roots:** [src/mantra/rebuild](../../mantra/src/mantra/rebuild) · [experiments/v1938_sota_clean_repro](../../mantra/experiments/v1938_sota_clean_repro) · [cleanup](../../mantra/cleanup) · [nuevo/environment.yml](../../mantra/nuevo/environment.yml) · [pyrightconfig.json](../../mantra/pyrightconfig.json) · [pyproject.toml](../../mantra/pyproject.toml) · [src/mantra/__init__.py](../../mantra/src/mantra/__init__.py)

**Test roots:** [src/mantra/rebuild/tests](../../mantra/src/mantra/rebuild/tests) · [conftest.py](../../mantra/conftest.py)

**Dependencies:** <nobr><code>H1-PB-04</code></nobr>

**Gate steps:**

```bash
# typecheck
(cd . && pyright src/mantra/rebuild/hopfield_replay.py src/mantra/rebuild/tests/test_hopfield_replay.py)
# test
(cd . && python3 -m pytest -q src/mantra/rebuild/tests/test_hopfield_replay.py)
# documentation
(cd . && python3 /Users/machina/.agents/skills/code-documentation/scripts/check-schema-descriptions.py src/mantra/rebuild/hopfield_replay.py src/mantra/rebuild/tests/test_hopfield_replay.py)
# lint
(cd . && ruff format --check src/mantra/rebuild/hopfield_replay.py src/mantra/rebuild/tests/test_hopfield_replay.py)
# lint
(cd . && ruff check src/mantra/rebuild/hopfield_replay.py src/mantra/rebuild/tests/test_hopfield_replay.py)
```

</details>

<a id="h1-pb-07"></a>

#### <nobr><code>H1-PB-07</code></nobr>

**Status:** complete

**Requirement contribution:** Run raw-gene retrieval and reference correction and prove exact final output parity.

**Review handoff**

**What changed**

- Two independent modern strict VIPER runs emitted the same raw-gene prediction file and hold PearsonDelta.
- The accepted prediction is 38391087 bytes with SHA-256 f8e8e6a6fe291143debd3d8e8b3ab9c4e2aed5afd3b2391e7856c7d8fd7e262b, and the accepted hold PearsonDelta is 0.5861640983697456.
- A third strict run passed Embed, Predict, and Evaluate against the pinned modern identities while retaining the Phase 0 artifacts as comparison oracles.

**Plan deviations:** The modern prediction arrays and serialized file differ from the historical environment despite an unchanged model, configuration, and input bundle. The repeated modern result was pinned under the approved environment-divergence rule.

**Start review:** [Open tested GitHub comparison](https://github.com/pvd232/MANTRA/compare/0a12592c784bcb95c48b22da6b459b3c090f6d6f...e38082e3ae72602d8c6d025e1b0d0cfcbcea7825)

**Review these files**

- [Complete H1-PB-07 diff](../plans/mantra-hopfield-reconstruction/H1-PB-07/patches/modern-prediction-baseline.patch#L1)
- [Modern prediction and score identities](../../mantra/src/mantra/rebuild/hopfield_replay.py#L75)

**Evidence:** [Passing gate receipt](../evidence/mantra-rebuild/H1-PB-07/gate-review-01.json)

**Decision:** <nobr><code>H1-PB-07</code></nobr> is complete; no further decision is required.

<details>
<summary>Implementation details</summary>

**Plan:** [plan.toml](../plans/mantra-hopfield-reconstruction/H1-PB-07/plan.toml)

**Retained patch:** [patches/modern-prediction-baseline.patch](../plans/mantra-hopfield-reconstruction/H1-PB-07/patches/modern-prediction-baseline.patch)

**Implementation roots:** [src/mantra/rebuild](../../mantra/src/mantra/rebuild) · [experiments/v1938_sota_clean_repro](../../mantra/experiments/v1938_sota_clean_repro) · [cleanup](../../mantra/cleanup) · [pyrightconfig.json](../../mantra/pyrightconfig.json) · [pyproject.toml](../../mantra/pyproject.toml) · [src/mantra/__init__.py](../../mantra/src/mantra/__init__.py)

**Test roots:** [src/mantra/rebuild/tests](../../mantra/src/mantra/rebuild/tests) · [conftest.py](../../mantra/conftest.py)

**Dependencies:** <nobr><code>H1-PB-06</code></nobr>

**Gate steps:**

```bash
# typecheck
(cd . && pyright src/mantra/rebuild/hopfield_replay.py src/mantra/rebuild/tests/test_hopfield_replay.py)
# test
(cd . && python3 -m pytest -q src/mantra/rebuild/tests/test_hopfield_replay.py)
# documentation
(cd . && python3 /Users/machina/.agents/skills/code-documentation/scripts/check-schema-descriptions.py src/mantra/rebuild/hopfield_replay.py src/mantra/rebuild/tests/test_hopfield_replay.py)
# lint
(cd . && ruff format --check src/mantra/rebuild/hopfield_replay.py src/mantra/rebuild/tests/test_hopfield_replay.py)
# lint
(cd . && ruff check src/mantra/rebuild/hopfield_replay.py src/mantra/rebuild/tests/test_hopfield_replay.py)
```

</details>

<a id="h1-pb-08"></a>

#### <nobr><code>H1-PB-08</code></nobr>

**Status:** waiting

**Requirement contribution:** Resolve the complete Phase 1 producer and evidence graph and close Hopfield reconstruction.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H1-PB-05</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="h1-pb-09"></a>

#### <nobr><code>H1-PB-09</code></nobr>

**Status:** waiting

**Requirement contribution:** Run the unchanged legacy Hopfield model on the exact retained MIL input stack and freeze the resulting bridge baseline before modular reconstruction.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H1-PB-08</code></nobr>, <nobr><code>M2-PB-06</code></nobr>, <nobr><code>E0-PB-08</code></nobr>, <nobr><code>E0-PB-09</code></nobr>

**Next action:** Wait for the declared dependencies.


### Requirements

| Requirement | Claim | Progress | Verifiers | PairBlocks |
|---|---|---|---|---|
| <nobr><code>H1-REQ-01</code></nobr> | Phase 1 must begin from the selected Phase 0 Hopfield encoder SHA-256 2433527c3b23b66a16cedc0f7bc43867e4298af4d7a0733b202a8018ba876610, prediction SHA-256 d7180c4669a11b0b2fb184814aafb48ebafe75b02e4bd07998c337aa64dc59b7, and hold PearsonDelta 0.5861640938949398. | complete | <nobr><code>H1-VR-01</code></nobr> | <nobr><code>H1-PB-01</code></nobr> |
| <nobr><code>H1-REQ-02</code></nobr> | Before any numerical comparison, training, or prediction, the selected Hopfield path must reject disagreement among the ordered perturbation labels for descriptor features, coefficient targets, and fit or tune truth rows. | complete | <nobr><code>H1-VR-02</code></nobr> | <nobr><code>H1-PB-02</code></nobr> |
| <nobr><code>H1-REQ-03</code></nobr> | Before replay training, one complete descriptor-input ledger must name every selected matched-control, control-program, core83, response40, family64, and gene-shift file, its retained digest, producing script or record, and restore route. Restoring that ledger must reproduce the historical keys, perturbation order, gene order, shapes, dtypes, and values without rerunning upstream producers. | complete | <nobr><code>H1-VR-03</code></nobr> | <nobr><code>H1-PB-03</code></nobr> |
| <nobr><code>H1-REQ-04</code></nobr> | Before replay training, one complete target-input ledger must name every selected coefficient target, fit and tune truth surface, response-block contract, response rotation, and response-similarity graph, together with its retained digest, producing script or record, and restore route. Restoring that ledger must reproduce the historical keys, row and column order, shapes, dtypes, and values without rerunning upstream producers. | complete | <nobr><code>H1-VR-04</code></nobr> | <nobr><code>H1-PB-04</code></nobr> |
| <nobr><code>H1-REQ-05</code></nobr> | The Hopfield loader must assemble the declared replay bundle and reproduce every retained model input array and fitted transformation state: descriptor columns use moments fitted on the declared fit plus tune rows; coefficient similarity uses per-row mean centering followed by L2 normalization; and every gene, perturbation, shape, dtype, and array order remains fixed. | planned | <nobr><code>H1-VR-05</code></nobr> | <nobr><code>H1-PB-05</code></nobr> |
| <nobr><code>H1-REQ-06</code></nobr> | The 187 to 384 to 384 to 128 Hopfield encoder must train under the selected objectives and seed in the declared Python 3.13, Torch 2.12.1, and CUDA 13 environment, including the configured auxiliary posterior target built from the whitened-PCA-denoised coefficient bank and neighbors selected by raw-coefficient cosine similarity. Two independent strict VIPER runs must reproduce encoder SHA-256 af1f62c4c315c65e7379b97c57646b49b35c7f3fc3f69fcf6f94f0c8df276da9 and 1084512 bytes while retaining the historical encoder as the comparison oracle. Final retrieval must continue to use the configured raw coefficient value memory. | complete | <nobr><code>H1-VR-06</code></nobr> | <nobr><code>H1-PB-06</code></nobr> |
| <nobr><code>H1-REQ-07</code></nobr> | Raw-gene retrieval from fit memory at temperature 0.055 and reference correction must reproducibly emit prediction SHA-256 f8e8e6a6fe291143debd3d8e8b3ab9c4e2aed5afd3b2391e7856c7d8fd7e262b, 38391087 bytes, and hold PearsonDelta 0.5861640983697456 in the declared modern environment while retaining the Phase 0 prediction and score as comparison oracles. | complete | <nobr><code>H1-VR-07</code></nobr> | <nobr><code>H1-PB-07</code></nobr> |
| <nobr><code>H1-REQ-08</code></nobr> | Every accepted Phase 1 producer, input, output, comparison, and implementation commit must remain reachable through retained VIPER and contract-protocol evidence. | planned | <nobr><code>H1-VR-08</code></nobr> | <nobr><code>H1-PB-08</code></nobr> |
| <nobr><code>H1-REQ-09</code></nobr> | After strict modern Hopfield and MIL replay baselines are frozen, the legacy Hopfield path must consume the exact retained MIL descriptor bundle: the shared 83-value core block, the 144-value five-source family block, and its matching 40-value response proxy. The bridge run must change only the encoder input-width binding from 187 to 267, retrain and evaluate the otherwise unchanged legacy model, and freeze its inputs, checkpoint, predictions, score, configuration, runtime, and implementation commit as the Hopfield MIL-stack bridge baseline. | planned | <nobr><code>H1-VR-09</code></nobr> | <nobr><code>H1-PB-09</code></nobr> |
| <nobr><code>H1-REQ-10</code></nobr> | Each of the thirteen declared Hopfield model inputs must be produced from its true external or versioned source by a retained VIPER source-acquisition and Build chain, then compared with the retained input on keys, ordered axes, shapes, dtypes, values, bytes, and SHA-256. Each chain must first build in the modern environment; on numerical mismatch it must rerun only acquisition and Build in the historical environment; if that matches, record environment-caused divergence and pin a repeated modern result; otherwise verify the configuration once, fail fast on another unexplained mismatch, and pin only a repeated corrected baseline. | in_progress | <nobr><code>H1-VR-10</code></nobr> | <nobr><code>H1-PB-05A</code></nobr>, <nobr><code>H1-PB-05B</code></nobr>, <nobr><code>H1-PB-05C</code></nobr>, <nobr><code>H1-PB-05D</code></nobr>, <nobr><code>H1-PB-05E</code></nobr>, <nobr><code>H1-PB-05F</code></nobr>, <nobr><code>H1-PB-05G</code></nobr>, <nobr><code>H1-PB-05H</code></nobr>, <nobr><code>H1-PB-05I</code></nobr>, <nobr><code>H1-PB-05J</code></nobr>, <nobr><code>H1-PB-05K</code></nobr>, <nobr><code>H1-PB-05L</code></nobr>, <nobr><code>H1-PB-05M</code></nobr> |
| <nobr><code>H1-REQ-11</code></nobr> | The final strict VIPER replay must consume only the thirteen accepted Build outputs, connect stage outputs to downstream stages as FutureInputRefs, and execute Embed, Predict, and Evaluate without reading retained model-input files directly. It must reproduce the accepted modern encoder, prediction, and score identities while retaining historical artifacts only as evaluation oracles. | planned | <nobr><code>H1-VR-11</code></nobr> | <nobr><code>H1-PB-05</code></nobr> |

### Verification rules

| Rule | Requirements | Acceptance conditions | Success case | Rejection cases |
|---|---|---|---|---|
| <nobr><code>H1-VR-01</code></nobr> | <nobr><code>H1-REQ-01</code></nobr> | The typed Phase 1 contract names the selected score and exact prediction digest, and the retained Phase 0 index resolves the replay receipt. | [HopfieldContractTests.test_names_selected_phase0_baseline](../tests/phase1/test_hopfield_contract.py) | [HopfieldContractTests.test_rejects_changed_prediction_identity](../tests/phase1/test_hopfield_contract.py) |
| <nobr><code>H1-VR-02</code></nobr> | <nobr><code>H1-REQ-02</code></nobr> | The existing Hopfield loader accepts equal feature, coefficient-target, and truth perturbation labels and rejects a truth surface whose fit or tune labels are reordered. | [test_accepts_matching_truth_perturbation_order](../../mantra/experiments/v1938_sota_clean_repro/tests/step01/test_hopfield_direct_family_contract.py) | [test_rejects_truth_perturbation_order_mismatch](../../mantra/experiments/v1938_sota_clean_repro/tests/step01/test_hopfield_direct_family_contract.py) |
| <nobr><code>H1-VR-03</code></nobr> | <nobr><code>H1-REQ-03</code></nobr> | The descriptor-input ledger resolves every retained file to its exact digest, producing script or record, and restore route; restoring it reproduces the historical NPZ keys, ordered perturbations and genes, shapes, dtypes, and arrays without running an upstream producer. | [test_restores_selected_descriptor_inputs](../../mantra/src/mantra/rebuild/tests/test_hopfield_preprocessing.py) | [test_rejects_changed_descriptor_input](../../mantra/src/mantra/rebuild/tests/test_hopfield_preprocessing.py) |
| <nobr><code>H1-VR-04</code></nobr> | <nobr><code>H1-REQ-04</code></nobr> | The target-input ledger resolves every retained file to its exact digest, producing script or record, and restore route; restoring it reproduces the historical NPZ or JSON keys, ordered rows and columns, shapes, dtypes, and values without running an upstream producer. | [test_restores_selected_target_inputs](../../mantra/src/mantra/rebuild/tests/test_hopfield_preprocessing.py) | [test_rejects_changed_target_input](../../mantra/src/mantra/rebuild/tests/test_hopfield_preprocessing.py) |
| <nobr><code>H1-VR-05</code></nobr> | <nobr><code>H1-REQ-05</code></nobr> | The loader assembles only ledger-restored inputs and reproduces every retained array and fitted normalization state; descriptor columns use fit plus tune moments, and coefficient similarities use row-mean centering followed by L2 normalization. | [test_assembles_selected_replay_inputs](../../mantra/src/mantra/rebuild/tests/test_hopfield_preprocessing.py) | [test_rejects_changed_model_input_or_population](../../mantra/src/mantra/rebuild/tests/test_hopfield_preprocessing.py) |
| <nobr><code>H1-VR-06</code></nobr> | <nobr><code>H1-REQ-06</code></nobr> | Two independent strict VIPER runs under the declared modern environment use the same source, configuration, seed, inputs, architecture, objectives, and raw value memory and emit the declared encoder bytes and SHA-256 with complete logs and checkpoints. | [test_accepts_repeated_modern_encoder_identity](../../mantra/src/mantra/rebuild/tests/test_hopfield_replay.py) | [test_rejects_changed_modern_encoder_identity](../../mantra/src/mantra/rebuild/tests/test_hopfield_replay.py) |
| <nobr><code>H1-VR-07</code></nobr> | <nobr><code>H1-REQ-07</code></nobr> | Two independent strict VIPER runs under the declared modern environment emit the declared prediction bytes, SHA-256, and hold PearsonDelta; equal score with changed arrays or file bytes fails. | [test_accepts_repeated_modern_prediction_identity](../../mantra/src/mantra/rebuild/tests/test_hopfield_replay.py) | [test_rejects_equal_score_with_changed_prediction_bytes](../../mantra/src/mantra/rebuild/tests/test_hopfield_replay.py) |
| <nobr><code>H1-VR-08</code></nobr> | <nobr><code>H1-REQ-08</code></nobr> | The terminal registration resolves every accepted Phase 1 receipt, artifact, source commit, and producer edge from retained records. | [test_resolves_complete_phase1_provenance](../tests/phase1/test_hopfield_registration.py) | [test_rejects_severed_phase1_provenance](../tests/phase1/test_hopfield_registration.py) |
| <nobr><code>H1-VR-09</code></nobr> | <nobr><code>H1-REQ-09</code></nobr> | The bridge run starts from the parity-proven legacy Hopfield source and configuration; resolves the exact retained 83-value core, 144-value family, and 40-value response artifact digests with their canonical row and split identities; changes only the encoder input width from 187 to 267; keeps the complete numeric training set GPU-resident; and reproduces its frozen bridge result from the retained checkpoint and inputs. | [test_freezes_legacy_hopfield_on_exact_mil_input_stack](../../mantra/src/mantra/rebuild/tests/test_hopfield_mil_input_bridge.py) | [test_rejects_mixed_input_stack_or_unrelated_model_change](../../mantra/src/mantra/rebuild/tests/test_hopfield_mil_input_bridge.py) |
| <nobr><code>H1-VR-10</code></nobr> | <nobr><code>H1-REQ-10</code></nobr> | One parameterized observer resolves all thirteen accepted inputs through their versioned source, Build owner and configuration, comparison receipt, mismatch classification, and repeatable accepted identity; missing source edges, missing comparisons, unexplained mismatches, and nonrepeatable replacements fail. | [test_reconstructs_every_hopfield_input_from_its_true_source](../../mantra/src/mantra/rebuild/tests/test_hopfield_source_reconstruction.py) | [test_rejects_incomplete_or_unexplained_input_reconstruction](../../mantra/src/mantra/rebuild/tests/test_hopfield_source_reconstruction.py) |
| <nobr><code>H1-VR-11</code></nobr> | <nobr><code>H1-REQ-11</code></nobr> | The frozen stage graph connects each accepted Build artifact to Embed by FutureInputRef, connects Embed to Predict and Predict to Evaluate, rejects direct retained model-input paths, and the resulting strict replay emits the accepted modern encoder, prediction, and score identities. | [test_replays_hopfield_from_rebuilt_outputs_only](../../mantra/src/mantra/rebuild/tests/test_hopfield_source_reconstruction.py) | [test_rejects_retained_input_in_rebuilt_replay](../../mantra/src/mantra/rebuild/tests/test_hopfield_source_reconstruction.py) |
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
