# Hopfield GPU and vectorization gap analysis

## Scope and evidence snapshot

This analysis covers the source-derived K562 path from control-state projection
through matched-control residuals, response coordinates, and Hopfield training.
It compares:

- the committed rebuild at `mantra-rebuild@bf12bc03591e09f5ea7a5f9adea197f4aa680839`;
- the retained `v1691_full_scratch_family64_ag_film_rebuild` implementation;
- the stopped L4 run `01M2TCW9MM3AA07RHMRF2NWGSQ`, attempt 3.

The governing optimization inventory requires one upload for resident numeric
inputs, batched GPU Sinkhorn, batched GPU NNLS, GPU low-rank reduction, and
full-dataset GPU-resident Hopfield operations
([inventory, line 14](/Users/machina/Developer/ChatGPT/RICO/docs/briefings/2026-09-15-mantra-gpu-optimization-inventory.md:14)).

At 2026-09-18 14:52:07 UTC, the live attempt was stopped during
`build_matched_control_residuals`. The stage had run for 36 minutes 47 seconds.
Linux reported 112,313,334,050 logical characters read by the worker. The
source H5AD is 10,661,879,995 bytes, so the process had issued logical reads
equal to 10.53 complete source files without finishing the stage. This is a
process-I/O ratio, not a claim that every byte came from the H5AD.

## Confirmed gaps

### Gap 1 — expression is read once per perturbation instead of once per selected cell surface

**Claim — Failed.** The matched-control stage must load the selected response
expression surface once, then index that resident matrix for every transport
batch.

**Observed path.** The rebuild loads controls once, but calls
`FastH5ADLoader.read_selected()` again for every perturbation group inside the
batch loop. With 1,784 perturbation groups, this creates 1,784 additional HDF5
selection operations.

Current implementation:
[`transport_residuals.py:646`](/Users/machina/Developer/ChatGPT/mantra-rebuild/src/rico/domain/k562/transport_residuals.py:646)

```python
for batch in batches:
    ...
    for batch_index, group in enumerate(batch):
        size = group.state_rows.size
        sizes[batch_index] = size
        treated_state[batch_index, :size] = whitened_state[group.state_rows]
        expression = atlas.read_selected(
            row_idx=group.atlas_rows,
            gene_ids=response_gene_ids,
        )
        if expression.missing_gene_ids:
            raise ValueError("treated expression lacks response genes")
        treated_expression[batch_index, :size] = expression.values
```

Historical optimized implementation:
[`perturbation_mean_cell_svd.py:66`](/Users/machina/Developer/ChatGPT/MANTRA/experiments/v1691_full_scratch_family64_ag_film_rebuild/src/step01_hopfield_base/response_programs/perturbation_mean_cell_svd.py:66)
and
[`perturbation_mean_cell_svd.py:238`](/Users/machina/Developer/ChatGPT/MANTRA/experiments/v1691_full_scratch_family64_ag_film_rebuild/src/step01_hopfield_base/response_programs/perturbation_mean_cell_svd.py:238)

```python
def load_expression_rows(raw_atlas, genes, projection):
    with open_raw_atlas_for_eval(...) as loader:
        expression = loader.load_genes_sorted_rows(
            genes,
            projection.cell_rows,
            use_shield=True,
        )
    return np.asarray(expression, dtype=np.float32, order="C")


expression = load_expression_rows(raw_atlas, genes, projection)
matched = matched_control_gene_rows(
    expression=expression,
    projection=projection,
    ...,
)
```

Required optimized shape:

```python
expression = atlas.read_selected(
    row_idx=state_atlas_rows,
    gene_ids=response_gene_ids,
)
expression_values = np.asarray(expression.values, dtype=np.float32, order="C")

control_expression = expression_values[state.split_labels == "control"]
for batch in batches:
    for batch_index, group in enumerate(batch):
        size = group.state_rows.size
        treated_expression[batch_index, :size] = expression_values[group.state_rows]
```

**First unsupported connector.** `_run_transport()` receives only
`control_atlas_rows`, so it cannot perform the historical one-read operation
over the complete ordered state surface.

**Counterexample.** The stopped L4 worker reached 112.3 GB of logical reads
against a 10.66 GB source file and had not completed.

**Missing evidence.** No retained test asserts one expression read for the
complete matched-control stage, and no benchmark compares logical bytes read
with the historical implementation.

**Disposition.** Confirmed implementation and evidence gap. This is the direct
cause of the stopped run's read amplification.

### Gap 2 — Sinkhorn forces two device-to-host synchronizations per iteration

**Claim — Failed.** The fixed-iteration Sinkhorn loop must remain on the GPU;
diagnostics may cross to the host after the loop.

