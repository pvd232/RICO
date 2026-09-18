# Hopfield GPU residency and replay failure gap analysis

## Decision

The rebuilt Hopfield path must keep every reusable numerical input on the L4
for the complete stage when that tensor fits in 24 GB. It must not divide
control cells, response cells, perturbation means, SVD rows, ridge rows, NNLS
rows, or Hopfield queries into input batches.

One exception is algorithmic working state whose simultaneous materialization
would exceed memory. Transport may solve one perturbation group at a time
because one dense all-perturbation transport plan is 10.45 GB before its cost,
kernel, scaling, and output tensors exist. This is not input batching: the
complete state and expression surfaces remain resident while each group selects
its rows.

This document has two parts:

1. the inspected GPU-residency, vectorization, synchronization, duplicated
   computation, and parity defect in the rebuilt numerical path;
2. recorded replay failures, supported causes, remaining evidence gaps, and the
   brittle workaround or principled repair that followed.

The user will implement the source changes through pair coding. The PairBlocks
below define implementation order and acceptance. No source file is changed by
this analysis.

**Review status.** The second source review corrected the decoder repair and
added monitoring and reuse omissions. Algorithm excerpts are proposals, not
validated replacement files; several use incomplete operations or proposed
types. Full working-set memory and numerical parity still require observation.

## Evidence snapshot

- Rebuilt source: `mantra-rebuild@bf12bc03591e09f5ea7a5f9adea197f4aa680839`.
- Historical source: `v1691_full_scratch_family64_ag_film_rebuild`.
- Accelerator: one NVIDIA L4 with 24 GB.
- Raw atlas: `K562_essential_raw_singlecell_01.h5ad`, 10,661,879,995 bytes.
- Selected cells: 257,507.
- Response genes: 5,000.
- Control-program genes: 2,000.
- Control cells: 10,576.
- Treated cells: 246,931.
- Retained failed run: `01M2TCW9MM3AA07RHMRF2NWGSQ`, attempt 3.

The attempt was stopped during matched-control residual construction after
36 minutes 47 seconds. Linux reported 112,313,334,050 logical characters read,
10.53 times the raw atlas size, before the stage completed.

### GPU memory ledger

| Resident object | Float32 bytes | Decision |
|---|---:|---|
| Control expression, 10,576 × 2,000 | 84,608,000 | One upload |
| Selected control-state input, 257,507 × 2,000 | 2,060,056,000 | One upload |
| Selected response surface, 257,507 × 5,000 | 5,150,140,000 | One upload |
| Treated response surface, 246,931 × 5,000 | 4,938,620,000 | One upload |
| Full slim response surface, 283,856 × 5,000 | 5,677,120,000 | One upload |
| Cell response coordinates, 257,507 × 210 | 216,305,880 | Keep resident |
| Dense all-cell transport plan, 246,931 × 10,576 | 10,446,169,024 | Group-local working state |
| Hopfield gathered donor cube, 2,057 × 1,600 × 5,000 | 65,824,000,000 | Eliminate the cube |
| Hopfield dense query-memory weights, 2,057 × 1,600 | 13,164,800 | One matrix multiply |

# Part I — Numerical gaps

## G1 — Control residualization runs on CPU

**Observed.** `control_programs.py` builds the control expression matrix once,
then performs covariate regression, residual construction, minimum reduction,
and shifting with NumPy:

```python
coefficients = np.linalg.pinv(design.T @ design).astype(np.float32) @ (
    design.T @ expression
)
residuals = expression - design @ coefficients
minimum = residuals.min(axis=0)
shifted = residuals + np.where(minimum < 0.0, -minimum, 0.0)
```

**Required.** Upload the 84.6 MB control expression surface once and perform
the regression and shift with Torch. Download only the final residual matrix
and small regression metadata.

```python
expression = torch.as_tensor(source.expression, device=device)
design = torch.as_tensor(design_numpy, device=device)
coefficients = torch.linalg.pinv(design.T @ design) @ design.T @ expression
residuals = torch.nan_to_num(
    expression - design @ coefficients, nan=0.0, posinf=0.0, neginf=0.0
)
shifts = torch.clamp_min(-residuals.amin(dim=0), 0.0)
shifted = residuals + shifts
```

**First unsupported connector.** The stage loads a GPU-fitting input but
returns to NumPy before the immediately following GPU cNMF.

**Disposition.** Confirmed avoidable host computation and transfer.

## G2 — Control-program RMSE uses forbidden row chunks

**Observed.** [control_programs.py:1028](/Users/machina/Developer/ChatGPT/mantra-rebuild/src/rico/domain/k562/control_programs.py:1028)
divides a resident tensor into 10,000-row chunks.

**Required.** Compute the Frobenius error without a
`restart × cell × gene` reconstruction:

```python
def reconstruction_rmse(
    values: torch.Tensor,
    usages: torch.Tensor,
    programs: torch.Tensor,
) -> torch.Tensor:
    value_norm = values.square().sum()
    cross = torch.einsum("rcp,cg,rpg->r", usages, values, programs)
    usage_gram = torch.matmul(usages.transpose(1, 2), usages)
    program_gram = torch.matmul(programs, programs.transpose(1, 2))
    reconstruction_norm = (usage_gram * program_gram).sum(dim=(1, 2))
    squared_error = torch.clamp_min(
        value_norm - 2.0 * cross + reconstruction_norm,
        0.0,
    )
    return torch.sqrt(squared_error / values.numel())
```

**Disposition.** Confirmed vectorization gap.

## G3 — Control-state projection repeatedly reads and uploads 32 batches

