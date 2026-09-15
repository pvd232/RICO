# MANTRA Pre-Graph Matrix Charter

## Outcome

Matrix resumes at the current Phase 1 PairBlock and executes dependency-ready
work through `B9-PB-02`. The run ends with rebuilt Hopfield and MIL models,
their corrected shared inputs, one canonical benchmark comparison, and complete
VIPER and contract evidence. `B9-PB-02` is the terminal PairBlock.

## Roadmap

The checklist contains one requirement and one PairBlock for each independently
reviewable result. Plans are created only when their PairBlock becomes current.

| Phase | Contract | Requirements and PairBlocks | Result |
|---|---|---:|---|
| 1 foundation | `mantra-execution-foundation` | 11 | Durable VIPER storage, verified GPU lifecycle, and every required accelerated kernel are ready before model work. |
| 1 | `mantra-hopfield-reconstruction` | 8 | Replayed Hopfield training, predictions, and score match the retained Phase 0 result. |
| 2 | `mantra-mil-reconstruction`; `mantra-hopfield-reconstruction` | 7 | Replayed MIL training, predictions, and score match the retained Phase 0 result; the unchanged legacy Hopfield then trains on the exact retained MIL input stack and freezes a separate bridge baseline. |
| 3 | `mantra-data-foundation` | 7 | One perturbation identity table, one selected cell set, one minimal H5AD, a verified fast reader, and distinct control-2K and GEARS-5K gene panels. |
| 4 | `mantra-prior-reconstruction` | 6 | Every selected prior is rebuilt from complete pinned sources and joined to the perturbation rows. |
| 5 | `mantra-response-reconstruction` | 7 | GPU cNMF, IEG residualization, GPU Sinkhorn, sparse programs with GPU NNLS, response coordinates, and parity-verified response-block definitions form one shared target bundle. |
| 6 | `mantra-first-principles-models` | 9 | The finite prior-transform, fusion, grouped-ridge, direct-Hopfield, held-out `ctrl19`, and response-block stages produce bound model-input bundles; separate input and model-component substitution ladders preserve both frozen baselines before variants train. |
| 7 | `mantra-first-principles-models` | 5 | Hopfield construction, training, inference, diagnostics, and evaluation run as separate VIPER stages. |
| 8 | `mantra-first-principles-models` | 6 | MIL bag construction, model construction, training, inference, diagnostics, and evaluation run as separate VIPER stages. |
| 9 | `mantra-first-principles-models` | 2 | One benchmark compares both rebuilt models with the original Hopfield, Hopfield MIL-stack bridge, and original MIL baselines and freezes the pre-graph evidence. |

Phases 7 and 8 are independent consumers of the Phase 6 input bundles. Phase 9
waits for both model evaluations.

## Launch preconditions

Matrix starts only after all of these checks pass:

- the contract compiler loads the current checklist and selects the expected
  PairBlock;
- the RICO, MANTRA, and VIPER branches are clean, pushed, and equal to their
  upstream branches;
- every retained Phase 0 input resolves to its recorded byte count and SHA-256
  digest;
- the selected MANTRA environment imports VIPER and the model dependencies from
  their declared interpreter;
- each GPU worker completes an NVIDIA L4 probe that records the zone, driver,
  CUDA runtime, PyTorch version, device name, and one successful CUDA tensor
  operation; and
- a completed test run can publish its artifacts to the configured durable
  store and restore the same bytes from another workspace.

The current GCP account can run an NVIDIA L4: a live probe completed one CUDA
tensor operation on `mantra-g2-spot`. That probe used `us-central1-a`, which is
excluded from Matrix. Non-central Spot capacity and the final runtime versions
remain launch checks, not assumed facts.

## Compute allocation

Hopfield and MIL consume separate historical inputs. Their Phase 1 and Phase 2
contracts therefore begin independently. Their training PairBlocks wait for
their GPU execution guarantees. Phase 3 depends on both terminal replay records
and is the explicit join.

After that revision, Matrix uses two workers when two non-central L4 allocations
are available:

| Interval | Hopfield worker | MIL worker | Join |
|---|---|---|---|
| Phases 1 and 2 | Execute `H1-PB-02` through `H1-PB-08`, then wait | Execute `M2-PB-01` through `M2-PB-06`, then wait | `H1-PB-09` runs only after both exact replay records exist and freezes the Hopfield MIL-stack bridge. |
| Phases 3 through 6 | Execute the shared dependency chain | Tear down; no idle GPU | `S6-PB-08` replaces shared inputs one at a time; `S6-PB-09` replaces legacy model components one at a time. |
| Phases 7 and 8 | Execute the Hopfield branch | Execute the MIL branch | Phase 9 waits for both evaluations. |