**Observed path.** The rebuild calls `.item()` twice in each of 60 iterations.
For the stopped run's 262 transport batches, that permits 31,440 forced host
synchronizations even though `convergence_tolerance` does not stop the loop.

Current implementation:
[`transport_residuals.py:549`](/Users/machina/Developer/ChatGPT/mantra-rebuild/src/rico/domain/k562/transport_residuals.py:549)

```python
for _ in range(config.iterations):
    previous_treated = treated_scaling
    previous_control = control_scaling
    ...
    maximum_update = max(
        float(torch.max(torch.abs(treated_scaling - previous_treated)).item()),
        float(torch.max(torch.abs(control_scaling - previous_control)).item()),
    )
```

Historical optimized implementation:
[`shared_cost.py:141`](/Users/machina/Developer/ChatGPT/MANTRA/experiments/v1691_full_scratch_family64_ag_film_rebuild/src/step01_hopfield_base/response_programs/shared_cost.py:141)

```python
for _ in range(int(cfg.iters)):
    kv = torch.matmul(kernel, v.unsqueeze(-1)).squeeze(-1).clamp_min(1.0e-30)
    u = torch.pow(a / kv, power)
    ktu = torch.matmul(kernel.transpose(1, 2), u.unsqueeze(-1)).squeeze(-1)
    ktu = ktu.clamp_min(1.0e-30)
    v = torch.pow(b / ktu, power)

plan = u.unsqueeze(-1) * kernel * v.unsqueeze(1)
```

Required optimized diagnostic:

```python
maximum_update_tensor = torch.zeros((), device=cost.device, dtype=cost.dtype)
for _ in range(config.iterations):
    previous_treated = treated_scaling
    previous_control = control_scaling
    ...
    current_update = torch.maximum(
        torch.max(torch.abs(treated_scaling - previous_treated)),
        torch.max(torch.abs(control_scaling - previous_control)),
    )
    maximum_update_tensor = torch.maximum(maximum_update_tensor, current_update)
maximum_update = float(maximum_update_tensor.item())
```

**First unsupported connector.** `_sinkhorn_plan()` computes a host scalar on
every iteration although its only consumer is post-loop metadata.

**Counterexample.** The historical loop performs the same fixed number of
batched tensor updates without an inner-loop `.item()` call.

**Missing evidence.** No profiler evidence records CUDA synchronization count
or kernel gaps for the rebuild.

**Disposition.** Confirmed GPU execution gap.

### Gap 3 — matched-control means repeat the largest expression matrix multiply

**Claim — Failed.** After computing every matched control cell, the
perturbation mean must be reduced from that result rather than multiplying the
transport weights by the complete control-expression matrix a second time.

**Observed path.** The rebuild computes `matched_cells`, then constructs
`control_weights` and performs a second multiplication by
`control_expression_tensor`.

Current implementation:
[`transport_residuals.py:712`](/Users/machina/Developer/ChatGPT/mantra-rebuild/src/rico/domain/k562/transport_residuals.py:712)

```python
row_mass = plan.sum(dim=2).clamp_min(1.0e-30)
normalized_plan = plan / row_mass.unsqueeze(-1)
matched_cells = normalized_plan @ control_expression_tensor
size_tensor = torch.as_tensor(sizes, device=execution_device, dtype=torch.float32)
control_weights = normalized_plan.sum(dim=1) / size_tensor.unsqueeze(1)
matched = control_weights @ control_expression_tensor
```

Optimized equivalent:

```python
row_mass = plan.sum(dim=2).clamp_min(1.0e-30)
normalized_plan = plan / row_mass.unsqueeze(-1)
matched_cells = normalized_plan @ control_expression_tensor
size_tensor = torch.as_tensor(sizes, device=execution_device, dtype=torch.float32)
matched = matched_cells.sum(dim=1) / size_tensor.unsqueeze(1)
```

The equivalence follows from associativity:

```text
sum_rows(normalized_plan @ controls) / size
= (sum_rows(normalized_plan) / size) @ controls
```

**First unsupported connector.** The aggregate mean ignores the already
materialized `matched_cells` tensor.

**Counterexample.** The historical implementation computes the cellwise
barycenter once as `(plan @ controls_gene) / row_mass` and later averages those
cell rows; it does not issue the second control-expression matrix multiply
([`perturbation_mean_cell_svd.py:130–136`](/Users/machina/Developer/ChatGPT/MANTRA/experiments/v1691_full_scratch_family64_ag_film_rebuild/src/step01_hopfield_base/response_programs/perturbation_mean_cell_svd.py:130)).