**Observed.** [control_state.py:422](/Users/machina/Developer/ChatGPT/mantra-rebuild/src/rico/domain/k562/control_state.py:422)
reads 8,192 atlas rows at a time and calls NNLS once per batch. The retained
attempt recorded 2,060,056,000 input bytes, 32 transfers, 299,138,048 peak
allocated GPU bytes, and 357.439 seconds. The full input is only 2.06 GB.

**Required.**

```python
selected_expression = atlas.read_selected(
    row_idx=selected.rows,
    gene_ids=bank.gene_ids,
)
expression = torch.as_tensor(
    selected_expression.values,
    dtype=torch.float32,
    device=kernel.basis.device,
)
result = solve_dense_nnls_tensor(
    expression,
    kernel,
    max_iterations=config.max_iterations,
    tolerance=config.tolerance,
)
```

Remove `batch_rows`, `batch_count`, and batch-shaped diagnostics. Require
`input_transfer_count == 1`.

**Disposition.** Confirmed full-residency violation.

## G4 — Dense NNLS owns transfers and synchronizes every iteration

**Observed.** [nnls.py:65](/Users/machina/Developer/ChatGPT/mantra-rebuild/src/rico/solvers/nnls.py:65)
accepts NumPy, uploads internally, returns NumPy, and calls `.item()` on every
iteration.

**Required.** The stage owns transfer boundaries. The solver accepts and
returns tensors. Compile the repeated update and inspect convergence only at a
declared cadence:

```python
def projected_gradient_step(
    coefficients: torch.Tensor,
    cross_product: torch.Tensor,
    gram: torch.Tensor,
    step_size: torch.Tensor,
) -> torch.Tensor:
    gradient = coefficients @ gram - cross_product
    return torch.clamp_min(coefficients - step_size * gradient, 0.0)


def solve_dense_nnls_tensor(
    expression: torch.Tensor,
    kernel: DenseNNLSKernel,
    *,
    max_iterations: int,
    tolerance: float,
    check_interval: int = 10,
) -> DenseNNLSTensorResult:
    cross_product = expression @ kernel.basis
    coefficients = torch.relu(cross_product)
    update = torch.compile(projected_gradient_step)
    maximum_update = torch.full(
        (), torch.inf, device=expression.device, dtype=expression.dtype
    )
    converged = False
    for iteration in range(max_iterations):
        previous = coefficients
        coefficients = update(
            coefficients, cross_product, kernel.gram, kernel.step_size
        )
        if (iteration + 1) % check_interval == 0 or iteration + 1 == max_iterations:
            maximum_update = (coefficients - previous).abs().amax()
            if bool((maximum_update <= tolerance).item()):
                converged = True
                break
    return DenseNNLSTensorResult(
        coefficients=coefficients,
        reconstruction_rmse=...,
        completed_iterations=iteration + 1,
        converged=converged,
        maximum_update=maximum_update,
        maximum_kkt_violation=...,
    )
```

The `prepare_dense_nnls()` spectral-norm scalar read is one setup check and may
remain. Stage metadata may convert final diagnostic tensors once.

**Disposition.** Confirmed shared solver API, compilation, and synchronization
gap.

## G5 — Transport reread was repaired, but the stage still batches resident inputs

**Baseline defect.** The committed implementation performed 1,784 separate
H5AD expression reads. The stopped worker read more than ten source-file
equivalents.

**Current working-tree repair.** `transport_residuals.py` now reads the complete
selected response surface once. That repair must be preserved.

**Remaining defect.** [transport_residuals.py:618](/Users/machina/Developer/ChatGPT/mantra-rebuild/src/rico/domain/k562/transport_residuals.py:618)
still packs perturbations into padded batches, creates NumPy input arrays,
uploads each batch, downloads cell residuals each batch, and copies aggregate
diagnostics each batch.

**Required.** Keep the complete state and expression surfaces resident. Build
group indices once. Solve one perturbation group at a time because the dense
all-group plan cannot coexist with its kernel and cost on a 24 GB card:

```python
state_tensor = torch.as_tensor(whitened_state, device=device)
expression_tensor = torch.as_tensor(expression_values, device=device)
control_rows = torch.as_tensor(control_state_rows, device=device)
control_state = state_tensor.index_select(0, control_rows)
control_expression = expression_tensor.index_select(0, control_rows)

for group in groups:
    rows = torch.as_tensor(group.state_rows, device=device)
    treated_state = state_tensor.index_select(0, rows)
    treated_expression = expression_tensor.index_select(0, rows)
    cost = squared_distance(treated_state, control_state)
    plan, final_update = sinkhorn_plan(cost, ...)
    matched_cells = normalized_plan(plan) @ control_expression
    cellwise_residuals.index_copy_(
        0,
        torch.as_tensor(group.output_rows, device=device),
        treated_expression - matched_cells,
    )
```

Delete `_pack_groups()`, padded tensors, `max_treated_rows_per_batch`,
`batch_count`, and `maximum_batch_perturbations`. Retain `group_count` because
group-local working state is part of the algorithm.

**Disposition.** The repeated-read defect is repaired locally; full residency
and padding removal remain confirmed gaps.

## G6 — Perturbation groups are built with repeated full-axis scans

**Observed.** The stage compares the complete split and perturbation label
arrays once for each perturbation.

**Required.**

```python
rows_by_key: dict[tuple[str, str], list[int]] = {}
for row, (split, perturbation) in enumerate(
    zip(state.split_labels, state.perturbation_labels, strict=True)
):
    rows_by_key.setdefault((str(split), str(perturbation)), []).append(row)
```

Convert each completed list to one tensor before the group loop.

**Disposition.** Confirmed `O(perturbations × cells)` label-scan defect.

## G7 — Sinkhorn synchronizes twice per iteration

**Observed.** [transport_residuals.py:540](/Users/machina/Developer/ChatGPT/mantra-rebuild/src/rico/domain/k562/transport_residuals.py:540)
calls `.item()` twice during each of 60 fixed iterations even though the
configured tolerance does not stop the loop.