Each worker gets a distinct `INSTANCE_NAME` and `SSH_HOST_ALIAS`. Both launch
through `mantra-deploy-spot.sh`; no ad hoc `gcloud compute instances create`
command is permitted. The script searches its configured non-central zones in
order, enables boot-disk auto-delete after the machine image has been restored,
and verifies that setting before returning success. Matrix deletes each worker
as soon as its durable outputs restore successfully and then verifies that the
instance and boot disk no longer exist.

VIPER may use `run_many(..., max_concurrency=2)` only for independent plans on
the same host. The two-host Hopfield/MIL split is coordinated by their contract
dependencies and retained run records, not by treating two remote machines as
one local `run_many` batch.

Each model copies its complete numeric training set to the GPU during
initialization and keeps those tensors resident through training and inference.
Hopfield optimizes the complete fit and tune tensors together. MIL preserves
its historical 128-row optimizer steps by selecting subsets with GPU indices;
resident GPU tensors supply every numeric training row. VIPER retains the frozen input
identities, device-placement report, host-to-device and device-to-host transfer
counts and bytes, runtime, peak memory, checkpoints, logs, and final artifacts.

## VIPER workspace and artifact ownership

Git owns source, specifications, and experiment history. Matrix changes the
MANTRA files under `src/mantra` directly in an isolated Git worktree, commits
the tested source revision, and never copies experimental source into a
parallel staging tree.

VIPER owns the run tree. A run keeps `spec.yaml` and `resolved.yaml` under
`experiments/<experiment>/runs/<variant>/<run-id>/`; stage outputs remain under
that run's `artifacts/<stage>/<output>/` tree. Matrix does not hand-create,
rename, or reuse those directories. A transient Spot preemption creates another
attempt for the same frozen plan. Any source, input, configuration, or variant
change creates a new plan and Git commit.