**Missing evidence.** No equality test covers the reduced result, and no
profiler separates the two matrix multiplications.

**Disposition.** Confirmed redundant GPU operation.

### Gap 4 — the transport batch budget regressed from 8,192 to 2,048 without retained evidence

**Claim — Unsupported.** The rebuild may reduce the historical batch budget
only when an L4 memory measurement demonstrates that 8,192 is unsafe or slower.

Current default:
[`config.py:328`](/Users/machina/Developer/ChatGPT/mantra-rebuild/src/rico/config.py:328)

```python
max_treated_rows_per_batch: int = Field(
    default=2048,
    gt=0,
    description="Maximum padded treated-cell rows in one GPU transport batch.",
)
```

Historical default:
[`perturbation_mean_cell_svd.py:225`](/Users/machina/Developer/ChatGPT/MANTRA/experiments/v1691_full_scratch_family64_ag_film_rebuild/src/step01_hopfield_base/response_programs/perturbation_mean_cell_svd.py:225)

```python
chunk_rows: int = 8192,
max_treated_rows_per_batch: int = 8192,
ot_eps: float = 0.5,
ot_tau: float = 1.0,
ot_iters: int = 60,
```

**Observed path.** The stopped run formed 262 transport batches under the
2,048-row budget.

**First unsupported connector.** The new default is not connected to an L4
peak-memory result, throughput comparison, or OOM boundary.

**Counterexample.** The retained implementation used 8,192 for the same model
family.

**Missing evidence.** A matched 2,048-versus-8,192 benchmark after the one-read
repair.

**Disposition.** Configuration gap. The correct value remains unverified; the
historical 8,192 value is the parity default until evidence supports a change.

### Gap 5 — dense NNLS dropped the compiled update and synchronizes every iteration

**Claim — Failed.** Dense NNLS must keep projected-gradient updates compiled
and device-resident, with convergence checks no more frequent than the retained
historical cadence.

Current implementation:
[`nnls.py:97`](/Users/machina/Developer/ChatGPT/mantra-rebuild/src/rico/solvers/nnls.py:97)

```python
for iteration in range(max_iterations):
    previous = coefficients
    gradient = coefficients @ kernel.gram - cross_product
    coefficients = torch.clamp(
        coefficients - kernel.step_size * gradient,
        min=0.0,
    )
    maximum_update = float(torch.max(torch.abs(coefficients - previous)).item())
    completed_iterations = iteration + 1
    if maximum_update <= tolerance:
        converged = True
        break
```

Historical optimized implementation:
[`nmf_torch_batched.py:291`](/Users/machina/Developer/ChatGPT/MANTRA/experiments/v1691_full_scratch_family64_ag_film_rebuild/src/step01_hopfield_base/control_programs/nmf_torch_batched.py:291)

```python
def _pgd_step_fn(h, xw, wtw, lr_val):
    grad = torch.matmul(h, wtw) - xw
    return torch.clamp(h - lr_val * grad, min=0.0)


_compiled_pgd_step = None

if _compiled_pgd_step is None:
    if hasattr(torch, "compile") and os.getenv("MANTRA_DISABLE_COMPILE", "0") != "1":
        _compiled_pgd_step = torch.compile(_pgd_step_fn)
    else:
        _compiled_pgd_step = _pgd_step_fn

for i in range(n_iter):
    h_previous = h
    h = _compiled_pgd_step(h, xw, wtw, learning_rate)
    if i % 10 == 0 and i > 0:
        change = torch.max(torch.abs(h - h_previous))
        if change < tolerance:
            break
```

Required optimized shape:

```python
update = torch.compile(_projected_gradient_step)
for iteration in range(max_iterations):
    previous = coefficients
    coefficients = update(coefficients, cross_product, kernel.gram, kernel.step_size)
    if iteration % 10 == 0 or iteration == max_iterations - 1:
        maximum_update = float(
            torch.max(torch.abs(coefficients - previous)).item()
        )
        if maximum_update <= tolerance:
            converged = True
            break
```

The rebuild also changed the control-state default from the historical 50
iterations to 500
([`config.py:283`](/Users/machina/Developer/ChatGPT/mantra-rebuild/src/rico/config.py:283),
[`04_build_control_state_cache.py:295–301`](/Users/machina/Developer/ChatGPT/MANTRA/experiments/v1691_full_scratch_family64_ag_film_rebuild/src/inputs/builders/numbered/04_build_control_state_cache.py:295)).
Early stopping can justify additional headroom, but the current implementation
pays for a host synchronization on every attempted iteration.