**Required.**

```python
final_update = torch.zeros((), device=cost.device, dtype=cost.dtype)
for _ in range(config.iterations):
    previous_treated = treated_scaling
    previous_control = control_scaling
    ...
    final_update = torch.maximum(
        (treated_scaling - previous_treated).abs().amax(),
        (control_scaling - previous_control).abs().amax(),
    )
return plan, final_update
```

Convert `final_update` once when building stage metadata.

**Disposition.** Confirmed synchronization gap.

## G8 — Matched-control means repeat the largest expression multiply

**Observed.**

```python
matched_cells = normalized_plan @ control_expression_tensor
control_weights = normalized_plan.sum(dim=1) / size_tensor.unsqueeze(1)
matched = control_weights @ control_expression_tensor
```

**Required.**

```python
matched_cells = normalized_plan @ control_expression_tensor
matched = matched_cells.mean(dim=0)
```

For a group-local plan, the mean over treated rows is exactly the
perturbation-level matched-control mean.

**Disposition.** Confirmed duplicate matrix multiplication.

## G9 — Response-program SVD and NNLS transfer the same small surface repeatedly

**Observed.** The perturbation-mean residual surface is uploaded for SVD,
downloaded, then uploaded in 512-row NNLS batches. The entire surface is only
about 35.7 MB.

**Additional parity defect.** The rebuild thresholds SVD loadings, normalizes
them, and fits nonnegative coefficients. The historical
[sparse_dictionary.py](../../../../mantra/experiments/v1691_full_scratch_family64_ag_film_rebuild/src/step01_hopfield_base/response_programs/sparse_dictionary.py),
line 182, thresholds signed projected coefficients and ridge-refits a decoder.
Optimizing response NNLS would retain a different model.

**Required.** One resident perturbation-mean tensor feeds the historical SVD,
coefficient threshold, and decoder refit:

```python
values = torch.as_tensor(residuals, device=device)
_, singular_values, right_vectors = torch.linalg.svd(
    values, full_matrices=False
)
components = right_vectors[:component_count]
projected = values @ components.T
codes = projected.sign() * (projected.abs() - alpha).clamp_min(0.0)
identity = torch.eye(component_count, device=values.device, dtype=values.dtype)
decoder = torch.linalg.solve(
    codes.T @ codes + dictionary_ridge * identity,
    codes.T @ values,
).T.contiguous()
```

Remove `batch_rows` and `batch_count` from response-program config and metadata.
Require one input transfer.

Use historical alpha 0.15 and dictionary ridge 0.001 for the selected profile.
Retire response-NNLS configuration and nonnegativity assertions for this
signed-code path. Preserve control-state NNLS.

**Disposition.** Confirmed full-residency violation.

## G10 — Response coordinates refit the wrong decoder on all cells

**Observed.** [response_coordinates.py:134](/Users/machina/Developer/ChatGPT/mantra-rebuild/src/rico/domain/k562/response_coordinates.py:134)
runs randomized SVD on every cellwise residual and fits a second decoder.

**Historical contract.** Fit the decoder on fit-and-tune perturbation means,
then use that decoder to encode cellwise residuals. The preceding response
program stage must own that perturbation-level fit after G9 is repaired. Its
current normalized loading matrix is not the historical fitted decoder.

**Required.** First implement G9 and persist its fitted decoder explicitly.
Then consume that decoder. Delete
`_fit_decoder()` from the coordinate stage and remove randomized SVD from this
hot path:

```python
decoder = torch.as_tensor(inputs.response_decoder, device=device)
residuals = torch.as_tensor(inputs.cellwise_residuals, device=device)
encoder = prepare_ridge_encoder_tensor(decoder, ridge=config.encoding_ridge)
coefficients = residuals @ encoder.projection
```

**Disposition.** Confirmed scientific parity defect and unnecessary
cell-scale workload.

## G11 — Randomized SVD rereads the complete matrix for every projection

**Observed.** `randomized_svd.py` uploads row batches for the initial
projection, both projections of every power iteration, and the final compressed
projection.

**Required.** G10 removes this solver from response coordinates. If another
consumer remains, its API must accept one resident tensor:

```python
def randomized_right_singular_vectors_tensor(
    values: torch.Tensor,
    *,
    rank: int,
    oversample: int,
    power_iterations: int,
    generator: torch.Generator,
) -> RandomizedSVDTensorResult:
    omega = torch.randn(
        values.shape[1],
        min(rank + oversample, min(values.shape)),
        device=values.device,
        generator=generator,
    )
    left = torch.linalg.qr(values @ omega, mode="reduced").Q
    for _ in range(power_iterations):
        right = torch.linalg.qr(values.T @ left, mode="reduced").Q
        left = torch.linalg.qr(values @ right, mode="reduced").Q
    _, singular_values, right_vectors = torch.linalg.svd(
        left.T @ values,
        full_matrices=False,
    )
    return RandomizedSVDTensorResult(
        right_vectors=right_vectors[:rank].T,
        singular_values=singular_values[:rank],
    )
```

Delete the row iterator and transfer-count semantics from this solver.

**Disposition.** Confirmed full-residency violation; likely dead code after
the parity repair.

## G12 — Ridge encoding owns transfers and response coordinates batch every pass

**Observed.** `encode_ridge()` accepts NumPy, uploads, computes, and downloads.
`response_coordinates.py` calls it once per 8,192-row batch, uploads all
coefficients again for rotation, returns to NumPy for decoder rotation, and
performs a second batched CPU reconstruction.

**Required.** Expose tensor operations and keep the complete 4.94 GB residual
surface and 216 MB coefficient matrix resident:

