# MANTRA Response Reconstruction

This contract rebuilds the response targets shared by Hopfield and MIL. Separate
VIPER stages exclude immediate-early genes from control-program discovery,
regress immediate-early-gene and other declared nuisance scores from control
expression, construct the control programs, match perturbation cells to controls
by Sinkhorn optimal transport, learn sparse response programs, fit the SVD and
basis rotation, and reconstruct the response-block definition artifacts instead
of copying the historical files.

The reconstruction preserves the verified GPU cNMF, NMF, NNLS, and Sinkhorn
paths. Byte-parity cNMF runs use seeded scikit-learn KMeans; throughput runs may
use the faster Triton implementation and record that non-byte-identical backend.

The control branch consumes the frozen IEG-excluded control panel and its
covariate-residualized expression. The response branch consumes the ordered
GEARS 5,000-gene panel, including any immediate-early genes present, so the
target keeps their induced response. The final bundle binds both panels and
every intermediate to one cell set, perturbation order, split contract,
execution profile, and producer record.

<!-- contract-protocol:generated:start -->
**Planned.** [Jump to current PairBlock](#r5-pb-01)

**Checklist:** [MANTRA rebuild](../checklists/mantra-rebuild.md)

### PairBlocks

<a id="r5-pb-01"></a>

#### <nobr><code>R5-PB-01</code></nobr>

**Status:** waiting

**Requirement contribution:** Rebuild control programs from IEG-excluded genes and covariate-residualized expression through verified GPU cNMF and the declared KMeans execution profile.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>R5-PB-02</code></nobr>, <nobr><code>E0-PB-04</code></nobr>, <nobr><code>E0-PB-08</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="r5-pb-02"></a>

#### <nobr><code>R5-PB-02</code></nobr>

**Status:** waiting

**Requirement contribution:** Estimate and remove the immediate-early-gene contribution from canonical control cells.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>P4-PB-06</code></nobr>, <nobr><code>D3-PB-07</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="r5-pb-03"></a>

#### <nobr><code>R5-PB-03</code></nobr>

**Status:** waiting

**Requirement contribution:** Build and diagnose vectorized GPU Sinkhorn matched-control residual response vectors.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>R5-PB-02</code></nobr>, <nobr><code>E0-PB-06</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="r5-pb-04"></a>

#### <nobr><code>R5-PB-04</code></nobr>

**Status:** waiting

**Requirement contribution:** Learn sparse response programs on the complete GEARS response axis and verify their GPU NNLS coefficients and reconstruction.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>R5-PB-03</code></nobr>, <nobr><code>E0-PB-05</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="r5-pb-05"></a>

#### <nobr><code>R5-PB-05</code></nobr>

**Status:** waiting

**Requirement contribution:** Fit the SVD and basis rotation and persist reconstructible ordered response coordinates.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>R5-PB-04</code></nobr>, <nobr><code>E0-PB-11</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="r5-pb-06"></a>

#### <nobr><code>R5-PB-06</code></nobr>

**Status:** waiting

**Requirement contribution:** Freeze one response-target bundle consumed unchanged by the Hopfield and MIL rebuilds.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>R5-PB-01</code></nobr>, <nobr><code>R5-PB-07</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="r5-pb-07"></a>

#### <nobr><code>R5-PB-07</code></nobr>

**Status:** waiting

**Requirement contribution:** Reconstruct the response-program graph, hard and soft block maps, and rotation and prove parity with the retained Phase 0 definitions.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>R5-PB-05</code></nobr>

**Next action:** Wait for the declared dependencies.


### Requirements

| Requirement | Claim | Progress | Verifiers | PairBlocks |
|---|---|---|---|---|
| <nobr><code>R5-REQ-01</code></nobr> | Control programs must be rebuilt by cNMF from canonical control cells restricted to the frozen control panel, which excludes the core immediate-early-gene blacklist. cNMF must consume the expression residuals produced by R5-REQ-02 through the verified GPU NMF path and retain the selected rank, restarts, regularization, consensus backend, ordered genes, programs, coefficients, reconstruction diagnostics, and execution profile. | planned | <nobr><code>R5-VR-01</code></nobr> | <nobr><code>R5-PB-01</code></nobr> |
| <nobr><code>R5-REQ-02</code></nobr> | One declared operation must regress the immediate-early-gene score, S-phase score, G2M-phase score, log UMI count, and mitochondrial percentage from the canonical control-cell expression matrix before cNMF fits control programs. The operation must retain the covariates, fitted population, coefficients, residual expression, and leakage diagnostics. | planned | <nobr><code>R5-VR-02</code></nobr> | <nobr><code>R5-PB-02</code></nobr> |
| <nobr><code>R5-REQ-03</code></nobr> | One vectorized GPU Sinkhorn stage must match perturbation cells to controls from the same canonical cell set, produce barycentric controls and residual response vectors, and retain convergence, marginal-error, transport-mass, transport-cost, batch, device, precision, and donor-versus-rebuilt diagnostics. | planned | <nobr><code>R5-VR-03</code></nobr> | <nobr><code>R5-PB-03</code></nobr> |
| <nobr><code>R5-REQ-04</code></nobr> | Response programs must be learned from the rebuilt Sinkhorn residual surface on the frozen GEARS 5,000-gene response panel by one declared sparse-dictionary stage. The response stage must use the complete GEARS target axis, including any core immediate-early genes present, because the response target includes their perturbation-induced signal. Program coefficients must use the verified GPU NNLS path, and the stage must retain its objective, initialization, selected parameters, ordered gene axis, loadings, coefficients, and reconstruction diagnostics. | planned | <nobr><code>R5-VR-04</code></nobr> | <nobr><code>R5-PB-04</code></nobr> |
| <nobr><code>R5-REQ-05</code></nobr> | One declared response-coordinate stage must reproduce the selected single-cell recipe: fit the signed sparse SVD decoder on the declared fit plus tune Sinkhorn residual cells, ridge-encode every cell against that decoder, and rotate the 210 coefficients through the ordered fit plus tune covariance eigendecomposition. The stage must preserve the exact fitted cells, decoder, eigensystem ordering, rotation, coefficients, inverse reconstruction, numerical backend, execution state, and comparison with the historical coordinates. | planned | <nobr><code>R5-VR-05</code></nobr> | <nobr><code>R5-PB-05</code></nobr> |
| <nobr><code>R5-REQ-06</code></nobr> | One response-target bundle must bind the canonical cells, distinct control and response gene panels, control programs, transport residuals, response programs, rotated coordinates, response-block definitions, perturbation order, response-gene order, split membership, execution profiles, and source evidence for both model rebuilds. | planned | <nobr><code>R5-VR-06</code></nobr> | <nobr><code>R5-PB-06</code></nobr> |
| <nobr><code>R5-REQ-07</code></nobr> | One response-block definition stage must reconstruct the historical program-similarity graph, hard 16-block labels, soft semantic 16-block map, and 210-dimensional rotation from the rebuilt response programs and coefficients, preserving program order, dimensions, parameters, and parity with each retained Phase 0 definition artifact. | planned | <nobr><code>R5-VR-07</code></nobr> | <nobr><code>R5-PB-07</code></nobr> |

### Verification rules

| Rule | Requirements | Acceptance conditions | Success case | Rejection cases |
|---|---|---|---|---|
| <nobr><code>R5-VR-01</code></nobr> | <nobr><code>R5-REQ-01</code></nobr> | The cNMF stage consumes only canonical control cells, the frozen IEG-excluded control panel, and the residual expression produced by R5-REQ-02; exercises the verified GPU NMF path; reproduces from its retained plan; emits finite non-collapsed programs; and uses CPU KMeans whenever the run claims byte parity. | [test_rebuilds_gpu_cnmf_control_programs](../../mantra/src/mantra/rebuild/tests/test_control_programs.py) | [test_rejects_other_cells_deoptimized_nmf_or_wrong_kmeans_profile](../../mantra/src/mantra/rebuild/tests/test_control_programs.py) |
| <nobr><code>R5-VR-02</code></nobr> | <nobr><code>R5-REQ-02</code></nobr> | The residualization reads canonical control cells and exactly the declared immediate-early-gene, cell-cycle, library-size, and mitochondrial covariates; reproduces from retained coefficients; reduces their measured contributions; and rejects another fitted population, a missing covariate, or an unremoved contribution. | [test_removes_declared_ieg_contribution](../../mantra/src/mantra/rebuild/tests/test_control_programs.py) | [test_rejects_other_cells_or_unremoved_ieg_signal](../../mantra/src/mantra/rebuild/tests/test_control_programs.py) |
| <nobr><code>R5-VR-03</code></nobr> | <nobr><code>R5-REQ-03</code></nobr> | The GPU transport stage uses only canonical cells, matches its CPU reference within named tolerances, satisfies its numerical checks, and emits a donor-versus-rebuilt comparison on the same response surface. | [test_builds_gpu_sinkhorn_matched_control_residuals](../../mantra/src/mantra/rebuild/tests/test_transport_residuals.py) | [test_rejects_failed_transport_mixed_cells_or_cpu_gpu_drift](../../mantra/src/mantra/rebuild/tests/test_transport_residuals.py) |
| <nobr><code>R5-VR-04</code></nobr> | <nobr><code>R5-REQ-04</code></nobr> | The sparse dictionary reproduces from retained parameters, preserves the exact GEARS response-gene order and its declared IEG-retention policy, its GPU NNLS coefficients match the CPU reference within tolerance, and it reports sparsity, reconstruction, stability, support, and redundancy. | [test_builds_sparse_programs_with_gpu_nnls](../../mantra/src/mantra/rebuild/tests/test_response_programs.py) | [test_rejects_misaligned_unstable_or_drifting_response_programs](../../mantra/src/mantra/rebuild/tests/test_response_programs.py) |
| <nobr><code>R5-VR-05</code></nobr> | <nobr><code>R5-REQ-05</code></nobr> | The saved sparse SVD decoder, ridge coefficients, fit-plus-tune covariance eigensystem, 210-dimensional rotation, and rotated coefficients reconstruct the declared residual inputs within tolerance; preserve cell, perturbation, gene, and coordinate order; and remain bound to the recorded VIPER execution identity. | [test_builds_reconstructible_rotated_response_coordinates](../../mantra/src/mantra/rebuild/tests/test_response_coordinates.py) | [test_rejects_changed_fit_population_or_coordinate_order](../../mantra/src/mantra/rebuild/tests/test_response_coordinates.py) |
| <nobr><code>R5-VR-06</code></nobr> | <nobr><code>R5-REQ-06</code></nobr> | The bundle resolves every ordered axis, gene panel, intermediate, and response-block definition to one passing producer record, records each execution profile, and both model loaders consume the same bundle identity. | [test_freezes_shared_response_target_bundle](../../mantra/src/mantra/rebuild/tests/test_response_target_bundle.py) | [test_rejects_mixed_surface_profile_or_unresolved_target_input](../../mantra/src/mantra/rebuild/tests/test_response_target_bundle.py) |
| <nobr><code>R5-VR-07</code></nobr> | <nobr><code>R5-REQ-07</code></nobr> | The rebuilt similarity graph, block labels, semantic map, and rotation preserve the declared response-program order and match their Phase 0 arrays or labels exactly under the parity profile; copying the historical files without executing their producers does not pass. | [test_rebuilds_response_block_definitions_with_parity](../../mantra/src/mantra/rebuild/tests/test_response_block_definitions.py) | [test_rejects_ingested_or_misaligned_response_block_definitions](../../mantra/src/mantra/rebuild/tests/test_response_block_definitions.py) |
<!-- contract-protocol:generated:end -->
