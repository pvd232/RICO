# Mantra rebuild master checklist

This file is the execution authority for the Hopfield rebuild, the MIL rebuild,
and the first biologically grounded graph encoder. The owning
contracts define what each model must do. This checklist owns work order,
current status, review points, and completion evidence.

## Table of contents

- [Current focus](#current-focus)
- [PairBlock resolution](#pairblock-resolution)
- [Terminal outcome](#terminal-outcome)
- [Checklist semantics](#checklist-semantics)
- [Governing sources](#governing-sources)
- [Verified baseline](#verified-baseline)
- [Phase 0 requirement assignments](#phase-0-requirement-assignments)
- [Phase 0A: MANTRA workspace and environment](#phase-0a-verify-the-mantra-workspace-and-environment)
- [Phase 0B: replay graphs](#phase-0b-freeze-the-two-independent-replay-graphs)
- [Phase 0C: restoration planning](#phase-0c-implement-restoration-bindings-and-capacity-planning)
- [Phase 0D: restoration and graph B](#phase-0d-restore-files-and-verify-graph-b-in-viper)
- [Phase 0E: parity replays](#phase-0e-replay-hopfield-and-mil)
- [Phase 0F: evidence freeze](#phase-0f-freeze-evidence-and-assess-viper)
- [Phase 1: Hopfield](#phase-1-rebuild-hopfield)
  - [1A: contract](#phase-1a-approve-the-hopfield-reconstruction-contract)
  - [1B: preprocessing](#phase-1b-rebuild-preprocessing-and-training-inputs)
  - [1C: encoder and readout](#phase-1c-rebuild-the-encoder-and-raw-gene-readout)
- [Phase 2: MIL](#phase-2-rebuild-mil)
  - [2A: contract](#phase-2a-approve-the-mil-reconstruction-contract)
  - [2B: teacher and student](#phase-2b-rebuild-teacher-and-student-training)
  - [2C: retrieval and correction](#phase-2c-rebuild-retrieval-and-final-correction)
- [Phase 3: graph identities and baselines](#phase-3-freeze-graph-encoder-identities-and-baselines)
- [Phase 4: topology and features](#phase-4-select-topology-and-build-v1-features)
  - [4A: topology diagnostics](#phase-4a-run-topology-diagnostics)
  - [4B: V1 features](#phase-4b-build-the-v1-feature-pipeline)
- [Phase 5: V1 graph encoder](#phase-5-train-and-evaluate-the-v1-graph-encoder)
  - [5A: first encoder](#phase-5a-train-the-first-encoder)
  - [5B: graph construction](#phase-5b-run-the-graph-construction-study)
  - [5C: V1 acceptance](#phase-5c-apply-the-v1-acceptance-gate)
- [Owner actions](#owner-actions)
- [Deferred scope](#deferred-scope)
- [Sources](#sources)

## Current focus

**Active tranche:** the user applies `P0-PB-04A`, `P0-PB-04B`, and
`P0-PB-05A` in MANTRA while Codex reviews each resulting diff. `P0-PB-10` is
applied. VIPER 0.1.0a4 is installed from the reviewed local checkout, and the
MANTRA-to-RICO local-store probe passes. `P0-PB-06` will register this evidence
and close `P0-PB-10`.

The resolution table identifies the next action. `Review` requires the user's
decision. `Approved` authorizes the user to apply the proposal. `Applied`
means Codex accepted the resulting diff, test evidence, and Git evidence.
`Complete` requires VIPER registration, the final receipt, and a checked box.

**`P0-PB-04B` inspection evidence:** Project release revision
`51cb27990244f1f418e8b7cd11cd98672d18919a` pins control revision
`a3c7405f375ba2f18f856fbfebe6480e98792df0`; both signatures verify with
`reinstantiation/CONTROL_SIGNING_PUBLIC_KEY.pem`.
The signed checksums match `ARCHIVE_INDEX.json`,
`FILESYSTEM_MANIFEST.jsonl.zst`, and the two inspected object manifests. Six
missing Hopfield inputs belong to `historical_and_shared_experiments`; the
saved encoder and historical prediction belong to `sota_reproducer`. The
`fit_tune_ctrl19_matched_log1p_cp10k_gene_deltas.npz` destination is an
absolute historical symlink whose target file carries the approved byte count
and SHA-256. The reader must resolve that link inside the historical MANTRA
root and reject links that escape it. Archive payload downloads remain at
zero. The staged resolver produced eight bindings from those controls: six
owned by `historical_and_shared_experiments` and two owned by
`sota_reproducer`.

## PairBlock resolution

| PairBlock | Proposal gate | Resolution status | Depends on | Contract declaration | Proposed code |
|---|---|---|---|---|---|
| `P0-PB-01` | Environment check passed | Applied | None | [Declaration](../contracts/mantra-rebuild-phase-0.md#p0-pb-01-declaration) | [Accepted implementation](../contracts/mantra-rebuild-phase-0.md#p0-pb-01-accepted-implementation) |
| `P0-PB-02` | Hopfield artifact table approved | Drafting | None | [Declaration](../contracts/mantra-rebuild-phase-0.md#p0-pb-02-declaration) | [Work description](../contracts/mantra-rebuild-phase-0.md#p0-pb-02-declaration) |
| `P0-PB-03` | Pending | Drafting | None | [Declaration](../contracts/mantra-rebuild-phase-0.md#p0-pb-03-declaration) | [Work description](../contracts/mantra-rebuild-phase-0.md#p0-pb-03-declaration) |
| `P0-PB-04` | Pending | Waiting for `P0-PB-04A`, `P0-PB-04B` | `P0-PB-04A`, `P0-PB-04B` | [Declaration](../contracts/mantra-rebuild-phase-0.md#p0-pb-04-declaration) | [Child blocks](../contracts/mantra-rebuild-phase-0.md#p0-pb-04-declaration) |
| `P0-PB-04A` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-04a/20260912T035904.514065Z-approve.json)) | Approved | None | [Declaration](../contracts/mantra-rebuild-phase-0.md#p0-pb-04a-declaration) | [Source and tests](../../../mantra/staging/p0-pb-04a/src/mantra/rebuild/restoration.py) · [Tests](../../../mantra/staging/p0-pb-04a/src/mantra/rebuild/tests/test_restoration.py) |
| `P0-PB-04B` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-04b/20260912T035904.710258Z-approve.json)) | Approved | None | [Declaration](../contracts/mantra-rebuild-phase-0.md#p0-pb-04b-declaration) | [Source and tests](../../../mantra/staging/p0-pb-04b/src/mantra/rebuild/restoration.py) · [Base tests](../../../mantra/staging/p0-pb-04a/src/mantra/rebuild/tests/test_restoration.py) · [Resolver tests](../../../mantra/staging/p0-pb-04b/src/mantra/rebuild/tests/test_control_resolution.py) |
| `P0-PB-05` | Pending | Waiting for `P0-PB-05A`, `P0-PB-05B` | `P0-PB-05A`, `P0-PB-05B` | [Declaration](../contracts/mantra-rebuild-phase-0.md#p0-pb-05-declaration) | [Child blocks](../contracts/mantra-rebuild-phase-0.md#p0-pb-05-declaration) |
| `P0-PB-05A` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-05a/20260912T035904.894879Z-approve.json)) | Approved | None | [Declaration](../contracts/mantra-rebuild-phase-0.md#p0-pb-05a-declaration) | [Source and tests](../../../mantra/staging/p0-pb-05a/src/mantra/rebuild/capacity.py) · [Tests](../../../mantra/staging/p0-pb-05a/src/mantra/rebuild/tests/test_capacity.py) |
| `P0-PB-05B` | Pending | Waiting for `P0-PB-04B` | `P0-PB-04B` | [Declaration](../contracts/mantra-rebuild-phase-0.md#p0-pb-05b-declaration) | Pending |
| `P0-PB-06` | Pending | Waiting for `P0-PB-04`, `P0-PB-05` | `P0-PB-04`, `P0-PB-05` | [Declaration](../contracts/mantra-rebuild-phase-0.md#p0-pb-06-declaration) | Pending |
| `P0-PB-07` | Pending | Waiting for `P0-PB-06` | `P0-PB-06` | [Declaration](../contracts/mantra-rebuild-phase-0.md#p0-pb-07-declaration) | Pending |
| `P0-PB-08` | Pending | Waiting for `P0-PB-06` | `P0-PB-06` | [Declaration](../contracts/mantra-rebuild-phase-0.md#p0-pb-08-declaration) | Pending |
| `P0-PB-09` | Pending | Waiting for `P0-PB-07`, `P0-PB-08`, `P0-PB-10` | `P0-PB-07`, `P0-PB-08`, `P0-PB-10` | [Declaration](../contracts/mantra-rebuild-phase-0.md#p0-pb-09-declaration) | Pending |
| `P0-PB-10` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-10/20260912T035542.464393Z-accept.json)) | Applied | None | [Declaration](../contracts/mantra-rebuild-phase-0.md#p0-pb-10-declaration) | [Source and tests](../contracts/mantra-rebuild-phase-0.md#p0-pb-10-proposed-code) |

## Terminal outcome

The program closes when this path passes:

```text
restore every required MANTRA input and record graph B in VIPER
-> reproduce Hopfield PearsonDelta 0.5861640938949398
-> rebuild Hopfield preprocessing, training, retrieval, and correction
-> reproduce MIL PearsonDelta 0.6025499488874759
-> rebuild MIL training, retrieval, and correction
-> build and train the V1 biologically grounded graph encoder
-> pass the V1 acceptance criteria and reproduce every result from VIPER records
```

The MIL input graph excludes every Hopfield output.

## Checklist semantics

A box closes only after the user approves the proposed change, the user applies
it, Codex reviews the applied diff, the focused gate passes, Git records the
accepted increment, and VIPER records the required run evidence. A prose claim
or proposed code block remains open.

The PairBlock resolution row is the source of its lifecycle stage. One linked
receipt supports each transition. The RICO profile derives the checkbox,
requirement state, dependent-block readiness, and contract state from those
rows, then invokes the global master-checklist validator. A passing proposal
gate advances `Drafting` to `Review`. User approval advances `Review` to
`Approved`; acceptance of the applied diff, tests, and Git evidence advances
`Approved` to `Applied`; VIPER registration advances `Applied` to `Complete`.
A failed gate or illegal transition preserves the checklist.

For each review cycle, Codex updates this file in the same RICO commit that
records any changed contract status. MANTRA implementation commits remain in
MANTRA. The RICO checklist cites their commit IDs and gate outputs.

An approved review cycle closes before the next cycle begins. Codex runs the
focused checks, commits only that cycle's owned paths, and pushes when the
repository has a configured upstream. A repository whose upstream is
unavailable closes the local cycle at the local commit and leaves publication
blocked.

A task-created branch closes before its PairBlock closes. The owning
repository's default branch must contain the accepted commit, the configured
upstream must identify the same default-branch commit, and no worktree may
retain the task branch. Codex then removes that merged local branch. This gate
applies only to branches and worktrees created for this rebuild.

## Governing sources

| Work unit | Current state | Owning phase | Completion evidence |
|---|---|---|---|
| [Phase 0 contract](../contracts/mantra-rebuild-phase-0.md) | In progress | Phase 0 | `P0-REQ-01` through `P0-REQ-10` and every mapped PairBlock close. |
| Hopfield reconstruction contract | Pending | Phase 1A | User-approved contract with exact intermediate and final parity gates. |
| MIL reconstruction contract | Pending | Phase 2A | User-approved contract with exact intermediate and final parity gates. |
| Graph encoder contract | Design complete; contract pending | Phase 3A | User-approved contract covering identity, topology, features, training, evaluation, and VIPER evidence. |

The checklist uses the Phase 0 contract stored in RICO commit `d0f2d07` with
SHA-256
`40f1396fc531acaabe61957ca182ad2ab5af4e45d2fa157e526ee5bf307189de`.

<!-- contract-baseline: P0 path=docs/contracts/mantra-rebuild-phase-0.md revision=d0f2d07 sha256=40f1396fc531acaabe61957ca182ad2ab5af4e45d2fa157e526ee5bf307189de -->

## Verified baseline

- [x] MANTRA commit `467d7d3dcdfcbcaaf40ab40a419ef89096bd465f`
      contains `viper.toml`; the Conda environment named `mantra` reports Python
      3.13.15, imports `viper-provenance` 0.1.0a3, and resolves the MANTRA Git
      root as the VIPER workspace.
- [x] The Phase 0 contract identifies the selected Hopfield result as
      `0.5861640938949398` and the MIL result as
      `0.6025499488874759` for v1952 seed 123460 `without_control`.

## Phase 0 requirement assignments

This table schedules every requirement in the approved Phase 0 contract once.

| Requirement | State | Phase | Depends on | Gate |
|---|---|---|---|---|
| `P0-REQ-01` | In progress | 0B | None | The approved Hopfield and MIL portions of graph $B$ contain every required file, producer, and edge and exclude parity graph $Q$. |
| `P0-REQ-02` | In progress | 0C | `P0-REQ-01` | Every absent file in $B$ resolves through exactly one valid `RestorationBinding`. |
| `P0-REQ-03` | In progress | 0C | `P0-REQ-01` | The capacity receipt records every term in $R_{max}$ and measured free space is at least $R_{max}$. |
| `P0-REQ-04` | Planned | 0D | `P0-REQ-02`, `P0-REQ-03` | Every restored canonical file matches its approved byte count and SHA-256. |
| `P0-REQ-05` | In progress | 0D | `P0-REQ-02`, `P0-REQ-03` | Restoration runs from the MANTRA root through the verified `mantra` environment, and VIPER retains the environment receipt. |
| `P0-REQ-06` | Planned | 0D | `P0-REQ-04`, `P0-REQ-05` | VIPER verifies graph $B$; deleting one required node or edge makes verification fail. |
| `P0-REQ-07` | Planned | 0E | `P0-REQ-06` | Hopfield replay reproduces `0.5861640938949398` within the approved tolerance and retains its predictions. |
| `P0-REQ-08` | Planned | 0E | `P0-REQ-06` | Standalone v1952 seed-123460 `without_control` replay reproduces `0.6025499488874759` and the approved prediction hashes. |
| `P0-REQ-09` | Planned | 0F | `P0-REQ-07`, `P0-REQ-08` | Every assessed VIPER check has a usefulness-ledger entry and independently confirmed findings. |
| `P0-REQ-10` | In progress | 0C | None | A declared proposal gate retains its result and applies only its legal checklist transition; traceability validation rejects broken IDs, dependencies, owners, code links, tests, or gates. |

## Phase 0A. Verify the MANTRA workspace and environment

**Owned contract:** [Phase 0 contract](../contracts/mantra-rebuild-phase-0.md)

- [x] Mark the MANTRA Git root with `viper.toml` and verify the Conda
      environment named `mantra`.

**Evidence:** MANTRA commit
`467d7d3dcdfcbcaaf40ab40a419ef89096bd465f`; observed Python 3.13.15,
`viper-provenance` 0.1.0a3, installed module path, and resolved MANTRA root.
The environment receipt enters VIPER during Phase 0D. That registration closes
`P0-PB-01`.

## Phase 0B. Freeze the two independent replay graphs

**Depends on:** the verified workspace and environment baseline

- [ ] Approve the complete Hopfield path from its eleven data inputs and saved
      encoder to the selected raw-gene prediction.
      <!-- pair-block: P0-PB-02 -->
      <!-- pair-block-contract: P0-PB-02 contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [ ] Approve the complete MIL path for v1952 seed 123460
      `without_control`, excluding every Hopfield output from its inputs.
      <!-- pair-block: P0-PB-03 -->
      <!-- pair-block-contract: P0-PB-03 contract=docs/contracts/mantra-rebuild-phase-0.md -->

**Gate:** Review the graph tables and source traces in the Phase 0 contract;
then confirm that each required file and producer reaches its selected output.
The Hopfield artifact table is approved. The MIL artifact table remains open.

**Commit boundary:** Commit the approved MIL artifact table and both graph
definitions in RICO.

## Phase 0C. Implement restoration bindings and capacity planning

**Depends on:** Phase 0B

- [ ] Implement and test the strict `RestorationBinding` value type proposed in
      `P0-PB-04A`.
      <!-- pair-block: P0-PB-04A -->
      <!-- pair-block-contract: P0-PB-04A contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [ ] Implement and test the control-record resolver proposed in `P0-PB-04B` so
      one approved MANTRA path resolves to one archive member.
      <!-- pair-block: P0-PB-04B -->
      <!-- pair-block-contract: P0-PB-04B contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [ ] Validate one binding record for every absent file in graph $B$.
      <!-- pair-block: P0-PB-04 -->
      <!-- pair-block-contract: P0-PB-04 contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [ ] Implement and test the `CapacityPlan` and `CapacityReceipt` proposed in
      `P0-PB-05A`.
      <!-- pair-block: P0-PB-05A -->
      <!-- pair-block-contract: P0-PB-05A contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [ ] Produce the ordered archive-chunk plan in `P0-PB-05B` and obtain the
      user's approval for cache retention and deletion timing.
      <!-- pair-block: P0-PB-05B -->
      <!-- pair-block-contract: P0-PB-05B contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [ ] Measure free space and save a passing capacity receipt before download.
      <!-- pair-block: P0-PB-05 -->
      <!-- pair-block-contract: P0-PB-05 contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [ ] Review and activate the `P0-PB-10` proposal-gate runner.
      <!-- pair-block: P0-PB-10 -->
      <!-- pair-block-contract: P0-PB-10 contract=docs/contracts/mantra-rebuild-phase-0.md -->

**Gate:** In the MANTRA environment, run the restoration and capacity test
modules. The tests must reject malformed paths, identities, duplicate or absent
control mappings, and insufficient free space.

```bash
conda run -n mantra python -m pytest \
  src/mantra/rebuild/tests/test_restoration.py \
  src/mantra/rebuild/tests/test_capacity.py -q
```

**Commit boundaries:** Commit the reviewed binding reader and tests first.
Commit the reviewed capacity calculator, bindings, and approved download plan
after the full Phase 0 artifact set is known.

## Phase 0D. Restore files and verify graph B in VIPER

**Depends on:** Phase 0C

- [ ] Restore only the approved archive members to their canonical MANTRA
      paths, verify their bytes, and persist restoration receipts.
- [ ] Run restoration from the MANTRA root through the Conda environment named
      `mantra` and register the environment receipt in VIPER.
      <!-- pair-block: P0-PB-01 -->
      <!-- pair-block-contract: P0-PB-01 contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [ ] Register graph $B$, the environment receipt, the capacity receipt, and
      every restoration receipt in VIPER.
- [ ] Verify the complete graph and demonstrate failure after removing one
      required node or edge.
      <!-- pair-block: P0-PB-06 -->
      <!-- pair-block-contract: P0-PB-06 contract=docs/contracts/mantra-rebuild-phase-0.md -->

**Gate:** `P0-VR-04` and `P0-VR-06` pass against the restored MANTRA checkout.

**Commit boundary:** Commit the MANTRA restoration code and checked-in receipts
after the focused tests and graph rejection test pass.

## Phase 0E. Replay Hopfield and MIL

**Depends on:** Phase 0D

- [ ] Replay the selected Hopfield raw-gene readout and compare the generated
      predictions and score with parity graph $Q_H$.
      <!-- pair-block: P0-PB-07 -->
      <!-- pair-block-contract: P0-PB-07 contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [ ] Replay v1952 seed 123460 `without_control` on the historical
      L4-class environment and compare its output with the approved MIL parity
      references.
      <!-- pair-block: P0-PB-08 -->
      <!-- pair-block-contract: P0-PB-08 contract=docs/contracts/mantra-rebuild-phase-0.md -->

**Gate:** `P0-VR-07` and `P0-VR-08` pass. Both primary run logs expose
intermediate scoring events while each job runs.

**Commit boundary:** Commit each replay adapter and receipt after its independent
gate passes.

## Phase 0F. Freeze evidence and assess VIPER

**Depends on:** Phase 0E

- [ ] Complete the VIPER usefulness ledger, register every Phase 0 evidence
      artifact, and obtain the user's approval to begin reconstruction.
      <!-- pair-block: P0-PB-09 -->
      <!-- pair-block-contract: P0-PB-09 contract=docs/contracts/mantra-rebuild-phase-0.md -->

**Gate:** `P0-VR-09` passes, the user approves the evidence set, and all ten
Phase 0 requirements are complete.

**Commit boundary:** Update the Phase 0 contract status and this checklist in
RICO; record the closing RICO and MANTRA commit IDs in VIPER.

## Phase 1. Rebuild Hopfield

**Depends on:** Phase 0F

### Phase 1A. Approve the Hopfield reconstruction contract

- [ ] Define exact identities, shapes, row and column orders, fitting
      populations, normalization statistics, and intermediate parity arrays for
      matched controls, control programs, response representations, biological
      descriptors, predicted control state, response summaries, and reference
      shifts.
- [ ] Define gates for the 187 -> 384 -> 384 -> 128 encoder, its KL objectives,
      raw-gene retrieval at temperature 0.055, and final PearsonDelta
      `0.5861640938949398`.
- [ ] Divide the contract into reviewable PairBlocks and map each PairBlock into
      this checklist before implementation.

**Gate:** The user approves the Hopfield reconstruction contract and every
intermediate comparison has a named producer, persisted artifact, tolerance,
and observing test.

### Phase 1B. Rebuild preprocessing and training inputs

- [ ] Rebuild each preprocessing artifact in dependency order and compare its
      ordered identities and numerical values with the historical artifact.
- [ ] Register each producer, input, output, comparison, and failed attempt in
      VIPER.

**Gate:** Every approved preprocessing parity test passes before encoder
training begins.

### Phase 1C. Rebuild the encoder and raw-gene readout

- [ ] Train the encoder under the approved historical objective and retain its
      checkpoints, logs, selection scores, and VIPER graph.
- [ ] Run raw-gene retrieval and the reference correction; compare intermediate
      arrays before evaluating the final score.

**Gate:** The rebuilt Hopfield path passes every intermediate tolerance and the
final `PearsonDelta` gate.

## Phase 2. Rebuild MIL

**Depends on:** Phase 1C

### Phase 2A. Approve the MIL reconstruction contract

- [ ] Define the teacher-bag, conditioning, teacher, donor-embedding,
      single-query student, covariance-shrinkage, teacher-neighbor smoothing,
      retrieval, residual-correction, reference-shift, and gene-calibration
      artifacts.
- [ ] Bind the runtime override that creates one student query and exclude the
      dormant `proto_count: 11` value from the active architecture.
- [ ] Map every MIL PairBlock into this checklist before implementation.

**Gate:** The user approves the MIL contract with exact intermediate
artifacts, tolerances, and tests.

### Phase 2B. Rebuild teacher and student training

- [ ] Rebuild teacher bags and conditioning, train the teacher, persist donor
      embeddings, and train the single-query student for seed 123460.
- [ ] Emit every selection score and checkpoint decision to stdout and the
      experiment's primary log; register the resulting evidence in VIPER.

**Gate:** Approved teacher and student intermediate comparisons pass.

### Phase 2C. Rebuild retrieval and final correction

- [ ] Rebuild covariance shrinkage, teacher-neighbor smoothing, retrieval,
      residual correction, reference shift, and per-gene calibration.
- [ ] Compare each intermediate array before evaluating the final prediction.

**Gate:** The MIL rebuild reproduces `PearsonDelta`
`0.6025499488874759` and all approved prediction-array identities or numerical
tolerances.

## Phase 3. Freeze graph-encoder identities and baselines

**Depends on:** Phase 2C

The graph-encoder design begins with two distinct ordered types:
`PerturbationRowKey` identifies intervention rows in split order, and
`ResponseColumnKey` identifies the 5,000 resolved response-gene columns. The
graph contract must preserve both types and their source releases.

- [ ] Approve the graph-encoder contract for all 2,057 perturbations, the 5,000
      response columns, train/tune/hold memberships, response-target
      computation, and held-out-data exclusion.
- [ ] Reproduce and freeze the corrected ridge and fusion-only baselines on the
      same evaluation surface.
- [ ] Register identity records, manifests, producer commands, splits,
      baselines, and checks in VIPER.

**Gate:** Every required perturbation and response column has one ordered,
typed identity; baseline artifacts reproduce from their recorded inputs.

## Phase 4. Select topology and build V1 features

**Depends on:** Phase 3

### Phase 4A. Run topology diagnostics

- [ ] Build the PPI, regulatory, and signaling graph candidates with edge
      provenance.
- [ ] Measure perturbation coverage, response coverage, response mass by
      message-passing depth, top-K differentially expressed gene recall, graph
      density, and per-perturbation failure modes.

**Gate:** The topology report identifies which perturbations and response genes
each graph can reach and supplies the evidence needed to choose message depth.

### Phase 4B. Build the V1 feature pipeline

- [ ] Validate AlphaGenome feature artifacts, define gene-level aggregation,
      normalize each modality, and train the fusion-only baseline.
- [ ] Reject missing graph nodes, invalid feature rows, and collapsed fused
      embeddings before graph training.

**Gate:** Every graph node has an approved feature row and the fusion-only
baseline passes its frozen evaluation command.

## Phase 5. Train and evaluate the V1 graph encoder

**Depends on:** Phase 4

### Phase 5A. Train the first encoder

- [ ] Build the binary PPI graph, run one-hop mean aggregation, gather the
      perturbation rows, and replace the legacy student identity at every
      inference-time consumer.
- [ ] Train end to end under the unchanged downstream objective and retain all
      inputs, checkpoints, logs, predictions, metrics, and VIPER relationships.

**Gate:** All 2,057 perturbations receive valid, non-collapsed embeddings; hold
response data remain excluded from graph construction and node features.

### Phase 5B. Run the graph-construction study

- [ ] Union candidate edges from the approved priors, retain each edge's
      provenance, rank unique neighbors by AlphaGenome cosine similarity, and
      sweep top-K under the same topology and evaluation gates.
- [ ] Select graph construction and message depth using tune data only.

**Gate:** The topology report explains the selected graph and depth; the held
evaluation remains untouched until selection is frozen.

### Phase 5C. Apply the V1 acceptance gate

- [ ] Confirm that the graph encoder beats fusion-only on at least one primary
      unseen-perturbation metric and is competitive with or better than the
      corrected ridge baseline.
- [ ] Reproduce the selected result from resolved VIPER records.

**Gate:** Every V1 acceptance criterion in Part XX of the graph-encoder design
specification passes.

## Owner actions

| Owner action | First consumer | Result unlocked |
|---|---|---|
| Review [`P0-PB-04A`](../contracts/mantra-rebuild-phase-0.md#p0-pb-04a-declaration) and [`P0-PB-05A`](../contracts/mantra-rebuild-phase-0.md#p0-pb-05a-declaration). | Phase 0C | MANTRA implementation of the first two proposed blocks. |
| Review [`P0-PB-04B`](../contracts/mantra-rebuild-phase-0.md#p0-pb-04b-declaration) after Codex drafts it. | Phase 0C | Signed-control resolution and complete binding records. |
| Approve cache deletion timing and the archive download plan. | Phase 0C | First archive download. |
| Provide or authorize the L4-class execution environment if local replay fails the historical gate. | Phase 0E | Acceptance-level MIL replay and later training runs. |
| Approve each reconstruction contract and its PairBlocks. | Phases 1A, 2A, and 3 | Implementation of each model generation. |

## Deferred scope

| Item | Scope basis |
|---|---|
| CPU-only MIL acceptance | The historical acceptance run used an L4-class CUDA environment. A CPU portability probe measures feasibility only. |
| Relation-specific message passing | V2 begins after V1 passes. |
| Learned edge weights | V3 begins after V2 establishes a comparison baseline. |
| Perturbation-conditioned node selection | V4 begins after the earlier graph versions establish its necessity. |

## Sources

- [Phase 0 contract](../contracts/mantra-rebuild-phase-0.md), RICO commit
  `9227c62`, SHA-256
  `2b8d94c50b78ab6737de5b791c8e5c2e5c8813e327de165d505ba3e46afdbeb5`.
- [Model rebuild handoff](../mantra-viper-rebuild-handoff.md).
- [Graph encoder design specification](../Biologically_Grounded_Graph_Encoder_Design_Specification.pdf),
  Part XIX and Part XX.
- [Identifier systems](../GENE_IDENTIFIER_SYSTEMS_COMPLETE_REVISED.pdf), Part 7.