```python
residuals = torch.as_tensor(inputs.cellwise_residuals, device=device)
decoder = torch.as_tensor(inputs.response_decoder, device=device)
encoder = prepare_ridge_encoder_tensor(decoder, ridge=config.encoding_ridge)
coefficients = residuals @ encoder.projection

second_moment = coefficients.T @ coefficients / coefficients.shape[0]
eigenvalues, eigenvectors = torch.linalg.eigh(second_moment)
order = torch.argsort(eigenvalues, descending=True)
rotation = eigenvectors.index_select(1, order).T.contiguous()
rotated_coefficients = coefficients @ rotation.T
rotated_decoder = decoder @ rotation.T
reconstruction_rmse = torch.sqrt(
    torch.mean(
        (residuals - rotated_coefficients @ rotated_decoder.T).square(),
        dim=1,
    )
)
```

Download persisted arrays once at the end. Remove `batch_rows`, `batch_count`,
repeated transfer diagnostics, and the CPU reconstruction loop.

**Disposition.** Confirmed full-residency, duplicate-pass, and solver-boundary
gap.

## G13 — Global Pearson-delta truth rereads atlas batches and reduces on CPU

**Observed.** [response_targets.py:687](/Users/machina/Developer/ChatGPT/mantra-rebuild/src/rico/domain/k562/response_targets.py:687)
reads 8,192 rows at a time and performs nested NumPy label reductions. The
entire 283,856 × 5,000 surface is 5.68 GB.

**Required.** Read once, upload once, and use indexed accumulation:

```python
surface = atlas.read_selected(
    row_idx=selected_rows,
    gene_ids=response_gene_ids,
)
values = torch.as_tensor(surface.values, device=device)
group_index = torch.as_tensor(encoded_labels, device=device)
sums = torch.zeros(
    len(ordered), values.shape[1], device=device, dtype=values.dtype
)
sums.index_add_(0, group_index, values)
counts = torch.bincount(group_index, minlength=len(ordered))
means = sums / counts[:, None]
deltas = means[1:] - means[0]
```

Remove `atlas_batch_rows`. Keep the global control mean: Pearson delta is
measured against that surface; the separately learned gene shift serves the
holdout prediction path.

**Disposition.** Confirmed read-amplification and CPU-reduction gap.

## G14 — Varimax synchronizes three times per iteration

**Observed.** [response_blocks.py:285](/Users/machina/Developer/ChatGPT/mantra-rebuild/src/rico/domain/k562/response_blocks.py:285)
converts both the previous and current objective to host scalars inside each
iteration.

**Required.** Keep convergence as a device predicate and inspect only at a
declared cadence, or run the fixed 32 iterations and inspect once:

```python
for iteration in range(config.varimax_max_iterations):
    ...
    objective = singular_values.sum()
    if (iteration + 1) % config.convergence_check_interval == 0:
        converged = (previous_objective > 0.0) & (
            objective < previous_objective * (1.0 + config.varimax_tolerance)
        )
        if bool(converged.item()):
            break
    previous_objective = objective
```

The matrices are small, so this is a synchronization cleanup rather than a
material runtime blocker.

**Disposition.** Confirmed low-cost synchronization gap.

## G15 — Control-state means use repeated Boolean scans

**Observed.** `ctrl19_holdout.py` scans the complete label vectors once per
fit/tune perturbation.

**Required.** Encode labels once and use indexed accumulation:

```python
group_index = np.fromiter(
    (
        label_to_index[(split, perturbation)]
        for split, perturbation in zip(split_labels, labels, strict=True)
    ),
    dtype=np.int64,
)
sums = np.zeros((len(label_to_index), coefficients.shape[1]), dtype=np.float64)
np.add.at(sums, group_index, coefficients)
counts = np.bincount(group_index, minlength=len(label_to_index))
means = (sums / counts[:, None]).astype(np.float32)
```

**Disposition.** Confirmed vectorization gap.

## G16 — Hopfield bank construction leaves the GPU

**Observed.** Training copies coefficients to CPU, runs NumPy whitened PCA and
neighbor smoothing, then uploads the bank.

**Required.** Torch-native PCA sign normalization and smoothing:

```python
value = coefficients.to(torch.float64)
mean = value.mean(dim=0, keepdim=True)
scale = value.std(dim=0, correction=0, keepdim=True).clamp_min(1.0e-6)
whitened = (value - mean) / scale
left, singular, right = torch.linalg.svd(whitened, full_matrices=False)
pivots = right.abs().argmax(dim=1)
rows = torch.arange(right.shape[0], device=device)
signs = torch.sign(right[rows, pivots])
signs = torch.where(signs == 0.0, torch.ones_like(signs), signs)
left = left * signs
right = right * signs[:, None]
reconstructed = (left[:, :rank] * singular[:rank]) @ right[:rank]
bank = ((reconstructed + whitened.mean(dim=0, keepdim=True)) * scale + mean)
bank = bank.to(torch.float32)

normalized = coefficients / coefficients.norm(dim=1, keepdim=True).clamp_min(1.0e-8)
similarity = normalized @ normalized.T
similarity.fill_diagonal_(-torch.inf)
neighbors = torch.topk(similarity, k=neighbor_count, dim=1)
weights = torch.softmax(neighbors.values, dim=1)
neighbor_mean = torch.einsum("nk,nkd->nd", weights, bank[neighbors.indices])
bank = (1.0 - blend) * bank + blend * neighbor_mean
```

**Disposition.** Confirmed avoidable CPU round trip.

The historical PCA uses float64 and population standard deviation. Preserve
both, plus its residual whitened mean. Test neighbor ordering, ties, and SVD
differences explicitly before claiming parity with NumPy.

## G17 — Hopfield inference uses 16-query batches to hide a 65.8 GB gather

