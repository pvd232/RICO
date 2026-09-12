# Mantra rebuild master checklist

This file is the execution authority for the Hopfield rebuild, the standalone
MIL rebuild, and the first biologically grounded graph encoder. The owning
contracts define what each model must do. This checklist owns work order,
current status, review points, and completion evidence.

## Current focus

**Active drafting tranche:** Phase 0C, restoration planning. Phase 0B remains
the implementation gate because the MIL artifact table is incomplete.

| Actor | Next action | Result |
|---|---|---|
| Codex | Draft `P0-PB-04B`: read the signed restoration controls, resolve each approved MANTRA path to one content-addressed archive member, and test absent and duplicate mappings. | Complete proposed source and tests in the Phase 0 contract. |
| User | Review the proposed `P0-PB-04A` and `P0-PB-05A` blocks already in the Phase 0 contract. | Approved blocks or named corrections. |
| Codex and user | Code-review each approved block; the user implements it in MANTRA; Codex reviews the applied diff and gate output. | Accepted MANTRA implementation with retained evidence. |

`P0-PB-04B` and the two reviews can proceed in parallel. `P0-PB-05B` starts
after `P0-PB-04B` resolves the archive chunks required by the approved paths.

## Terminal outcome

The program closes when this path passes:

```text
restore every required MANTRA input and record graph B in VIPER
-> reproduce Hopfield PearsonDelta 0.5861640938949398
-> rebuild Hopfield preprocessing, training, retrieval, and correction
-> reproduce standalone MIL PearsonDelta 0.6025499488874759
-> rebuild standalone MIL training, retrieval, and correction
-> build and train the V1 biologically grounded graph encoder
-> pass the V1 acceptance criteria and reproduce every result from VIPER records
```

Hopfield and MIL are independent models. The checklist places MIL after
Hopfield because the user selected that execution order. The MIL input graph
excludes every Hopfield output.

## Checklist semantics

A box closes only after the user approves the proposed change, the user applies
it, Codex reviews the applied diff, the focused gate passes, Git records the
accepted increment, and VIPER records the required run evidence. A prose claim
or proposed code block remains open.

For each review cycle, Codex updates this file in the same RICO commit that
records any changed contract status. MANTRA implementation commits remain in
MANTRA. The RICO checklist cites their commit IDs and gate outputs.

## Governing sources

| Work unit | Current state | Owning phase | Completion evidence |
|---|---|---|---|
| [Phase 0 contract](../contracts/mantra-rebuild-phase-0.md) | In progress | Phase 0 | `P0-REQ-01` through `P0-REQ-09` and every mapped PairBlock close. |
| Hopfield reconstruction contract | Pending | Phase 1A | User-approved contract with exact intermediate and final parity gates. |
| Standalone MIL reconstruction contract | Pending | Phase 2A | User-approved contract with exact intermediate and final parity gates. |
| Graph encoder contract | Design complete; contract pending | Phase 3A | User-approved contract covering identity, topology, features, training, evaluation, and VIPER evidence. |

The checklist uses the Phase 0 contract stored in RICO commit `f54e35b` with
SHA-256
`8878155e391695e2e43b5e9a282427c574aa2a1235c8991af67556531df65b52`.

<!-- contract-baseline: P0 path=docs/contracts/mantra-rebuild-phase-0.md revision=f54e35b sha256=8878155e391695e2e43b5e9a282427c574aa2a1235c8991af67556531df65b52 -->

## Verified baseline

- [x] MANTRA commit `467d7d3dcdfcbcaaf40ab40a419ef89096bd465f`
      contains `viper.toml`; the Conda environment named `mantra` reports Python
      3.13.15, imports `viper-provenance` 0.1.0a3, and resolves the MANTRA Git
      root as the VIPER workspace.
- [x] The Phase 0 contract identifies the selected Hopfield result as
      `0.5861640938949398` and the standalone MIL result as
      `0.6025499488874759` for v1952 seed 123460 `without_control`.

## Phase 0 requirement assignments

