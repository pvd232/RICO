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
**In progress.** [Jump to current PairBlock](#r5-pb-01)

**Checklist:** [MANTRA rebuild](../checklists/mantra-rebuild.md)

### PairBlocks

<a id="r5-pb-01"></a>

#### <nobr><code>R5-PB-01</code></nobr>

**Status:** waiting

**Requirement contribution:** Rebuild control programs from IEG-excluded genes and covariate-residualized expression through verified GPU cNMF and the declared KMeans execution profile.

**Review handoff**

**What changed**

- Extend the accepted control-residual namespace with the reviewed GPU-resident multi-restart NMF fit and deterministic CPU KMeans consensus.
- Require exactly 19 stable control programs and retain the program bank, restart candidates, assignments, coverage, ordered axes, source-authority recipe, and execution diagnostics.
- Extend the download-rooted VIPER graph so the program-bank Build consumes only the accepted residual and panel artifacts, with focused parity, determinism, and worker-safety tests.
- Provide a bank-only execution graph that consumes the accepted residual receipt without rerunning residualization.

**Plan deviations:** No deviations from the declared requirement.

**Start work:** [Open current plan](../plans/mantra-response-reconstruction/R5-PB-01/plan.toml)

**Review these files**

- [GPU cNMF domain implementation](../plans/mantra-response-reconstruction/R5-PB-01/replace/src/rico/cell_types/k562/control_programs.py#L1)
- [Download-rooted residual and program-bank graph](../plans/mantra-response-reconstruction/R5-PB-01/replace/src/rico/plans/k562/control_programs.py#L1)
- [Program-bank acceptance and rejection tests](../plans/mantra-response-reconstruction/R5-PB-01/replace/tests/test_control_programs.py#L175)

**Evidence:** No passing gate receipt.

**Decision:** Wait for the declared dependencies.

<details>
<summary>Implementation details</summary>

**Plan:** [plan.toml](../plans/mantra-response-reconstruction/R5-PB-01/plan.toml)

**Candidate files:** [patches/control-program-bank.patch](../plans/mantra-response-reconstruction/R5-PB-01/patches/control-program-bank.patch) · [src/rico/cell_types/k562/control_programs.py](../plans/mantra-response-reconstruction/R5-PB-01/replace/src/rico/cell_types/k562/control_programs.py) · [src/rico/stages/k562/control_programs.py](../plans/mantra-response-reconstruction/R5-PB-01/replace/src/rico/stages/k562/control_programs.py) · [src/rico/plans/k562/control_programs.py](../plans/mantra-response-reconstruction/R5-PB-01/replace/src/rico/plans/k562/control_programs.py) · [tests/test_control_programs.py](../plans/mantra-response-reconstruction/R5-PB-01/replace/tests/test_control_programs.py)

**Implementation roots:** [src/rico](../../mantra-rebuild/src/rico) · [pyproject.toml](../../mantra-rebuild/pyproject.toml)

**Test roots:** [tests/test_control_programs.py](../../mantra-rebuild/tests/test_control_programs.py)

**Dependencies:** <nobr><code>R5-PB-02</code></nobr>, <nobr><code>E0-PB-04</code></nobr>, <nobr><code>E0-PB-08</code></nobr>

**Gate steps:**

```bash
# typecheck
(cd . && pyright --pythonpath /Users/machina/Developer/ChatGPT/mantra-rebuild/.venv/bin/python src/rico/cell_types/k562/control_programs.py src/rico/stages/k562/control_programs.py src/rico/plans/k562/control_programs.py tests/test_control_programs.py)
# test
(cd . && python3 -m pytest -q tests/test_control_programs.py)
# documentation
(cd . && python3 /Users/machina/.agents/skills/code-documentation/scripts/check-schema-descriptions.py src/rico/cell_types/k562/control_programs.py src/rico/stages/k562/control_programs.py src/rico/plans/k562/control_programs.py tests/test_control_programs.py)
# lint
(cd . && ruff format --check src/rico/cell_types/k562/control_programs.py src/rico/stages/k562/control_programs.py src/rico/plans/k562/control_programs.py tests/test_control_programs.py)
# lint
(cd . && ruff check src/rico/cell_types/k562/control_programs.py src/rico/stages/k562/control_programs.py src/rico/plans/k562/control_programs.py tests/test_control_programs.py)
```

</details>

<a id="r5-pb-02"></a>

#### <nobr><code>R5-PB-02</code></nobr>

**Status:** complete

**Requirement contribution:** Regress exactly mitopercent and IEG_score with an intercept from canonical control cells, apply the retained nonnegative residual offsets, and bind the residual matrix to its fitted cell and gene axes.

**Review handoff**

**What changed**

- Add the typed K562 control-residual producer that regresses exactly mitopercent and IEG_score with an intercept, then applies and records one nonnegative offset per gene.
- Bind residual values, coefficients, offsets, and their immutable metadata to the canonical control-cell and ordered control-gene axes.
- Expose the residual producer as a download-rooted VIPER Build with focused deterministic and axis-rejection tests.

**Plan deviations:** The reviewed worktree also contains the dependent cNMF bank in these namespaces. This plan intentionally stops at residual production; R5-PB-01 activates and verifies the 19-program bank in the next plan.

**Start review:** [Open tested GitHub comparison](https://github.com/pvd232/rico-rebuild/compare/54e1f3aaf74abd45abdb5a5bff7b9ae8a611a336...0649557b6724b3d9ffcc2ef9e8a215a1ed7b72b6)

**Review these files**

- [Control-residual domain implementation](../plans/mantra-response-reconstruction/R5-PB-02/add/src/rico/cell_types/k562/control_programs.py#L1)
- [Download-rooted residual plan](../plans/mantra-response-reconstruction/R5-PB-02/add/src/rico/plans/k562/control_programs.py#L1)
- [Residual acceptance and rejection tests](../plans/mantra-response-reconstruction/R5-PB-02/add/tests/test_control_programs.py#L1)

**Evidence:** [Passing gate receipt](../evidence/mantra-response-reconstruction/R5-PB-02/gate-review-01.json)

**Decision:** <nobr><code>R5-PB-02</code></nobr> is complete; no further decision is required.

<details>
<summary>Implementation details</summary>

**Plan:** [plan.toml](../plans/mantra-response-reconstruction/R5-PB-02/plan.toml)

**Candidate files:** [patches/control-residuals-config.patch](../plans/mantra-response-reconstruction/R5-PB-02/patches/control-residuals-config.patch) · [src/rico/cell_types/k562/control_programs.py](../plans/mantra-response-reconstruction/R5-PB-02/add/src/rico/cell_types/k562/control_programs.py) · [src/rico/stages/k562/control_programs.py](../plans/mantra-response-reconstruction/R5-PB-02/add/src/rico/stages/k562/control_programs.py) · [src/rico/plans/k562/control_programs.py](../plans/mantra-response-reconstruction/R5-PB-02/add/src/rico/plans/k562/control_programs.py) · [tests/test_control_programs.py](../plans/mantra-response-reconstruction/R5-PB-02/add/tests/test_control_programs.py)

**Implementation roots:** [src/rico](../../mantra-rebuild/src/rico) · [pyproject.toml](../../mantra-rebuild/pyproject.toml)

**Test roots:** [tests/test_control_programs.py](../../mantra-rebuild/tests/test_control_programs.py)

**Dependencies:** None

**Gate steps:**

```bash
# typecheck
(cd . && pyright --pythonpath /Users/machina/Developer/ChatGPT/mantra-rebuild/.venv/bin/python src/rico/cell_types/k562/control_programs.py src/rico/stages/k562/control_programs.py src/rico/plans/k562/control_programs.py tests/test_control_programs.py)
# test
(cd . && python3 -m pytest -q tests/test_control_programs.py)
# documentation
(cd . && python3 /Users/machina/.agents/skills/code-documentation/scripts/check-schema-descriptions.py src/rico/cell_types/k562/control_programs.py src/rico/stages/k562/control_programs.py src/rico/plans/k562/control_programs.py tests/test_control_programs.py)
# lint
(cd . && ruff format --check src/rico/cell_types/k562/control_programs.py src/rico/stages/k562/control_programs.py src/rico/plans/k562/control_programs.py tests/test_control_programs.py)
# lint
(cd . && ruff check src/rico/cell_types/k562/control_programs.py src/rico/stages/k562/control_programs.py src/rico/plans/k562/control_programs.py tests/test_control_programs.py)
```

</details>

<a id="r5-pb-03"></a>

#### <nobr><code>R5-PB-03</code></nobr>

**Status:** waiting

**Requirement contribution:** Build cellwise nonnegative ctrl19 control-state coordinates, then use them to build and diagnose vectorized GPU Sinkhorn matched treated means, control means, and fit/tune residual response vectors without loading hold responses.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>R5-PB-01</code></nobr>, <nobr><code>E0-PB-06</code></nobr>

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

**Requirement contribution:** Freeze one response-target bundle that keeps global-control scoring truth, ctrl19-matched training targets, coefficient targets, and gene shift distinct and is consumed unchanged by the Hopfield and MIL rebuilds.

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
| <nobr><code>R5-REQ-02</code></nobr> | One declared operation must validate the canonical log1p-CP10K slim-atlas metadata and ordered cell and gene axes, then regress exactly mitopercent and the derived IEG_score, with an intercept, from its control-cell expression matrix before cNMF fits control programs. It must shift each residual gene by its fitted nonnegative offset and retain the ordered two-covariate contract, fitted control-cell and gene axes, regression coefficients, per-gene offsets, residual expression, and array digests. Cell-cycle scores, log UMI count, and other removed atlas fields must not enter this operation. | complete | <nobr><code>R5-VR-02</code></nobr> | <nobr><code>R5-PB-02</code></nobr> |
| <nobr><code>R5-REQ-03</code></nobr> | One cellwise control-state stage must project canonical fit, tune, and control cells onto the ordered 19 control programs by nonnegative least squares, preserving the cell, gene, and program axes and the solver diagnostics. One vectorized GPU Sinkhorn stage must use those ctrl19 coordinates to match fit and tune perturbation cells to canonical controls, then persist the ordered treated means, barycentric matched-control means, and matched-control residual response vectors. The stages must retain convergence, marginal-error, transport-mass, transport-cost, batch, device, precision, and donor-versus-rebuilt diagnostics; neither stage may consume hold response rows. | planned | <nobr><code>R5-VR-03</code></nobr> | <nobr><code>R5-PB-03</code></nobr> |
| <nobr><code>R5-REQ-04</code></nobr> | Response programs must be learned from the rebuilt Sinkhorn residual surface on the frozen GEARS 5,000-gene response panel by one declared sparse-dictionary stage. The response stage must use the complete GEARS target axis, including any core immediate-early genes present, because the response target includes their perturbation-induced signal. Program coefficients must use the verified GPU NNLS path, and the stage must retain its objective, initialization, selected parameters, ordered gene axis, loadings, coefficients, and reconstruction diagnostics. | planned | <nobr><code>R5-VR-04</code></nobr> | <nobr><code>R5-PB-04</code></nobr> |
| <nobr><code>R5-REQ-05</code></nobr> | One declared response-coordinate stage must reproduce the selected single-cell recipe: fit the signed sparse SVD decoder on the declared fit plus tune Sinkhorn residual cells, ridge-encode every cell against that decoder, and rotate the 210 coefficients through the ordered fit plus tune covariance eigendecomposition. The stage must preserve the exact fitted cells, decoder, eigensystem ordering, rotation, coefficients, inverse reconstruction, numerical backend, execution state, and comparison with the historical coordinates. | planned | <nobr><code>R5-VR-05</code></nobr> | <nobr><code>R5-PB-05</code></nobr> |
| <nobr><code>R5-REQ-06</code></nobr> | One response-target bundle must bind the canonical cells, distinct control and response gene panels, control programs, ctrl19-matched fit/tune transport residuals, canonical global-control PearsonDelta truth, matched fit/tune coefficient targets, direct fit/tune gene shift, the legal descriptor-ridge hold gene shift, response programs, rotated coordinates, response-block definitions, perturbation order, response-gene order, split membership, execution profiles, and source evidence for both model rebuilds. The bundle must preserve the identity matched training truth plus gene shift equals global-control truth on fit and tune rows while keeping global-control truth as the only PearsonDelta scoring surface. | planned | <nobr><code>R5-VR-06</code></nobr> | <nobr><code>R5-PB-06</code></nobr> |
| <nobr><code>R5-REQ-07</code></nobr> | One response-block definition stage must reconstruct the historical program-similarity graph, hard 16-block labels, soft semantic 16-block map, and 210-dimensional rotation from the rebuilt response programs and coefficients, preserving program order, dimensions, parameters, and parity with each retained Phase 0 definition artifact. | planned | <nobr><code>R5-VR-07</code></nobr> | <nobr><code>R5-PB-07</code></nobr> |

### Verification rules

| Rule | Requirements | Acceptance conditions | Success case | Rejection cases |
|---|---|---|---|---|
| <nobr><code>R5-VR-01</code></nobr> | <nobr><code>R5-REQ-01</code></nobr> | The cNMF stage consumes only canonical control cells, the frozen IEG-excluded control panel, and the residual expression produced by R5-REQ-02; exercises the verified GPU NMF path; reproduces from its retained plan; emits finite non-collapsed programs; and uses CPU KMeans whenever the run claims byte parity. | [test_gpu_compiled_path_emits_nineteen_programs_and_diagnostics](../../mantra-rebuild/tests/test_control_programs.py) | [test_gpu_rejects_a_worker_initialized_without_the_reviewed_workspace](../../mantra-rebuild/tests/test_control_programs.py) |
| <nobr><code>R5-VR-02</code></nobr> | <nobr><code>R5-REQ-02</code></nobr> | The residualization validates the canonical log1p-CP10K slim-atlas metadata and axes; reads canonical control cells and exactly mitopercent and IEG_score; includes an intercept; persists the fitted coefficients and nonnegative residual offsets; reproduces the same residual bytes; and rejects another expression transform, normalization target, fitted cell or gene axis, covariate set, intercept policy, or output bytes. | [test_builds_deterministic_nonnegative_control_residuals](../../mantra-rebuild/tests/test_control_programs.py) | [test_rejects_a_control_panel_from_a_different_cell_axis](../../mantra-rebuild/tests/test_control_programs.py)<br>[test_rejects_a_noncanonical_or_misaligned_slim_atlas](../../mantra-rebuild/tests/test_control_programs.py) |
| <nobr><code>R5-VR-03</code></nobr> | <nobr><code>R5-REQ-03</code></nobr> | The control-state stage projects the canonical fit, tune, and control cells onto the ordered ctrl19 programs with nonnegative coefficients and a checked reconstruction; the GPU transport stage consumes those coordinates, emits ordered treated means, barycentric matched-control means, and residuals, matches its CPU reference within named tolerances, satisfies its numerical checks, and rejects any hold response input. | [test_builds_ctrl19_matched_means_and_residuals](../../mantra-rebuild/tests/test_transport_residuals.py) | [test_rejects_changed_program_or_cell_axis](../../mantra-rebuild/tests/test_control_state.py)<br>[test_rejects_hold_rows_or_failed_transport_diagnostics](../../mantra-rebuild/tests/test_transport_residuals.py) |
| <nobr><code>R5-VR-04</code></nobr> | <nobr><code>R5-REQ-04</code></nobr> | The sparse dictionary reproduces from retained parameters, preserves the exact GEARS response-gene order and its declared IEG-retention policy, its GPU NNLS coefficients match the CPU reference within tolerance, and it reports sparsity, reconstruction, stability, support, and redundancy. | [test_builds_sparse_programs_with_gpu_nnls](../../mantra-rebuild/tests/test_response_programs.py) | [test_rejects_misaligned_unstable_or_drifting_response_programs](../../mantra-rebuild/tests/test_response_programs.py) |
| <nobr><code>R5-VR-05</code></nobr> | <nobr><code>R5-REQ-05</code></nobr> | The saved sparse SVD decoder, ridge coefficients, fit-plus-tune covariance eigensystem, 210-dimensional rotation, and rotated coefficients reconstruct the declared residual inputs within tolerance; preserve cell, perturbation, gene, and coordinate order; and remain bound to the recorded VIPER execution identity. | [test_builds_reconstructible_rotated_response_coordinates](../../mantra-rebuild/tests/test_response_coordinates.py) | [test_rejects_changed_fit_population_or_coordinate_order](../../mantra-rebuild/tests/test_response_coordinates.py) |
| <nobr><code>R5-VR-06</code></nobr> | <nobr><code>R5-REQ-06</code></nobr> | The bundle resolves every ordered axis, gene panel, global-control scoring truth, ctrl19-matched training truth, coefficient target, gene shift, intermediate, and response-block definition to one passing producer record; verifies matched_delta + gene_shift == global_delta on fit and tune rows; proves that the hold shift uses no hold responses; records each execution profile; and both model loaders consume the same bundle identity. | [test_freezes_shared_response_target_bundle](../../mantra-rebuild/tests/test_response_target_bundle.py) | [test_rejects_mixed_surface_profile_or_unresolved_target_input](../../mantra-rebuild/tests/test_response_target_bundle.py) |
| <nobr><code>R5-VR-07</code></nobr> | <nobr><code>R5-REQ-07</code></nobr> | The rebuilt similarity graph, block labels, semantic map, and rotation preserve the declared response-program order and match their Phase 0 arrays or labels exactly under the parity profile; copying the historical files without executing their producers does not pass. | [test_rebuilds_response_block_definitions_with_parity](../../mantra-rebuild/tests/test_response_block_definitions.py) | [test_rejects_ingested_or_misaligned_response_block_definitions](../../mantra-rebuild/tests/test_response_block_definitions.py) |
<!-- contract-protocol:generated:end -->