**Observed.** [hopfield.py:1111](/Users/machina/Developer/ChatGPT/mantra-rebuild/src/rico/domain/k562/hopfield.py:1111)
constructs `memory_values[selected.indices]` in 16-query chunks. Removing the
loop without changing the representation would materialize a 65.8 GB donor
cube.

**Required.** Scatter top-k weights into one query-memory matrix and multiply
once:

```python
selected = torch.topk(
    similarities,
    k=min(config.topk, similarities.shape[1]),
    dim=1,
)
selected_weights = torch.softmax(selected.values / config.temperature, dim=1)
dense_weights = torch.zeros_like(similarities)
dense_weights.scatter_(1, selected.indices, selected_weights)
prediction = dense_weights @ memory_values
coefficient_prediction = dense_weights @ memory_coefficients
```

The dense weights occupy about 13 MB. This removes query batching and the donor
cube.

**Disposition.** Confirmed batching and intermediate-representation defect.

## G18 — CUDA AdamW explicitly disables its fused implementation

**Observed.**

```python
optimizer = torch.optim.AdamW(..., fused=False)
```

**Required.**

```python
optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=config.learning_rate,
    weight_decay=config.weight_decay,
    fused=device.type == "cuda",
)
```

The focused test compares one deterministic update with the unfused reference
within the declared tolerance.

**Disposition.** Confirmed kernel-fusion opportunity.

G1 and G18 are proposed acceleration opportunities, not measured historical
regressions. Preserve their numerical settings until focused comparisons
justify changes. G2's norm identity can suffer cancellation near convergence;
compare it against direct residual error, including near-exact reconstruction.
Use a higher-precision reduction or direct full-resident reconstruction if the
identity changes convergence decisions.

G4 and G14 must preserve the accepted stopping rule. Changing check cadence or
forcing extra iterations can change outputs. In varimax, combine the existing
condition into one device Boolean and one scalar read per required check
before considering a different cadence. A profiler gain alone is not parity.

G13 must preserve float64 accumulation and the configured determinism policy.
A float32 atomic indexed reduction is not automatically equivalent to the
current CPU sums. Validate an appropriate grouped reduction on the installed
runtime; retain the global-control definition and exact membership.

The memory ledger describes individual arrays, not measured peak allocation.
Account for simultaneous residual, reconstruction, squared-error, solver
workspace, and allocator storage before accepting each full-resident stage.
The 65.8 GB Hopfield cube is an illustrative all-query upper-bound construction;
actual split sizes and the fit-memory count determine the current peak.

## G19 — Monitoring reuploads resident data and repeats forward passes

[hopfield.py](../../../../mantra-rebuild/src/rico/domain/k562/hopfield.py),
lines 921–969: every `_predict_coefficients()` call concatenates and uploads
the same feature and coefficient memories. It computes memory embeddings, then
computes the same rows again as split queries. Lines 1013 and 1042 also
normalize the fixed bank repeatedly.

Pass existing resident memories and split offsets into the monitor. Compute
memory embeddings once per monitoring epoch, slice them for queries, use the
scatter-and-multiply readout from G17, and cache the normalized bank before
the training loop. Recompute embeddings when model weights change. Preserve
evaluation mode, self-exclusion, checkpoint selection, and monitor cadence.
GPU-PB-06 owns this repair; its observer must count uploads and forward calls.

## Audited CPU boundaries and unmeasured opportunities

The following boundaries were inspected. Their relative runtime benefit has
not been measured; retaining them is a baseline-preservation recommendation,
not proof that no optimization exists:

- consensus KMeans over control-program vectors;
- spectral clustering over the response-program graph;
- perturbation-level Core83 ridge selection and SVD;
- response40 perturbation-level retrieval and diagnostics;
- metadata construction, hashing, serialization, and Pydantic validation;
- periodic Hopfield metric reads and checkpoint copies.

They remain subject to vectorized label grouping, but they are not GPU
residency failures.

# Part II — Why replay kept failing

## Observed failure sequence

The terminal errors below were recorded in the earlier audit. Their run IDs
are abbreviated and this document does not link complete immutable receipts.
The final column contains hypotheses requiring those receipts and the exact
candidate definitions. An HTTP failure alone does not establish an auth cause,
and missing credentials alone does not establish inconsistent retry state.

| Run | Stage | Terminal evidence | First unsupported connector |
|---|---|---|---|
| `01M2T90X…` | preflight | `preflight_failed: http.credentials` | GPU run began without proving every DownloadSpec credential |
| `01M2T92P…` attempts 1–2 | GEARS download | HTTP retrieval failed | Source acquisition was retried inside replay instead of accepted once and reused |
| `01M2T9HX…`, `01M2T9NN…` | IEG download | HTTP retrieval failed | Private-source credential and response-body acceptance were unresolved |
| `01M2T9WJ…` | gene panels | artifact pointer run was not a valid ResolvedRun | Promotion rewrote a child reference without preserving the typed parent identity |
| `01M2TADX…` | gene panels | expected SHA `f31d…`, received `3835…` | Promotion changed document bytes without bottom-up identity propagation |
| `01M2TB74…` | perturbation splits | HTTP retrieval failed | Download preflight still did not cover every source |
| `01M2TBED…` | control residuals | slim atlas lacks canonical expression metadata | Artifact shape existed, but semantic compatibility was not checked before execution |
| `01M2TC41…` | control programs | realized rank 20 != 19 | A historical name was treated as a fixed dimension without evidence |
| `01M2TCW…` attempt 1 | plan validation | extra `source_surface_npz` | Producer and consumer schemas changed out of step |
| `01M2TCW…` attempt 2 | preflight | missing `http.credentials` | Retry rebuilt global preflight state inconsistently |
| `01M2TCW…` attempt 3 | matched controls | preempted after 36m47s | Stage performed amplified H5AD reads and batched transfers |