The canonical directory tree is the one documented in the
[VIPER protocol](https://github.com/pvd232/viper/blob/main/docs/reference/protocol.md)
and generated by `viper init`; MANTRA does not invent a second run layout. A
cloud object adds
only `<owner>/<workspace>/<source-revision>/` before the exact VIPER-relative
path. The path recorded in the artifact reference is therefore identical on
the local worker and in GCS.

The inspected VIPER checkout currently defaults to the repository-local
`.viper/store`. Its `viper_cloud` destination requires a `ViperCloudClient`, and
the checkout contains the client protocol but no production client
implementation. Cloud-first publication is therefore a launch prerequisite:
before the first training run, a governed cloud client must publish and restore
one probe artifact. Existing GCS sync scripts may transport raw data during
setup, but they do not substitute for VIPER's immutable artifact references.
No GPU is torn down until every accepted run record and artifact is restorable
without that GPU's boot disk.

## Variant and branch policy

Phase 1 and Phase 2 are replays, not searches. Each uses exactly one retained
historical configuration and seed. A mismatch triggers diagnosis against the
first differing producer; Matrix never changes a tolerance, seed,
hyperparameter, or input to manufacture parity.

Before either training launch, the replay records the complete numerical
recipe rather than treating “centering” or “denoising” as one operation. For
Hopfield, descriptor columns use moments fitted on the declared fit-plus-tune
rows, coefficient similarities subtract each row mean and L2-normalize, and
the configured whitened-PCA coefficient bank is smoothed over neighbors chosen
by raw-coefficient cosine similarity to supply an auxiliary posterior target
during training. The selected final retrieval still uses raw coefficient
values. For MIL, each descriptor records the rows
used to fit its column moments, and Step02 builds the configured
ridge-whitened, teacher-neighbor-smoothed memory before retrieval. These fitted
states are replay inputs and must match before an output score is interpreted.

VIPER binds every replay attempt to its source commit, resolved plan and
configuration, input digests, command, declared seeds, Python and accelerator
RNG states, determinism environment variables, locked packages, operating
system, image, CUDA stack, GPU identity, device, and dtype policy. Restarting a
preempted run reuses that identity exactly. A changed field creates a reviewed
new attempt; it cannot silently resume or inherit the prior parity claim.

Every replay, bridge run, and one-at-a-time substitution uses the parity
execution profile. Whenever that execution reaches KMeans, it uses seeded
scikit-learn Lloyd KMeans on CPU. The faster GPU KMeans implementation remains
outside the baseline-preserving chain and may run later as a named throughput
variant whose results report throughput only.

After both replays pass, `H1-PB-09` runs the parity-proven legacy Hopfield code
against the exact retained MIL input stack. The bridge changes the required
input-width binding, retrains the legacy encoder, evaluates it on the canonical
surface, and freezes the complete result. The bridge defines a new baseline
independently of the original 64-value Hopfield prediction and score. The run
retains every legacy producer and model component unchanged.

Phase 3 applies one authoritative QC policy to the raw cells: mitochondrial
percentage must be at most 15 percent and must fall within the declared
five-MAD bound, alongside the five-MAD bounds for count, detected-gene, and
top-20-gene-fraction covariates. That single pass freezes one ordered cell set
for every downstream consumer. This is MANTRA's selected policy, not a claim
that the cited best-practices example uses the same mitochondrial threshold.
The AnnData reader and `FastH5ADLoader` read the same selected file; the fast
reader becomes the execution path only after rows, columns, order, dtypes, and
values match.

Phase 4 keeps historical and corrected priors as named artifacts rather than
mixing them into a factorial model search. The corrected prior becomes the
downstream input only after source completeness, parsing, perturbation coverage,
and edge identities pass. Phase 5 produces one selected target bundle. Phase 6
executes only the finite variant manifest recorded in the contract; it does not
form an uncontrolled Cartesian product of switches.

Phase 7 rebuilds and evaluates every declared pre-graph Hopfield representation
variant. Phase 8 rebuilds the frozen MIL model against its named bundle. Phase
9 compares those outputs with the original Hopfield replay, the Hopfield
MIL-stack bridge, and the original MIL replay. Graph topology and message
passing remain outside this run.

## Perturbation identity

The raw label in the canonical split contract remains the model row key. For
example, the row stays `ALG1L` while the resolver attaches the current
`ALG1L1P` HGNC record. The identity table gives HGNC, Ensembl
gene, transcript, guide-pair, locus-type, resolution-result, and source-snapshot
values their own fields. The response-gene key remains a separate column-axis
identity.

This scheme promotes the existing
[`HgncCatalog`](../../../mantra/experiments/v1938_sota_clean_repro/src/step00/sequence_graph_composite/identifiers.py)
and follows the distinctions already established in the
[gene identifier write-up](../../../mantra/experiments/v1938_sota_clean_repro/docs/GENE_IDENTIFIER_SYSTEMS_WHITE_PAPER.md).
Those existing objects supply the complete identity mechanism.

`ALG1L` remains a perturbation row and resolves to the current pseudogene
record `ALG1L1P`. Protein-derived fields remain missing because a pseudogene
record supplies gene identity alone. The implementation decision will
be checked against the [HGNC naming guidelines](https://hgnc.genenames.org/about/guidelines/)
and [GENCODE biotype definitions](https://www.gencodegenes.org/pages/biotypes.html).

## Data and QC

Phase 3 reacquires the atlas, then builds the identity table from the pinned
atlas and authority snapshots. One QC pass combines a fixed mitochondrial
percentage at or below 15 with five-MAD outlier rules for log total counts, log
detected genes, top-20-gene count fraction, and mitochondrial percentage. The
[single-cell best-practices QC chapter](https://www.sc-best-practices.org/preprocessing-visualization/quality-control/)
supplies the MAD method; the 15 percent ceiling is the selected MANTRA policy.
The QC stage writes one ordered cell set consumed by every later builder.

The same selected cells produce two distinct gene panels. Control-program
learning applies the documented Seurat v3 highly-variable-gene procedure to an
eligible universe that excludes mitochondrial, ribosomal, globin, and core
immediate-early genes. Response learning and evaluation use the exact ordered
GEARS 5,000-gene panel and retain any immediate-early genes present because the
response target includes their induced signal. Each panel retains its selection
rule, fitted population, membership, order, and digest. Consumers use the panel
declared for their stage.

The H5AD builder retains the expression matrix, cell and perturbation identity,
mitochondrial fraction, and gene-axis identity. Every retained field must have
a named downstream consumer. Layers, embeddings, graphs, cell-cycle values,
Mixscape values, and other derived analysis state are omitted. The existing
[`FastH5ADLoader`](../../../mantra/src/mantra/utils/fast_h5_loader.py) is reused
after it matches the reference AnnData reader on the canonical file.

## Priors and response targets

Both models consume one shared biological foundation. The 2K and 5K branches
describe two feature-producing operations on the same selected training cells;
they do not create separate Hopfield and MIL datasets.

```text
canonical atlas + one QC mask
        ├── control-gene panel: HVG selection + structural/IEG exclusions
        │       └── regress IEG, cycle, library-size, and mitochondrial scores
        │               └── GPU cNMF control programs
        └── response-gene panel: exact GEARS 5,000, including present IEGs
                └── GPU Sinkhorn residuals → sparse response programs
                                                   └── response-block definitions
corrected priors + split-safe query features ──────┘
                                                   └── response_block40 rows
                                                           ├── Hopfield
                                                           └── MIL
```

The retained local artifacts confirm the shared boundary. Hopfield and MIL use
byte-identical `core83`, fit/tune truth, held-out truth, response-block
contract, and response-rotation artifacts. Their final input bundles are not
globally identical. The retained Hopfield `family64` is 64-dimensional; the
later MIL input uses a 144-dimensional five-source representation. Their
`response40` fit and tune arrays are equal, but the held-out proxy differs
because each was regenerated from its matching query representation. Those
differences belong to the named proxy and representation boundary, not to the
biological foundation or response-program definitions.

Phase 4 first inventories every prior read by the two parity models. Each
selected source then receives a VIPER download or restoration stage, a typed
ingest stage, and an observing reconstruction test. The interaction rebuild
must consume the complete pinned IntAct source and reject the known historical
prefix. The current evidence shows that prefix contains about 18 percent of the
source bytes; the corrected result must report actual edge and perturbation
coverage from the corrected parse.

The inventory keeps three levels separate: raw biological sources, transformed
prior blocks, and model-input bundles. In particular, it must account for all
eleven arrays in the retained compressed bundle: `corum`,
`depmap_essentiality`, `dorothea_grn`, `gene_family`, `mechanistic256`, `motif`,
`pathway_hallmark`, `ppi_spectral`, `ptm`, `regulatory256`, and `subcellular`.
The retained reconstruction reports and scripts are the starting recipes, not
permission to assume full raw-source parity. Each recipe records its exact,
near-equivalent, source-native, or blocked boundary before the corrected prior
is allowed into either model.

The known Hallmark exception is narrower than the response-program rotation.
The historical Hallmark builder applied a randomized 50-by-50 PCA after the
process had skipped the only seed-setting call. That full-rank transform
discarded no dimensions and only selected an unrecorded coordinate rotation.
The source-native rebuild therefore preserves the exact 50 named Hallmark
memberships in a deterministic centered basis while retaining the historical
random coordinates as provenance. The 210-dimensional response-program
rotation remains a separate artifact and must satisfy its own Phase 5 parity
gate.

Phase 5 uses the one selected cell set throughout. It regresses the
immediate-early-gene score, S-phase score, G2M-phase score, log UMI count, and
mitochondrial percentage from control-cell expression before cNMF discovers
control programs on the IEG-excluded control panel. The response branch keeps
the complete ordered GEARS 5K target panel, builds Sinkhorn matched-control
residuals, and learns a sparse response dictionary before fitting the SVD and
basis-rotation coordinates. It also reconstructs
the program-similarity graph, hard and soft block maps, and rotation that the
historical pipeline only copied. One target bundle joins those outputs for both
model branches.

The response-coordinate recipe is fixed: fit the signed sparse SVD decoder on
the declared fit-plus-tune Sinkhorn residual cells, ridge-encode all cells,
then order the 210 cell coefficients with the fit-plus-tune covariance
eigendecomposition. A second, distinct Varimax rotation acts on those response
coordinates when constructing the response-program usage graph and block maps.
Both fitted rotations, their input axes, numerical backends, and execution
state must be retained by VIPER and compared with the historical artifacts.
Copying the historical rotation files satisfies neither producer gate.

Before prior-fusion experiments, the input-substitution ladder starts Hopfield
from the frozen MIL-stack bridge and MIL from its parity-proven bundle. It
replaces the shared atlas, gene panels, control programs, response programs,
block definitions, block rows, and priors one producer at a time. Every step
keeps all other artifact digests fixed, points both models to the same rebuilt
artifact when that artifact is shared, and preserves the corresponding frozen
prediction and score.

The model-component ladder then replaces one section of each legacy training,
inference, or evaluation script with its modular owner. Each step retains the
component inputs, fitted state, outputs, and diagnostics; holds every
non-target source, configuration, and artifact digest fixed; and reproduces the
owning model's frozen prediction and score. Each replacement begins after its
predecessor passes. Prior-fusion variants train after both ladders close.

The [GPU and vectorization inventory](2026-09-15-mantra-gpu-optimization-inventory.md)
is the migration ledger for cNMF, NMF, NNLS, Sinkhorn, ridge, Hopfield, MIL,
and FastH5AD execution. A reconstruction stage cannot close until its modular
owner passes both the named reference comparison and the retained L4 benchmark.

## Model rebuild and benchmark

Phase 6 aligns every corrected prior to one perturbation table, then executes
the manifest's identity, per-prior PCA, per-prior MLP, fusion, grouped-ridge,
and direct-to-Hopfield routes. A separate auxiliary MLP predicts the held-out
`ctrl19` vector without hold-response truth; those rows feed `core83` and any
declared PCA64 control features. A separate stage reproduces the historical
40-value response-block rows: hard 16, soft semantic 16, and spectral 8. Fit
rows use direct response coefficients; tune and held-out rows use only fit rows
through the declared query features and retrieval rule. Each resulting
representation is bound to the Phase 5 target bundle by its own immutable
input-bundle digest.

Phases 7 and 8 split construction, training, inference, diagnostics, and
evaluation into replayable VIPER stages. Training and checkpoint selection
receive fit and tune responses only. Each evaluation calls the existing canonical
PearsonDelta implementation on the same ordered response surface used by the
corresponding parity run.

Phase 9 compares the original Hopfield replay, the Hopfield MIL-stack bridge,
every rebuilt Hopfield variant, the original MIL replay, and rebuilt MIL on one
surface. `B9-PB-02` closes the evidence graph and ends the run before the graph
encoder.

## Protocol precondition

`CP-PB-12` is approved and allows a checklist with bootstrap history to register
new contracts. The compiler continues to verify every contract named by the
bootstrap receipt and rejects removal of any such contract. Matrix begins only
after that approved implementation completes its remaining lifecycle evidence
and the compiler loads the expanded MANTRA checklist.

## Execution rule

The compiled checklist selects the current PairBlock. For each block, Matrix
creates its `plan.toml`, changes only declared targets in an isolated worktree,
runs the smallest sufficient gate, self-reviews the complete diff, commits and
pushes the exact tested candidate, records implementation review and required
VIPER evidence, and recompiles the checklist before selecting another block.

The invariants in the owning requirement decide implementation details that the
roadmap leaves open. Matrix first reuses an existing MANTRA or VIPER primitive,
then extends its current owner. A new abstraction enters only when the
requirement needs a distinct representation or verifier.

## Stop conditions

| Observed condition | Required response |
|---|---|
| Contract compilation selects the wrong PairBlock, rejects a registered contract, or finds stale evidence. | Stop before editing source. Repair the declaration or lifecycle record through its own reviewed PairBlock. |
| A required source is absent or differs in size or digest. | Stop that branch. Record the missing identity; do not substitute another file. |
| A perturbation, gene, cell, split, or row order differs. | Stop before the next transformation or training stage. Report the first producer that changed the identity. |
| The declared interpreter, CUDA device, or durable artifact store fails its launch probe. | Do not train. Tear down any partial VM and disk after retaining the failure output. |
| A Spot VM is preempted without changing source or configuration. | Retry the same frozen VIPER plan as a new attempt. |
| The same stage fails twice with the same input and error. | Stop the branch and report a repeatable implementation or data failure. |
| Exact parity fails. | Compare the first differing intermediate. Do not weaken equality, tune against hold data, or start a search. |
| A replay omits a fitted mean, scale, decomposition state, memory transform, or smoothing rule used by the retained model. | Stop before training and bind that state to the replay recipe and VIPER record. |
| A resumed attempt changes a seed, RNG state, input digest, source commit, command, resolved configuration, environment, accelerator, device, or dtype policy. | Refuse the resume. Start a reviewed new VIPER attempt or restore the original execution identity. |
| A replay, bridge, or substitution plan selects GPU KMeans. | Reject the plan before execution and select the seeded scikit-learn parity profile. |
| A training step loads numeric rows from the host after initialization. | Stop the run and restore full GPU residency before accepting parity or performance evidence. |
| The QC variants change different cell identities for a reason not covered by the requirements. | Stop for the user's biological-policy decision. |
| A prior omits perturbations, invents identities, or cannot trace an edge to a pinned source. | Stop before building the shared representation. |
| A PairBlock needs an undeclared target or changes an accepted invariant. | Stop and revise the requirement or plan before changing that target. |
| One independent model branch fails after `S6-PB-06`. | Stop that branch; the other branch may finish. Phase 9 waits for both. |
| `B9-PB-02` completes. | Publish the terminal evidence, tear down both workers and their disks, and stop before the graph encoder. |

Matrix reports the last completed PairBlock, the first blocked requirement, the
exact retained artifacts and commits, and the next owner decision. The run ends
at `B9-PB-02`, before the graph-encoder contract.