This table schedules every requirement in the approved Phase 0 contract once.

| Requirement | State | Phase | Depends on | Gate |
|---|---|---|---|---|
| `P0-REQ-01` | In progress | 0B | None | The approved Hopfield and MIL portions of graph $B$ contain every required file, producer, and edge and exclude parity graph $Q$. |
| `P0-REQ-02` | Planned | 0C | `P0-REQ-01` | Every absent file in $B$ resolves through exactly one valid `RestorationBinding`. |
| `P0-REQ-03` | Planned | 0C | `P0-REQ-01` | The capacity receipt records every term in $R_{max}$ and measured free space is at least $R_{max}$. |
| `P0-REQ-04` | Planned | 0D | `P0-REQ-02`, `P0-REQ-03` | Every restored canonical file matches its approved byte count and SHA-256. |
| `P0-REQ-05` | In progress | 0D | `P0-REQ-02`, `P0-REQ-03` | Restoration runs from the MANTRA root through the verified `mantra` environment, and VIPER retains the environment receipt. |
| `P0-REQ-06` | Planned | 0D | `P0-REQ-04`, `P0-REQ-05` | VIPER verifies graph $B$; deleting one required node or edge makes verification fail. |
| `P0-REQ-07` | Planned | 0E | `P0-REQ-06` | Hopfield replay reproduces `0.5861640938949398` within the approved tolerance and retains its predictions. |
| `P0-REQ-08` | Planned | 0E | `P0-REQ-06` | Standalone v1952 seed-123460 `without_control` replay reproduces `0.6025499488874759` and the approved prediction hashes. |
| `P0-REQ-09` | Planned | 0F | `P0-REQ-07`, `P0-REQ-08` | Every assessed VIPER check has a usefulness-ledger entry and independently confirmed findings. |

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
- [ ] Approve the complete standalone MIL path for v1952 seed 123460
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
- [ ] Implement and test the signed-control reader proposed in `P0-PB-04B` so
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

## Phase 0E. Replay Hopfield and standalone MIL

**Depends on:** Phase 0D

The two replay jobs may run in parallel. Each job reads its own inputs and
produces its own predictions.

- [ ] Replay the selected Hopfield raw-gene readout and compare the generated
      predictions and score with parity graph $Q_H$.
      <!-- pair-block: P0-PB-07 -->
      <!-- pair-block-contract: P0-PB-07 contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [ ] Replay standalone v1952 seed 123460 `without_control` on the historical
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

**Gate:** `P0-VR-09` passes, the user approves the evidence set, and all nine
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

## Phase 2. Rebuild standalone MIL

**Depends on:** Phase 1C by chosen work order only

### Phase 2A. Approve the standalone MIL reconstruction contract

- [ ] Define the teacher-bag, conditioning, teacher, donor-embedding,
      single-query student, covariance-shrinkage, teacher-neighbor smoothing,
      retrieval, residual-correction, reference-shift, and gene-calibration
      artifacts.
- [ ] Bind the runtime override that creates one student query and exclude the
      dormant `proto_count: 11` value from the active architecture.
- [ ] Map every MIL PairBlock into this checklist before implementation.

**Gate:** The user approves the standalone MIL contract with exact intermediate
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

**Gate:** The standalone rebuild reproduces `PearsonDelta`
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
| Review `P0-PB-04A` and `P0-PB-05A`. | Phase 0C | MANTRA implementation of the first two proposed blocks. |
| Review `P0-PB-04B` after Codex drafts it. | Phase 0C | Signed-control resolution and complete binding records. |
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
  `f54e35b`, SHA-256
  `8878155e391695e2e43b5e9a282427c574aa2a1235c8991af67556531df65b52`.
- [Model rebuild handoff](../mantra-viper-rebuild-handoff.md).
- [Graph encoder design specification](../Biologically_Grounded_Graph_Encoder_Design_Specification.pdf),
  Part XIX and Part XX.
- [Identifier systems](../GENE_IDENTIFIER_SYSTEMS_COMPLETE_REVISED.pdf), Part 7.