## F1 — Every commit changed the stage reuse key

**Observed VIPER identity.** [reuse.py:358](/Users/machina/Developer/ChatGPT/viper/src/viper/reuse.py:358)
hashes the complete environment model:

```python
env_sha256=_canonical_sha256(env)
```

**Observed MANTRA environment.** [replay.py:75](/Users/machina/Developer/ChatGPT/mantra-rebuild/src/rico/commands/replay.py:75)
puts the active Git commit into the lockfile reference:

```python
lockfile=GitFileRef(
    repository=source.repository,
    commit=source.commit,
    path="pyproject.toml",
)
```

Any commit therefore changes `env_sha256` even when `pyproject.toml` bytes,
the observed Python environment, CUDA compute, stage implementation, inputs,
seed, reproducibility settings, and metrics are identical. This proves a
cross-commit invalidation mechanism. Assigning it as the cause of any specific
failed reuse requires that candidate's key comparison or rejection receipt;
those comparisons are not retained here.

**Brittle workaround.** `--gene-panel-run` and `--response-run` manually bypass
normal stage discovery. They duplicate orchestration knowledge and require the
operator to select an entire prior run.

**Principled repair.** Keep the Git commit in provenance, but exclude its
storage location from semantic environment identity:

```python
class ReuseEnvironmentIdentity(ProtocolModel):
    compute: ComputeSpec
    lockfile: FileIdentity
    python_env: PythonEnvironment


def reuse_environment_identity(env: ResolvedEnv) -> ReuseEnvironmentIdentity:
    return ReuseEnvironmentIdentity(
        compute=env.compute,
        lockfile=FileIdentity(
            sha256=env.lockfile.sha256,
            bytes=env.lockfile.bytes,
        ),
        python_env=env.python_env,
    )
```

The test holds lockfile bytes constant while changing the Git commit and proves
the reuse key remains equal. It then changes one lockfile byte and proves the
key changes.

### F1b — Shared config identity and imported-code coverage

[authoring.py](../../../../viper/src/viper/authoring.py), lines 1095–1120,
hashes the entire configuration source file and the stage wrapper file.
`_normalized_stage()` retains both references. Thus changing an unrelated
class in shared `config.py` changes a stage key even when its own fields and
values are unchanged. Normalizing only `env_sha256` is insufficient; an explicit
stage environment also remains inside the hashed stage payload.

Conversely, the control-state wrapper calls imported domain and solver code.
Its own file digest does not identify those dependencies. Removing the Git
commit discriminator without covering executed dependencies risks reusing
outputs after numerical code changes.

VIPER-PB-01 must first establish a content identity for the relevant executable
dependency closure and selected config schema, using existing framework
mechanisms where available. Tests must prove: unrelated config changes preserve
reuse; relevant schema or imported solver changes invalidate reuse; explicit
and inherited environments apply the same normalization. Keep conservative
invalidation until these requirements are supported.

## F2 — Cloud promotion uses duplicated walks and special-case identity repair

**Observed.** `_RunGraphPromoter` has:

- a manual type-to-decoder chain;
- `discover_typed()` for traversal;
- `rewrite_typed()` for a second traversal;
- a separate second pass for `RunSpec` stage SHA repair;
- full snapshot materialization into `dict[str, bytes]`;
- full snapshot rereads to calculate a content revision.

The recent fixes cover the known pointer and SHA failures, but ownership
remains split across ad hoc passes.

**Principled repair.** One typed graph transformer must visit every child once,
rewrite leaves first, serialize changed children, propagate each new identity
to its immediate parent, continue to the root, and stream unchanged payloads
to the configured provider.

The provider-neutral `ViperCloud` and immutable references remain. This repair
removes duplicated traversal and the `RunSpec` exception; it does not redesign
cloud storage.

## F3 — Immutable experiment identity was handled by caller-selected renaming

VIPER correctly rejects a changed experiment definition under an existing
immutable experiment ID. The rebuild responded by adding an arbitrary
`experiment_id` parameter to `declare_gene_panel_build_experiment()` and
passing `k562_gene_panel_source_rebuild` from the command.

This is brittle because callers can invent identities to evade a definition
collision.

**Principled repair.**

- The experiment declaration owns one stable semantic ID.
- A real graph-definition change receives a reviewed versioned ID in the
  declaration, not a caller override.
- Plans select the declaration; commands cannot rename it.
- A byte-identical declaration reuses the existing immutable experiment.

Delete the public `experiment_id` parameter.

## F4 — Preflight checked execution too late and too narrowly

Credentials, source response bodies, artifact metadata, producer-consumer
schema compatibility, and GPU capacity were discovered by separate stages
after expensive setup or GPU allocation.

**Principled repair.** One replay preflight finishes before mutable or GPU
execution. It verifies:

- every DownloadSpec URL and credential is resolvable;
- accepted immutable downloads are reused, not replayed;
- every selected artifact matches typed semantic metadata;
- producer and consumer schema versions agree;
- CUDA model and memory satisfy the full-residency declaration;
- every reusable stage has a semantic reuse key.

It does not redownload, rehash large accepted payloads, or rerun prior stages.
It traverses immutable receipts and performs small compatibility reads.

## F5 — Repairs to retain

Two repairs were principled:

- allowing exact Download roots through failed-run reuse when immutable receipt
  and attempt membership are verified;
- making the control-state width dynamic after stable rank 20 proved `ctrl19`
  was a stale name rather than an invariant.

These are not cleanup targets.

# Implementation PairBlocks

## GPU-PB-01 — Tensor-native linear solvers

**Requirement.** NNLS, ridge, and any retained randomized SVD accept and return
Torch tensors. They never own stage input transfers or row batches.

**Depends on.** None.