**First unsupported connector.** `solve_dense_nnls()` replaced the compiled
historical step with eager operations and moved convergence inspection from
every tenth iteration to every iteration.

**Counterexample.** The retained solver compiled the update once and checked
change every ten iterations.

**Missing evidence.** No parity benchmark reports coefficient error, iteration
count, host synchronization count, or elapsed time for the new shared solver.

**Disposition.** Confirmed GPU-kernel and synchronization gap shared by
control-state and response-program projection.

### Gap 6 — the response decoder is refit on every cell instead of perturbation means

**Claim — Failed for parity.** The historical baseline fits the 5,000-by-210
decoder on fit-and-tune perturbation means, then applies that decoder to cell
rows. It does not fit a second decoder on all cellwise residuals.

Current implementation:
[`response_coordinates.py:325`](/Users/machina/Developer/ChatGPT/mantra-rebuild/src/rico/domain/k562/response_coordinates.py:325)

```python
decoder_fit = _fit_decoder(
    inputs.cellwise_residuals,
    config,
    device=device,
)
coefficients, batch_count, transfer_count, transfer_bytes = _encode_cells(
    inputs.cellwise_residuals,
    decoder_fit.decoder,
    config,
    device=device,
)
```

Historical optimized and parity-preserving implementation:
[`perturbation_mean_cell_svd.py:253`](/Users/machina/Developer/ChatGPT/MANTRA/experiments/v1691_full_scratch_family64_ag_film_rebuild/src/step01_hopfield_base/response_programs/perturbation_mean_cell_svd.py:253)

```python
treated_rows = np.where(~projection.control_mask)[0].astype(np.int64)
residual_gene = np.asarray(
    expression[treated_rows] - matched[treated_rows],
    dtype=np.float32,
    order="C",
)
train = np.concatenate([matrices["fit"], matrices["tune"]], axis=0)
decoder, perturbation_codes, solver_meta = fit_torch_svd_sparse_dictionary(
    train=train,
    matrices=matrices,
    n_components=int(n_components),
    alpha=float(alpha),
    ridge=float(dictionary_ridge),
    device=device,
)
cell_coeff = encode_rows_with_decoder(
    residual_gene,
    decoder,
    ridge=float(projection_ridge),
    chunk_rows=int(chunk_rows),
    device=device,
    emit=emit,
)
```

**First unsupported connector.** `_fit_coordinates()` feeds
`cellwise_residuals` into `_fit_decoder()` even though the preceding response
program stage already fits the perturbation-level basis.

**Counterexample.** The retained baseline's default
`decoder_fit_mode="perturbation_mean"` fits on roughly one row per fit/tune
perturbation, then performs only the cell encoding at cell scale.

**Missing evidence.** There is no approved scientific change, parity result,
or runtime result for replacing perturbation-mean decoder fitting with a second
cell-scale fit.

**Disposition.** Confirmed parity and workload gap. This is not merely an
optimization choice; it changes the fitted object.

### Gap 7 — response coordinates perform a second full CPU reconstruction pass

**Claim — Failed.** Reconstruction error should be accumulated while each
cell batch and its encoded coefficients are already on the GPU. The complete
cell-by-gene surface should not be multiplied again on CPU.

Current implementation:
[`response_coordinates.py:347`](/Users/machina/Developer/ChatGPT/mantra-rebuild/src/rico/domain/k562/response_coordinates.py:347)

```python
reconstruction_rmse = np.empty(inputs.cellwise_residuals.shape[0], dtype=np.float32)
for start in range(0, inputs.cellwise_residuals.shape[0], config.batch_rows):
    stop = min(start + config.batch_rows, inputs.cellwise_residuals.shape[0])
    observed = np.asarray(inputs.cellwise_residuals[start:stop], dtype=np.float32)
    reconstructed = np.asarray(
        rotated_coefficients[start:stop] @ rotated_decoder.T,
        dtype=np.float32,
    )
    reconstruction_rmse[start:stop] = np.sqrt(
        np.mean((observed - reconstructed) ** 2, axis=1)
    )
```

Optimized variant:

```python
values = torch.as_tensor(batch, device=execution_device)
encoded = values @ encoder.projection
reconstructed = encoded @ decoder_tensor.T
batch_rmse = torch.sqrt(torch.mean((values - reconstructed) ** 2, dim=1))

coefficients[start:stop] = encoded.detach().cpu().numpy()
reconstruction_rmse[start:stop] = batch_rmse.detach().cpu().numpy()
```

**First unsupported connector.** `_encode_cells()` returns coefficients but
discards the resident input tensor before reconstruction diagnostics are
computed.

