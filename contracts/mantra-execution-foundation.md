# MANTRA Execution and Acceleration Foundation

This contract makes ephemeral GPU execution recoverable. VIPER must publish and
restore artifacts through durable GCS storage before training starts, and each
worker and its boot disk must be removed after accepted outputs restore.

It also freezes the accelerated MANTRA operations that the modular rebuild must
preserve. Numerical parity and L4 throughput gates cover GPU cNMF, NMF, NNLS,
Sinkhorn, ridge, low-rank PCA and SVD, Hopfield, MIL, and the deterministic CPU
KMeans exception used for byte-parity replay.

<!-- contract-protocol:generated:start -->
**In progress.** [Jump to current PairBlock](#e0-pb-04)

**Checklist:** [MANTRA rebuild](../checklists/mantra-rebuild.md)

### PairBlocks

<a id="e0-pb-01"></a>

#### <nobr><code>E0-PB-01</code></nobr>

**Status:** complete

**Requirement contribution:** Implement and verify durable GCS publication and restoration through VIPER's existing cloud-client boundary.

**Review handoff**

**What changed**

- VIPER now publishes immutable content revisions to Google Cloud Storage through its existing cloud-client protocol.
- Cloud object keys preserve each exact workspace-relative path beneath the owner, workspace, and content revision.
- A revision becomes readable only after its manifest is sealed; every restored file is checked against its recorded byte count and SHA-256 digest.
- The launch probe publishes and restores one object through the production client and writes a durable receipt before an ephemeral GPU worker may start.

**Plan deviations:** The live probe first exposed an Application Default Credentials quota-project mismatch. Rebinding ADC from the closed MEDIT billing context to MANTRA resolved it; no cloud object was written before that repair. The CodeQL-selected fast gate also exposed two frozen public API and package inventories. Final self-review corrected the verifier's revision terminology; runtime scope and candidate bytes did not change.

**Start review:** [Open tested GitHub comparison](https://github.com/pvd232/viper/compare/5b5f97feed28a857df70202b8a3d6023d742c31f...718aaa2a1406d1afa214efccf33407eaf64cf902)

**Review these files**

- [Complete E0-PB-01 diff](../plans/mantra-execution-foundation/E0-PB-01/patches/gcs-storage.patch#L1)
- [Production GCS client](../plans/mantra-execution-foundation/E0-PB-01/patches/gcs-storage.patch#L200)
- [Publish and restore launch probe](../plans/mantra-execution-foundation/E0-PB-01/patches/gcs-storage.patch#L448)
- [Workspace and cloud path contract](../../viper/docs/reference/protocol.md#L56)
- [Immutable publication acceptance cases](../plans/mantra-execution-foundation/E0-PB-01/patches/gcs-storage.patch#L751)

**Evidence:** [Passing gate receipt](../evidence/mantra-rebuild/E0-PB-01/gate-review-02.json)

**Decision:** <nobr><code>E0-PB-01</code></nobr> is complete; no further decision is required.

<details>
<summary>Implementation details</summary>

**Plan:** [plan.toml](../plans/mantra-execution-foundation/E0-PB-01/plan.toml)

**Retained patch:** [patches/gcs-storage.patch](../plans/mantra-execution-foundation/E0-PB-01/patches/gcs-storage.patch)

**Implementation roots:** [src/viper/gcs.py](../../viper/src/viper/gcs.py) · [src/viper/storage.py](../../viper/src/viper/storage.py)

**Test roots:** [tests/test_gcs_storage.py](../../viper/tests/test_gcs_storage.py) · [tests/test_storage.py](../../viper/tests/test_storage.py)

**Dependencies:** <nobr><code>E0-PB-02</code></nobr>

**Gate steps:**

```bash
# typecheck
(cd . && pyright src/viper/gcs.py src/viper/storage.py tests/test_gcs_storage.py tests/test_public_api.py tests/test_release_tools.py tests/conftest.py)
# test
(cd . && python3 -m pytest -q -p no:cacheprovider tests -m '(domain_storage) and (unit or contract)')
# test
(cd . && python3 -m pytest -q -p no:cacheprovider tests/test_public_api.py tests/test_release_tools.py tests/test_documentation.py tests/test_workflow_documentation.py)
# documentation
(cd . && python3 /Users/machina/.agents/skills/code-documentation/scripts/check-schema-descriptions.py src/viper/gcs.py tests/test_gcs_storage.py)
# lint
(cd . && ruff format --check src/viper/gcs.py src/viper/storage.py tests/test_gcs_storage.py tests/test_public_api.py tests/test_release_tools.py tests/conftest.py)
# lint
(cd . && ruff check src/viper/gcs.py src/viper/storage.py tests/test_gcs_storage.py tests/test_public_api.py tests/test_release_tools.py tests/conftest.py)
```

</details>

<a id="e0-pb-02"></a>

#### <nobr><code>E0-PB-02</code></nobr>

**Status:** complete

**Requirement contribution:** Harden lower-demand-region launch, partial-failure cleanup, and deterministic worker-plus-disk teardown before any GPU is created.

**Review handoff**

**What changed**

- The Spot launcher searches lower-demand regions in order and continues after either capacity or quota rejection.
- Every launch requires a successful cloud publish-and-restore probe, forces boot-disk deletion, and records the exact resources it created.
- The same launcher provides a teardown action that runs only after an artifact restore probe and verifies that the worker and boot disk are gone.
- Failed launches clean their worker, disk, and newly created network resources while preserving network resources that existed before the attempt.

**Plan deviations:** Self-review separated live worker execution identity into E0-PB-12 because CUDA, driver, RNG, and runtime facts can only be measured after boot. Everything else went according to plan.

**Start review:** [Open tested GitHub comparison](https://github.com/pvd232/RICO/compare/b59e6f712af462dc50b532d17e62d7df4c7c6643...13a46dcae18bcf3f9cf1d4bf7af85d2e47c185b4)

**Review these files**

- [Complete E0-PB-02 diff](../plans/mantra-execution-foundation/E0-PB-02/patches/gpu-lifecycle.patch#L1)
- [Launch and teardown entrypoint](../mantra-deploy-spot.sh#L39)
- [Regional fallback and cleanup acceptance cases](../tests/infrastructure/test_mantra_gpu_lifecycle.py#L190)

**Evidence:** [Passing gate receipt](../evidence/mantra-rebuild/E0-PB-02/gate-review-04.json)

**Decision:** <nobr><code>E0-PB-02</code></nobr> is complete; no further decision is required.

<details>
<summary>Implementation details</summary>

**Plan:** [plan.toml](../plans/mantra-execution-foundation/E0-PB-02/plan.toml)

**Retained patch:** [patches/gpu-lifecycle.patch](../plans/mantra-execution-foundation/E0-PB-02/patches/gpu-lifecycle.patch)

**Implementation roots:** [mantra-deploy-spot.sh](../mantra-deploy-spot.sh)

**Test roots:** [tests/infrastructure](../tests/infrastructure)

**Dependencies:** None

**Gate steps:**

```bash
# typecheck
(cd . && pyright tests/infrastructure/test_mantra_gpu_lifecycle.py)
# test
(cd . && python3 -m pytest -q -p no:cacheprovider tests/infrastructure/test_mantra_gpu_lifecycle.py)
# documentation
(cd . && python3 /Users/machina/.agents/skills/code-documentation/scripts/check-schema-descriptions.py tests/infrastructure/test_mantra_gpu_lifecycle.py)
# lint
(cd . && ruff format --check tests/infrastructure/test_mantra_gpu_lifecycle.py)
# lint
(cd . && ruff check tests/infrastructure/test_mantra_gpu_lifecycle.py)
```

</details>

<a id="e0-pb-03"></a>

#### <nobr><code>E0-PB-03</code></nobr>

**Status:** complete

**Requirement contribution:** Freeze the complete optimization inventory and its owners, consumers, and gates.

**Review handoff**

**What changed**

- A versioned inventory now names every accelerated operation that the MANTRA rebuild must preserve.
- Each operation maps its historical implementation to one planned modular owner, CPU reference, governing requirement, implementation PairBlock, verifier, device policy, determinism policy, and downstream consumers.
- The checker rejects omitted operations or fields, missing historical files, undeclared contract IDs, undeclared consumers, and modular owners outside the MANTRA rebuild namespace.

**Plan deviations:** The existing Markdown inventory supplied the operation list but bundled several required mappings into prose. The implementation retained it as the readable overview and added one machine-readable sidecar plus one validator. Self-review replaced a dictionary-key assertion with mutations observed by the production validator.

**Start review:** [Open tested GitHub comparison](https://github.com/pvd232/RICO/compare/22084295769d3f3d71f9f9e4eca2be7554419aae...00ceadedcea1994329a17600064c9988eb98809b)

**Review these files**

- [Complete E0-PB-03 diff](../plans/mantra-execution-foundation/E0-PB-03/patches/optimization-inventory.patch#L1)
- [Versioned optimization inventory](../plans/mantra-execution-foundation/E0-PB-03/patches/optimization-inventory.patch#L7)
- [Inventory validation boundary](../plans/mantra-execution-foundation/E0-PB-03/patches/optimization-inventory.patch#L238)
- [Missing-field rejection cases](../plans/mantra-execution-foundation/E0-PB-03/patches/optimization-inventory.patch#L159)

**Evidence:** [Passing gate receipt](../evidence/mantra-rebuild/E0-PB-03/gate-review-01.json)

**Decision:** <nobr><code>E0-PB-03</code></nobr> is complete; no further decision is required.

<details>
<summary>Implementation details</summary>

**Plan:** [plan.toml](../plans/mantra-execution-foundation/E0-PB-03/plan.toml)

**Retained patch:** [patches/optimization-inventory.patch](../plans/mantra-execution-foundation/E0-PB-03/patches/optimization-inventory.patch)

**Implementation roots:** [tools/validate_mantra_optimization_inventory.py](../tools/validate_mantra_optimization_inventory.py) · [docs/briefings/mantra-optimization-inventory.toml](../docs/briefings/mantra-optimization-inventory.toml)

**Test roots:** [tests/roadmap/test_mantra_optimization_inventory.py](../tests/roadmap/test_mantra_optimization_inventory.py)

**Dependencies:** <nobr><code>E0-PB-02</code></nobr>

**Gate steps:**

```bash
# typecheck
(cd . && pyright tools/validate_mantra_optimization_inventory.py tests/roadmap/test_mantra_optimization_inventory.py)
# test
(cd . && python3 -m pytest -q -p no:cacheprovider tests/roadmap/test_mantra_optimization_inventory.py)
# documentation
(cd . && python3 /Users/machina/.agents/skills/code-documentation/scripts/check-schema-descriptions.py tools/validate_mantra_optimization_inventory.py tests/roadmap/test_mantra_optimization_inventory.py)
# lint
(cd . && ruff format --check tools/validate_mantra_optimization_inventory.py tests/roadmap/test_mantra_optimization_inventory.py)
# lint
(cd . && ruff check tools/validate_mantra_optimization_inventory.py tests/roadmap/test_mantra_optimization_inventory.py)
```

</details>

<a id="e0-pb-04"></a>

#### <nobr><code>E0-PB-04</code></nobr>

**Status:** drafting

**Requirement contribution:** Port and benchmark batched GPU cNMF and NMF behind their modular owner.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>E0-PB-03</code></nobr>

**Next action:** Run the current PairBlock plan.

<a id="e0-pb-05"></a>

#### <nobr><code>E0-PB-05</code></nobr>

**Status:** drafting

**Requirement contribution:** Port and benchmark the dense and sparse GPU NNLS paths behind their modular owners.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>E0-PB-03</code></nobr>

**Next action:** Run the current PairBlock plan.

<a id="e0-pb-06"></a>

#### <nobr><code>E0-PB-06</code></nobr>

**Status:** drafting

**Requirement contribution:** Port and benchmark vectorized GPU Sinkhorn transport and barycentric residuals.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>E0-PB-03</code></nobr>

**Next action:** Run the current PairBlock plan.

<a id="e0-pb-07"></a>

#### <nobr><code>E0-PB-07</code></nobr>

**Status:** drafting

**Requirement contribution:** Port and verify the shared GPU ridge solver across every declared consumer.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>E0-PB-03</code></nobr>

**Next action:** Run the current PairBlock plan.

<a id="e0-pb-08"></a>

#### <nobr><code>E0-PB-08</code></nobr>

**Status:** waiting

**Requirement contribution:** Enforce separate parity and throughput profiles, including the deterministic CPU KMeans parity path.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>E0-PB-04</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="e0-pb-09"></a>

#### <nobr><code>E0-PB-09</code></nobr>

**Status:** drafting

**Requirement contribution:** Inventory, port, and benchmark every selected Hopfield GPU and vectorized operation.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>E0-PB-03</code></nobr>

**Next action:** Run the current PairBlock plan.

<a id="e0-pb-10"></a>

#### <nobr><code>E0-PB-10</code></nobr>

**Status:** drafting

**Requirement contribution:** Inventory, port, and benchmark every selected MIL GPU and vectorized operation.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>E0-PB-03</code></nobr>

**Next action:** Run the current PairBlock plan.

<a id="e0-pb-11"></a>

#### <nobr><code>E0-PB-11</code></nobr>

**Status:** drafting

**Requirement contribution:** Port and benchmark deterministic GPU low-rank PCA and SVD behind their modular owners.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>E0-PB-03</code></nobr>

**Next action:** Run the current PairBlock plan.

<a id="e0-pb-12"></a>

#### <nobr><code>E0-PB-12</code></nobr>

**Status:** drafting

**Requirement contribution:** Record and verify the live worker's complete execution identity through VIPER before replay training begins.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>E0-PB-01</code></nobr>, <nobr><code>E0-PB-02</code></nobr>

**Next action:** Run the current PairBlock plan.


### Requirements

| Requirement | Claim | Progress | Verifiers | PairBlocks |
|---|---|---|---|---|
| <nobr><code>E0-REQ-01</code></nobr> | Before an ephemeral GPU run starts, VIPER must publish and restore one probe artifact through a production GCS-backed ViperCloudClient, verify its digest after restoration, and retain the durable reference in the run record. Each GCS object key must prefix the owner, workspace, and content-derived revision while preserving the exact repository-relative path produced by VIPER's canonical initialized workspace layout. | complete | <nobr><code>E0-VR-01</code></nobr> | <nobr><code>E0-PB-01</code></nobr> |
| <nobr><code>E0-REQ-02</code></nobr> | The governed GPU launcher must search declared lower-demand regions before us-central1, continue after regional capacity or quota rejection, force boot-disk auto-delete after machine-image overrides, and clean up every worker, boot disk, NAT, and router created by a failed launch. A live launch must require a verified durable-storage probe, record every resource it created, select Spot deletion on preemption, and provide one deterministic teardown action that deletes the worker and boot disk after accepted records and artifacts restore while preserving reused network resources. | complete | <nobr><code>E0-VR-02</code></nobr> | <nobr><code>E0-PB-02</code></nobr> |
| <nobr><code>E0-REQ-03</code></nobr> | One versioned optimization inventory must map every accelerated MANTRA operation to its historical owner, modular owner, CPU reference, numerical parity gate, throughput gate, device and precision policy, determinism policy, and consuming reconstruction stage. | complete | <nobr><code>E0-VR-03</code></nobr> | <nobr><code>E0-PB-03</code></nobr> |
| <nobr><code>E0-REQ-04</code></nobr> | The modular response pipeline must preserve batched GPU cNMF and NMF execution, including parallel restarts, mini-batching, sparse-input handling, lazy split-sign expansion, stable float32 factors, and preloaded dense device tensors. | in_progress | <nobr><code>E0-VR-04</code></nobr> | <nobr><code>E0-PB-04</code></nobr> |
| <nobr><code>E0-REQ-05</code></nobr> | The modular response pipeline must preserve the GPU NNLS implementations used to score and project response programs, including batched dense and sparse Ghost paths, and must compare their coefficients and reconstructions with the declared CPU reference within a named tolerance. | in_progress | <nobr><code>E0-VR-05</code></nobr> | <nobr><code>E0-PB-05</code></nobr> |
| <nobr><code>E0-REQ-06</code></nobr> | The modular response pipeline must preserve vectorized GPU Sinkhorn transport and barycentric matched-control residuals and must retain convergence, marginal error, transport mass, device, precision, batch shape, and CPU-reference diagnostics. | in_progress | <nobr><code>E0-VR-06</code></nobr> | <nobr><code>E0-PB-06</code></nobr> |
| <nobr><code>E0-REQ-07</code></nobr> | The modular feature and model pipelines must preserve GPU ridge solvers for grouped-prior, control-state, coefficient, and correction regressions, with the selected primal or dual form, penalty, device, dtype, and CPU-reference prediction error retained. | in_progress | <nobr><code>E0-VR-07</code></nobr> | <nobr><code>E0-PB-07</code></nobr> |
| <nobr><code>E0-REQ-08</code></nobr> | Each execution must declare a parity or throughput profile. Every replay, bridge run, or one-at-a-time substitution that preserves a frozen result must use seeded scikit-learn Lloyd KMeans on CPU wherever clustering occurs. A later throughput run may use Triton KMeans on GPU but must record that backend and may not claim parity with the deterministic KMeans result. | planned | <nobr><code>E0-VR-08</code></nobr> | <nobr><code>E0-PB-08</code></nobr> |
| <nobr><code>E0-REQ-09</code></nobr> | The modular Hopfield pipeline must copy every numeric training tensor to the GPU once before training, keep the complete fit and tune tensors resident through full-dataset training and inference, and limit later host-device transfers to checkpoint, log, and final-artifact persistence. It must also preserve vectorized matrix operations and top-k retrieval, deterministic CUDA settings, explicit precision, historical normalization and checkpoint selection, and retain transfer counts and bytes, runtime, and peak GPU memory through VIPER. | in_progress | <nobr><code>E0-VR-09</code></nobr> | <nobr><code>E0-PB-09</code></nobr> |
| <nobr><code>E0-REQ-10</code></nobr> | The modular MIL pipeline must copy every numeric training tensor to the GPU once before teacher or student training, keep the complete tensors resident through training and inference, and form the historical 128-row optimizer batches only through device-side indices. Every training step must read numeric rows from those resident tensors. The pipeline must also preserve fused CUDA optimizers, vectorized top-k and einsum routing, deterministic CUDA settings, explicit precision, historical checkpoint selection, and retain transfer counts and bytes, runtime, and peak GPU memory through VIPER. | in_progress | <nobr><code>E0-VR-10</code></nobr> | <nobr><code>E0-PB-10</code></nobr> |
| <nobr><code>E0-REQ-11</code></nobr> | The modular prior and response pipelines must preserve deterministic GPU low-rank PCA and SVD where the historical pipeline used them, including fitted rows, centering, rank, seed, sign convention, device, precision, components, singular values, projections, and reconstruction diagnostics. | in_progress | <nobr><code>E0-VR-11</code></nobr> | <nobr><code>E0-PB-11</code></nobr> |
| <nobr><code>E0-REQ-12</code></nobr> | After a GPU worker boots and before training starts, one VIPER launch probe must record the source commit, resolved plan and configuration, command, input digests, declared seeds, Python and accelerator RNG states, determinism environment variables, image, locked Python environment, operating system, CUDA and driver versions, GPU model and count, device and dtype policy, writable canonical VIPER workspace, and durable artifact destination. Resume must reject every unreviewed difference in that execution identity. | in_progress | <nobr><code>E0-VR-12</code></nobr> | <nobr><code>E0-PB-12</code></nobr> |

### Verification rules

| Rule | Requirements | Acceptance conditions | Success case | Rejection cases |
|---|---|---|---|---|
| <nobr><code>E0-VR-01</code></nobr> | <nobr><code>E0-REQ-01</code></nobr> | A production VIPER client publishes a probe to GCS under owner, workspace, and content-revision prefixes while preserving VIPER's exact repository-relative artifact path; a fresh process restores the same bytes through the retained viper:// reference, and digest, path, or object substitution fails. | [test_publishes_and_restores_durable_snapshot](../../viper/tests/test_gcs_storage.py) | [test_rejects_changed_or_missing_cloud_object](../../viper/tests/test_gcs_storage.py) |
| <nobr><code>E0-VR-02</code></nobr> | <nobr><code>E0-REQ-02</code></nobr> | The launcher searches lower-demand regions first, skips capacity and quota failures, forces and verifies boot-disk auto-delete, selects deletion on Spot preemption, cleans every resource created by a failed attempt, and blocks a live worker without a verified storage probe. Final teardown finds no worker or boot disk after accepted artifacts restore and preserves any router or NAT reused from an earlier launch. | [test_probes_launch_and_deletes_worker_and_disk](../tests/infrastructure/test_mantra_gpu_lifecycle.py) | [test_blocks_training_or_teardown_on_failed_probe](../tests/infrastructure/test_mantra_gpu_lifecycle.py) |
| <nobr><code>E0-VR-03</code></nobr> | <nobr><code>E0-REQ-03</code></nobr> | Every required optimization has one resolvable historical owner, modular owner, reference comparison, performance threshold, execution policy, and downstream consumer, and an omitted operation fails. | [test_inventory_covers_every_accelerated_operation](../tests/roadmap/test_mantra_optimization_inventory.py) | [test_rejects_missing_owner_gate_or_consumer](../tests/roadmap/test_mantra_optimization_inventory.py) |
| <nobr><code>E0-VR-04</code></nobr> | <nobr><code>E0-REQ-04</code></nobr> | The modular GPU cNMF path matches the CPU reference within tolerance for fixed initialization, exercises every declared optimization, and exceeds the retained minimum throughput on an L4. | [test_preserves_batched_gpu_cnmf](../../mantra-rebuild/tests/test_gpu_response_kernels.py) | [test_rejects_unverified_or_deoptimized_cnmf](../../mantra-rebuild/tests/test_gpu_response_kernels.py) |
| <nobr><code>E0-VR-05</code></nobr> | <nobr><code>E0-REQ-05</code></nobr> | Dense and sparse GPU NNLS paths satisfy coefficient and reconstruction tolerances against their CPU references and the selected path and iteration count are retained. | [test_preserves_gpu_nnls_paths](../../mantra-rebuild/tests/test_gpu_response_kernels.py) | [test_rejects_nnls_drift_or_unrecorded_backend](../../mantra-rebuild/tests/test_gpu_response_kernels.py) |
| <nobr><code>E0-VR-06</code></nobr> | <nobr><code>E0-REQ-06</code></nobr> | The GPU Sinkhorn result matches the CPU reference within declared transport and residual tolerances and fails on non-finite output, bad marginals, or missing execution diagnostics. | [test_preserves_vectorized_gpu_sinkhorn](../../mantra-rebuild/tests/test_gpu_response_kernels.py) | [test_rejects_sinkhorn_drift_or_missing_diagnostics](../../mantra-rebuild/tests/test_gpu_response_kernels.py) |
| <nobr><code>E0-VR-07</code></nobr> | <nobr><code>E0-REQ-07</code></nobr> | Every declared GPU ridge use matches the CPU reference within tolerance and records the form, penalty, device, dtype, and prediction error. | [test_preserves_all_gpu_ridge_consumers](../../mantra-rebuild/tests/test_gpu_ridge_contract.py) | [test_rejects_unmapped_or_drifting_ridge_use](../../mantra-rebuild/tests/test_gpu_ridge_contract.py) |
| <nobr><code>E0-VR-08</code></nobr> | <nobr><code>E0-REQ-08</code></nobr> | Replay, bridge, and substitution plans select seeded CPU scikit-learn Lloyd KMeans wherever clustering occurs; throughput plans record GPU Triton KMeans, and the verifier rejects a frozen-result parity claim from that path. | [test_selects_kmeans_backend_by_execution_profile](../../mantra-rebuild/tests/test_execution_profiles.py) | [test_rejects_gpu_kmeans_byte_parity_claim](../../mantra-rebuild/tests/test_execution_profiles.py) |
| <nobr><code>E0-VR-09</code></nobr> | <nobr><code>E0-REQ-09</code></nobr> | The modular Hopfield benchmark records one initialization transfer for each numeric training tensor, full-dataset device-resident optimization, only declared persistence transfers afterward, transfer counts and bytes, runtime, and peak GPU memory; it also matches the historical numerical result under the parity profile and meets the retained L4 thresholds. | [test_preserves_hopfield_gpu_execution](../../mantra-rebuild/tests/test_gpu_model_kernels.py) | [test_rejects_hopfield_drift_or_deoptimization](../../mantra-rebuild/tests/test_gpu_model_kernels.py) |
| <nobr><code>E0-VR-10</code></nobr> | <nobr><code>E0-REQ-10</code></nobr> | The modular MIL benchmark records one initialization transfer for each numeric training tensor, 128-row batches selected only through GPU indices, only declared persistence transfers afterward, transfer counts and bytes, runtime, and peak GPU memory; it also matches the historical numerical result under the parity profile and meets the retained L4 thresholds. | [test_preserves_mil_gpu_execution](../../mantra-rebuild/tests/test_gpu_model_kernels.py) | [test_rejects_mil_drift_or_deoptimization](../../mantra-rebuild/tests/test_gpu_model_kernels.py) |
| <nobr><code>E0-VR-11</code></nobr> | <nobr><code>E0-REQ-11</code></nobr> | Each ported GPU PCA or SVD reproduces its declared components and projections within tolerance, applies the retained sign convention, records its execution policy, and meets the L4 benchmark threshold. | [test_preserves_deterministic_gpu_pca_and_svd](../../mantra-rebuild/tests/test_gpu_reduction_kernels.py) | [test_rejects_changed_fit_rows_signs_or_deoptimized_reduction](../../mantra-rebuild/tests/test_gpu_reduction_kernels.py) |
| <nobr><code>E0-VR-12</code></nobr> | <nobr><code>E0-REQ-12</code></nobr> | The live worker probe records every declared execution-identity field through VIPER before training, confirms the canonical workspace and durable destination are writable, and rejects a resume after any unreviewed source, plan, configuration, command, input, seed, RNG state, environment, runtime, accelerator, device, dtype, workspace, or destination change. | [test_records_complete_live_worker_identity](../../mantra-rebuild/tests/test_gpu_launch_probe.py) | [test_rejects_changed_or_incomplete_worker_identity](../../mantra-rebuild/tests/test_gpu_launch_probe.py) |
<!-- contract-protocol:generated:end -->