**Targets.** `src/rico/solvers/nnls.py`, `ridge.py`, `randomized_svd.py`, and
new `tests/test_gpu_solvers.py`.

**Context.** These solvers hide NumPy-to-GPU and GPU-to-NumPy copies, so every
caller repeats transfers. Tensor APIs give each stage one explicit residency
boundary and let later operations reuse the same tensors.

**Focused test.** Tensor NNLS and ridge equal deterministic current references;
no batch parameter exists; a CUDA profiler observes no scalar read inside the
declared fixed-update interval.

**Completion gate.** No solver public function contains a row loop,
`.cpu().numpy()`, or NumPy upload after setup.

**Stop condition.** Stop if the tensor result exceeds numerical tolerance; do
not loosen parity.

**Documentation.** Solver docstrings state that callers own transfer and
persistence boundaries.

## GPU-PB-02 — Full-resident control path

**Requirement.** Control residualization, cNMF diagnostics, and control-state
projection use one complete resident input each. No cell-row batches remain.

**Depends on.** GPU-PB-01.

**Targets.** `control_programs.py`, `control_state.py`, `config.py`,
`tests/test_control_programs.py`, and new `tests/test_control_state.py`.

**Context.** cNMF is resident, but residualization is CPU-bound, RMSE is
row-chunked, and control-state projection performs 32 reads and uploads for a
2.06 GB tensor.

**Focused test.** Frobenius RMSE equals explicit reconstruction; control
residuals preserve tolerance; one atlas read and one upload project all cells;
batch fields are absent.

**Completion gate.** Diagnostics record one transfer and zero input batches.

**Stop condition.** Stop if measured peak memory exceeds the declared budget;
do not reintroduce batching without a reviewed memory proof.

**Documentation.** Record resident shapes, bytes, and the retained CPU
consensus boundary.

## GPU-PB-03 — Resident group-local transport

**Requirement.** Read and upload selected state and response surfaces once.
Solve one perturbation group at a time without padded input batches, repeated
H5AD reads, inner-loop scalar reads, or a second expression multiply.

**Depends on.** GPU-PB-01 and GPU-PB-02.

**Targets.** `transport_residuals.py`, `config.py`, and new
`tests/test_transport_residuals.py`.

**Context.** Source surfaces fit, but the combined transport plan, kernel, and
cost do not. Group-local temporary state preserves full input residency without
an impossible global plan.

**Focused test.** One response read; one state and expression upload;
group-local output equals the current algorithm; matched mean equals the
cellwise mean; no Sinkhorn scalar read; exact row order is preserved.

**Completion gate.** No `_pack_groups`, padding tensor, row-budget config, or
per-group host transfer remains.

**Stop condition.** Stop if one perturbation group's peak memory exceeds the
budget; name the group before changing the design.

**Documentation.** State why group-local plan state is not input batching.

## GPU-PB-04 — Perturbation-mean response programs and resident coordinates

**Requirement.** Fit the response decoder once on perturbation means, then
encode the complete cell residual surface with one upload and no row batches.

**Depends on.** GPU-PB-01 and GPU-PB-03.

**Targets.** `response_programs.py`, `response_coordinates.py`,
`randomized_svd.py`, `config.py`, and new response-program and coordinate
tests.

**Context.** The coordinate stage changes the fitted object by refitting on
cell rows, repeatedly retransfers the surface, then reconstructs on CPU.

**Focused test.** Signed SVD codes and ridge decoder refit match the historical
function on the same perturbation means; coordinate decoder identity equals
that fitted decoder; one upload produces coordinates,
rotation, decoder, and RMSE; no randomized SVD or batch field remains.

**Completion gate.** Decoder fit rows are perturbation means and coordinate
diagnostics record one transfer.

**Stop condition.** Stop on decoder-identity or coefficient-parity failure.

**Documentation.** Name the response-program stage as sole decoder owner.

## GPU-PB-05 — Full-resident truth and vectorized label reductions

**Requirement.** Global Pearson-delta truth uses one atlas read, one upload,
and one indexed reduction. Control-state perturbation means use one vectorized
reduction.

**Depends on.** GPU-PB-03.

**Targets.** `response_targets.py`, `ctrl19_holdout.py`, `config.py`, and new
truth and holdout tests.

**Context.** Both builders rescan labels and divide data that fits. The global
control mean remains the only Pearson-delta truth baseline.

**Focused test.** Indexed means equal the old loop on shuffled labels; one
atlas read occurs; split counts are unchanged; delta equals perturbation mean
minus global control mean.

**Completion gate.** No atlas batch field or per-perturbation Boolean scan.

**Stop condition.** Stop if row order or global-control identity changes.

**Documentation.** Distinguish global-control truth from hold gene shift.

## GPU-PB-06 — Full-resident Hopfield setup and inference

**Requirement.** Training bank construction and inference remain on GPU.
Inference has no query batches and no donor cube.

**Depends on.** GPU-PB-04 and GPU-PB-05.

**Targets.** `hopfield.py` and new `tests/test_hopfield_model.py`.

**Context.** Training is full-batch, but bank construction round-trips through
NumPy. Inference chunks queries because its gather creates a 65.8 GB
intermediate; a 13 MB weight matrix gives the same sum.

**Focused test.** Monitoring reuses resident tensors and computes each memory
embedding once per monitoring epoch; bank normalization is cached. Torch
PCA/smoothing preserves float64 population statistics and matches NumPy within tolerance; scatter
plus matrix multiplication equals indexed gathering; fit self-exclusion and
hold shift remain exact; fused and unfused AdamW agree for one update.

**Completion gate.** No 16-query loop, CPU bank construction, or
`fused=False` remains.

**Stop condition.** Stop on fit self-exclusion or hold gene-shift mismatch.

**Documentation.** Record the avoided donor cube and replacement matrix size.

