# MANTRA GPU and vectorization inventory

This inventory names the accelerated operations that the modular rebuild must
preserve. It is a migration checklist, not permission to copy an entire legacy
module. Each new owner must preserve the listed behavior, prove numerical
agreement with its reference, and retain a benchmark on the target L4 runtime.

Replay, bridge, and one-at-a-time substitution runs use the parity execution
profile. Every KMeans call in that chain uses seeded scikit-learn Lloyd KMeans
on CPU so cluster assignments remain fixed while one input or implementation
component changes. Triton KMeans returns only in a separately named throughput
run after the baseline-preserving chain closes.

| Operation | Current owner | Acceleration that must survive | Reference and execution rule | Consuming rebuild |
| --- | --- | --- | --- | --- |
| cNMF and NMF | `src/mantra/sota/programs/discovery/cnmf.py::run_cnmf`; `nmf_torch_batched.py::nmf_torch_batched` | Parallel GPU restarts, mini-batches, sparse batches, lazy signed expansion, float32 factors, dense tensor preloading, compiled tensor updates | Compare fixed initialization with the CPU NMF result. Byte-parity runs force CPU consensus KMeans; throughput runs may use Triton KMeans. | Control- and response-program construction |
| Response-program NNLS | `src/mantra/sota/programs/discovery/nmf_torch_batched.py::batched_nnls`; `ghost_solver.py::ghost_nnls`; `selection/response_oracle_eval.py::_nnls_coefficients` | Batched dense GPU projection and sparse Triton Ghost projection | Compare coefficients and reconstruction error with the declared CPU solver. Retain backend and iteration count. | Program selection, coefficients, and response diagnostics |
| Sinkhorn matched controls | `src/mantra/sota/control/ot_sinkhorn_gpu.py::unbalanced_sinkhorn_plan`; `ot_barycentric_controls_and_residual_mean` | Batched GPU distance, transport, barycentric control, and residual operations | Compare transport mass, marginals, cost, and residual vectors with a CPU reference within declared tolerances. | Matched-control residual response surface |
| Ridge regression | `src/mantra/utils/ridge_gpu.py::ridge_fit_predict_torch`; `ridge_predict_fixed_design_torch` | GPU Cholesky solves, automatic primal or dual form, multi-target matrix operations | Compare predictions with the NumPy reference. Retain penalty, selected form, device, dtype, and maximum error. | Grouped priors, `ctrl19`, `core83`, gene shift, and model corrections |
| Low-rank PCA and SVD | `experiments/v1938_sota_clean_repro/src/step00/family64/transforms.py::fit_pca_project_splits`; shared deterministic Torch reduction helpers | Seeded GPU low-rank factorization, device-resident projections, and stable component signs | Compare components, singular values, projections, and reconstruction with the deterministic reference under the declared sign convention. | Prior variants, `family64`, response coordinates, and model inputs |
| cNMF consensus KMeans | `src/mantra/sota/programs/discovery/cnmf.py::_stability_kmeans_labels_centers`; `src/mantra/programs/v6/kmeans_gpu.py::KMeansSingularity` | Triton assignment and center updates for throughput runs | `consensus_kmeans_backend="cpu"` and seeded scikit-learn Lloyd KMeans are mandatory for every baseline-preserving run. GPU KMeans reports throughput separately. | cNMF consensus only |
| Hopfield retrieval | `experiments/v1938_sota_clean_repro/src/step01/hopfield/model.py` and `train.py` | One initialization transfer for the complete numeric training set, full-dataset GPU-resident optimization, vectorized matrix operations, and top-k target construction and retrieval | Apply strict CUDA determinism and the historical precision policy; retain transfer counts and bytes; compare weights, predictions, checkpoints, runtime, and peak memory. | Phase 1 replay, MIL-stack bridge, and first-principles Hopfield |
| MIL proposal and routing | `experiments/v1938_sota_clean_repro/src/step02/proposal.py`; `mil_proto/routing_readout.py`; `mil_proto/objective.py` | GPU top-k, batched matrix multiplication, `einsum` donor and slot routing | Compare proposals, routing weights, and coefficient predictions with the retained arrays. | Phase 2 replay and first-principles MIL |
| MIL training | `experiments/v1938_sota_clean_repro/src/step02/mil_proto/train.py` | One initialization transfer for the complete numeric training set, GPU-resident tensors, 128-row batches selected through GPU indices, fused CUDA Adam, vectorized objectives, and effect-gene selection | Apply strict CUDA determinism; retain transfer counts and bytes; compare teacher and student checkpoints, predictions, runtime, and peak memory. | Phase 2 replay and first-principles MIL |
| Fast H5AD input | `src/mantra/utils/fast_h5_loader.py` | Direct reads of selected H5AD arrays without full Scanpy materialization | Compare selected cells, genes, values, dtypes, and order with the canonical reader before accepting the speed path. | Canonical atlas and every downstream GPU stage |

## Perturbation representation variants

The first-principles rebuild will execute only variants named in its retained
manifest. The minimum approved paths are:

1. per-prior PCA, fusion, grouped ridge, then Hopfield;
2. per-prior MLP, fusion, grouped ridge, then Hopfield;
3. unreduced prior rows, grouped ridge, then Hopfield;
4. reduced or fused prior rows directly into Hopfield, bypassing grouped ridge;
5. unreduced prior rows directly into Hopfield, bypassing both reduction and
   grouped ridge.

The manifest names every prior input, fitted transform, output dimension,
fusion rule, grouped-ridge setting, Hopfield input width, seed, and artifact
reference. The runner rejects an unlisted composition instead of silently
forming the Cartesian product of every switch.

## Held-out control-state prediction

The historical `ctrl19` path predicts a distribution over fit control-state
clusters with an MLP and decodes that distribution into a 19-value control
state for each held-out perturbation. The modular stage must retain that fitted
MLP, cluster centers, decoder, inputs, and predictions. The predicted rows feed
the control-state portion of `core83` and any declared PCA64/control-derived
features; held-out response truth may not enter fitting or selection.
