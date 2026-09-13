# Phase 0 completion and model-rebuild briefing

**Date:** September 12, 2026  
**Reporting window:** From acceptance of `P0-PB-05B` through Phase 0 closure  
**Repositories:** RICO, MANTRA, and VIPER

The next action is to draft and review the Phase 1 Hopfield reconstruction
contract. That contract must name each historical intermediate, its producer,
its ordered rows and columns, its numerical tolerance, and the test that will
compare it with the rebuilt value before any new training code is accepted.

## Contents

- [Executive result](#executive-result)
- [Project boundary](#project-boundary)
- [What changed since the earlier briefing](#what-changed-since-the-earlier-briefing)
- [The completed Phase 0 execution](#the-completed-phase-0-execution)
- [VIPER assessment and repairs](#viper-assessment-and-repairs)
- [Contract, review, and Git closure](#contract-review-and-git-closure)
- [Current position in the full program](#current-position-in-the-full-program)
- [Immediate Phase 1 tranche](#immediate-phase-1-tranche)
- [Open risks and decisions](#open-risks-and-decisions)
- [Source record](#source-record)

## Executive result

Phase 0 is complete. Its purpose was to establish a trustworthy historical
oracle before reconstructing either model. The completed work now supports five
claims:

1. The approved historical artifact set is present and byte-identified. The
   restored-disk receipt contains 27 files totaling 811,130,091 bytes. Each row
   records the MANTRA destination, output name, byte count, and SHA-256 digest.
   See the [disk-import receipt](../../evidence/phase0/mantra/disk_import_receipt.json).
2. The selected Hopfield application reproduces the exact reported
   `hold_PearsonDelta` of `0.5861640938949398`. The replay used the saved
   encoder, the fit-only donor memory, raw-gene retrieval temperature `0.055`,
   and 1,427 effective donors. Its 38,397,104-byte prediction file has SHA-256
   `d7180c4669a11b0b2fb184814aafb48ebafe75b02e4bd07998c337aa64dc59b7`.
   See the [Hopfield replay receipt](../../evidence/phase0/mantra/hopfield_replay_receipt.json).
3. The standalone MIL application reproduces the exact final
   `hold_PearsonDelta` of `0.6025499488874759`. Its Step 02 score is
   `0.5924883417873266`, and all four checked Step 02 and Step 03 prediction and
   weight arrays match their reference SHA-256 identities. See the
   [MIL replay receipt](../../evidence/phase0/mantra/mil_replay_receipt.json).
4. VIPER connects restoration, Hopfield replay, MIL replay, and the final RICO
   evidence registration. The graph verifier also rejects one severed input
   edge and one severed output edge. See the
   [graph receipt](../../evidence/phase0/mantra/viper_graph_receipt.json) and
   [dependency graph](../../evidence/phase0/dependency_graph.json).
5. The master checklist resolves all 29 Phase 0 PairBlocks, all 25 Phase 0
   requirements, and the Phase 0 contract to `Complete`. Four early blocks use
   explicit compatibility certifications because their accepted work predates
   the final lifecycle-receipt protocol. See the
   [master checklist](../checklists/mantra-rebuild.md#current-focus).

The result is an application-replay baseline. It proves that we can retrieve
the historical bytes, execute the selected applications, reproduce their final
outputs, and preserve their lineage. Phase 1 remains responsible for rebuilding
the Hopfield preprocessing and training path from its declared sources.

## Project boundary

Three repositories have distinct responsibilities:

| Repository | Responsibility now | Responsibility after Phase 0 |
|---|---|---|
| MANTRA | Historical source, restored artifacts, exact Hopfield replay, exact standalone MIL replay | Read-only historical oracle except for a narrowly approved diagnostic or replay repair |
| RICO | Contracts, checklist, review records, frozen Phase 0 evidence, terminal evidence registration | All reconstructed model source, tests, model contracts, and graph-encoder work |
| VIPER | Experiment declarations, execution, artifact custody, measurements, graph verification | External provenance library used by every reconstructed pipeline |

This boundary keeps the historical implementation separate from the new one.
The Hopfield and MIL models are also independent. MIL's input set contains its
own checkpoint, memory, correction artifacts, and parity references and ends
before the Hopfield output boundary. The checklist places MIL after Hopfield to
preserve one focused reconstruction and review cycle at a time. That ordering
is a work-scheduling decision; the two model graphs remain independent. The
boundary and target identities are defined in the
[model-rebuild handoff](../mantra-viper-rebuild-handoff.md).

## What changed since the earlier briefing

This reporting window begins with the accepted archive-planning block at RICO
commit `fa38ed5` and MANTRA commit `3ea3a04`. Work before that point appears
only where it explains a later decision.

### 1. The restoration plan became executable

`P0-PB-05B` converted the signed archive controls into an ordered archive plan.
The initial local strategy streamed remote archive parts and extracted only the
required objects. The available restored compute disk provided a faster source
of the exact files, so `P0-PB-06` added a disk-import path while preserving the
same approved destination and digest checks.

The final capacity receipt records 52,620,079,104 free bytes and 1,853,986,370
required bytes. The requirement includes 1,622,260,182 bytes for VIPER custody,
221,240,428 temporary bytes, and a 10 MiB reserve. The receipt checks the actual
storage operation. The 34-part download remains a planning fallback. See the
[capacity receipt](../../evidence/phase0/mantra/capacity_receipt.json).

MANTRA gained the archive plan, archive restoration, VIPER restoration stages,
artifact loaders, and focused tests. The relevant accepted source begins at
[archive_plan.py](../../../mantra/src/mantra/rebuild/archive_plan.py) and
[viper_restore.py](../../../mantra/src/mantra/rebuild/viper_restore.py).
Generated historical environments were also removed from Git tracking and
covered by the repository ignore rules at MANTRA commit `75eae7f3e`.

### 2. Hopfield replay became a two-stage provenance graph

The replay adapter separates prediction from evaluation:

```text
saved encoder + eleven model data inputs + frozen configuration
                            |
                            v
                      predict stage
                            |
                  predictions + attention
                            |
                 hold truth + parity report
                            |
                            v
                     evaluate stage
                            |
                            v
                   parity receipt and score
```

The split matters because the generated prediction is now a named artifact
consumed by a separate evaluation stage. The named prediction bytes remain
distinct from the scalar score. The accepted implementation lives in
[hopfield_replay.py](../../../mantra/src/mantra/rebuild/hopfield_replay.py), and
its observing tests live in
[test_hopfield_replay.py](../../../mantra/src/mantra/rebuild/tests/test_hopfield_replay.py).

### 3. MIL replay became its own two-stage provenance graph

The MIL adapter applies the selected v1952 seed-123460 `without_control`
configuration, emits Step 02 and Step 03 arrays, and evaluates those arrays
against the four historical parity references. Its graph remains separate from
the Hopfield graph. The accepted implementation is
[mil_replay.py](../../../mantra/src/mantra/rebuild/mil_replay.py), with checks in
[test_mil_replay.py](../../../mantra/src/mantra/rebuild/tests/test_mil_replay.py).

### 4. The restored files became prior-run inputs

The restoration run publishes each verified disk file as a named VIPER output.
The replay runs then consume those outputs through stored-input references. This
replaced a decorative file list with executable producer-to-consumer edges. The
completed graph contains 27 restoration data edges and three verified MANTRA
runs:

| Run | Run ID | Result SHA-256 |
|---|---|---|
| Restoration | `01M2C319YF5PN1G8DN2YGEAQ4K` | `82a5072ebc688dd009e69c6d17d908f4aa4ac2f7fb9f1f1559ec70fe1563625c` |
| Hopfield | `01M2C3JFXQ2D8A0VB84R5493EY` | `e6482dd72beee7010afcec9292e98c0fd71d6f9d823c9add901a8d2d553ac1b1` |
| MIL | `01M2C3SVNE98XZ0D8S4CZJ64T8` | `cd47771ce8c35c205cb23b0dec4147538916653c1c37e3bb0aaef96456463f5a` |

The [graph-completeness report](../../evidence/phase0/mantra/graph_completeness_report.json)
retains each stage implementation identity, declared input, declared output,
pointer, producer run, and data role.

### 5. Phase 0 evidence became one frozen, registered result

RICO gained an evidence freezer and a terminal registration program. The
freezer hashes the required receipts and graph artifacts into
[index.json](../../evidence/phase0/index.json). The registration program consumes
those frozen entries, runs their loaders, and publishes the terminal receipt.
Its self-contained JSON loader is in
[artifact_loaders.py](../../tools/artifact_loaders.py); this separation is
required because VIPER executes an artifact loader in a disposable workspace
containing the loader's frozen source.

The terminal RICO-rooted run has ID `01M2C9563W9TQWT67RBRCG6YD2`. It completed
successfully in 283.833269 seconds and produced resolved-run SHA-256
`f291dc0c12259b52305dd6b0cee966c1cf9a2d910a2c830bd08d5c62fcb16e12`.
Its registration receipt binds 11 Phase 0 evidence artifacts and the VIPER
usefulness ledger. See the
[run record](../../evidence/phase0/rico/phase0_registration_run.json) and
[terminal receipt](../../evidence/phase0/rico/phase0_registration_receipt.json).

### 6. The lifecycle protocol gained a compatibility-certification path

Four accepted blocks predated the final receipt chain:

- `P0-PB-01` predates lifecycle-receipt creation.
- `P0-PB-04A` and `P0-PB-05A` lacked the predecessor pointer introduced later.
- `P0-PB-04B` used superseded lifecycle labels.

`P0-PB-10A` adds one narrow `certify` event. The profile names those four
PairBlock IDs explicitly. The controller requires an `artifact` evidence kind,
a written reason, an existing repository-relative artifact, and a revision
equal to that artifact's current SHA-256. The validator recomputes the same
conditions. Version-1 receipts retain their original schema; compatibility
certificates use schema version 2.

Each certificate points to the terminal Phase 0 registration receipt at digest
`e030e4fbc538e03e41fe03ae7ab3de2508366d4316a7b5055abac264a184ceee`.
The exact records are linked from the
[PairBlock resolution table](../checklists/mantra-rebuild.md#pairblock-resolution).
The implementation is in
[profile.py](../../tools/pairblock_status/profile.py),
[pairblock_controller.py](../../tools/pairblock_status/pairblock_controller.py),
and [checklist_profile.py](../../tools/pairblock_status/checklist_profile.py).

### 7. Compute policy became explicit

Local execution owns source inspection, hashing, focused tests, and lightweight
inference. L4-class execution owns acceptance-level historical replay, training,
embedding generation, large matrix operations, and repeated sweeps. The Spot
deployment script now marks a disposable boot disk for automatic deletion
because the image remains the durable machine template. See
[mantra-deploy-spot.sh](../../mantra-deploy-spot.sh).

## The completed Phase 0 execution

### Artifact custody

The disk-import run checked 27 approved files. They cover the Hopfield encoder,
Hopfield training and evaluation arrays, response-program artifacts, the
historical Hopfield parity prediction, the independent MIL input arrays, the
selected MIL identity vector, and four MIL parity arrays. The total byte count
is 811,130,091. The receipt assigns one output name to each destination and
binds it to its byte count and SHA-256.

The restoration stage then wrote these files into VIPER's run-owned artifact
locations. The stage-access receipt records 57 reads and 30 writes for that
stage. The Hopfield prediction and evaluation stages record 14 and 4 reads,
respectively. The MIL application and evaluation stages record 24 and 12 reads,
respectively. See the
[stage-access receipt](../../evidence/phase0/mantra/stage_file_access_receipt.json).

### Hopfield parity

The selected historical configuration is
`mixed_src_snk_ripple_raw_pen1_base_lr2e4`. The replay requested 1,600 donors,
used all 1,427 fit donors available, applied `family64_scale=1.3`, and retrieved
raw-gene responses at temperature `0.055`. The measured score equals the target
within the declared `1e-10` tolerance. The prediction digest also equals the
historical reference digest.

This result fixes the historical application surface for Phase 1. Reconstructed
matched-control fitting, response programs, descriptor assembly, encoder
training, and checkpoint selection remain untested.

### MIL parity

The standalone MIL replay emitted and checked:

| Artifact | SHA-256 |
|---|---|
| Step 02 predictions | `c0011d71436c540bde8dd00f9e2f8ac8fb46aa787161460a1aefce5f0f1277be` |
| Step 02 weights | `8290145991446afd9f45c3f3be1ad7fe95518dfe6f75e1e950b86a2b84c323ab` |
| Step 03 predictions | `e39230c8c17954602a2c3dbfc26ed4759922be36bdabc6b27ffb96204a07f7fd` |
| Step 03 weights | `372e4409468d7d0441383833601d2a008ab24fd309ae4cd6fb2ebaa36e1dd3f0` |

All four byte identities passed. Step 03 improved the recorded Step 02 score
from `0.5924883417873266` to `0.6025499488874759`. This baseline will later
separate teacher/student reconstruction errors from retrieval, residual
correction, reference shift, and per-gene calibration errors.

### Graph rejection evidence

The accepted graph passed normal verification. The severed-edge checks then
removed one required restoration input and one selected output relationship.
VIPER rejected both altered graphs. This provides direct evidence that the
saved graph depends on the declared connector. A descriptive artifact list
lacks this failure behavior.

## VIPER assessment and repairs

Real restoration and replay runs exposed ten framework or implementation
issues. The [VIPER usefulness ledger](../../evidence/viper-usefulness-ledger.json)
records the claim, observed result, independent check, ordinary-test
equivalent, cost, repair, and later reuse for each one.

| Finding | What the real execution exposed | Repair and retained guarantee |
|---|---|---|
| Cross-workspace prior-run retrieval | A RICO consumer compiled a MANTRA reference, then searched RICO's store for the producer artifact. | A local reference now carries the producer workspace and store identities. RICO can retrieve the exact MANTRA bytes and retain the producing run. |
| Declared stage file access | A stage graph listed paths while ordinary Python code could open a different workspace file. | Opt-in `file_access="declared"` observes successful CPython-visible opens, rejects undeclared opens and writes, and retains the observed paths. It also rejects threads, subprocesses, and directory changes that would escape this observer. |
| Unbenchmarked result selection | The verifier required every selected model artifact to come from a training stage and rejected a valid replay receipt as a terminal result. | An unbenchmarked run may select a build-produced model or another declared stage artifact. Benchmarked model selection retains the training-stage requirement. |
| Failed-attempt finalization | A loader-verification error triggered an immutable-publication error that hid the first failure. | Result verification now replaces the provisional attempt with one failed attempt that preserves the originating verification error. |
| Stored-input namespace timing | The `inputs/` custody boundary was valid; enforcement occurred after an expensive prediction completed. | Stored-input paths are validated while the plan is authored, before stage execution or pointer publication. |
| Repeated producer verification | Multiple pointers to one producer caused the same producer run to be verified repeatedly. | One verification pass memoizes the exact producer result by `ResolvedRunRef`; each pointer still receives its own artifact check. |
| Repeated external Git retrieval | Each exact source file caused another temporary repository and fetch of the same immutable commit. | One execution reuses a verified checkout for each repository-and-commit pair and retains up to 64 MiB of exact file bytes. |
| Import-alias impact widening | The CodeQL selector treated imported local names as runtime callers and widened focused validation unnecessarily. | Import edges stay outside the runtime one-hop neighbor set. A changed, unobserved import remains a target and still triggers its domain fallback. |
| Stage process policy | The stage worker and its tests imported the standard subprocess module directly. | Repository-owned launch sites now use VIPER's spawn-safe subprocess facade, enforced by the existing AST policy test. |
| Artifact-loader isolation | RICO selected a loader from a module whose sibling import was absent from the disposable verification workspace. | RICO uses a self-contained JSON loader whose frozen file contains every dependency needed for import and validation. |

Four additional compatibility repairs support the formal assessments:

| PairBlock | Runtime problem | Accepted behavior |
|---|---|---|
| `P0-PB-05F` | Governed file access treated the operating system's null device as undeclared data. | The exact null-device path is runtime plumbing; the observer excludes it from provenance and declared-input accounting. |
| `P0-PB-05G` | Loading a frozen stage callable displaced workspace module objects needed during invocation. | The worker activates the callable's captured workspace modules for the call and restores the previous module registry afterward. |
| `P0-PB-05H` | Governed execution rejected Python imports from the stage's own frozen source commit. | The observer permits exact tracked Python files from that commit while retaining the data boundary for other files. |
| `P0-PB-05J` | RICO verification needed to execute a frozen loader owned by the MANTRA producer repository. | The execution caller names each additional trusted source repository explicitly; that trust reaches prior-run loader verification. |

The file-access repair has a deliberate scope. It establishes which files
ordinary Python open operations reached. Its evidence ends at file-open
behavior, and native code can perform file access outside Python's audit
surface. Hostile stage code therefore requires an operating-system
sandbox. For these rebuilds, severed-input tests and exact output comparisons
remain the evidence that a named input matters to a particular result.

The performance repairs preserve verification while avoiding repeated work.
Checkout reuse authenticates one repository-and-commit pair once per execution.
Producer memoization verifies one exact producer result once per verification
pass. Per-file and per-pointer digest checks still run. The terminal RICO
registration completed in 283.833269 seconds after these changes; the earlier
attempts exposed repeated Git retrieval, repeated producer verification, and a
loader-only import failure.

## Contract, review, and Git closure

### Single source of status

The checklist row owns each PairBlock's lifecycle status. The controller writes
legal transitions and their receipts. The profile compiler derives checkboxes,
requirement state, dependency readiness, and contract state from those rows,
then submits the normalized manifest to the global master-checklist validator.
Accepted code links point to active source and tests; proposal links remain
staging links only through `Approved`.

The closure pass found and corrected five stale derived statements: two Phase
0D checkboxes, the MIL artifact-table status, the Phase 0 requirement count,
and an obsolete owner action. A live traceability check now reports 29
PairBlocks, 25 requirements, and one complete Phase 0 contract.

### Self-review records

Each completed implementation block has a repository-scoped review receipt.
The receipt identifies the base and result commits, owned paths, canonical diff
digest, invariants, counterexamples, repairs, focused checks, Git state, and
verdict. The current RICO evidence tree contains 30 review receipts, 58 gate
receipts, and 95 lifecycle receipts, including superseded attempts retained for
audit. The counts include multiple attempts for some PairBlocks.

The compatibility-certification implementation received two repair cycles
during self-review. First, the controller originally checked only that evidence
was labeled `artifact`; the accepted version also recomputes the file digest.
Second, the first schema draft would have added an empty certification field to
ordinary version-1 receipts; the accepted version reserves that field for
version-2 certification receipts. The latest controller validation passed all
61 focused tests.

### Repository state at closure

| Repository | Closure revision | Upstream state | Principal result in this reporting window |
|---|---|---|---|
| MANTRA | `7c76c9772378f94f55012a06fc9f13354a46a4e7` | `main` matched `origin/main` | Restoration, disk import, Hopfield replay, MIL replay, and their tests |
| VIPER | `3383713d7c6c90528b133df4b402d23bb86ddcee` | `main` matched `origin/main` | File governance, result selection, cross-workspace retrieval, failure preservation, caching, targeted-test repair, and process policy |
| RICO | `7735c13` before this briefing | `main` matched `origin/main` | Contracts, checklist, PairBlock controller, evidence freezer, terminal registration, receipts, reviews, and usefulness ledger |

From the accepted archive-planning baseline through closure, MANTRA changed 17
tracked files with 3,702 inserted lines and 38 deleted lines. VIPER changed 25
tracked files with 1,145 inserted lines and 67 deleted lines. RICO's larger diff
is dominated by immutable JSON gate, lifecycle, review, and graph evidence.

## Current position in the full program

The [master checklist](../checklists/mantra-rebuild.md) divides the work into six
execution phases:

| Phase | Outcome | Current state |
|---|---|---|
| 0 | Restore the historical artifacts, replay both independent models, verify lineage, and assess VIPER | Complete |
| 1 | Rebuild Hopfield preprocessing, encoder training, retrieval, and correction | Contract pending |
| 2 | Rebuild the independent MIL teacher, student, retrieval, and correction path | Contract pending; scheduled after Phase 1 |
| 3 | Freeze graph-encoder identities, splits, targets, and corrected baselines | Design complete; contract pending |
| 4 | Compare graph topologies and build the V1 feature pipeline | Pending Phase 3 |
| 5 | Train, study, and accept the first biologically grounded graph encoder | Pending Phase 4 |

### Hopfield reconstruction target

Phase 1 must rebuild matched controls, control programs, response
representations, biological descriptors, predicted control state, response
summaries, and reference shifts. It then rebuilds the
`187 -> 384 -> 384 -> 128` encoder and its distribution-matching objectives.
The final application retrieves raw-gene responses at temperature `0.055` and
must reproduce `0.5861640938949398`. Intermediate comparisons precede the final
score so the first divergent producer can be identified.

### MIL reconstruction target

Phase 2 rebuilds teacher bags, conditioning, teacher training, donor
embeddings, the single-query student, covariance shrinkage, teacher-neighbor
smoothing, retrieval, residual correction, reference shift, and per-gene
calibration. The selected runtime uses one query even though a dormant YAML
field records `proto_count: 11`. The final target remains the standalone v1952
seed-123460 `without_control` result of `0.6025499488874759`.

### Graph-encoder target

The graph-encoder design starts with two ordered key types:

- `PerturbationRowKey` is the source experimental symbol in split order.
- `ResponseColumnKey` is the unique `resolved_gene_key` in GEARS order.

The identifier design fixes 2,057 gene-target perturbations across 1,427 fit,
357 tune, and 273 hold rows, plus 5,000 response columns. This distinction
prevents a target-gene identity from being substituted for a response-axis
coordinate. The response-axis record must retain its raw GEARS identity,
Ensembl identity, matched atlas column, and unique model-facing key.

The first graph encoder uses a binary PPI graph, one-hop mean aggregation, and
128-dimensional hidden representations. Before training it, the program must
measure PPI, regulatory, and signaling graph coverage; freeze corrected ridge
and fusion-only baselines; validate the AlphaGenome feature pipeline; and
select topology and message depth using tune data. V1 succeeds only after all
2,057 perturbations receive valid embeddings, held response data stay outside
graph construction and node features, embeddings remain non-collapsed, the
model beats fusion-only on at least one primary unseen-perturbation metric, and
the result reproduces from resolved provenance artifacts. These requirements
come from Parts XIX and XX of the
[graph-encoder design specification](../Biologically_Grounded_Graph_Encoder_Design_Specification.pdf)
and Part 7 of the
[identifier-system monograph](../GENE_IDENTIFIER_SYSTEMS_COMPLETE_REVISED.pdf).

## Immediate Phase 1 tranche

The first Phase 1 deliverable is a Hopfield reconstruction contract. Training
begins after that contract defines and passes the following review surface.

### Proposed PairBlock sequence

| PairBlock | User-visible decision | Codex preparation | Completion gate |
|---|---|---|---|
| `P1-PB-01` historical intermediate inventory | Approve the exact oracle arrays and fitting populations | Trace every loaded and produced Hopfield array to source, producer, shape, dtype, row axis, column axis, and digest | Every required intermediate has one historical producer and one retained identity |
| `P1-PB-02` identity and split contract | Approve perturbation and response key types, ordering, and join policy | Bind split rows, response columns, gene ordering, duplicate-symbol handling, and source releases | Reordered, missing, duplicated, or type-confused axes fail focused tests |
| `P1-PB-03` preprocessing reconstruction | Review the complete proposed source before applying it | Specify matched controls, normalization populations and statistics, control programs, response programs, descriptors, summaries, and shifts as separate producers | Each rebuilt intermediate matches its oracle within a named tolerance |
| `P1-PB-04` encoder reconstruction | Review architecture, initialization, objectives, optimizer, seed, checkpoint policy, and logging | Specify the `187 -> 384 -> 384 -> 128` implementation and training evidence | Architecture and objective tests pass; one approved training run retains checkpoints and selection evidence |
| `P1-PB-05` retrieval and final parity | Review retrieval, reference shift, and evaluation surface | Specify raw-gene donor retrieval at `0.055`, intermediate outputs, and final metric | Intermediate tolerances pass and final PearsonDelta equals the approved target within contract tolerance |

### First concrete action

Begin with `P1-PB-01`. Read the historical preprocessing and training entry
points from the [handoff source map](../mantra-viper-rebuild-handoff.md#hopfield-source-and-selected-result),
then emit one table with these columns:

| Field | Meaning |
|---|---|
| Artifact | The exact historical file or in-memory array |
| Producer | Function, script, and source revision that creates it |
| Consumer | First Hopfield operation that reads it |
| Shape and dtype | The stored or runtime numerical interface |
| Row identity | Ordered perturbation or cell population |
| Column identity | Ordered feature, program, coefficient, or response axis |
| Fit population | Rows used to estimate any statistic or fitted transform |
| Numerical identity | SHA-256 for frozen bytes or explicit tolerance for recomputation |
| Observing test | The focused check that fails on the smallest meaningful divergence |
| VIPER role | Named input, output, metric, or comparison artifact |

The contract should freeze this table before new RICO implementation code is
written. The user reviews the table and each complete proposed code block.
Codex maintains the contract, source trace, gates, review records, and status
transitions. The user remains the author of each manually applied reconstruction
block unless that division of labor is explicitly changed.

## Open risks and decisions

### 1. Replay parity covers application execution

Phase 0 exercised saved checkpoints and fitted artifacts. Reconstructing those
artifacts may expose omitted seeds, row filters, normalization populations,
library-version behavior, or checkpoint-selection rules. Phase 1 addresses this
by comparing each intermediate before training and final evaluation.

### 2. Numerical tolerance needs an artifact-specific rule

Frozen historical files can require exact digests. Recomputed floating-point
arrays may require elementwise, distributional, or metric tolerances. The
contract must choose the tolerance from the operation and downstream
sensitivity. A single global threshold would conceal those differences.

### 3. File-access observation proves boundary conformance

The governed VIPER mode detects CPython-visible file opens and rejects paths
outside the declaration. Its evidence ends before byte-level causality.
Intermediate parity tests, severed-input tests, and final output comparisons
supply that evidence for each model stage.

### 4. Source verification still has measurable fixed cost

Exact external Git retrieval and prior-run verification now reuse work within
one execution. A fresh process still authenticates the required source and
producer state. Phase 1 should measure this fixed cost separately from model
compute and avoid reconstructing a large multi-repository graph for a local
unit test.

### 5. The CodeQL test map remains reviewed evidence

CodeQL identifies changed declarations and runtime callers. The observer map
states which tests exercise a declaration. The repaired selector avoids import
alias widening, while semantic relevance of a mapped test remains a review
claim. Each PairBlock self-review must check the smallest counterexample rather
than accepting a mapping entry by itself.

### 6. Identity work is a prerequisite for the graph encoder

The graph model joins experimental perturbations, response columns, external
gene records, protein products, graph nodes, and feature rows. Those objects
share some identifier formats while serving different roles. Phase 3 must
preserve the two ordered model axes and treat biological mappings as versioned
metadata beside them.

## Source record

The following sources support the status and implementation claims in this
briefing:

- [Phase 0 contract](../contracts/mantra-rebuild-phase-0.md)
- [Master execution checklist](../checklists/mantra-rebuild.md)
- [Model-rebuild handoff](../mantra-viper-rebuild-handoff.md)
- [Frozen Phase 0 evidence index](../../evidence/phase0/index.json)
- [Terminal Phase 0 registration receipt](../../evidence/phase0/rico/phase0_registration_receipt.json)
- [Terminal Phase 0 run record](../../evidence/phase0/rico/phase0_registration_run.json)
- [VIPER usefulness ledger](../../evidence/viper-usefulness-ledger.json)
- [Graph-completeness report](../../evidence/phase0/mantra/graph_completeness_report.json)
- [Hopfield replay receipt](../../evidence/phase0/mantra/hopfield_replay_receipt.json)
- [MIL replay receipt](../../evidence/phase0/mantra/mil_replay_receipt.json)
- [Graph-encoder design specification](../Biologically_Grounded_Graph_Encoder_Design_Specification.pdf)
- [Identifier-system monograph](../GENE_IDENTIFIER_SYSTEMS_COMPLETE_REVISED.pdf)