## GPU-PB-07 — Small synchronization and vectorization cleanup

**Requirement.** Remove varimax inner-loop scalar reads and all remaining
repeated label scans in the in-scope path.

**Depends on.** GPU-PB-05.

**Targets.** `response_blocks.py`, `ctrl19_holdout.py`, and focused test
additions.

**Context.** These are not primary runtime blockers, but they are the remaining
confirmed synchronization and vectorization defects.

**Focused test.** Outputs remain within tolerance and profiler traces show no
per-iteration scalar read except the declared convergence cadence.

**Completion gate.** No repeated whole-axis Boolean scan or undeclared
inner-loop `.item()` remains.

**Stop condition.** Retain deterministic CPU clustering.

**Documentation.** Document the intentional CPU clustering boundary.

## VIPER-PB-01 — Semantic environment reuse identity

**Requirement.** A Git commit location does not invalidate reuse when
lockfile bytes, observed environment, compute, stage, inputs, seed,
reproducibility settings, and metrics are identical.

**Depends on.** None.

**Targets.** `viper/src/viper/reuse.py`, environment resolution, and
`viper/tests/test_stage_reuse.py`.

**Context.** The key hashes the Git commit embedded in a lockfile location.
Unrelated commits therefore reject completed stages and forced manual
bypasses.

**Focused test.** Two commits with identical lockfile bytes produce the same
key; one changed byte changes it; other semantic changes change it; provenance
still retains the original commit.

Additionally require imported-domain/solver changes to invalidate reuse, and
unrelated shared-config edits to preserve it. Normalize explicit stage
environments as well as inherited run environments.

**Completion gate.** Cross-commit reuse selects the completed stage without an
operator-provided run.

**Stop condition.** Stop if any semantic environment change becomes invisible.

**Documentation.** Distinguish provenance location from reuse identity.

## VIPER-PB-02 — One bottom-up typed promotion transformer

**Requirement.** Cloud promotion rewrites one typed reference DAG bottom-up,
propagates changed child identities, and streams unchanged payloads.

**Depends on.** None.

**Targets.** `viper/src/viper/execution/_promotion.py` and existing focused
promotion tests.

**Context.** Known document types and `RunSpec` hashes now work through
separate discovery, rewrite, and repair passes.

**Focused test.** Nested local references become provider-neutral cloud refs;
all parent identities match; GCS and Hugging Face use one traversal; a large
unchanged payload is not retained in the transformer's byte map; terminal
verification passes.

**Completion gate.** One transformer owns discovery, rewrite, and parent
identity propagation. The `RunSpec` second-pass exception is gone.

**Stop condition.** Do not change provider APIs or immutable schemas without a
failing focused test.

**Documentation.** Document leaf-first transformation and streaming ownership.

## REPLAY-PB-01 — One preflight and removal of manual bypasses

**Requirement.** Replay validates sources, credentials, artifact semantics,
schemas, GPU capacity, and reusable stages before execution. Commands do not
accept whole-run bypasses for normally reusable work.

**Depends on.** VIPER-PB-01 and VIPER-PB-02.

**Targets.** `src/rico/commands/replay.py`,
`src/rico/plans/k562/gene_panels.py`, and replay-focused tests.

**Context.** `gene_panel_run`, `response_run`, and caller-selected experiment
IDs were introduced to bypass invalid reuse and immutable-definition
collisions.

**Focused test.** Dry preflight reports all missing credentials and
incompatible artifacts together; accepted downloads are not replayed;
completed stages reuse across unrelated commits; changed definitions require
declaration-owned versions.

**Completion gate.** Replay resolves dependencies through verified stage reuse
and stable declarations.

**Stop condition.** Preserve explicit external baseline references whose role
is scientific comparison.

**Documentation.** Remove obsolete bypass examples and document one preflight.

## FINAL-PB-01 — Fast validation, Hopfield result, then MIL

**Requirement.** Validate the repaired path once, record Hopfield Pearson
delta, then run MIL before unrelated test expansion.

**Depends on.** All preceding PairBlocks.

**Targets.** Focused CPU fixtures, one full L4 replay, immutable Hopfield
prediction and Pearson-delta artifacts, and MIL replay from the same sources.

**Context.** Intermediate source checks must not rerun expensive measurement
stages. Each successful output is persisted once and reused downstream.

**Focused gate order.**

1. format and type-check changed target files;
2. run only PairBlock-focused CPU tests;
3. run one CPU end-to-end smoke on reduced fixtures;
4. run one full L4 source-derived Hopfield replay;
5. record Hopfield Pearson delta;
6. run MIL immediately from the same accepted source artifacts;
7. record MIL metrics;
8. run broader regressions only after both scientific results exist.

**Completion gate.** Hopfield and MIL each have immutable source-rooted result
artifacts and recorded metrics.

**Stop condition.** If a downstream verifier or serializer fails after a
measurement succeeds, rerun only the changed downstream stage.

# Acceptance summary

The final replay may start only when:

1. every complete numerical source tensor that fits the L4 is read and uploaded
   once per stage;
2. no input/data batch parameter remains in the control, response, truth, or
   Hopfield path;
3. transport uses resident inputs with group-local working state;
4. no fixed-iteration GPU loop performs an undeclared per-iteration scalar
   read;
5. no duplicated cell-scale multiply or reconstruction pass remains;
6. response programs are fit on perturbation means and solely own the decoder;
7. Hopfield inference uses scatter-plus-matmul, not a donor cube or query
   chunks;
8. stage reuse uses semantic environment bytes, not their Git location;
9. cloud promotion uses one bottom-up typed transform;
10. replay preflight resolves every source and compatibility issue before GPU
    allocation;
11. Hopfield Pearson delta is recorded before MIL;
12. successful measurement artifacts are never rerun for downstream
    orchestration repairs.