**Counterexample.** The shared NNLS solver already computes reconstruction
RMSE on the device before returning
([`nnls.py:116–124`](/Users/machina/Developer/ChatGPT/mantra-rebuild/src/rico/solvers/nnls.py:116)).

**Missing evidence.** No benchmark separates coordinate fitting, cell
encoding, and the CPU reconstruction pass.

**Disposition.** Confirmed duplicate transfer and CPU-vectorization gap.

## Secondary vectorization defects

These are real but are not the stopped run's primary cause.

### Repeated full-axis scans while constructing perturbation groups

[`transport_residuals.py:447–452`](/Users/machina/Developer/ChatGPT/mantra-rebuild/src/rico/domain/k562/transport_residuals.py:447)
compares both complete label arrays once for each perturbation:

```python
for split_name, perturbations in pairs:
    for perturbation in perturbations:
        rows = np.flatnonzero(
            (state.split_labels == split_name)
            & (state.perturbation_labels == perturbation)
        )
```

One pass can build the same index:

```python
rows_by_key: dict[tuple[str, str], list[int]] = {}
for row, (split, perturbation) in enumerate(
    zip(state.split_labels, state.perturbation_labels, strict=True)
):
    rows_by_key.setdefault((str(split), str(perturbation)), []).append(row)
```

This removes `O(perturbations × cells)` label comparisons. It does not repair
the HDF5 amplification unless Gap 1 is fixed.

### Per-batch scalar synchronization in decoder fitting

[`response_coordinates.py:189`](/Users/machina/Developer/ChatGPT/mantra-rebuild/src/rico/domain/k562/response_coordinates.py:189)
calls `.item()` once per batch to count zeros. The count can remain a device
tensor and cross to the host once after the loop:

```python
zero_coefficients = torch.zeros((), dtype=torch.int64, device=execution_device)
for batch in batches:
    ...
    zero_coefficients += torch.count_nonzero(coefficients == 0.0)

coefficient_sparsity = int(zero_coefficients.item()) / coefficient_count
```

## Audited accelerated paths without a confirmed gap

- **Control-program cNMF:** one residual upload, concurrent restart dimension,
  compiled multiplicative updates, and chunked reconstruction error are present
  in
  [`control_programs.py:546–660`](/Users/machina/Developer/ChatGPT/mantra-rebuild/src/rico/domain/k562/control_programs.py:546).
- **Pairwise transport distance:** squared distances use batched tensor matrix
  multiplication in
  [`transport_residuals.py:516–531`](/Users/machina/Developer/ChatGPT/mantra-rebuild/src/rico/domain/k562/transport_residuals.py:516).
- **Control-state input batching:** selected atlas rows are ordered and read in
  8,192-row batches before GPU NNLS in
  [`control_state.py:422–469`](/Users/machina/Developer/ChatGPT/mantra-rebuild/src/rico/domain/k562/control_state.py:422).
- **Randomized SVD:** row batches use device matrix multiplication and retain
  transfer counts in
  [`randomized_svd.py:69–202`](/Users/machina/Developer/ChatGPT/mantra-rebuild/src/rico/solvers/randomized_svd.py:69).
- **Ridge encoding:** the decoder projection is prepared on the device and
  reused by batched encoding in
  [`ridge.py:30–80`](/Users/machina/Developer/ChatGPT/mantra-rebuild/src/rico/solvers/ridge.py:30).
- **Hopfield training:** complete fit/tune feature and coefficient matrices are
  transferred before the epoch loop; similarity, softmax, retrieval, and both
  losses are tensor operations in
  [`hopfield.py:973–1108`](/Users/machina/Developer/ChatGPT/mantra-rebuild/src/rico/domain/k562/hopfield.py:973).
- **Hopfield prediction:** retrieval uses GPU top-k and batched weighted donor
  values. Its 16-query chunks bound the temporary
  `query × neighbor × 5,000-gene` tensor and are not classified as a defect
  without a memory benchmark
  ([`hopfield.py:1124–1173`](/Users/machina/Developer/ChatGPT/mantra-rebuild/src/rico/domain/k562/hopfield.py:1124)).

## Required closure evidence

The performance claim remains open until one retained L4 run records:

1. exactly one read of the ordered expression surface;
2. logical bytes read and H5AD read-call count;
3. Sinkhorn batch count, host synchronization count, elapsed time, and peak GPU memory;
4. NNLS parity, completed iterations, synchronization count, and elapsed time;
5. numerical equality for the single-multiply matched-control mean;
6. response decoder training rows proving perturbation-mean parity;
7. separate timings for decoder fit, cell encoding, rotation, and reconstruction diagnostics;
8. final Hopfield Pearson delta from the resulting source-derived artifacts.
