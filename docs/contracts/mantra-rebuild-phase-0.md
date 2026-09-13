# Mantra Rebuild Phase 0 Contract

## 1. Status

**Contract status:** In progress

**Implementation state:** [Master checklist](../checklists/mantra-rebuild.md#pairblock-resolution)

This contract governs artifact discovery, capacity planning, restoration, and provenance capture before the Hopfield or MIL rebuild begins. The model rebuild remains out of scope until every Phase 0 acceptance condition passes. The user actively reviews each PairBlock's scope, proposed work, observed result, and gate evidence before the next PairBlock begins.

The [Mantra rebuild master checklist](../checklists/mantra-rebuild.md) owns execution order, current status, and the next action. This contract owns Phase 0 requirements, PairBlock definitions, and gates. Before a block reaches `Applied`, its staging files contain the proposal under review. At `Applied`, the active source at the cited Git commit becomes the implementation authority. A review finding cannot add an acceptance requirement: a new obligation must first enter this contract with its observing gate.

## Table of contents

- [Status](#1-status)
  - [Phase 0 requirement map](#phase-0-requirement-map)
- [Required claim](#2-required-claim)
- [Current gap](#3-current-gap)
- [Restoration and storage contract](#4-restoration-and-storage-contract)
- [Phase 0 dependency model](#5-phase-0-dependency-model)
- [Persisted evidence](#6-persisted-evidence)
- [Verification](#7-verification)
- [Acceptance boundary](#8-acceptance-boundary)
- [PairBlock order](#9-pairblock-order)
  - [Phase 0 ownership record](#phase-0-ownership-record)
- [Implementation records](#10-implementation-records)
- [Sources](#11-sources)

### Phase 0 requirement map

| ID | Contract boundary | Blocks |
|---|---|---|
| `P0-REQ-01` | Define $B$ for the selected Hopfield and MIL outputs. | [`P0-PB-02`](#p0-pb-02), [`P0-PB-03`](#p0-pb-03) |
| `P0-REQ-02` | Give every restored file node in $B$ one verified `RestorationBinding`. | [`P0-PB-04`](#p0-pb-04), [`P0-PB-04A`](#p0-pb-04a), [`P0-PB-04B`](#p0-pb-04b) |
| `P0-REQ-03` | Calculate the maximum simultaneous local storage requirement before downloading an archive. | [`P0-PB-05`](#p0-pb-05), [`P0-PB-05A`](#p0-pb-05a), [`P0-PB-05B`](#p0-pb-05b) |
| `P0-REQ-04` | Verify the 27 files on the restored MANTRA disk and publish their exact bytes as named VIPER outputs. | [`P0-PB-06`](#p0-pb-06) |
| `P0-REQ-05` | Run restoration from the MANTRA workspace with `viper-provenance` installed in MANTRA's `venv`. | [`P0-PB-01`](#p0-pb-01), [`P0-PB-06`](#p0-pb-06) |
| `P0-REQ-06` | Record and verify $B$ in the VIPER provenance graph. | [`P0-PB-06`](#p0-pb-06) |
| `P0-REQ-07` | Replay the historical Hopfield raw-gene readout from its saved encoder and restored inputs. | [`P0-PB-07`](#p0-pb-07) |
| `P0-REQ-08` | Replay the v1952 MIL seed-123460 `without_control` result from restored inputs. | [`P0-PB-08`](#p0-pb-08) |
| `P0-REQ-09` | Maintain an independent usefulness ledger for VIPER checks, failures, costs, and confirmed findings. | [`P0-PB-09`](#p0-pb-09), [`P0-PB-09A`](#p0-pb-09a) |
| `P0-REQ-10` | Compile the RICO checklist into the global master-checklist manifest and propagate tested code transitions or externally reviewed non-code transitions through each PairBlock's checkbox, requirements, dependent blocks, and contract state. | [`P0-PB-10`](#p0-pb-10) |
| `P0-REQ-11` | Make each governed VIPER stage reject undeclared CPython-visible file-open attempts and retain each successful Python file open, including one read-open for every declared input. | [`P0-PB-05C`](#p0-pb-05c) |
| `P0-REQ-12` | Permit an unbenchmarked VIPER run to select a `model` artifact from a non-training stage while retaining the training-stage requirement for benchmarked runs. | [`P0-PB-05D`](#p0-pb-05d) |
| `P0-REQ-13` | Bind an approved runtime destination absent from the signed filesystem manifest only when its required digest exists in its approved signed archive. | [`P0-PB-04B`](#p0-pb-04b), [`P0-PB-06`](#p0-pb-06) |
| `P0-REQ-14` | Permit an unbenchmarked VIPER run to select any artifact declared by one of its stages while retaining model selection from a training stage for benchmarked runs. | [`P0-PB-05E`](#p0-pb-05e) |
| `P0-REQ-15` | Permit a governed stage to open the operating system's null device without treating it as a data input or persisted output. | [`P0-PB-05F`](#p0-pb-05f) |
| `P0-REQ-16` | Keep the exact workspace module objects loaded with a frozen stage callable available while that callable executes. | [`P0-PB-05G`](#p0-pb-05g) |
| `P0-REQ-17` | Permit governed reads of exact Python source files present in the run's frozen Git commit without treating those files as data inputs. | [`P0-PB-05H`](#p0-pb-05h) |
| `P0-REQ-18` | Publish the final failed attempt after result verification rejects a provisional successful attempt. | [`P0-PB-05I`](#p0-pb-05i) |
| `P0-REQ-19` | Let an execution caller explicitly approve additional source repositories whose artifact loaders must run while verifying prior-run inputs. | [`P0-PB-05J`](#p0-pb-05j) |
| `P0-REQ-20` | Reject a stored-input destination outside `inputs/` while authoring the plan. | [`P0-PB-05L`](#p0-pb-05l) |
| `P0-REQ-21` | Reuse authenticated Git state while one execution retrieves several files from the same external repository revision. | [`P0-PB-05K`](#p0-pb-05k) |
| `P0-REQ-22` | Verify one exact producer run once while one verification pass checks several pointers into that run. | [`P0-PB-05M`](#p0-pb-05m) |
| `P0-REQ-23` | Exclude imported local names from a changed declaration's runtime-dependent one-hop callers. | [`P0-PB-05N`](#p0-pb-05n) |
| `P0-REQ-24` | Route repository-owned stage-worker child processes through VIPER's spawn-safe subprocess facade. | [`P0-PB-05O`](#p0-pb-05o) |
| `P0-REQ-25` | Certify a named legacy PairBlock from one retained terminal artifact while preserving its incomplete historical receipt chain and recording the reason for the exception. | [`P0-PB-10A`](#p0-pb-10a) |
| `P0-REQ-27` | Author every post-bootstrap requirement, verifier, PairBlock, dependency, implementation path, and gate once in a typed declaration manifest; bind each accepted declaration revision to its affected PairBlocks; derive each state after `Drafting` from receipts; and render the human contract and checklist views from those records. | [`P0-PB-10B`](#p0-pb-10b) |

## 2. Required claim

Before a model rebuild starts, VIPER can trace each selected result through every file the rebuild reads and every producer entrypoint it executes.

The graph $B=(F,P,E)$ contains:

- $F$ contains exact file identities. A file enters $F$ only when a selected rebuild stage reads it or an upstream stage produces it.
- $P$ contains exact producer entrypoints. Each entrypoint is identified by repository commit, source path, symbol, source-file byte count, and source-file SHA-256.
- $E$ contains `consumes` edges from files to producer entrypoints and `produces` edges from producer entrypoints to files.

A `consumes` edge requires both a named stage input and a successful Python read-open beneath that input path. A `produces` edge requires both a declared stage output and a successful run receipt for that output. Every member of $F \cup P$ must lie on a directed path ending at the selected Hopfield or MIL output. Severing any required node or edge must make graph verification fail.

The Hopfield and MIL portions of $B$ are independent. Neither model consumes an output produced by the other model. A shared raw or derived data file may appear in both portions only when each model reads that file directly.

Historical predictions, checkpoints, and reports used only to compare the rebuild form a separate parity-reference graph $Q$. Reconstruction and training stages exclude every member of $Q$ from their inputs.

This claim establishes byte identity, executed-producer identity, and graph completeness. Historical training reproducibility and scientific correctness remain later acceptance boundaries.

For a stage governed by `file_access="declared"`, graph completeness covers
file-open attempts emitted through CPython's audit interface. The stage must
successfully open every declared input for reading and may successfully open
only declared outputs and attached metric files for writing. The policy forbids working-directory changes
and Python thread or child-process launches. Interpreter-owned files beneath `sys.prefix` and
`sys.base_prefix` belong to the recorded runtime environment and remain outside
the stage receipt. A native-library file open appears in the receipt only when
the library emits a CPython audit event; each Phase 0 replay gate
must exercise its real loaders and show that every required input appears in
the invocation receipt.

A retained read-open establishes that a wrapped Python file-opening call
returned successfully. Semantic use of particular bytes requires separate evidence. The receipt supports the graph edge by showing that cooperative stage
code successfully opened the declared input; the artifact identity and stage
result supply the separate byte and execution evidence. Python classifies
`sys.addaudithook()` as an observation interface. Hostile code requires an
operating-system sandbox.

## 3. Current gap

The repository contains restoration controls, artifact pointers, application verification inputs, and historical producer code. The missing rebuild-specific graph must identify the selected result first, then trace only the files and producers required to rebuild it.

The first missing result is therefore the complete graph $B$. When the signed Hugging Face records identify an absent local file's bytes, Phase 0 classifies that file as a restoration task. An unrecoverable classification requires a failed search of the signed restoration records.

Current VIPER invocation evidence binds the declared paths to the stage context
while leaving workspace reads unobserved. The same
function can open another workspace path directly. `P0-PB-05C` closes this
runtime-evidence gap before restoration begins.

## 4. Restoration and storage contract

### `RestorationBinding`

`RestorationBinding` tells the MANTRA restoration stage where one required file belongs, where its archived bytes reside, and which bytes must result. For a file node $f \in F$:

$$
r=(f,d,s,c),\qquad
s=(repo,control\_revision,archive,member),\qquad
c=(bytes,sha256).
$$

Here $d$ is the destination relative to the MANTRA repository root. The value $s$ identifies the signed control package, the archive declared by that package, and the archive member that contains the file bytes. `control_revision` is the immutable Hugging Face revision containing the signed archive manifest. That manifest lists the archive's ordered parts; each part has its own immutable data revision, path, byte count, and SHA-256. The value $c$ identifies the extracted file bytes. The binding records restoration identity; $B$ records producer and consumer relationships.

RICO owns this definition and its approval history. The proposed executable type is `src/mantra/rebuild/restoration.py::RestorationBinding` in MANTRA. VIPER stores each resolved binding with the run evidence that used it; Phase 0 will select a checked-in MANTRA path for the reviewed binding set when `P0-PB-04` defines that file's consumer.

### Ownership boundary

MANTRA is the historical oracle. It contains the restored legacy artifacts,
historical source, Phase 0 restoration and replay adapters, and exact Hopfield
and MIL replay evidence. RICO contains the contracts and receipts for Phase 0.
RICO owns reconstructed model source, tests, VIPER declarations, and future
graph encoders from Phase 1 onward. Restoration imports the installed VIPER
distribution. Framework repairs remain in the separate VIPER repository; the
MANTRA environment may install a reviewed local VIPER checkout before the
session-close release.

The existing MANTRA Git repository is the VIPER workspace. A root `viper.toml` marks that boundary because `viper.repository.resolve_root()` requires the marker to equal the Git work-tree root. `viper init` serves empty targets by generating a Python package, build configuration, test tree, and example stages. MANTRA supplies those structures itself, so Phase 0 adds only the workspace marker and MANTRA-owned adapters.

The MANTRA execution environment is the Conda environment named `mantra`. It must contain Python 3.13 and the `viper-provenance` package. The environment receipt records the environment name, Python executable, installed VIPER version, and module path as observations. The gate accepts every installed VIPER version.

New orchestration code belongs under `src/mantra/rebuild/`. It calls the historical MANTRA implementation at its current paths and preserves the historical experiment layout. The Hopfield replay adapter and its focused test are `src/mantra/rebuild/hopfield_replay.py` and `src/mantra/rebuild/tests/test_hopfield_replay.py`. `P0-PB-02` identifies every declared stage input before we draft their complete source.

### Cross-workspace artifact handoff

VIPER intentionally confines `ExternalInputRef` to a file beneath the
active repository root. `capture_external_input()` then copies those bytes into
the consuming attempt. This restriction gives the active workspace custody of
the bytes it declares. The local [cross-workspace assessment](../../evidence/viper-assessments/local-prior-run-cross-workspace.json)
records both the original 0.1.0a3 failure and the repaired behavior.

VIPER 0.1.0a4 binds each `LocalFileRef` to the producer workspace and persistent
local-store identity as well as its immutable revision and path. Compilation
retrieves and validates the producer run before publishing the consumer
pointer. Every local retrieval resolves the store named by the reference and
rejects a mismatched workspace or store identity.

The repaired [cross-workspace probe](../../evidence/viper-assessments/local-prior-run-cross-workspace.json)
created a MANTRA run reference, published its pointer in RICO, and retrieved
the declared MANTRA bytes through that pointer. The receipt records both store
identities, both immutable revisions, and the retrieved SHA-256. A same-machine
`LocalFileRef` may therefore cross these workspace roots while the recorded
MANTRA workspace and store remain available. A remote-backed reference remains
necessary when the consumer cannot access that exact local store. `P0-PB-09`
registers the assessment and repaired probe in the VIPER graph.

### Local storage

Phase 0 uses three storage roles:

| Role | Local path | Retention rule |
|---|---|---|
| Recovery download cache | The `part_cache/` directory inside an archive-restoration stage's evidence output | Holds one verified Hugging Face archive part when the preserved disk cannot supply an approved file. |
| Restored disk files | `/home/machina/MANTRA/` at each documented repository-relative destination | Supplies the 27 identity-checked inputs imported by the GPU restoration run. |
| VIPER evidence | `/Users/machina/Developer/ChatGPT/mantra/.viper/store/` and `/Users/machina/Developer/ChatGPT/mantra/.viper/catalog.sqlite3` | Holds the provenance objects and graph catalog produced by governed runs. |

Phase 0 reads the approved files from `/home/machina/MANTRA` and writes copies
only to the declared VIPER attempt and store paths. The signed archive plan
remains the recovery source when a preserved-disk identity differs.

### Capacity gate

Before the first archive download, Phase 0 must measure current free space and calculate:

$$
R_{max}=C+D+V+T+H,
$$

| Symbol | Required measurement |
|---|---|
| $C$ | Maximum compressed cache retained at once. |
| $D$ | Extracted canonical footprint. |
| $V$ | Additional bytes retained by VIPER. |
| $T$ | Peak temporary extraction space. |
| $H$ | 10 MiB reserved free space. |

The download gate passes only when observed free space is at least $R_{max}$. Shared archive chunks count once.

## 5. Phase 0 dependency model

$B$ contains the files, programs, and read/write links required to reproduce the selected Hopfield and MIL results. $Q$ contains historical outputs used only for comparison.

```mermaid
flowchart TB
    roots["Select result roots"]
    environment["Create venv for the rebuild<br/>install VIPER"]
    trace["Build B"]
    binding["Bind missing files<br/>to archive sources"]
    parity["Build Q"]
    capacity["Check disk capacity"]
    restore["Import 27 restored disk files<br/>as VIPER outputs"]
    verify["Verify B in VIPER"]
    rejection_test["Remove one required edge<br/>confirm verification fails"]
    replay_ready["Verify replay inputs"]
    hopfield_replay["Replay Hopfield readout"]
    mil_replay["Replay MIL application"]
    evidence_review["Review Phase 0 evidence"]
    hopfield["Begin Hopfield reconstruction"]

    roots --> environment
    roots --> trace
    trace --> binding
    trace --> parity
    binding --> capacity
    environment --> restore
    capacity --> restore
    restore --> verify
    trace --> verify
    verify --> rejection_test
    rejection_test --> replay_ready
    parity --> replay_ready
    replay_ready --> hopfield_replay
    replay_ready --> mil_replay
    hopfield_replay --> evidence_review
    mil_replay --> evidence_review
    evidence_review --> hopfield

    classDef workNode fill:#f3f7ff,color:#111827,stroke:#315a8a,stroke-width:1.5px
    classDef gateNode fill:#fff4d6,color:#111827,stroke:#9a6700,stroke-width:2px
    classDef outcomeNode fill:#e8f7ee,color:#111827,stroke:#237a44,stroke-width:2px
    class roots,environment,trace,binding,parity,restore workNode
    class capacity,verify,rejection_test,replay_ready,hopfield_replay,mil_replay,evidence_review gateNode
    class hopfield outcomeNode
```

1. Confirm the selected Hopfield and MIL result files that terminate $B$.
2. Create the MANTRA development environment and prove that it uses the released VIPER distribution.
3. Trace the Hopfield result backward to its required file nodes, producer entrypoints, and edges.
4. Trace the MIL result backward through its required file nodes, producer entrypoints, and edges.
5. Classify historical comparison files in $Q$ and exclude them from rebuild inputs.
6. Write one `RestorationBinding` for each absent file node in $B$.
7. Calculate $R_{max}$ and stop if the capacity gate fails.
8. Download and extract the required archive members through MANTRA-rooted VIPER stages.
9. Verify $B$, including a rejection case with one required relationship severed.
10. Replay the historical Hopfield raw-gene readout and the saved MIL application.
11. Freeze Phase 0 evidence and request approval to begin Hopfield reconstruction.

## 6. Persisted evidence

| Evidence | Required content |
|---|---|
| Graph $B$ | Every required member of $F$, $P$, and $E$, with the selected result as its terminal node. |
| Restoration bindings | One reviewed $r=(f,d,s,c)$ record for every absent restored file in $F$. |
| Environment receipt | Python executable, installed VIPER version, and imported VIPER module path. |
| Capacity receipt | The measured terms in $R_{max}=C+D+V+T+H$, the measurement time, and the gate result. |
| Restoration receipt | The resolved `RestorationBinding` and outcome for each restored file. |
| VIPER graph | The verified runtime representation of $B$. |
| Graph-completeness report | Missing members of $F$, $P$, or $E$, plus the pass or fail result. |
| Hopfield replay receipt | Approved command, saved-encoder identity, input digests, produced predictions, metric, tolerance, and comparison result. |
| MIL replay receipt | Exact command, environment, input digests, output digests, metrics, tolerances, and comparison result. |
| Cross-workspace assessment | The original failure, defect classification, repair revision, producer and consumer store identities, retrieved byte identity, and project rule. |
| Stage file-access receipt | The repository-relative reads and writes observed while a stage runs with `file_access="declared"`. |
| Project declaration manifest | Typed requirement, verifier, PairBlock, dependency, repository-relative path, and gate records for every manifest-native block. |
| Declaration revision receipt | Previous and accepted manifest digests, changed record digests, affected PairBlock IDs, approval reference, and superseded receipt heads. |
| VIPER usefulness ledger | Claimed check, real defect detected, independent confirmation, ordinary-test coverage, false alarms, infrastructure failures, time cost, and later reuse. |

The dependency graph, restoration bindings, environment receipt, capacity receipt, restoration receipts, completeness report, both replay receipts, and usefulness ledger must themselves be registered in VIPER. Each checked-in evidence file requires a corresponding graph record.

## 7. Verification

| Rule | Executable condition | Blocks |
|---|---|---|
| `P0-VR-01` | Every member of $F \cup P$ lies on a path ending at a selected result, and every edge in $E$ has its required evidence. | [`P0-PB-02`](#p0-pb-02), [`P0-PB-03`](#p0-pb-03) |
| `P0-VR-02` | Every absent restored file in $F$ has exactly one valid `RestorationBinding`. | [`P0-PB-04`](#p0-pb-04) |
| `P0-VR-03` | The measured free space is greater than or equal to $R_{max}$ before download begins. | [`P0-PB-05`](#p0-pb-05) |
| `P0-VR-04` | Every disk file exists at its approved MANTRA path, matches its `RestorationBinding`, and has one same-identity VIPER output. | [`P0-PB-06`](#p0-pb-06) |
| `P0-VR-05` | The active Conda environment is named `mantra`, uses Python 3.13, and imports its installed `viper-provenance` package. | [`P0-PB-01`](#p0-pb-01) |
| `P0-VR-06` | The VIPER graph contains every member of $B$, and severing one required node or edge makes verification fail. | [`P0-PB-06`](#p0-pb-06) |
| `P0-VR-07` | The Hopfield replay reproduces the selected raw-gene readout score `0.5861640938949398` within the approved tolerance and retains its produced predictions. | [`P0-PB-07`](#p0-pb-07) |
| `P0-VR-08` | The MIL replay reproduces the v1952 seed-123460 `without_control` hold PearsonDelta `0.6025499488874759` and its declared prediction-array hashes. | [`P0-PB-08`](#p0-pb-08) |
| `P0-VR-09` | Every assessed VIPER check has a usefulness-ledger row and independent evidence for any confirmed defect; one RICO-rooted VIPER run verifies every frozen evidence identity. | [`P0-PB-09`](#p0-pb-09), [`P0-PB-09A`](#p0-pb-09a) |
| `P0-VR-10` | The global master-checklist validator accepts incremental sibling-block closure. The RICO profile rejects an unsupported transition or any disagreement among a PairBlock row, checkbox, mapped requirement, dependent-block readiness, completion evidence, and contract state. | [`P0-PB-10`](#p0-pb-10) |
| `P0-VR-11` | A stage using `file_access="declared"` fails after a declared input lacks a successful Python read-open, an undeclared read-open or write-open attempt, a directory change, or a Python thread or child-process launch. Its verified invocation receipt contains only successful opens permitted by the frozen inputs, outputs, and metric declarations. | [`P0-PB-05C`](#p0-pb-05c) |
| `P0-VR-12` | Plan verification accepts a `model` artifact produced by a build stage when the run has no benchmark. It rejects a missing selected artifact and retains the training-stage requirement when the run has a benchmark. | [`P0-PB-05D`](#p0-pb-05d) |
| `P0-VR-13` | An unbenchmarked `RunSpec` accepts a selected artifact with any declared output name. Plan verification rejects an output absent from its selected stage. A benchmarked `RunSpec` accepts only the `model` output, and plan verification requires a training-stage producer. | [`P0-PB-05E`](#p0-pb-05e) |
| `P0-VR-14` | A stage using `file_access="declared"` may read from or write to the exact path returned by `os.devnull`. The observer excludes that path from retained data-access evidence and continues to reject every other undeclared device path. | [`P0-PB-05F`](#p0-pb-05f) |
| `P0-VR-15` | The stage loader retains the exact workspace module objects imported with the frozen callable. The worker exposes those objects through `sys.modules` only during invocation and restores every prior entry afterward. Runtime module lookup resolves without reopening repository source or bytecode. | [`P0-PB-05G`](#p0-pb-05g) |
| `P0-VR-16` | Before governed access begins, the worker derives the exact tracked `.py` paths from the frozen source commit. The observer permits those source reads without recording data-access evidence, while an untracked Python file and a tracked non-Python file remain undeclared reads. | [`P0-PB-05H`](#p0-pb-05h) |
| `P0-VR-17` | A result-verification failure writes one failed `resolved.yaml` whose failure message preserves the verification error. | [`P0-PB-05I`](#p0-pb-05i) |
| `P0-VR-18` | Execution trusts the current run source plus only the additional repositories named by the caller. A prior-run loader from an unnamed repository remains rejected. | [`P0-PB-05J`](#p0-pb-05j) |
| `P0-VR-19` | `run_artifact()` rejects a materialization path outside `inputs/` before it publishes a pointer or constructs an executable plan. Deserializing `StoredInputRef` enforces the same rule. | [`P0-PB-05L`](#p0-pb-05l) |
| `P0-VR-20` | One `RunFetcher` creates at most one checkout for each external repository and commit, verifies that checkout's origin and fetched commit, and retains no more than 64 MiB of exact fetched file bytes. | [`P0-PB-05K`](#p0-pb-05k) |
| `P0-VR-21` | `verify_stored_inputs()` calls producer-run verification once for equal `ResolvedRunRef` values and still checks each selected artifact, data role, and materialization path. | [`P0-PB-05M`](#p0-pb-05m) |
| `P0-VR-22` | An `imports` edge does not create an independent one-hop caller for its target. An import selected as the changed declaration still requires a reachable test or domain fallback. | [`P0-PB-05N`](#p0-pb-05n) |
| `P0-VR-23` | The repository AST policy finds no direct standard-library `subprocess` import outside the facade and its own observer test; stage source inspection and file-access tests pass through the facade. | [`P0-PB-05O`](#p0-pb-05o) |
| `P0-VR-24` | The `certify` event accepts only a PairBlock named by `ChecklistProfile.legacy_certifiable_pair_blocks`, requires `artifact` evidence and a nonempty reason, preserves any existing receipt link, and produces the same derived `Complete` state as an ordinary completion receipt. | [`P0-PB-10A`](#p0-pb-10a) |
| `P0-VR-26` | For a manifest-native PairBlock, the declaration manifest is the only source for IDs, relationships, paths, gates, and the initial `Drafting` state; lifecycle receipts determine each later state; revision validation recomputes changed records and affected PairBlocks from adjacent accepted manifests, validates the external approval reference's schema, and resolves every superseded receipt; deterministic rendering supplies every human link and command; directory discovery requires documentation for every active Python definition, dataclass field, and persisted `TypedDict` field; validation rejects an unapproved declaration change, duplicate legacy ownership, a severed reference, receipt disagreement, undocumented source, or manual changes inside a generated region. | [`P0-PB-10B`](#p0-pb-10b) |

## 8. Acceptance boundary

### Success

The restoration and replay baseline remains accepted by `P0-VR-01` through
`P0-VR-24`. This maintenance revision returns the Phase 0 contract to `Final`
when `P0-VR-26` passes, its implementation review and Git evidence are retained,
and VIPER registers the protocol result.

### Rejection

The maintenance gate rejects a manifest-native record when Markdown supplies an
authoritative field, the same ID also belongs to the legacy adapter, a reference
is missing or ambiguous, a lifecycle state differs from its receipts, or a
generated region differs from deterministic rendering. The existing Phase 0
rejection conditions continue to govern the accepted restoration and replay
baseline.

## 9. PairBlock order

| PairBlock | Bounded deliverable | Gate |
|---|---|---|
| `P0-PB-01` | MANTRA-rooted VIPER workspace and external-VIPER development environment | The root marker resolves to the MANTRA Git root; `P0-VR-05` passes. |
| `P0-PB-02` | Complete Hopfield subgraph of $B$ | `P0-VR-01` for Hopfield. |
| `P0-PB-03` | Complete MIL subgraph of $B$ | `P0-VR-01` for MIL. |
| `P0-PB-04` | `RestorationBinding` implementation and reviewed records | `P0-VR-02`. |
| `P0-PB-05` | Capacity receipt and download plan | `P0-VR-03`. |
| `P0-PB-05C` | VIPER stage file-access enforcement and invocation evidence | `P0-VR-11`. |
| `P0-PB-05D` | VIPER support for unbenchmarked model-producing workflows | `P0-VR-12`. |
| `P0-PB-05E` | VIPER support for unbenchmarked terminal artifacts | `P0-VR-13`. |
| `P0-PB-05F` | VIPER null-device handling in governed stages | `P0-VR-14`. |
| `P0-PB-05G` | VIPER workspace-module activation during stage invocation | `P0-VR-15`. |
| `P0-PB-05H` | VIPER frozen-source reads during governed stage invocation | `P0-VR-16`. |
| `P0-PB-05I` | VIPER failed-attempt finalization after result verification | `P0-VR-17`. |
| `P0-PB-05J` | Explicit trust for prior-run source repositories during execution | `P0-VR-18`. |
| `P0-PB-05K` | Reused external Git checkout and bounded file cache | `P0-VR-20`. |
| `P0-PB-05L` | Authoring-time stored-input namespace validation | `P0-VR-19`. |
| `P0-PB-05M` | Per-verification producer-run reuse | `P0-VR-21`. |
| `P0-PB-05N` | Import-aware CodeQL one-hop test selection | `P0-VR-22`. |
| `P0-PB-05O` | Spawn-safe stage-worker process calls | `P0-VR-23`. |
| `P0-PB-06` | Verified restoration and graph-completeness rejection test | `P0-VR-04` and `P0-VR-06`. |
| `P0-PB-07` | Hopfield VIPER adapter, focused test, and historical raw-gene readout replay | `P0-VR-07`. |
| `P0-PB-08` | v1952 MIL seed-123460 `without_control` replay | `P0-VR-08`. |
| `P0-PB-09` | Phase 0 evidence freeze and usefulness assessment | `P0-VR-09` and user approval. |
| `P0-PB-09A` | RICO-rooted registration of the frozen Phase 0 evidence | `P0-VR-09`. |
| `P0-PB-10` | Traceability validation, proposal-gate receipts, and legal checklist transitions | `P0-VR-10`. |
| `P0-PB-10A` | Explicit certification of named pre-protocol PairBlocks | `P0-VR-24`. |
| `P0-PB-10B` | Structured declaration origin and deterministic human views for newly authored PairBlocks | `P0-VR-26`. |

### Phase 0 ownership record

Resolution status lives in the [master checklist](../checklists/mantra-rebuild.md#pairblock-resolution).

| Block | Work | Review or implementation owner | Proposed code | Gate |
|---|---|---|---|---|
| [`P0-PB-01`](../checklists/mantra-rebuild.md#pairblock-resolution) | Mark and verify the MANTRA workspace. | Codex reviews; user implements. | [Accepted implementation](#p0-pb-01-accepted-implementation) | `P0-VR-05` |
| [`P0-PB-02`](../checklists/mantra-rebuild.md#pairblock-resolution) | Trace the Hopfield replay. | Codex traces; user approves. | [Work description](#p0-pb-02) | Hopfield portion of `P0-VR-01` |
| [`P0-PB-03`](../checklists/mantra-rebuild.md#pairblock-resolution) | Trace the MIL replay. | Codex traces; user approves. | [Work description](#p0-pb-03) | MIL portion of `P0-VR-01` |
| [`P0-PB-04`](../checklists/mantra-rebuild.md#pairblock-resolution) | Produce every restoration binding. | User implements approved code; Codex reviews it. | [`P0-PB-04A`](#p0-pb-04a-accepted-implementation); [`P0-PB-04B`](#p0-pb-04b-accepted-implementation) | `P0-VR-02` |
| [`P0-PB-04A`](../../../mantra/src/mantra/rebuild/restoration.py) | Define and validate `RestorationBinding`. | User implemented; Codex reviewed MANTRA commit `2304674e1fc9730801d1afe39edc7585c81081f4`. | [Source](../../../mantra/src/mantra/rebuild/restoration.py) · [Tests](../../../mantra/src/mantra/rebuild/tests/test_restoration.py) | Reject malformed bindings and incomplete coverage. |
| [`P0-PB-04B`](../../../mantra/src/mantra/rebuild/restoration.py) | Resolve an approved MANTRA destination and identity through signed controls to one archive member. | User implemented the original resolver; Codex repaired and reviewed MANTRA commit `75e7ce38dc85918c1f593886f20ed33601daa288`. | [Source](../../../mantra/src/mantra/rebuild/restoration.py) · [Tests](../../../mantra/src/mantra/rebuild/tests/test_control_resolution.py) | Resolve all 27 restorations; require manifest agreement when a destination exists and an approved archive-object match when it does not. |
| [`P0-PB-05`](../checklists/mantra-rebuild.md#pairblock-resolution) | Prove capacity and produce the download plan. | User implements approved code; Codex reviews it. | [`P0-PB-05A`](#p0-pb-05a-accepted-implementation); [`P0-PB-05B`](../../../mantra/src/mantra/rebuild/archive_plan.py) | `P0-VR-03` |
| [`P0-PB-05A`](../../../mantra/src/mantra/rebuild/capacity.py) | Calculate capacity and write its receipt. | User implemented; Codex reviewed and accepted MANTRA commit `af4e589451a90a88f59c806b12a90e74e2bba043`. | [Source](../../../mantra/src/mantra/rebuild/capacity.py) · [Tests](../../../mantra/src/mantra/rebuild/tests/test_capacity.py) | Report every term in $R_{max}$ and reject insufficient space. |
| [`P0-PB-05B`](../checklists/mantra-rebuild.md#pairblock-resolution) | Derive the ordered archive-part plan from the signed archive index. | Codex implemented and independently reviewed MANTRA commit `3ea3a042e71f3ed71c804839698dde51b36f64bf`. | [Source](../../../mantra/src/mantra/rebuild/archive_plan.py) · [Tests](../../../mantra/src/mantra/rebuild/tests/test_archive_plan.py) | Select 36 verified parts for the completed artifact set and expose the measured capacity values. |
| [`P0-PB-05C`](../checklists/mantra-rebuild.md#pairblock-resolution) | Enforce and retain each governed VIPER stage's declared file boundary. | Codex implements in VIPER; user reviews the guarantee, workflow cost, measured overhead, and applied diff. | [Protocol](../../../viper/src/viper/stages.py) · [Authoring](../../../viper/src/viper/authoring.py) · [Observer](../../../viper/src/viper/_workers/file_access.py) · [Worker](../../../viper/src/viper/_workers/stages.py) · [Verifier](../../../viper/src/viper/_verification/attempt.py) · [Tests](../../../viper/tests/test_stage_file_access.py) | `P0-VR-11` and the framework tradeoff review pass. |
| [`P0-PB-05D`](../checklists/mantra-rebuild.md#pairblock-resolution) | Permit a build stage to supply an unbenchmarked run's selected `model` artifact. | Codex implements and independently reviews the VIPER change. | [Verifier](../../../viper/src/viper/_verification/plan.py) · [Tests](../../../viper/tests/test_verification.py) · [Test map](../../../viper/tests/declaration_observers.toml) | `P0-VR-12` |
| [`P0-PB-05E`](../checklists/mantra-rebuild.md#pairblock-resolution) | Permit an unbenchmarked run to select a declared terminal artifact such as a replay receipt. | Codex implements and independently reviews the VIPER change. | [Run model](../../../viper/src/viper/runs.py) · [Protocol tests](../../../viper/tests/test_protocol.py) · [Relationship tests](../../../viper/tests/test_verification.py) | `P0-VR-13` |
| [`P0-PB-05F`](../checklists/mantra-rebuild.md#pairblock-resolution) | Exclude the operating system's null device from governed data-access evidence. | Codex implements and independently reviews the VIPER change. | [Observer](../../../viper/src/viper/_workers/file_access.py) · [Tests](../../../viper/tests/test_stage_file_access.py) | `P0-VR-14` |
| [`P0-PB-05G`](../checklists/mantra-rebuild.md#pairblock-resolution) | Preserve the frozen callable's workspace modules during invocation. | Codex implements and independently reviews the VIPER change. | [Loader](../../../viper/src/viper/stages.py) · [Worker](../../../viper/src/viper/_workers/stages.py) · [Tests](../../../viper/tests/test_stage_invocation.py) | `P0-VR-15` |
| [`P0-PB-05H`](../checklists/mantra-rebuild.md#pairblock-resolution) | Permit reads of Python source captured by the run's frozen Git commit. | Codex implements and independently reviews the VIPER change. | [Observer](../../../viper/src/viper/_workers/file_access.py) · [Worker](../../../viper/src/viper/_workers/stages.py) · [Tests](../../../viper/tests/test_stage_file_access.py) | `P0-VR-16` |
| [`P0-PB-05I`](../checklists/mantra-rebuild.md#pairblock-resolution) | Finalize a failed attempt after result verification rejects it. | Codex implements and independently reviews the VIPER change. | [Attempt execution](../../../viper/src/viper/execution/_attempt.py) · [Publication](../../../viper/src/viper/execution/_publication.py) · [Tests](../../../viper/tests/test_run_execution.py) | `P0-VR-17` |
| [`P0-PB-05J`](../checklists/mantra-rebuild.md#pairblock-resolution) | Accept explicit trust for prior-run source repositories during execution. | Codex implements and independently reviews the VIPER change. | [Public execution](../../../viper/src/viper/execution/__init__.py) · [Attempt execution](../../../viper/src/viper/execution/_attempt.py) · [Tests](../../../viper/tests/test_run_execution.py) | `P0-VR-18` |
| [`P0-PB-05K`](../checklists/mantra-rebuild.md#pairblock-resolution) | Reuse one authenticated external Git checkout during an execution. | Codex implemented and independently reviewed VIPER commits `08d78749` and `fe2114ef`. | [Fetcher](../../../viper/src/viper/execution/_source.py) · [Storage](../../../viper/src/viper/_verification/storage.py) · [Tests](../../../viper/tests/test_storage.py) | `P0-VR-20` |
| [`P0-PB-05L`](../checklists/mantra-rebuild.md#pairblock-resolution) | Reject invalid stored-input paths during authoring. | Codex implemented and independently reviewed VIPER commit `cdd7ec5b`. | [Input model](../../../viper/src/viper/inputs.py) · [Draft model](../../../viper/src/viper/benchmark.py) · [Tests](../../../viper/tests/test_prior_run_inputs.py) | `P0-VR-19` |
| [`P0-PB-05M`](../checklists/mantra-rebuild.md#pairblock-resolution) | Reuse one verified producer result across equal run references. | Codex implemented and independently reviewed VIPER commit `427f1894`. | [Verifier](../../../viper/src/viper/verification.py) · [Tests](../../../viper/tests/test_verification_acceptance.py) | `P0-VR-21` |
| [`P0-PB-05N`](../checklists/mantra-rebuild.md#pairblock-resolution) | Resolve one-hop runtime callers without treating imported names as callers. | Codex implemented and independently reviewed VIPER commit `98dcf084`. | [Selector](../../../viper/tools/select_impacted_tests.py) · [Tests](../../../viper/tests/test_impacted_test_selection.py) | `P0-VR-22` |
| [`P0-PB-05O`](../checklists/mantra-rebuild.md#pairblock-resolution) | Route stage-worker process calls through the shared facade. | Codex implemented and independently reviewed VIPER commit `3383713d`. | [Worker](../../../viper/src/viper/_workers/stages.py) · [Policy test](../../../viper/tests/test_process_startup.py) · [File-access tests](../../../viper/tests/test_stage_file_access.py) | `P0-VR-23` |
| [`P0-PB-06`](../checklists/mantra-rebuild.md#pairblock-resolution) | Import the 27 restored disk files and verify graph $B$. | Codex implemented and independently reviewed MANTRA through `ee8a23cd1085846a0c14bb9272c336247483a437`. | [Bindings](../../../mantra/src/mantra/rebuild/restoration.py) · [VIPER workflow](../../../mantra/src/mantra/rebuild/viper_restore.py) · [Tests](../../../mantra/src/mantra/rebuild/tests/test_viper_restore.py) · [Review](../../evidence/pairblock-reviews/p0-pb-06/ee8a23cd1085846a0c14bb9272c336247483a437.json) | `P0-VR-04`, `P0-VR-06`, and `P0-REQ-13` |
| [`P0-PB-07`](../checklists/mantra-rebuild.md#pairblock-resolution) | Replay Hopfield. | Codex independently reviewed the restoration-run linkage through `461d605af8d4dd68c903779136b0cc365fb453e4`. | [Source](../../../mantra/src/mantra/rebuild/hopfield_replay.py) · [Artifact loaders](../../../mantra/src/mantra/rebuild/loaders.py) · [Tests](../../../mantra/src/mantra/rebuild/tests/test_hopfield_replay.py) · [Review](../../evidence/pairblock-reviews/p0-pb-07/461d605af8d4dd68c903779136b0cc365fb453e4.json) | `P0-VR-07` |
| [`P0-PB-08`](../checklists/mantra-rebuild.md#pairblock-resolution) | Replay standalone MIL application. | Codex independently reviewed the restoration-run linkage through `5e822ffa289d58092a2a6b9edc5799b477e44eee`. | [Source](../../../mantra/src/mantra/rebuild/mil_replay.py) · [Artifact loaders](../../../mantra/src/mantra/rebuild/loaders.py) · [Tests](../../../mantra/src/mantra/rebuild/tests/test_mil_replay.py) · [Review](../../evidence/pairblock-reviews/p0-pb-08/5e822ffa289d58092a2a6b9edc5799b477e44eee.json) | `P0-VR-08` |
| [`P0-PB-09`](../checklists/mantra-rebuild.md#pairblock-resolution) | Freeze evidence and assess VIPER. | Codex implemented and independently reviewed RICO commit `64964135`. | [Source](../../tools/freeze_phase0.py) · [Tests](../../tests/test_freeze_phase0.py) · [Review](../../evidence/pairblock-reviews/p0-pb-09/64964135b66a4706501d9e768527241941397566.json) | `P0-VR-09` |
| [`P0-PB-09A`](../checklists/mantra-rebuild.md#pairblock-resolution) | Register and verify the frozen evidence through VIPER. | Codex implemented and independently reviewed RICO through commit `3b575be1`; the real run supplies completion evidence. | [Source](../../tools/register_phase0.py) · [Loader](../../tools/artifact_loaders.py) · [Tests](../../tests/test_register_phase0.py) · [Latest review](../../evidence/pairblock-reviews/p0-pb-09a/3b575be150cfd9691fac75d2b0586af14f665527.json) | `P0-VR-09` |
| [`P0-PB-10`](../checklists/mantra-rebuild.md#pairblock-resolution) | Validate PairBlock traceability and retain each tested-code or externally reviewed non-code lifecycle transition. | RICO owns the active controller; the user reviews lifecycle changes. | [Active source and tests](#p0-pb-10-accepted-implementation) | `P0-VR-10` |
| [`P0-PB-10A`](../checklists/mantra-rebuild.md#pairblock-resolution) | Certify the four applied PairBlocks whose preserved records predate the active receipt chain. | Codex implements and independently reviews the compatibility path. | [Implementation and gate](#p0-pb-10a-implementation-record) | `P0-VR-24` |
| [`P0-PB-10B`](../checklists/mantra-rebuild.md#pairblock-resolution) | Make typed declarations and lifecycle receipts generate every new PairBlock's human review surface. | Codex drafts the implementation; the user reviews the charter, code, gate result, and diff before acceptance. | [Charter, targets, and gate](#p0-pb-10b) | `P0-VR-26` |

### Blocks

#### Approved MANTRA integration boundary

**Requirement:** Make the existing MANTRA Git repository discoverable as the VIPER workspace, then connect the historical Hopfield replay through one MANTRA-owned VIPER adapter.

**Dependency:** The approved Hopfield target is `0.5861640938949398`; the approved MIL target is `0.6025499488874759`.

**Files introduced across `P0-PB-01`, `P0-PB-02`, and `P0-PB-07`:**

- `viper.toml` marks the MANTRA Git root as the VIPER workspace.
- `src/mantra/rebuild/hopfield_replay.py` will own the thin VIPER adapter for the historical replay.
- `src/mantra/rebuild/tests/test_hopfield_replay.py` will observe workspace resolution, declared input custody, the historical call boundary, and the produced replay receipt.

MANTRA already owns its package, tests, configuration, and historical experiment code. `viper init` targets empty directories and would generate competing structure here. The adapter will call the historical Hopfield implementation at its existing path. `P0-PB-02` identifies the complete Hopfield input set; `P0-PB-07` requires the adapter to declare that set.

#### P0-PB-02

Traces the selected Hopfield computation. It reads eleven data files and one saved encoder. Five data files are present and hash-match; six data files and the encoder are absent and restorable. The adapter will call the selected helper path with `memory=("fit",)`, `topk=1600`, and `temperature=0.055`. It will write a new prediction and receipt. Its boundary excludes the historical ten-encoder, 42-readout-per-encoder sweep. The historical prediction and report remain unchanged in $Q$.

#### P0-PB-03

Targets the v1952 seed-123460 `without_control` result in `experiments/v1952_direct_mil_control_term_ablation/diagnostics/CONTROL_TERM_MULTISEED_RESULTS.json`. Its hold PearsonDelta is `0.6025499488874759`. The scorer reads the saved single-query MIL prototype, saved teacher representations, biological descriptor files, coefficient targets, and gene labels. Its input set excludes Hopfield predictions. The runner's CUDA guard makes the historical GPU replay and CPU evaluation of stored predictions separate gates.

The standalone MIL compute graph has fifteen inputs: the base and projected
Step01 prediction files, the seed-123460 prototype, and the twelve files under
the selected Step02 `input_root` recorded in the [approved MIL artifact
set](#approved-mil-artifact-set). Its parity graph adds the historical Step02
prediction and weights and the historical Step03 prediction and weights.
These files belong to the MIL run; no edge connects them to the Hopfield replay.

#### P0-PB-04

Closes when its two implementation blocks produce every restoration binding:

- [`P0-PB-04A` source](../../../mantra/src/mantra/rebuild/restoration.py) · [tests](../../../mantra/src/mantra/rebuild/tests/test_restoration.py)
- [`P0-PB-04B` source](../../../mantra/src/mantra/rebuild/restoration.py) · [tests](../../../mantra/src/mantra/rebuild/tests/test_control_resolution.py)

#### P0-PB-05

Closes when [`P0-PB-05A` source](../../../mantra/src/mantra/rebuild/capacity.py) and its [tests](../../../mantra/src/mantra/rebuild/tests/test_capacity.py) prove capacity and `P0-PB-05B` fixes the archive-chunk order.

#### P0-PB-05B

Reads the signed `ARCHIVE_INDEX.json` and the 27 approved restoration
bindings. It selects every part of each required archive because the archive
format has no object-to-part index. The selected order is the nine
`historical_and_shared_experiments` parts followed by the twenty-five
`sota_reproducer` parts and two `later_experiments` parts, with part numbers
increasing inside each archive.

**Implementation:** inspect the [accepted source](../../../mantra/src/mantra/rebuild/archive_plan.py)
and [observing tests](../../../mantra/src/mantra/rebuild/tests/test_archive_plan.py).

The real plan must report 36 parts, a 4,294,967,296-byte largest part, a
145,574,762,417-byte download upper bound, and 811,130,091 restored bytes.
The bounded reader keeps at most one verified archive part locally.
`P0-PB-05A` must therefore record a 6,960,083,757-byte maximum simultaneous
local requirement: one 4,294,967,296-byte part, the 811,130,091 canonical
bytes, two 811,130,091-byte VIPER copies, one 221,240,428-byte temporary file,
and the 10 MiB reserve.

**Focused check:**

```bash
pytest src/mantra/rebuild/tests/test_archive_plan.py -q
ruff check src/mantra/rebuild/archive_plan.py src/mantra/rebuild/tests/test_archive_plan.py
```

**Stop condition:** stop before downloading an archive part if the signed part
sequence is incomplete, a readback identity differs, the real values differ
from the values above, or the `P0-PB-05A` capacity receipt fails.

#### P0-PB-05C

Adds an optional `file_access="declared"` policy to a VIPER stage. The worker
checks CPython-visible file-open attempts, rejects paths outside the stage's
declared inputs, outputs, and metric files, and rejects a successful return
unless every input produced a successful Python read-open. Verification checks
the stored paths against the frozen stage specification. The observer checks cooperative
code. Hostile stage code requires an operating-system sandbox. [Review the
implementation and gate](#p0-pb-05c-proposed-code).

#### P0-PB-05D

Aligns plan verification with `RunSpec`: an unbenchmarked run selects a real
artifact named `model` from any declared producer stage. A benchmarked run
continues to require a training-stage estimator because its evaluation stage
consumes that trained model. [Review the implementation and gate](#p0-pb-05d-proposed-code).

#### P0-PB-05E

Keeps the early selection check while matching it to the run type. An
unbenchmarked run may select any artifact declared by one of its stages, such
as a replay receipt. A benchmarked run must select `model`; plan verification
then requires that artifact to come from a training stage. [Review the
implementation and gate](#p0-pb-05e-proposed-code).

#### P0-PB-05F

Treat the exact path returned by `os.devnull` as runtime plumbing during a
governed stage. Reads and writes to that path neither create provenance edges
nor satisfy a declared-input read. Every other undeclared device path remains
forbidden. [Review the implementation and gate](#p0-pb-05f-proposed-code).

#### P0-PB-05G

Retain the exact workspace module objects imported while VIPER loads the frozen
stage callable. Expose those objects through Python's module registry during
the call, then restore the registry. This lets deserialization resolve the
already-loaded implementation modules without reopening repository source or
bytecode. [Review the implementation and gate](#p0-pb-05g-proposed-code).

#### P0-PB-05H

Derive the exact tracked Python paths from the run's frozen Git source before
governed access begins. Permit those implementation reads while retaining the
declared data boundary for every untracked path and tracked non-Python file.
[Review the implementation and gate](#p0-pb-05h-proposed-code).

#### P0-PB-05I

When result verification rejects an attempt that completed its stages, publish
the failed attempt at `attempts/<id>/resolved.yaml` and preserve the original
verification message in `AttemptFailure.message`. [Review the implementation
and gate](#p0-pb-05i-proposed-code).

#### P0-PB-05J

Accept an optional set of trusted source-repository URLs on VIPER execution
entry points. Verification trusts the current run's source and adds only the
repositories in that caller-supplied set. This lets a RICO run verify and load
MANTRA prior-run artifacts without granting implicit trust to every referenced
repository. [Review the implementation and gate](#p0-pb-05j-proposed-code).

#### P0-PB-05K

Reuse one verified checkout for files from the same external repository and
commit. [Inspect the implementation and gate](#p0-pb-05k-implementation-record).

#### P0-PB-05L

Reject a stored-input path outside `inputs/` during authoring, before pointer
publication or execution. [Inspect the implementation and gate](#p0-pb-05l-implementation-record).

#### P0-PB-05M

Verify an exact producer run once per verification pass while retaining every
pointer-specific check. [Inspect the implementation and gate](#p0-pb-05m-implementation-record).

#### P0-PB-05N

Exclude import bindings from a changed declaration's runtime caller set while
retaining fallback for a changed unobserved import. [Inspect the implementation
and gate](#p0-pb-05n-implementation-record).

#### P0-PB-05O

Route stage-worker process launches through VIPER's spawn-safe subprocess
facade. [Inspect the implementation and gate](#p0-pb-05o-implementation-record).

#### P0-PB-06

The first VIPER stage authenticates the signed control package, resolves the 27
`RestorationBinding` records, and writes the binding and control receipts. The
second stage reads the 27 files at their approved MANTRA paths on the restored
GPU disk. It checks each source byte count and SHA-256, copies the file to its
named VIPER output, checks the output identity, and writes the archive plan,
capacity receipt, and disk-import receipt.

The Hopfield and MIL stages select these outputs through `run_artifact()`.
VIPER can therefore follow each model input to the signed binding records and
the exact disk file imported by `P0-PB-06`.

**Implementation:** review the active [binding resolver](../../../mantra/src/mantra/rebuild/restoration.py),
[VIPER workflow](../../../mantra/src/mantra/rebuild/viper_restore.py),
[resolver tests](../../../mantra/src/mantra/rebuild/tests/test_control_resolution.py),
and [VIPER tests](../../../mantra/src/mantra/rebuild/tests/test_viper_restore.py).

**Gate:** the focused tests authenticate the control package, reject a changed
disk file, prove the declared VIPER inputs and outputs, and prove that each
source and output identity matches its binding. VIPER verification must pass
for the real run and fail after removing either a required input edge or a
restored-file output edge.

#### P0-PB-07

Runs one selected historical row through two VIPER stages. Prediction reads the
saved encoder and the ten non-scoring data inputs, then calls
`load_arrays_for_scale(1.3, ...)`, `load_saved_encoder(...)`, and
`predict_raw_gene_readout(..., memory_splits=("fit",), topk=1600,
temperature=0.055)`. Evaluation adds the hold truth, calls the historical
scorer, and compares the new hold PearsonDelta with `0.5861640938949398`.

The accepted [source](../../../mantra/src/mantra/rebuild/hopfield_replay.py)
and [observing tests](../../../mantra/src/mantra/rebuild/tests/test_hopfield_replay.py)
implement this boundary. The full historical sweep and its output paths remain
untouched. CPU execution is supported; acceptance uses the user-approved
numerical tolerance because the historical report omits its device.

#### P0-PB-08

Runs the saved v1952 seed-123460 MIL prototype through the historical Step02
and Step03 application functions in two VIPER stages. The application stage
consumes its 15 standalone compute inputs and produces predictions, fitted
weights, and scores. The evaluation stage consumes those products and the four
historical parity artifacts. The MIL graph consumes no Hopfield-rebuild output.

The accepted [source](../../../mantra/src/mantra/rebuild/mil_replay.py)
and [observing tests](../../../mantra/src/mantra/rebuild/tests/test_mil_replay.py)
implement this boundary. The L4 parity gate compares prediction keys, dtypes,
shapes, and values; compares the deterministic fitted-weight archive hashes;
and reproduces the Step02 and Step03 hold scores before closing the block. A
CPU diagnostic may waive artifact parity but cannot close `P0-VR-08`.

#### P0-PB-09

Hashes the capacity, restoration, graph-verification, severed-graph,
Hopfield-replay, and MIL-replay receipts into one Phase 0 index. It also hashes
the VIPER usefulness ledger and rejects a confirmed-defect entry that lacks an
independent check.

The accepted [evidence freezer](../../tools/freeze_phase0.py) and its
[tests](../../tests/test_freeze_phase0.py) implement this boundary. The real
index is written after restoration and both replay runs supply their receipts.

#### P0-PB-09A

Runs one RICO-rooted VIPER stage after the index is frozen. The stage consumes
the restoration evidence bundle and replay receipts through prior-run artifact
references, consumes the RICO evidence directly, verifies every indexed byte
count and SHA-256, and emits the terminal Phase 0 registration receipt.

The accepted [registration source](../../tools/register_phase0.py) and
[observing tests](../../tests/test_register_phase0.py) implement this boundary.
The successful run is retained as [run identity](../../evidence/phase0/rico/phase0_registration_run.json)
and [terminal receipt](../../evidence/phase0/rico/phase0_registration_receipt.json).

#### Approved Hopfield artifact set

The eleven data files below are relative to `experiments/v1938_sota_clean_repro/inputs/`.

| Relative path | Bytes | SHA-256 | Local state |
|---|---:|---|---|
| `core83/features.npz` | 652,627 | `a5830b935877fa9cfdbe42d294ebf036a362a20a62958d2a8b8c17e193389f8c` | Present |
| `response40/features.npz` | 320,705 | `f3b4f9e5c828b383821323c43246121fe166fbf62562b9753e9b9d679348f441` | Present |
| `family64/features.npz` | 506,130 | `766eb05aae7ab17556fb737524bc95659399d7a82f08d6f7baaf99045ebb8f57` | Present |
| `gene_shift/features.npz` | 34,605,824 | `744ae998b0158c672a0bc8adcbe7a417cf8a99b0915d71a713be6a116529a6f7` | Present |
| `response_programs/response_program_blocks_16.json` | 23,092 | `67ec90e5a39b008067f6ac85958053b6c67fca029c00f2be6c724378e3b78fff` | Present |
| `coefficient_targets/fit_tune_ctrl19_matched_response_coefficients.npz` | 9,470,125 | `387b195778ce7c5a5b33024b3a841fdb9a294bc44ff35ab19d32d8b07da1e5fd` | Restore |
| `gene_delta_labels/fit_tune_ctrl19_matched_log1p_cp10k_gene_deltas.npz` | 64,472,752 | `4df4d1fd20e26f43a19c2108d6432a8597aecaee99838af09eed91f178cde5b3` | Restore |
| `gene_delta_labels/hold_global_control_log1p_cp10k_gene_deltas.npz` | 5,087,281 | `30ab233c4563a27afbb8680ca44ead200db1066da1cb6a64c0f7496e8adf1585` | Restore |
| `response_programs/response_program_block_contract_16.npz` | 4,504 | `a7e551e8e2f5a637ba5c8801d50b9109007e225536a213bd3bca2894c6331166` | Restore |
| `response_programs/response_program_rotation_210d.npz` | 4,102,000 | `85cf1d7dff2ece81b9cbe7d9bb2b9bcb2aaed3dba48d948a4234a9f275301364` | Restore |
| `response_programs/response_program_similarity_graph.npz` | 609,109 | `a9680ddf0082a1072328e0329bb8e0c63b251375c3d22ec7ff4b342605f9ec10` | Restore |

The selected encoder is:

`experiments/v1938_sota_clean_repro/runs/clean_shared_mil_proto_hyperparam_sweep_20260714T063000Z/base_step01/base_lr2e4/candidates/mixed_src_snk_ripple_raw_pen1_base_lr2e4/checkpoints/weights/BASE_STEP01_MODEL_WEIGHTS.npz`

Its byte count is `1,084,512`; its SHA-256 is `2433527c3b23b66a16cedc0f7bc43867e4298af4d7a0733b202a8018ba876610`; it requires restoration.

The Hopfield parity set $Q_H$ is:

| Artifact path | Bytes | SHA-256 | Local state |
|---|---:|---|---|
| `experiments/v1938_sota_clean_repro/runs/clean_shared_mil_proto_hyperparam_sweep_20260714T063000Z/base_step01/base_lr2e4/candidates/mixed_src_snk_ripple_raw_pen1_base_lr2e4/diagnostics/BASE_STEP01_RESULT_REPORT.json` | 6,268 | `8e690f5e1ba18846e34cccec3f48a84d4adf013d7ef64731b13ff06cca9c4529` | Present |
| `experiments/v1938_sota_clean_repro/runs/matrix_fit_only_bold_step02_20260715T083000Z/diagnostics/RAW_GENE_READOUT_TUNING_FIT_ONLY_RESULTS.json` | 656,400 | `cbb3d786ff85ce15eed5e16335cf7d9a28c7ad3f076b6f019c58e4a16c140a10` | Present |
| `experiments/v1938_sota_clean_repro/runs/matrix_fit_only_bold_step02_20260715T083000Z/out/raw_gene_readout_tuning_fit_only/best/RAW_GENE_PREDICTIONS.npz` | 38,397,104 | `d7180c4669a11b0b2fb184814aafb48ebafe75b02e4bd07998c337aa64dc59b7` | Restore |

#### Approved MIL artifact set

The exact destination, archive, byte count, and SHA-256 for each row live in
[`MIL_RESTORATIONS`](../../../mantra/src/mantra/rebuild/viper_restore.py). The
fifteen compute inputs are:

| Name | MANTRA destination |
|---|---|
| Base Step01 predictions | `experiments/v1938_sota_clean_repro/runs/checkpoint_bootstrap_20260713T030000Z/base_step01/candidates/mixed_src_snk_ripple_raw_pen1_directw2p0_local/checkpoints/mean/HOPFIELD_PREDICTIONS.npz` |
| Projected Step01 predictions | `experiments/v1938_sota_clean_repro/runs/checkpoint_bootstrap_20260713T030000Z/projected_step01/candidates/aggregate_proto64_scale2p8_temp0p095/checkpoints/mean/HOPFIELD_PREDICTIONS.npz` |
| Seed-123460 prototype | `experiments/v1952_direct_mil_control_term_ablation/runs/control_ablation_seed_123460/checkpoints/transformed_training_memory/derived/mil_proto/mil_proto_identity_vectors.npz` |
| Core83 features | `experiments/v1938_sota_clean_repro/runs/matrix_fit_only_bold_step02_20260715T083000Z/reproduce_top_donor_long_train_standard_spread/out/input_root/inputs/core83/features.npz` |
| Family64 features | `experiments/v1938_sota_clean_repro/runs/matrix_fit_only_bold_step02_20260715T083000Z/reproduce_top_donor_long_train_standard_spread/out/input_root/inputs/family64/features.npz` |
| Response40 features | `experiments/v1938_sota_clean_repro/runs/matrix_fit_only_bold_step02_20260715T083000Z/reproduce_top_donor_long_train_standard_spread/out/input_root/inputs/response40/features.npz` |
| Control-program features | `experiments/v1938_sota_clean_repro/runs/matrix_fit_only_bold_step02_20260715T083000Z/reproduce_top_donor_long_train_standard_spread/out/input_root/inputs/control_state/ot_matched_control_program_features.npz` |
| Coefficient targets | `experiments/v1938_sota_clean_repro/runs/matrix_fit_only_bold_step02_20260715T083000Z/reproduce_top_donor_long_train_standard_spread/out/input_root/inputs/coefficient_targets/fit_tune_response_coefficients.npz` |
| Fit/tune gene deltas | `experiments/v1938_sota_clean_repro/runs/matrix_fit_only_bold_step02_20260715T083000Z/reproduce_top_donor_long_train_standard_spread/out/input_root/inputs/gene_delta_labels/fit_tune_ctrl19_matched_log1p_cp10k_gene_deltas.npz` |
| Hold gene deltas | `experiments/v1938_sota_clean_repro/runs/matrix_fit_only_bold_step02_20260715T083000Z/reproduce_top_donor_long_train_standard_spread/out/input_root/inputs/gene_delta_labels/hold_global_control_log1p_cp10k_gene_deltas.npz` |
| Hold control shift | `experiments/v1938_sota_clean_repro/runs/matrix_fit_only_bold_step02_20260715T083000Z/reproduce_top_donor_long_train_standard_spread/out/input_root/inputs/control_state/ot_matched_control_program_gene_shift.npz` |
| Response-block contract | `experiments/v1938_sota_clean_repro/runs/matrix_fit_only_bold_step02_20260715T083000Z/reproduce_top_donor_long_train_standard_spread/out/input_root/inputs/response_programs/response_program_block_contract_16.npz` |
| Response rotation | `experiments/v1938_sota_clean_repro/runs/matrix_fit_only_bold_step02_20260715T083000Z/reproduce_top_donor_long_train_standard_spread/out/input_root/inputs/response_programs/response_program_rotation_210d.npz` |
| Cell-program projections | `experiments/v1938_sota_clean_repro/runs/matrix_fit_only_bold_step02_20260715T083000Z/reproduce_top_donor_long_train_standard_spread/out/input_root/inputs/cellwise/cell_program_projections.npz` |
| Matched cell programs | `experiments/v1938_sota_clean_repro/runs/matrix_fit_only_bold_step02_20260715T083000Z/reproduce_top_donor_long_train_standard_spread/out/input_root/inputs/cellwise/ot_matched_cell_programs.npz` |

The four parity files are:

| Name | MANTRA destination |
|---|---|
| Step02 predictions | `experiments/v1953_direct_mil_simplified_scorer_promotion/runs/simplified_scorer_full_stack_20260725T000500Z/step02_step03/checkpoints/mean/STEP02_SLOT_COUPLED_PREDICTIONS.npz` |
| Step02 weights | `experiments/v1953_direct_mil_simplified_scorer_promotion/runs/simplified_scorer_full_stack_20260725T000500Z/step02_step03/checkpoints/weights/STEP02_MODEL_WEIGHTS.npz` |
| Step03 predictions | `experiments/v1953_direct_mil_simplified_scorer_promotion/runs/simplified_scorer_full_stack_20260725T000500Z/step02_step03/checkpoints/mean/STEP03_GENE_PREDICTIONS.npz` |
| Step03 weights | `experiments/v1953_direct_mil_simplified_scorer_promotion/runs/simplified_scorer_full_stack_20260725T000500Z/step02_step03/checkpoints/weights/STEP03_RIDGE_WEIGHTS.npz` |

Seven compute destinations have no row in the signed filesystem manifest.
Their approved archive and digest select a signed content-object row directly.
The other twelve files also require their filesystem row to agree with the
approved archive and digest.

The selected Hopfield source closure contains the following seventeen present, tracked Python files. Its source-restoration set is empty.

```text
experiments/v1938_sota_clean_repro/runs/matrix_fit_only_bold_step02_20260715T083000Z/scripts/run_raw_gene_readout_tuning.py
experiments/v1938_sota_clean_repro/runs/matrix_fit_only_bold_step02_20260715T083000Z/scripts/run_raw_gene_readout_tuning_fit_only.py
experiments/v1938_sota_clean_repro/src/runtime/config.py
experiments/v1938_sota_clean_repro/src/runtime/layout.py
experiments/v1938_sota_clean_repro/src/shared/io.py
experiments/v1938_sota_clean_repro/src/shared/logging.py
experiments/v1938_sota_clean_repro/src/shared/metrics.py
experiments/v1938_sota_clean_repro/src/shared/determinism.py
experiments/v1938_sota_clean_repro/src/shared/splits.py
experiments/v1938_sota_clean_repro/src/shared/normalization.py
experiments/v1938_sota_clean_repro/src/step01/hopfield/encoder.py
experiments/v1938_sota_clean_repro/src/step01/hopfield/config.py
experiments/v1938_sota_clean_repro/src/step01/hopfield/contract.py
experiments/v1938_sota_clean_repro/src/step01/hopfield/inputs.py
experiments/v1938_sota_clean_repro/src/step01/hopfield/transforms.py
experiments/v1938_sota_clean_repro/src/step01/hopfield/loader.py
experiments/v1938_sota_clean_repro/src/step01/hopfield/spec.py
```

#### MIL compute finding

The v1952 training entrypoint contains an explicit CUDA guard:

```python
device = configure_reproducible_torch(
    seed=int(specification["training"]["seeds"][0]),
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu"),
)
if device.type != "cuda":
    raise RuntimeError("CUDA is required")
```

That guard establishes the historical execution policy. The active training code selects fused optimizers only on CUDA:

```python
fused=(device.type == "cuda" and bool(config.training.optimizer_fused_on_cuda))
```

The inspected teacher, student, and proposal paths contain zero unconditional `.cuda()` calls. Phase 0 therefore separates two claims: an L4-class GPU is required for acceptance-level historical replay, while a later CPU portability probe may remove only the guard and measure whether one seed completes within local memory. The recorded L4 run remains the parity reference.

## 10. Implementation records

The [Phase 0 ownership record](#phase-0-ownership-record) records each block's scope, owner, implementation link, and gate. The master checklist records resolution status.

### Repeatable block loop

This section instantiates `MC-07` from the global master-checklist contract.
Use the same sequence for every proposed implementation below. Run these
commands from the already activated Conda environment named `mantra`.

1. Open the block's **Source and tests** link in the checklist and review the
   linked staging files.
2. Before applying the proposal, Codex runs its staging gate. A pass changes
   `Drafting` to `Review` and writes the gate receipt:

   ```bash
   cd /Users/machina/Developer/ChatGPT/RICO
   python -m tools.pairblock_status.pairblock_controller \
     --repository "$PWD" gate BLOCK_ID
   ```

3. After the user approves the reviewed proposal, Codex records the approval:

   ```bash
   cd /Users/machina/Developer/ChatGPT/RICO
   python -m tools.pairblock_status.pairblock_controller \
     --repository "$PWD" advance BLOCK_ID approve \
     --evidence-kind external \
     --evidence-target 'User approval in the Codex task' \
     --evidence-revision 'CODEX_MESSAGE_ID'
   ```

A block without runnable code uses two external-evidence transitions. `submit`
moves the completed trace to `Review`; `confirm` records the user's decision
and closes the block:

```bash
cd /Users/machina/Developer/ChatGPT/RICO
python -m tools.pairblock_status.pairblock_controller \
  --repository "$PWD" advance BLOCK_ID submit \
  --evidence-kind external \
  --evidence-target 'Completed contract trace' \
  --evidence-revision 'CONTRACT_REVISION'
python -m tools.pairblock_status.pairblock_controller \
  --repository "$PWD" advance BLOCK_ID confirm \
  --evidence-kind external \
  --evidence-target 'User approval in the Codex task' \
  --evidence-revision 'CODEX_MESSAGE_ID'
```

4. The implementation owner applies the proposal to the active paths and runs
   the block's **Applied check**. Codex commits and pushes that bounded change,
   then performs an independent code review of the exact base commit, result
   commit, owned paths, and canonical diff digest. Codex records the checked
   invariants, findings, mechanical evidence, exclusions, and verdict under
   `evidence/pairblock-reviews/BLOCK_ID/`. Every finding is repaired, retested,
   recommitted, and rereviewed before acceptance.

5. An approving review receipt permits the `accept` transition:

   ```bash
   cd /Users/machina/Developer/ChatGPT/RICO
   python -m tools.pairblock_status.pairblock_controller \
     --repository "$PWD" advance BLOCK_ID accept \
     --evidence-kind artifact \
     --evidence-target 'OWNING_REPOSITORY_AND_ACTIVE_PATHS' \
     --evidence-revision 'ACCEPTED_GIT_COMMIT'
   ```

   The same atomic checklist update replaces each
   `staging/BLOCK_ID/ACTIVE_PATH` link with `ACTIVE_PATH` and removes the
   proposal-only **Source and tests** link. The transition fails when a staging
   link names another PairBlock, so an `Applied` row always links to the active
   implementation.

6. After the block's declared VIPER run exists and verifies, Codex records its
   graph reference. This changes `Applied` to `Complete` and checks the block:

   ```bash
   cd /Users/machina/Developer/ChatGPT/RICO
   python -m tools.pairblock_status.pairblock_controller \
     --repository "$PWD" advance BLOCK_ID register \
     --evidence-kind artifact \
     --evidence-target 'VIPER_RUN_OR_ARTIFACT_REFERENCE' \
     --evidence-revision 'VIPER_CONTENT_ID'
   ```

`BLOCK_ID` and the quoted evidence values are replaced with the exact block
and retained result. The controller rejects a skipped transition, an unresolved
dependency, a changed proposal during its gate, or missing evidence.

### Repository evidence protocol

RICO records the contract, checklist, approvals, and lifecycle receipts. MANTRA
owns Phase 0 restoration and replay source. RICO owns reconstruction source from
Phase 1 onward. A proposal-gate receipt supports `Review` or `Approved`. The
implementation receipt proves that the repository named by the PairBlock's code
boundary contains the accepted code.

An `Applied` transition requires one approving review receipt with the owning
repository identity, verified base and result commits, exact owned paths, the
canonical diff SHA-256, focused-test result, checked invariants, findings,
exclusions, and verdict. The canonical diff uses the command defined by the
global master-checklist contract. Every finding requires a later repaired
commit and approving review receipt. A `Complete` transition then requires the
VIPER record named by the block's gate.

Any task-created branch must be merged into the owning repository's default
branch before the PairBlock closes. The closure gate compares the local and
upstream default-branch commits, confirms that the default branch contains the
accepted implementation commit, confirms that no worktree retains the task
branch, and then removes the merged local branch. The gate never operates on a
branch or worktree that predates this rebuild.

This project rule instantiates the global lifecycle-evidence contract. Git
supplies the immutable commit identities and commit comparison. in-toto and
SLSA supply the digest-bound attestation model. W3C PROV supplies the distinction
between the changed source, the review or test activity, and the responsible
actor. The exact receipt fields and canonical diff command are local protocol
choices.

### Record index

| Block | Record |
|---|---|
| [`P0-PB-01`](../checklists/mantra-rebuild.md#pairblock-resolution) | [Accepted implementation](#p0-pb-01-accepted-implementation) |
| [`P0-PB-02`](../checklists/mantra-rebuild.md#pairblock-resolution) | [Block](#p0-pb-02) |
| [`P0-PB-03`](../checklists/mantra-rebuild.md#pairblock-resolution) | [Block](#p0-pb-03) |
| [`P0-PB-04`](../checklists/mantra-rebuild.md#pairblock-resolution) | [Block](#p0-pb-04) |
| [`P0-PB-04A`](../../../mantra/src/mantra/rebuild/restoration.py) | [Accepted source](../../../mantra/src/mantra/rebuild/restoration.py) · [Tests](../../../mantra/src/mantra/rebuild/tests/test_restoration.py) · MANTRA `2304674e1fc9730801d1afe39edc7585c81081f4` |
| [`P0-PB-04B`](../../../mantra/src/mantra/rebuild/restoration.py) | [Accepted source](../../../mantra/src/mantra/rebuild/restoration.py) · [Tests](../../../mantra/src/mantra/rebuild/tests/test_control_resolution.py) · [Latest review](../../evidence/pairblock-reviews/p0-pb-04b/75e7ce38dc85918c1f593886f20ed33601daa288.json) |
| [`P0-PB-05`](../checklists/mantra-rebuild.md#pairblock-resolution) | [Block](#p0-pb-05) |
| [`P0-PB-05A`](../../../mantra/src/mantra/rebuild/capacity.py) | [Accepted source](../../../mantra/src/mantra/rebuild/capacity.py) · [Tests](../../../mantra/src/mantra/rebuild/tests/test_capacity.py) · MANTRA `af4e589451a90a88f59c806b12a90e74e2bba043` |
| [`P0-PB-05B`](../../../mantra/src/mantra/rebuild/archive_plan.py) | [Accepted source](../../../mantra/src/mantra/rebuild/archive_plan.py) · [Tests](../../../mantra/src/mantra/rebuild/tests/test_archive_plan.py) · [Review receipt](../../evidence/pairblock-reviews/p0-pb-05b/3ea3a042e71f3ed71c804839698dde51b36f64bf.json) |
| [`P0-PB-05C`](../checklists/mantra-rebuild.md#pairblock-resolution) | [Protocol](../../../viper/src/viper/stages.py) · [Authoring](../../../viper/src/viper/authoring.py) · [Observer](../../../viper/src/viper/_workers/file_access.py) · [Worker](../../../viper/src/viper/_workers/stages.py) · [Verifier](../../../viper/src/viper/_verification/attempt.py) · [Tests](../../../viper/tests/test_stage_file_access.py) · [Gate](#p0-pb-05c-proposed-code) |
| [`P0-PB-05D`](../checklists/mantra-rebuild.md#pairblock-resolution) | [Verifier](../../../viper/src/viper/_verification/plan.py) · [Tests](../../../viper/tests/test_verification.py) · [Test map](../../../viper/tests/declaration_observers.toml) · [Gate](#p0-pb-05d-proposed-code) |
| [`P0-PB-05E`](../checklists/mantra-rebuild.md#pairblock-resolution) | [Run model](../../../viper/src/viper/runs.py) · [Protocol tests](../../../viper/tests/test_protocol.py) · [Relationship tests](../../../viper/tests/test_verification.py) · [Gate](#p0-pb-05e-proposed-code) |
| [`P0-PB-05F`](../checklists/mantra-rebuild.md#pairblock-resolution) | [Observer](../../../viper/src/viper/_workers/file_access.py) · [Tests](../../../viper/tests/test_stage_file_access.py) · [Gate](#p0-pb-05f-proposed-code) |
| [`P0-PB-05G`](../checklists/mantra-rebuild.md#pairblock-resolution) | [Loader](../../../viper/src/viper/stages.py) · [Worker](../../../viper/src/viper/_workers/stages.py) · [Tests](../../../viper/tests/test_stage_invocation.py) · [Gate](#p0-pb-05g-proposed-code) |
| [`P0-PB-05H`](../checklists/mantra-rebuild.md#pairblock-resolution) | [Observer](../../../viper/src/viper/_workers/file_access.py) · [Worker](../../../viper/src/viper/_workers/stages.py) · [Tests](../../../viper/tests/test_stage_file_access.py) · [Gate](#p0-pb-05h-proposed-code) |
| [`P0-PB-05I`](../checklists/mantra-rebuild.md#pairblock-resolution) | [Attempt](../../../viper/src/viper/execution/_attempt.py) · [Publication](../../../viper/src/viper/execution/_publication.py) · [Tests](../../../viper/tests/test_run_execution.py) · [Gate](#p0-pb-05i-proposed-code) |
| [`P0-PB-05J`](../checklists/mantra-rebuild.md#pairblock-resolution) | [Public execution](../../../viper/src/viper/execution/__init__.py) · [Attempt execution](../../../viper/src/viper/execution/_attempt.py) · [Tests](../../../viper/tests/test_run_execution.py) · [Gate](#p0-pb-05j-proposed-code) |
| [`P0-PB-05K`](../checklists/mantra-rebuild.md#pairblock-resolution) | [Fetcher](../../../viper/src/viper/execution/_source.py) · [Storage](../../../viper/src/viper/_verification/storage.py) · [Tests](../../../viper/tests/test_storage.py) · [Gate](#p0-pb-05k-implementation-record) |
| [`P0-PB-05L`](../checklists/mantra-rebuild.md#pairblock-resolution) | [Input model](../../../viper/src/viper/inputs.py) · [Draft model](../../../viper/src/viper/benchmark.py) · [Tests](../../../viper/tests/test_prior_run_inputs.py) · [Gate](#p0-pb-05l-implementation-record) |
| [`P0-PB-05M`](../checklists/mantra-rebuild.md#pairblock-resolution) | [Verifier](../../../viper/src/viper/verification.py) · [Tests](../../../viper/tests/test_verification_acceptance.py) · [Gate](#p0-pb-05m-implementation-record) |
| [`P0-PB-05N`](../checklists/mantra-rebuild.md#pairblock-resolution) | [Selector](../../../viper/tools/select_impacted_tests.py) · [Tests](../../../viper/tests/test_impacted_test_selection.py) · [Gate](#p0-pb-05n-implementation-record) |
| [`P0-PB-05O`](../checklists/mantra-rebuild.md#pairblock-resolution) | [Worker](../../../viper/src/viper/_workers/stages.py) · [Policy test](../../../viper/tests/test_process_startup.py) · [File-access tests](../../../viper/tests/test_stage_file_access.py) · [Gate](#p0-pb-05o-implementation-record) |
| [`P0-PB-06`](../checklists/mantra-rebuild.md#pairblock-resolution) | [Bindings](../../../mantra/src/mantra/rebuild/restoration.py) · [VIPER workflow](../../../mantra/src/mantra/rebuild/viper_restore.py) · [Artifact loaders](../../../mantra/src/mantra/rebuild/loaders.py) · [Tests](../../../mantra/src/mantra/rebuild/tests/test_viper_restore.py) · [Gate](#p0-pb-06-proposed-code) · [Review](../../evidence/pairblock-reviews/p0-pb-06/ee8a23cd1085846a0c14bb9272c336247483a437.json) |
| [`P0-PB-07`](../checklists/mantra-rebuild.md#pairblock-resolution) | [Source](../../../mantra/src/mantra/rebuild/hopfield_replay.py) · [Artifact loaders](../../../mantra/src/mantra/rebuild/loaders.py) · [Tests](../../../mantra/src/mantra/rebuild/tests/test_hopfield_replay.py) · [Gate](#p0-pb-07-accepted-implementation) · [Review](../../evidence/pairblock-reviews/p0-pb-07/461d605af8d4dd68c903779136b0cc365fb453e4.json) |
| [`P0-PB-08`](../checklists/mantra-rebuild.md#pairblock-resolution) | [Source](../../../mantra/src/mantra/rebuild/mil_replay.py) · [Artifact loaders](../../../mantra/src/mantra/rebuild/loaders.py) · [Tests](../../../mantra/src/mantra/rebuild/tests/test_mil_replay.py) · [Gate](#p0-pb-08-accepted-implementation) · [Review](../../evidence/pairblock-reviews/p0-pb-08/5e822ffa289d58092a2a6b9edc5799b477e44eee.json) |
| [`P0-PB-09`](../checklists/mantra-rebuild.md#pairblock-resolution) | [Source](../../tools/freeze_phase0.py) · [Tests](../../tests/test_freeze_phase0.py) · [Gate](#p0-pb-09-accepted-implementation) · [Review](../../evidence/pairblock-reviews/p0-pb-09/64964135b66a4706501d9e768527241941397566.json) |
| [`P0-PB-09A`](../checklists/mantra-rebuild.md#pairblock-resolution) | [Source](../../tools/register_phase0.py) · [Loader](../../tools/artifact_loaders.py) · [Tests](../../tests/test_register_phase0.py) · [Gate](#p0-pb-09a-accepted-implementation) · [Latest review](../../evidence/pairblock-reviews/p0-pb-09a/3b575be150cfd9691fac75d2b0586af14f665527.json) |
| [`P0-PB-10`](../checklists/mantra-rebuild.md#pairblock-resolution) | [Active implementation](#p0-pb-10-accepted-implementation) |
| [`P0-PB-10A`](../checklists/mantra-rebuild.md#pairblock-resolution) | [Controller](../../tools/pairblock_status/pairblock_controller.py) · [Profile](../../tools/pairblock_status/profile.py) · [Validator](../../tools/pairblock_status/checklist_profile.py) · [Tests](../../tests/pairblock_status/test_pairblock_controller.py) · [Gate](#p0-pb-10a-implementation-record) |

A pending row links its block definition and checklist state while omitting an implementation body.

### Accepted implementation

#### P0-PB-01

**Resolution status:** [Master checklist](../checklists/mantra-rebuild.md#pairblock-resolution)

**Requirement:** Mark the MANTRA Git root as the VIPER workspace and verify the Conda environment named `mantra` uses Python 3.13 with `viper-provenance` installed.

**Dependency:** The Conda environment named `mantra` exists.

##### `P0-PB-01` accepted implementation

**Code boundary:** One applied MANTRA file and its environment commands follow.

**File: `viper.toml`**

```toml
[workspace]
schema_version = 2
```

**Install:**

```bash
cd /Users/machina/Developer/ChatGPT/mantra
conda activate mantra
python -m pip install viper-provenance
```

**Focused check:**

```bash
cd /Users/machina/Developer/ChatGPT/mantra
conda activate mantra
python -c 'import os; print(os.environ.get("CONDA_DEFAULT_ENV"))'
python -c 'import sys; print(sys.executable); print(sys.version)'
python -c 'from importlib.metadata import version; import viper; print(version("viper-provenance")); print(viper.__file__)'
python -c 'from pathlib import Path; from viper.repository import resolve_root; print(resolve_root(Path.cwd()))'
```

**Gate:** The commands identify `mantra` as the active Conda environment, Python 3.13, the installed `viper-provenance` version, a `viper` module under that environment, and `/Users/machina/Developer/ChatGPT/mantra` as the resolved VIPER root. `P0-PB-06` must register this output in the VIPER graph before Phase 0 closes.

**Stop condition:** Stop before `P0-PB-02` if any value differs. Stop before `P0-PB-07` if its focused test shows that the adapter reads an undeclared input.

**Git evidence:** MANTRA commit `467d7d3dcdfcbcaaf40ab40a419ef89096bd465f` contains `viper.toml`. The environment check resolved the Conda environment `mantra`, Python 3.13.15, `viper-provenance` 0.1.0a3, and the MANTRA Git root.

### Proposed implementation

#### P0-PB-04A

**Resolution status:** [Master checklist](../checklists/mantra-rebuild.md#pairblock-resolution)

**Requirement:** Represent one canonical MANTRA destination, its signed archive member, and its expected byte identity. Validate exact fields, normalized paths, content-addressed member names, unique destinations, order, and full missing-file coverage.

**Dependency:** The `RestorationBinding` definition in Section 4 and the approved missing-file identities in graph $B$.

##### `P0-PB-04A` accepted implementation

**Code boundary:** MANTRA owns these implementation paths:

- [`src/mantra/rebuild/__init__.py`](../../../mantra/src/mantra/rebuild/__init__.py)
- [`src/mantra/rebuild/restoration.py`](../../../mantra/src/mantra/rebuild/restoration.py)
- [`src/mantra/rebuild/tests/test_restoration.py`](../../../mantra/src/mantra/rebuild/tests/test_restoration.py)

**Focused check:**

```bash
cd /Users/machina/Developer/ChatGPT/mantra
PYTHONPATH="$PWD/src" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
python -m pytest \
  --rootdir="$PWD/src" \
  --confcutdir="$PWD/src" \
  src/mantra/rebuild/tests/test_restoration.py -q
```

**Gate:** Every `P0-PB-04A` rejection case passes, and the valid binding fixture survives full-set validation.

**Stop condition:** Return the proposal for revision when any declared field, path rule, identity rule, coverage rule, or focused test lacks an observing assertion.

**Evidence:** The proposal gate passed `17` tests before approval. That receipt supports the approved proposal. The MANTRA implementation receipt defined above supports `Applied`; VIPER registration supports `Complete`.

#### P0-PB-04B

**Resolution status:** [Master checklist](../checklists/mantra-rebuild.md#pairblock-resolution)

**Requirement:** Accept records only after MANTRA's existing archive verifier, or an equivalent retained signature-and-checksum procedure, authenticates their control files. Resolve each required destination through the filesystem manifest. Follow symlinks only within `/home/machina/MANTRA`. Join the resolved file digest to exactly one row in its `object_archive_id` manifest. Preserve the requested destination in the resulting `RestorationBinding`.

**Dependency:** The `RestorationBinding` value type proposed in `P0-PB-04A`; the signed release, archive index, filesystem manifest, and required object manifests identified in the Phase 0 inspection evidence.

##### `P0-PB-04B` accepted implementation

**Code boundary:** MANTRA owns the cumulative implementation at these paths:

- [`src/mantra/rebuild/__init__.py`](../../../mantra/src/mantra/rebuild/__init__.py)
- [`src/mantra/rebuild/restoration.py`](../../../mantra/src/mantra/rebuild/restoration.py)
- [`src/mantra/rebuild/tests/test_restoration.py`](../../../mantra/src/mantra/rebuild/tests/test_restoration.py)
- [`src/mantra/rebuild/tests/test_control_resolution.py`](../../../mantra/src/mantra/rebuild/tests/test_control_resolution.py)

**Focused check:**

```bash
cd /Users/machina/Developer/ChatGPT/mantra
python -m ruff check src/mantra/rebuild && \
PYTHONPATH="$PWD/src" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
python -m pytest \
  --rootdir="$PWD/src" \
  --confcutdir="$PWD/src" \
  src/mantra/rebuild/tests/test_restoration.py \
  src/mantra/rebuild/tests/test_control_resolution.py -q
```

**Gate:** Ruff passes. All `P0-PB-04A` tests still pass. The `P0-PB-04B` tests resolve both a regular file and the observed absolute historical symlink, use `object_archive_id`, and reject absent or duplicate paths, symlink escape or cycles, mismatched file or object identity, undeclared archives, malformed control records, and invalid revisions.

**Stop condition:** Return the proposal for revision unless each required destination stays inside the archived MANTRA root, resolves through one path and object row, matches graph $B$ byte identity, and has a signed archive-index owner.

**Evidence:** The original proposal resolved the eight Hopfield restorations.
The completed Phase 0 set resolves 27 destinations across
`historical_and_shared_experiments`, `sota_reproducer`, and
`later_experiments`. Archive payload downloads remained at zero during control
resolution. The MANTRA implementation receipt supports `Applied`; the
restoration run later supports `Complete`.

#### P0-PB-05A

**Resolution status:** [Master checklist](../checklists/mantra-rebuild.md#pairblock-resolution)

**Requirement:** Represent every term in $R_{max}$, measure free bytes on the target filesystem, reject a negative or non-integer measurement, and expose the resulting pass or fail decision in a serializable receipt.

**Dependency:** The capacity formula in Section 4. `P0-PB-05B` supplies the measured archive-plan values used in the real receipt.

##### `P0-PB-05A` accepted implementation

**Code boundary:** MANTRA owns these implementation paths:

- [`src/mantra/rebuild/capacity.py`](../../../mantra/src/mantra/rebuild/capacity.py)
- [`src/mantra/rebuild/tests/test_capacity.py`](../../../mantra/src/mantra/rebuild/tests/test_capacity.py)

**Focused check:**

```bash
cd /Users/machina/Developer/ChatGPT/mantra
PYTHONPATH="$PWD/src" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
python -m pytest \
  --rootdir="$PWD/src" \
  --confcutdir="$PWD/src" \
  src/mantra/rebuild/tests/test_capacity.py -q
```

**Gate:** The focused tests observe the exact-boundary pass, below-boundary failure, rejection of invalid plan terms and supplied free-byte measurements, and every serialized contract term. `P0-PB-05B` supplies the archive totals; the real `P0-PB-05` capacity receipt calls `measure_capacity()` and records the filesystem's observed free bytes before download.

**Stop condition:** Return the proposal for revision when the receipt omits a capacity term or any input can understate `required_bytes`.

**Evidence:** MANTRA commit `af4e589451a90a88f59c806b12a90e74e2bba043` contains the accepted implementation. The declared gate passed `12` tests, Ruff passed, the diff check passed, and the reviewed diff SHA-256 was `2ce583f37affefc5eb1af2c7435b6e75cf4cdc4740d34332fa2c18e95049e73b`. The later real capacity receipt observes filesystem free bytes and VIPER registration supports `Complete`.

### P0-PB-05B implementation record

**Resolution status:** [Master checklist](../checklists/mantra-rebuild.md#pairblock-resolution)

**Requirement:** Join each approved restoration binding to a complete,
ordered sequence of remotely verified archive parts and expose the byte counts
used by `P0-PB-05A`.

**Dependency:** `P0-PB-04B` supplies the 27 restoration bindings. The
signed `ARCHIVE_INDEX.json` supplies each part's repository, data revision,
path, byte count, upload state, readback state, and SHA-256.

##### `P0-PB-05B` accepted code

**Code boundary:**

- [archive plan source](../../../mantra/src/mantra/rebuild/archive_plan.py)
- [archive plan tests](../../../mantra/src/mantra/rebuild/tests/test_archive_plan.py)

**Fixture boundary:** [Python overlay runner](../../tools/pairblock_status/python_overlay.py)

**Implementation requirements:**

- `ArchivePart.from_index_row()` accepts only dataset parts whose upload and
  remote readback passed and whose readback digest equals the signed digest.
- `build_archive_plan()` selects the archives named by the bindings, orders
  archive IDs and one-based part numbers deterministically, and requires the
  selected count to equal each signed archive count.
- `ArchivePlan.to_dict()` records every remote part identity, the part count,
  largest part, full-download upper bound, and restored-file total.
- The real signed controls yield 36 parts, `4,294,967,296` largest-part bytes,
  `145,574,762,417` download bytes, and `811,130,091` restored bytes.

**Focused check:**

```bash
cd /Users/machina/Developer/ChatGPT/mantra
python -m ruff check \
  src/mantra/rebuild/archive_plan.py \
  src/mantra/rebuild/tests/test_archive_plan.py
PYTHONPATH="$PWD/src" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
python -m pytest --rootdir="$PWD/src" --confcutdir="$PWD/src" \
  src/mantra/rebuild/tests/test_archive_plan.py -q
```

**Gate:** Ruff and the tests pass. The real signed controls produce 36 parts,
4,294,967,296 largest-part bytes, 145,574,762,417 upper-bound download bytes,
and 811,130,091 restored bytes.

**Applied paths:** `src/mantra/rebuild/archive_plan.py` and
`src/mantra/rebuild/tests/test_archive_plan.py`.

**Applied check:**

```bash
cd /Users/machina/Developer/ChatGPT/mantra
python -m ruff check \
  src/mantra/rebuild/archive_plan.py \
  src/mantra/rebuild/tests/test_archive_plan.py && \
PYTHONPATH="$PWD/src" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
python -m pytest \
  --rootdir="$PWD/src" \
  --confcutdir="$PWD/src" \
  src/mantra/rebuild/tests/test_archive_plan.py -q
```

**Stop condition:** do not begin `P0-PB-06` when a selected part is absent,
unverified, non-contiguous, or different from the signed identity.

### P0-PB-05C implementation record

**Resolution status:** [Master checklist](../checklists/mantra-rebuild.md#pairblock-resolution)

**Requirement:** A stage governed by `file_access="declared"` must retain every
CPython-visible file-open attempt, reject undeclared read-opens and write-opens,
and require a successful Python read-open for every declared input before a
successful return.

**Dependency:** None. `P0-PB-05C` and `P0-PB-05B` can proceed in parallel.
`P0-PB-06` depends on both.

##### `P0-PB-05C` proposed code

**Code boundary:**

- [protocol types](../../../viper/src/viper/stages.py)
- [authoring API](../../../viper/src/viper/authoring.py)
- [file-access observer](../../../viper/src/viper/_workers/file_access.py)
- [stage worker](../../../viper/src/viper/_workers/stages.py)
- [verification rule](../../../viper/src/viper/_verification/attempt.py)
- [boundary tests](../../../viper/tests/test_stage_file_access.py)
- [execution test](../../../viper/tests/test_run_execution.py)
- [authoring test](../../../viper/tests/test_authoring.py)
- [declaration observers](../../../viper/tests/declaration_observers.toml)
- [user documentation](../../../viper/docs/how-to/stages.md)
- [protocol reference](../../../viper/docs/reference/protocol.md)
- [contribution protocol](../../../viper/CONTRIBUTING.md)

The [framework-tradeoff review rule](../../../viper/CONTRIBUTING.md#review-a-framework-tradeoff)
governs the user review of this block.

**Implementation requirements:**

- `stage()` and its frozen `ParameterizedSpec` expose
  `file_access="unrestricted" | "declared"`; the default remains
  `"unrestricted"`.
- During a declared invocation, one process-wide audit observer permits
  read-opens beneath declared input and output paths, permits write-opens
  beneath declared output and attached metric paths, and rejects other
  file-open operations.
- Temporary wrappers around `builtins.open`, `io.open`, and `os.open` retain an
  allowed access only after the underlying call returns successfully. The
  worker restores all three functions when the governed call ends.
- The observer rejects working-directory changes and Python thread or child-process
  launches because those operations can move file access outside the recorded
  boundary or outlive the observer.
- `StageInvocationReceipt.file_access` stores unique, sorted,
  repository-relative read and write paths on success and failure.
- Verification reconstructs allowed paths from the frozen stage, input
  binding, attempt, and metrics; it rejects missing evidence, undeclared paths,
  and any declared input that lacks a successful Python read-open.
- Documentation states that the CPython audit interface establishes a file-open
  attempt. The retained receipt establishes a successful call through one of
  the three wrapped Python APIs. Semantic byte consumption requires separate
  evidence. Native-library
  access appears only when the library emits a Python audit event. A Python
  audit hook checks cooperative code; hostile code requires an operating-system
  sandbox. Each real Phase 0 loader
  must therefore pass an observing execution test before its graph edge is
  accepted.

**Measured runtime effect:** A local microbenchmark added about 30 microseconds
per cached `Path.read_bytes()` open and about 125 microseconds per cached
`torch.load()` of a 4 MiB checkpoint. Thirty CPU matrix multiplications stayed
within timing noise. These measurements characterize the current machine; a
performance guarantee requires measurements across supported environments.

**Focused check:**

```bash
cd /Users/machina/Developer/ChatGPT/viper
source .venv/bin/activate
python -m ruff check \
  src/viper/_workers/file_access.py \
  src/viper/_workers/stages.py \
  src/viper/_verification/attempt.py \
  src/viper/authoring.py src/viper/stages.py \
  tests/test_stage_file_access.py tests/test_run_execution.py \
  tests/test_authoring.py tests/conftest.py && \
python -m pytest \
  tests/test_stage_file_access.py \
  tests/test_run_execution.py::test_train_stage_captures_local_external_input \
  tests/test_authoring.py::test_python_stage_drafts_replace_yaml_authoring \
  tests/test_authoring.py::test_plan_freezes_declared_file_access -q
```

**Gate:** Ruff passes. The tests retain accepted paths and reject a missing
read-open for a declared input, an undeclared read-open or write-open, a
directory change, a Python thread or child process, and missing or tampered
verification evidence. The authoring tests prove that the field reaches the
frozen stage specification and a real execution receipt.

**Applied paths:** The VIPER paths listed in the code boundary.

**Applied check:** Run the focused check against the committed VIPER source,
then use the accepted VIPER commit in MANTRA's `venv` before `P0-PB-06`.

**Stop condition:** Return the patch for revision if the default execution path
changes, the receipt can authorize itself independently of the frozen declarations, a
declared input can disappear from verified evidence, or real Hopfield and MIL
loaders bypass the observer.

### P0-PB-05D implementation record

**Resolution status:** [Master checklist](../checklists/mantra-rebuild.md#pairblock-resolution)

**Requirement:** Verify that the selected `model` artifact exists on its
declared producer. Require that producer to be a training stage only when the
run names a benchmark.

**Dependency:** None. `P0-PB-06` depends on this repair because its restoration
study has no benchmark and restores an existing model through a build stage.

##### `P0-PB-05D` proposed code

**Code boundary:** [plan relationship verifier](../../../viper/src/viper/_verification/plan.py),
[relationship tests](../../../viper/tests/test_verification.py), and the
[declaration-to-test map](../../../viper/tests/declaration_observers.toml).

**Implementation requirements:**

- Resolve `run.estimator.stage_id` to one declared stage and require that
  stage to expose `run.estimator.artifact_name`.
- Accept a non-training producer when `run.benchmark_id` is absent.
- Require a training producer when `run.benchmark_id` is present.
- Preserve the benchmark evaluation-to-estimator identity check.

**Focused check:**

```bash
cd /Users/machina/Developer/ChatGPT/viper
source .venv/bin/activate
python -m ruff check src/viper/_verification/plan.py tests/test_verification.py
python -m pytest \
  tests/test_verification.py::RunPlanRelationshipTests::test_unbenchmarked_build_may_supply_the_model \
  tests/test_verification.py::RunPlanRelationshipTests::test_benchmark_estimator_requires_training -q
```

**Gate:** The two tests cover three relationship cases and Ruff passes. The
change surface contains plan relationship verification, its tests, and the
declaration-to-test map.

**Applied check:** Repeat the focused check against the committed VIPER source,
then rerun the P0-PB-06 restoration preflight through MANTRA's active `mantra`
environment.

**Stop condition:** Reject the patch if it permits a missing selected artifact
or a benchmark whose estimator comes from a non-training stage.

### P0-PB-05E implementation record

**Resolution status:** [Master checklist](../checklists/mantra-rebuild.md#pairblock-resolution)

**Requirement:** Validate the selected artifact name according to the run's
evaluation boundary. An unbenchmarked run may select any stage output. A
benchmarked run must select `model`.

**Dependency:** Applied `P0-PB-05D`. The plan relationship verifier remains
responsible for proving that the selected stage actually declares the named
artifact and that a benchmarked run selects a training-stage output.

##### `P0-PB-05E` proposed code

**Code boundary:** [run model](../../../viper/src/viper/runs.py),
[protocol tests](../../../viper/tests/test_protocol.py), and
[relationship tests](../../../viper/tests/test_verification.py), and the
[declaration-to-test map](../../../viper/tests/declaration_observers.toml).

**Implementation requirements:**

- Require `estimator.stage_id` to name one stage in `RunSpec.stages`.
- When `benchmark_id` is absent, accept any `estimator.artifact_name` and let
  plan relationship verification require that output on the selected stage.
- When `benchmark_id` is present, require `estimator.artifact_name == "model"`.
- Retain the plan relationship rule that requires a training-stage producer
  whenever the run names a benchmark.

**Focused check:**

```bash
cd /Users/machina/Developer/ChatGPT/viper
source .venv/bin/activate
python -m ruff check src/viper/runs.py tests/test_protocol.py tests/test_verification.py
python -m pytest \
  tests/test_protocol.py::RunPlanTests::test_unbenchmarked_run_may_select_a_declared_terminal_artifact \
  tests/test_protocol.py::RunPlanTests::test_benchmarked_run_must_select_the_model_artifact \
  tests/test_verification.py::RunPlanRelationshipTests::test_unbenchmarked_run_requires_the_selected_terminal_artifact \
  tests/test_verification.py::RunPlanRelationshipTests::test_benchmark_estimator_requires_training -q
```

**Gate:** Ruff passes. The protocol tests accept an unbenchmarked `receipt`
selection and reject the same selection after a benchmark is named. The
relationship test accepts that selection only when the producer declares the
receipt. The existing benchmark relationship test retains the training-stage
constraint.

**Applied check:** Repeat the focused check against the committed VIPER source,
then compile the Hopfield replay plan through MANTRA's active `mantra`
environment.

**Stop condition:** Reject the patch if a benchmarked run can select a
non-model artifact or plan verification accepts an artifact absent from the
selected stage.

### P0-PB-05F implementation record

**Resolution status:** [Master checklist](../checklists/mantra-rebuild.md#pairblock-resolution)

**Requirement:** Treat the operating system's null device as runtime plumbing
instead of stage data while retaining the declared file boundary for every
other path.

**Dependency:** Applied `P0-PB-05C` file-access observer.

##### `P0-PB-05F` proposed code

**Code boundary:** [file-access observer](../../../viper/src/viper/_workers/file_access.py),
[boundary tests](../../../viper/tests/test_stage_file_access.py), and the
[declaration-to-test map](../../../viper/tests/declaration_observers.toml).

**Implementation requirements:**

- Resolve the runtime null device from `os.devnull`.
- Permit reads and writes only to that exact device path.
- Exclude null-device access from the retained read and write sets.
- Keep every other undeclared device path subject to the existing rejection.

**Focused check:**

```bash
cd /Users/machina/Developer/ChatGPT/viper
source .venv/bin/activate
python -m ruff check \
  src/viper/_workers/file_access.py \
  tests/test_stage_file_access.py
python -m pytest \
  tests/test_stage_file_access.py::test_null_device_is_runtime_plumbing \
  tests/test_stage_file_access.py::test_undeclared_device_is_rejected -q
```

**Gate:** Ruff passes. The null-device test proves successful reads and writes
produce no retained data-access evidence. The counterexample proves another
device path remains forbidden.

**Applied check:** Repeat the focused check against committed VIPER source,
install that commit in the isolated `mantra-rebuild` GPU environment, and run
the Hopfield replay through its real governed stages.

**Stop condition:** Reject the patch if it exempts a device path other than
`os.devnull`, records the null device as stage data, or lets null-device access
satisfy a declared-input read.

### P0-PB-05G implementation record

**Resolution status:** [Master checklist](../checklists/mantra-rebuild.md#pairblock-resolution)

**Requirement:** Keep runtime module lookup bound to the workspace module
objects imported with the frozen stage callable.

**Dependency:** Applied `P0-PB-05C` file-access observer.

##### `P0-PB-05G` proposed code

**Code boundary:** [stage loader](../../../viper/src/viper/stages.py),
[stage worker](../../../viper/src/viper/_workers/stages.py),
[observing tests](../../../viper/tests/test_stage_invocation.py), and the
[declaration-to-test map](../../../viper/tests/declaration_observers.toml).

**Implementation requirements:** the loader retains the exact workspace module
objects imported with the callable without leaving them in the caller's module
registry. The worker installs that retained mapping before it activates
declared file access, invokes the callable once, and restores every replaced or
absent module entry afterward.

**Focused check:**

```bash
cd /Users/machina/Developer/ChatGPT/viper
source .venv/bin/activate
python -m ruff check \
  src/viper/stages.py \
  src/viper/_workers/stages.py \
  tests/test_stage_invocation.py
python -m pytest tests/test_stage_invocation.py -q
```

**Gate:** Ruff passes. One loader test proves the retained config module is the
same object used by the loaded callable. One worker test proves runtime import
lookup receives the retained object and the prior module-registry entry is
restored after invocation. The real MIL replay reads only its materialized
inputs under `file_access="declared"`.

**Stop condition:** Reject the patch if it retains arbitrary modules outside
the workspace package prefixes, leaves a loaded workspace module installed
after invocation, replaces the framework's running `viper` package, or permits
an undeclared data-file read.

### P0-PB-05H implementation record

**Resolution status:** [Master checklist](../checklists/mantra-rebuild.md#pairblock-resolution)

**Requirement:** Distinguish source-code reads covered by the run's frozen Git
identity from data reads governed by stage inputs.

**Dependency:** Applied `P0-PB-05C` file-access observer.

##### `P0-PB-05H` proposed code

**Code boundary:** [file-access observer](../../../viper/src/viper/_workers/file_access.py),
[stage worker](../../../viper/src/viper/_workers/stages.py),
[observing tests](../../../viper/tests/test_stage_file_access.py), and the
[declaration-to-test map](../../../viper/tests/declaration_observers.toml).

**Implementation requirements:** before activating file-access enforcement,
the worker asks Git for the files present in `run.source.commit` and retains
only paths ending in `.py`. The observer permits reads of those exact paths as
source reads. Source reads create no data-access evidence and cannot satisfy a
declared-input read. Every untracked path and every tracked path with another
suffix remains governed by the declared input and output sets.

**Focused check:**

```bash
cd /Users/machina/Developer/ChatGPT/viper
source .venv/bin/activate
python -m ruff check \
  src/viper/_workers/file_access.py \
  src/viper/_workers/stages.py \
  tests/test_stage_file_access.py
python -m pytest \
  tests/test_stage_file_access.py::test_frozen_python_source_is_runtime_code \
  tests/test_stage_file_access.py::test_untracked_python_source_is_rejected \
  tests/test_stage_file_access.py::test_tracked_non_python_file_is_rejected -q
```

**Gate:** Ruff passes. The source test proves an exact frozen `.py` read creates
no data-access evidence. The counterexamples prove path suffix alone grants no
access and Git tracking grants no access to non-Python data. The real MIL replay
runs under declared access without a repository source-read rejection.

**Stop condition:** Reject the patch if it permits every `.py` path, permits a
tracked non-Python path, lets a source read satisfy a data input, invokes Git
after the observer is active, or requires a new stage-author setting.

### P0-PB-05I implementation record

**Resolution status:** [Master checklist](../checklists/mantra-rebuild.md#pairblock-resolution)

**Requirement:** Finalize a failed attempt when `verify_run_result()` rejects
the provisional successful attempt document.

**Dependency:** None. The observed failure occurred during `P0-PB-06` artifact
verification.

##### `P0-PB-05I` proposed code

**Code boundary:** [attempt execution](../../../viper/src/viper/execution/_attempt.py),
[attempt publication](../../../viper/src/viper/execution/_publication.py), and
[execution tests](../../../viper/tests/test_run_execution.py). The independent
[review receipt](../../evidence/pairblock-reviews/p0-pb-05i/68153714be50ec477af808d462ada809b9908acd.json)
binds the complete change to VIPER commit
`68153714be50ec477af808d462ada809b9908acd`.

**Implementation requirements:** `write_attempt_document()` retains its
immutable-write behavior for ordinary publication. The exception path replaces
the provisional local attempt document atomically, publishes the failed bytes,
and returns the failed attempt reference. `AttemptFailure.code` remains
`verification_failed`, and `AttemptFailure.message` retains the originating
`VerificationError`. Successful runs keep their existing publication path.

**Runtime and workflow effect:** Successful runs execute the same operations.
A verification failure performs one atomic local replacement and publishes the
failed attempt bytes. Stage authors add no setting or command.

**Focused check:**

```bash
cd /Users/machina/Developer/ChatGPT/viper
source .venv/bin/activate
python -m ruff check \
  src/viper/execution/_attempt.py \
  src/viper/execution/_publication.py \
  tests/test_run_execution.py
python -m pytest \
  tests/test_run_execution.py::test_failed_attempt_replaces_provisional_document \
  tests/test_run_execution.py::test_two_stage_local_run_writes_and_verifies_terminal_result \
  -q
```

**Gate:** The focused test forces `verify_run_result()` to reject a provisional
successful attempt, then proves the terminal run and canonical attempt both
record `failed`, `verification_failed`, and the original verification message.

**Stop condition:** Reject the patch if it changes successful publication,
overwrites a terminal attempt from another execution, or replaces the original
verification message.

### P0-PB-05J implementation record

**Resolution status:** [Master checklist](../checklists/mantra-rebuild.md#pairblock-resolution)

**Requirement:** Accept explicit trust for prior-run source repositories while
executing and verifying a run.

**Dependency:** None. RICO terminal registration supplies the MANTRA repository
as an additional trusted source.

##### `P0-PB-05J` proposed code

**Code boundary:** [public execution](../../../viper/src/viper/execution/__init__.py),
[run execution](../../../viper/src/viper/execution/_run.py), [attempt execution](../../../viper/src/viper/execution/_attempt.py),
and [execution tests](../../../viper/tests/test_run_execution.py). The
[independent review receipt](../../evidence/pairblock-reviews/p0-pb-05j/54f01105cf6c09d4a5c4f44da6064d82152adffd.json)
binds the change to VIPER commit
`54f01105cf6c09d4a5c4f44da6064d82152adffd`.

**Implementation requirements:** `execution.run()` and `execution.retry()` accept
`trusted_source_repositories` as an optional frozen set of repository URLs.
`execute_attempt()` constructs one `VerificationPolicy` from the current run
source and that explicit set. The default set is empty. The resulting policy is
used both when prior-run inputs materialize and when the terminal result is
verified.

**Runtime and workflow effect:** Runs without cross-repository prior inputs add
no setting. A caller that consumes such an input names its producer repository
once. Policy construction adds one set union per attempt; model and artifact
execution are unchanged.

**Focused check:**

```bash
cd /Users/machina/Developer/ChatGPT/viper
source .venv/bin/activate
python -m ruff check \
  src/viper/execution/__init__.py \
  src/viper/execution/_run.py \
  src/viper/execution/_attempt.py \
  tests/test_run_execution.py
python -m pytest \
  tests/test_run_execution.py -k 'trusted_source_repositories' -q
```

**Gate:** The focused tests prove that execution passes the explicit set into
attempt verification, the current run source remains trusted, an approved
prior-run source is trusted, and an unapproved source remains rejected.

**Stop condition:** Reject the patch if any referenced repository becomes
trusted implicitly, the default trusts an additional repository, or the policy
used for materialization differs from the policy used for terminal
verification.

### P0-PB-05K implementation record

**Resolution status:** [Master checklist](../checklists/mantra-rebuild.md#pairblock-resolution)

**Requirement:** Reuse authenticated Git state when one execution reads files
from the same external repository and commit.

##### `P0-PB-05K` proposed code

**Code boundary:** [fetcher](../../../viper/src/viper/execution/_source.py),
[Git storage](../../../viper/src/viper/_verification/storage.py), and
[tests](../../../viper/tests/test_storage.py) at VIPER commits `08d78749` and
`fe2114ef`.

**Focused check:**

```bash
cd /Users/machina/Developer/ChatGPT/viper
source .venv/bin/activate
python -m ruff check src/viper/execution/_source.py src/viper/_verification/storage.py tests/test_storage.py
python -m pytest tests/test_storage.py -k 'external_git' -q
```

**Gate:** Equal repository-and-commit references share one checkout; exact file
bytes remain content-bound; the in-memory cache never exceeds 64 MiB.

### P0-PB-05L implementation record

**Resolution status:** [Master checklist](../checklists/mantra-rebuild.md#pairblock-resolution)

**Requirement:** Reject an invalid stored-input namespace before execution can
start or a pointer can be published.

##### `P0-PB-05L` proposed code

**Code boundary:** [input model](../../../viper/src/viper/inputs.py),
[draft model](../../../viper/src/viper/benchmark.py), and
[tests](../../../viper/tests/test_prior_run_inputs.py) at VIPER commit
`cdd7ec5b`.

**Focused check:**

```bash
cd /Users/machina/Developer/ChatGPT/viper
source .venv/bin/activate
python -m ruff check src/viper/inputs.py src/viper/benchmark.py tests/test_prior_run_inputs.py
python -m pytest tests/test_prior_run_inputs.py -q
```

**Gate:** `run_artifact()` rejects a path outside `inputs/`, publishes no
pointer, and `StoredInputRef` enforces the same serialized boundary.

### P0-PB-05M implementation record

**Resolution status:** [Master checklist](../checklists/mantra-rebuild.md#pairblock-resolution)

**Requirement:** Reuse one verified producer result while checking several
stored inputs that carry the same exact run reference.

##### `P0-PB-05M` proposed code

**Code boundary:** [verifier](../../../viper/src/viper/verification.py) and
[acceptance tests](../../../viper/tests/test_verification_acceptance.py) at
VIPER commit `427f1894`.

**Focused check:**

```bash
cd /Users/machina/Developer/ChatGPT/viper
source .venv/bin/activate
python -m ruff check src/viper/verification.py tests/test_verification_acceptance.py
python -m pytest tests/test_verification_acceptance.py -k 'stored_inputs_verify_one_shared_producer_run_once or stored_input_role_must_match_the_selected_artifact' -q
```

**Gate:** Equal `ResolvedRunRef` values cause one producer verification while
each pointer retains artifact, role, and materialization validation.

### P0-PB-05N implementation record

**Resolution status:** [Master checklist](../checklists/mantra-rebuild.md#pairblock-resolution)

**Requirement:** Select runtime-dependent callers from the CodeQL/AST graph
without treating a local import name as another caller.

##### `P0-PB-05N` proposed code

**Code boundary:** [selector](../../../viper/tools/select_impacted_tests.py) and
[tests](../../../viper/tests/test_impacted_test_selection.py) at VIPER commit
`98dcf084`.

**Focused check:**

```bash
cd /Users/machina/Developer/ChatGPT/viper
source .venv/bin/activate
python -m ruff check tools/select_impacted_tests.py tests/test_impacted_test_selection.py
python -m pytest tests/test_impacted_test_selection.py -q
```

**Gate:** An import edge cannot force domain fallback for its imported target;
an unobserved import selected as the changed declaration still does.

### P0-PB-05O implementation record

**Resolution status:** [Master checklist](../checklists/mantra-rebuild.md#pairblock-resolution)

**Requirement:** Route stage-worker and stage-file-access test process calls
through VIPER's spawn-safe facade.

##### `P0-PB-05O` proposed code

**Code boundary:** [worker](../../../viper/src/viper/_workers/stages.py),
[repository policy](../../../viper/tests/test_process_startup.py), and
[file-access tests](../../../viper/tests/test_stage_file_access.py) at VIPER
commit `3383713d`.

**Focused check:**

```bash
cd /Users/machina/Developer/ChatGPT/viper
source .venv/bin/activate
python -m ruff check src/viper/_workers/stages.py tests/test_stage_file_access.py
python -m pytest tests/test_process_startup.py::test_repository_launch_sites_use_spawn_safe_subprocess tests/test_stage_file_access.py tests/test_stage_invocation.py -q
```

**Gate:** The AST policy finds no direct subprocess import, and the stage
invocation and declared-file-access behavior still pass.

### P0-PB-06 implementation record

**Resolution status:** [Master checklist](../checklists/mantra-rebuild.md#pairblock-resolution)

**Requirement:** Authenticate the signed binding records, verify the 27 files
on the restored MANTRA disk, retain the same bytes as named VIPER outputs, and
prove graph $B$ fails verification after one required edge is removed.

**Dependency:** applied `P0-PB-04A` and `P0-PB-04B` binding code, applied
`P0-PB-05A` and `P0-PB-05B` capacity and archive-plan code, and applied
`P0-PB-05C` file-access enforcement, `P0-PB-05D` model-producer support, and
`P0-PB-05E` terminal-artifact selection. This block produces the real binding and
capacity receipts that later close the aggregate `P0-PB-04` and `P0-PB-05`
records.

##### `P0-PB-06` proposed code

**Code boundary:** the existing [control-package helper](../../../mantra/cleanup/reinstantiation_archive.py),
its [tests](../../../mantra/cleanup/tests/test_reinstantiation_archive.py),
[binding resolver](../../../mantra/src/mantra/rebuild/restoration.py),
[archive extraction](../../../mantra/src/mantra/rebuild/archive_restore.py),
[VIPER workflow](../../../mantra/src/mantra/rebuild/viper_restore.py),
[self-contained artifact loaders](../../../mantra/src/mantra/rebuild/loaders.py),
and the [rebuild tests](../../../mantra/src/mantra/rebuild/tests).

**Fixture boundary:** [Python overlay runner](../../tools/pairblock_status/python_overlay.py)

**Implementation requirements:**

- Download exactly the five signed control files named by this block.
- Build the signed 36-part recovery plan and call `measure_capacity()` before
  copying a disk file. Persist the capacity receipt and require `passed`.
  Count the persistent VIPER store, the VIPER attempt workspace, one
  largest-file temporary write, and the 10 MiB reserve.
- Declare a preparation stage that consumes the signed root release, detached
  signature, and public key. It authenticates the pinned project release and
  control package, resolves all 27 bindings from the filesystem and content
  object manifests, and emits a control bundle, binding file, and receipt.
- Run control preparation with unrestricted file access because Hugging Face
  network retrieval and OpenSSL signature verification cross the declared-file
  observer's cooperative Python boundary. Retain this limitation in the VIPER
  usefulness ledger.
- Require all 27 approved destination, byte-count, SHA-256, repository,
  control-revision, and archive identities before archive planning.
- The restoration stage consumes the authenticated control bundle, binding
  file, control receipt, and 27 approved MANTRA disk paths. It declares one
  named file output per binding and one evidence-bundle output.
- For each binding, require the source byte count and SHA-256, copy the source
  to the same-named output, and require the output byte count and SHA-256.
- Run restoration with `file_access="declared"`. Every disk source is a
  declared input; every copied file and receipt is a declared output.
- Make the Hopfield and MIL studies require the resolved restoration run and
  select its named outputs with `run_artifact()`.
- Run VIPER verification, then retain a severed-edge verification failure for
  one disk-file input edge and one named-output edge.
- Load JSON and binary outputs through a self-contained source file that
  remains importable when VIPER materializes only that exact loader file.

**Focused check:**

```bash
cd /Users/machina/Developer/ChatGPT/mantra
python -m ruff check src/mantra/rebuild cleanup/tests/test_reinstantiation_archive.py
PYTHONPATH="$PWD/src:$PWD" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
python -m pytest --rootdir="$PWD/src" --confcutdir="$PWD/src" \
  src/mantra/rebuild/tests -q
```

**Gate:** Ruff and the focused tests pass; the real disk-import receipt identifies
all 27 source and output identities; `verify_run()` passes;
and the retained severed-edge fixture fails verification.

**Applied paths:** `src/mantra/rebuild/viper_restore.py`,
`src/mantra/rebuild/hopfield_replay.py`, `src/mantra/rebuild/mil_replay.py`, and
their corresponding files under `src/mantra/rebuild/tests/`.

**Applied check:**

```bash
cd /Users/machina/Developer/ChatGPT/mantra
python -m ruff check \
  src/mantra/rebuild/viper_restore.py \
  src/mantra/rebuild/hopfield_replay.py \
  src/mantra/rebuild/mil_replay.py \
  src/mantra/rebuild/tests/test_viper_restore.py \
  src/mantra/rebuild/tests/test_hopfield_replay.py \
  src/mantra/rebuild/tests/test_mil_replay.py
PYTHONPATH="$PWD/src" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
python -m pytest \
  --rootdir="$PWD/src" \
  --confcutdir="$PWD/src" \
  src/mantra/rebuild/tests/test_viper_restore.py \
  src/mantra/rebuild/tests/test_hopfield_replay.py \
  src/mantra/rebuild/tests/test_mil_replay.py -q
```

**Stop condition:** stop before either replay when one canonical identity or
one required provenance edge differs.

### P0-PB-07 accepted implementation

**Resolution status:** [Master checklist](../checklists/mantra-rebuild.md#pairblock-resolution)

**Requirement:** Run the selected historical Hopfield prediction once, retain
the new six-array prediction NPZ, and evaluate it separately with the hold
truth.

**Dependency:** `P0-PB-06` restores the six missing data files and saved
encoder. The user approves the numerical tolerance before the real replay.

**Code boundary:** [Hopfield replay source](../../../mantra/src/mantra/rebuild/hopfield_replay.py),
[self-contained artifact loaders](../../../mantra/src/mantra/rebuild/loaders.py),
and [observing tests](../../../mantra/src/mantra/rebuild/tests/test_hopfield_replay.py).

**Implementation requirements:** initialize scikit-learn's native threadpool
inventory when the worker imports the replay implementation; select one
`NVIDIA L4` in the VIPER environment when `device="cuda"`; verify all twelve
input identities; call the selected historical loader and saved encoder once;
call the raw-gene readout with `memory_splits=("fit",)`, `topk=1600`, and
`temperature=0.055`; write the new six-array prediction; score it against hold
truth; and persist the prediction identity, device, effective top-k, scores,
tolerance, and decision. Runtime inventory initialization occurs before the
governed stage begins, so the stage retains its child-process ban.
VIPER verifies the produced JSON and binary artifacts through the
self-contained loader source it materializes into its validation workspace.

**Gate:** the tests prove the selected call arguments, output schema, CPU
path, effective donor count, and parity decision. The real run retains the
prediction, attention summaries, score receipt, and VIPER prediction-to-
evaluation edge.

**Stop condition:** reject any invocation of the historical grid search, any
historical output destination, an undeclared file read, or a score outside the
approved tolerance from `0.5861640938949398`.

**Applied paths:** `src/mantra/rebuild/hopfield_replay.py` and
`src/mantra/rebuild/tests/test_hopfield_replay.py`.

**Applied check:**

```bash
cd /Users/machina/Developer/ChatGPT/mantra
python -m ruff check \
  src/mantra/rebuild/hopfield_replay.py \
  src/mantra/rebuild/tests/test_hopfield_replay.py && \
PYTHONPATH="$PWD/src" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
python -m pytest \
  --rootdir="$PWD/src" \
  --confcutdir="$PWD/src" \
  src/mantra/rebuild/tests/test_hopfield_replay.py -q
```

### P0-PB-08 accepted implementation

**Resolution status:** [Master checklist](../checklists/mantra-rebuild.md#pairblock-resolution)

**Requirement:** Apply the saved v1952 seed-123460 MIL prototype through the
v1953 Step02 and Step03 runtime in a fresh output root.

**Dependency:** the standalone MIL restoration bindings close independently
of the Hopfield replay. They include the prototype, two historical Step01
predictions, and the Step02 input-root files named below.

**Code boundary:** [MIL replay source](../../../mantra/src/mantra/rebuild/mil_replay.py),
[self-contained artifact loaders](../../../mantra/src/mantra/rebuild/loaders.py),
and [observing tests](../../../mantra/src/mantra/rebuild/tests/test_mil_replay.py).

**Implementation requirements:** initialize scikit-learn's native threadpool
inventory when the worker imports the replay implementation; select one
`NVIDIA L4` in the VIPER environment when `device="cuda"`; load the saved v1952
seed-123460 prototype; verify the selected Step02, Step03, and prototype
identities; recreate the legacy input-root layout inside the declared output
bundle with links to the VIPER-materialized compute inputs; pass that localized
root and the materialized direct-input paths to the historical runner; remove
the temporary links before retaining the output bundle; assign a
source-commit-specific VIPER experiment identity and a fresh output root; call
the maintained application runtime once; and retain the four prediction arrays,
Step02 and Step03 scores, and their identities. The declared input set is the
standalone MIL graph.
VIPER verifies each output through the self-contained loader source it
materializes into its validation workspace.

**Gate:** the focused check rejects drift from the selected settings and
confirms output isolation. The real L4 run reproduces Step02 hold
`0.5924883417873266` and Step03 hold `0.6025499488874759` within `1e-8`, compares
the two prediction archives by logical array content, and compares the two
deterministic fitted-weight archives by SHA-256.

**Stop condition:** stop when the runtime tries to train a teacher or student,
reads a Hopfield-rebuild output, reuses an existing run root, or changes a
selected setting or input identity. Stop when the historical runner opens an
original repository input instead of the corresponding VIPER-materialized
input.

**Applied paths:** `src/mantra/rebuild/mil_replay.py` and
`src/mantra/rebuild/tests/test_mil_replay.py`.

**Applied check:**

```bash
cd /Users/machina/Developer/ChatGPT/mantra
python -m ruff check \
  src/mantra/rebuild/mil_replay.py \
  src/mantra/rebuild/tests/test_mil_replay.py && \
PYTHONPATH="$PWD/src" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
python -m pytest \
  --rootdir="$PWD/src" \
  --confcutdir="$PWD/src" \
  src/mantra/rebuild/tests/test_mil_replay.py -q
```

### P0-PB-09 accepted implementation

**Resolution status:** [Master checklist](../checklists/mantra-rebuild.md#pairblock-resolution)

**Requirement:** Freeze each Phase 0 result receipt and every VIPER usefulness
assessment into one digest-bound index.

**Dependency:** completed `P0-PB-07`, `P0-PB-08`, and the active traceability
controller from `P0-PB-10`.

**Code boundary:** [Phase 0 freezer](../../tools/freeze_phase0.py)
and [observing tests](../../tests/test_freeze_phase0.py).

**Implementation requirements:** index the eleven evidence roles in Section 6
across their RICO and MANTRA repository owners; bind each file to its repository,
normalized relative path, byte count, and SHA-256; require one usefulness-ledger
assessment for every declared assessed check; require independent evidence for
each confirmed framework or implementation defect; preserve every indexed
input; and write one deterministic Phase 0 index.

**Gate:** Ruff and the focused tests pass. The real Phase 0 index resolves
every required receipt and ledger record at its recorded identity.

**Applied paths:** `tools/freeze_phase0.py` and
`tests/test_freeze_phase0.py` in RICO.

**Applied check:**

```bash
cd /Users/machina/Developer/ChatGPT/RICO
python -m ruff check \
  tools/freeze_phase0.py \
  tests/test_freeze_phase0.py && \
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
python -m pytest tests/test_freeze_phase0.py -q
```

**Stop condition:** keep Phase 0 open when an input receipt, digest, assessed
VIPER check, or independent defect confirmation is absent.

### P0-PB-09A accepted implementation

**Resolution status:** [Master checklist](../checklists/mantra-rebuild.md#pairblock-resolution)

**Requirement:** Verify the complete frozen Phase 0 evidence set in one
RICO-rooted VIPER run and retain its registration receipt.

**Dependency:** applied `P0-PB-07`, `P0-PB-08`, and `P0-PB-09`; their real
runs and evidence index must exist before registration executes.

**Code boundary:** [Registration source](../../tools/register_phase0.py),
[self-contained artifact loader](../../tools/artifact_loaders.py),
[observing tests](../../tests/test_register_phase0.py),
[workspace marker](../../viper.toml), and
[runtime dependency](../../requirements.txt).

**Implementation requirements:** consume the restoration evidence bundle,
restoration bindings, Hopfield receipt, and MIL receipt through prior-run
artifact references; consume the remaining indexed RICO evidence directly;
verify every indexed byte count and SHA-256; run with `file_access="declared"`;
and emit one terminal registration receipt.

**Gate:** Ruff and the focused tests pass. The real run verifies through
VIPER, its lineage reaches all three MANTRA producer runs and every RICO
evidence input, and its receipt reports `passed: true`.

**Completion evidence:** VIPER run `01M2C9563W9TQWT67RBRCG6YD2` succeeded in
283.833269 seconds. Its [run identity](../../evidence/phase0/rico/phase0_registration_run.json)
binds the RICO and VIPER commits and its [terminal receipt](../../evidence/phase0/rico/phase0_registration_receipt.json)
reports `passed: true`.

**Applied paths:** `tools/register_phase0.py`, `tools/artifact_loaders.py`, and
`tests/test_register_phase0.py` in RICO.

**Applied check:**

```bash
cd /Users/machina/Developer/ChatGPT/RICO
python -m ruff check tools/register_phase0.py tools/artifact_loaders.py tests/test_register_phase0.py && \
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
python -m pytest tests/test_register_phase0.py -q
```

**Stop condition:** keep Phase 0 open when an indexed identity differs or the
verified lineage omits a required MANTRA producer run or RICO evidence input.

#### P0-PB-10

**Resolution status:** [Master checklist](../checklists/mantra-rebuild.md#pairblock-resolution)

**Requirement:** Compile the RICO Markdown checklist into schema version 2 of the global master-checklist manifest. One linked receipt advances a PairBlock through `Drafting`, `Review`, `Approved`, `Applied`, and `Complete`. The RICO profile updates the block's checkbox, mapped requirements, newly ready dependents, and contract state before the global validator accepts the transition. The global contract permits one of several sibling PairBlocks to close while their shared requirement remains in progress and requires that requirement to close with evidence after its final block closes.

**Dependency:** The block has one checklist row, one contract ownership row, and one complete code section. A declared PairBlock dependency must reach an approved or later state before execution. `P0-PB-06` owns the later VIPER registration needed to move this applied block to `Complete`; implementation and review may finish before that registration.

##### `P0-PB-10` accepted implementation

**Code boundary:** These nine files are the active RICO implementation:

- [`tools/pairblock_status/__init__.py`](../../tools/pairblock_status/__init__.py)
- [`tools/pairblock_status/checklist_profile.py`](../../tools/pairblock_status/checklist_profile.py)
- [`tools/pairblock_status/execution_identity.py`](../../tools/pairblock_status/execution_identity.py)
- [`tools/pairblock_status/profile.py`](../../tools/pairblock_status/profile.py)
- [`tools/pairblock_status/pairblock_controller.py`](../../tools/pairblock_status/pairblock_controller.py)
- [`tools/pairblock_status/python_overlay.py`](../../tools/pairblock_status/python_overlay.py)
- [`tests/pairblock_status/conftest.py`](../../tests/pairblock_status/conftest.py)
- [`tests/pairblock_status/test_pairblock_controller.py`](../../tests/pairblock_status/test_pairblock_controller.py)
- [`tests/pairblock_status/test_python_overlay.py`](../../tests/pairblock_status/test_python_overlay.py)

**Fixture boundary:** These two documents define the minimal RICO profile used by the tests. The fixture factory copies the actual `checklist_profile.py` and `test_pairblock_controller.py` into each disposable repository:

- [`tests/pairblock_status/fixtures/minimal_profile/docs/checklists/checklist.md`](../../tests/pairblock_status/fixtures/minimal_profile/docs/checklists/checklist.md)
- [`tests/pairblock_status/fixtures/minimal_profile/docs/contracts/contract.md`](../../tests/pairblock_status/fixtures/minimal_profile/docs/contracts/contract.md)

**Structural tests:**

| Boundary | Observing tests |
|---|---|
| Python lint | `ruff check` over the active controller package and its tests |
| Project policy and lifecycle validity | `test_lifecycle_policy_rejects_undeclared_transition_status`; `test_checklist_profile_requires_two_phase_capture_groups`; `test_project_profile_excludes_markdown_dialect`; `test_markdown_dialect_rejects_empty_markers` |
| Global lifecycle contract | `test_profile_fixture_compiles_with_global_validator`; `test_mantra_profile_compiles_current_contract`; `test_lifecycle_completion_updates_every_derived_status`; `test_non_code_review_completion_updates_every_derived_status`; `test_checkbox_must_match_pairblock_completion` |
| Complete PairBlock inventory and requirement mapping | `test_every_contract_pair_block_requires_one_status_row`; `test_unmapped_pair_block_is_rejected`; `test_duplicate_status_row_is_rejected`; `test_standard_pair_block_contract_marker_is_required`; `test_external_document_fragment_is_outside_repository_validation` |
| PairBlock dependency order | `test_unknown_dependency_is_rejected`; `test_unresolved_pair_block_dependency_blocks_gate`; `test_accepted_dependency_releases_waiting_block` |
| Owner, code, and fixture boundaries | `test_missing_owner_is_rejected`; `test_missing_proposed_source_is_rejected`; `test_missing_fixture_source_is_rejected`; `test_proposed_code_must_stay_in_governing_contract` |
| Gate and lifecycle behavior | `test_gate_must_name_every_observing_test`; `test_failing_gate_retains_receipt_without_changing_checklist`; `test_nested_conda_run_is_rejected_before_gate_execution`; `test_illegal_lifecycle_event_changes_no_status`; `test_non_code_review_rejects_runnable_proposal`; `test_non_code_review_requires_external_evidence` |
| Sibling-repository proposals | `test_profile_may_name_a_sibling_proposal_owner`; `test_proposal_module_overrides_active_module`; `test_requires_both_source_roots` |
| Active environment | `test_gate_preserves_the_controller_python_environment` |
| Controller and Markdown-adapter boundary | `test_gate_controller_does_not_parse_or_render_markdown`; `test_passing_gate_writes_receipt_and_advances_one_status` |
| Git-backed execution identity | `test_execution_identity_drift_invalidates_pass` for source, contract, checklist, validator, and `HEAD` drift |
| Code documentation | `test_active_modules_and_definitions_have_docstrings` |

**Focused check:**

```bash
cd /Users/machina/Developer/ChatGPT/RICO
python -m ruff check \
  tools/pairblock_status \
  tests/pairblock_status &&
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
python -m pytest tests/pairblock_status -q
```

**Gate:** The focused tests prove incremental sibling-block closure in the
global validator; complete RICO PairBlock coverage; legal receipt-backed
transitions; automatic checkbox, requirement, dependency-readiness, and
contract updates; sibling-repository proposal gates through the active Python
environment; retained pass and failure evidence; and rejection of nested Conda
execution, identity drift, broken links, missing owners, missing files, or
invalid observing gates.

**Stop condition:** Return the proposal for revision if a gate can run outside its declared code or runtime boundary, bypass an unresolved dependency, change status after failure or identity drift, accept an illegal lifecycle event, or leave a rendered status inconsistent with its evidence.

**Evidence:** Global commit `58b59175e2a4a949bc8dd33302099cf780249c75`
repairs incremental PairBlock closure and passes its three focused tests,
normalized-manifest validation, and Ruff. The RICO implementation reuses that
validator. `ChecklistProfile` owns project paths, proposal-owner roots, and
lifecycle events; `MarkdownChecklistAdapter` owns RICO parsing and rendering;
`pairblock_controller.py` runs proposal gates in the active environment; and
`python_overlay.py` tests staged files against the active package. The current
focused RICO check passes `54` cases. Historical receipts retain the paths and
file identities captured when they were written; current links resolve to the
accepted functional paths above. The [master-checklist resolution table](../checklists/mantra-rebuild.md#pairblock-resolution)
owns the current lifecycle state and links its supporting receipt.

#### P0-PB-10A

Certify the four named pre-protocol PairBlocks from the terminal Phase 0
registration artifact. [Inspect the implementation and gate](#p0-pb-10a-implementation-record).

### P0-PB-10A implementation record

**Resolution status:** [Master checklist](../checklists/mantra-rebuild.md#pairblock-resolution)

**Requirement:** Close only the four named Phase 0 PairBlocks whose accepted
implementations predate the active receipt chain. Preserve their historical
receipts and attach the terminal Phase 0 artifact plus an explicit reason to
each certification receipt.

##### `P0-PB-10A` proposed code

**Code boundary:** [lifecycle policy](../../tools/pairblock_status/profile.py),
[controller](../../tools/pairblock_status/pairblock_controller.py),
[completion validator](../../tools/pairblock_status/checklist_profile.py),
[fixture profile](../../tests/pairblock_status/conftest.py), and
[observing tests](../../tests/pairblock_status/test_pairblock_controller.py).

**Focused check:**

```bash
cd /Users/machina/Developer/ChatGPT/RICO
python -m ruff check tools/pairblock_status tests/pairblock_status
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
python -m pytest tests/pairblock_status/test_pairblock_controller.py -q
```

**Gate:** A named legacy block reaches `Complete` from `Applied` through one
`certify` receipt. The receipt requires `artifact` evidence and a nonempty
reason, retains the prior receipt link when one exists, and updates the
checkbox, requirement, and contract state. The controller rejects certification
for every PairBlock absent from `legacy_certifiable_pair_blocks`.

**Stop condition:** Keep each legacy block `Applied` when its terminal artifact
is absent, its reason is empty, or the profile does not name its PairBlock ID.

#### P0-PB-10B

**Resolution status:** [Master checklist](../checklists/mantra-rebuild.md#pairblock-resolution)

**Requirement:** A typed project declaration record owns each post-bootstrap
requirement, verifier, PairBlock, dependency, repository-relative source or test
path, and gate. Lifecycle receipts own observed state transitions. The renderer
uses those two inputs to produce the contract and checklist sections used for
human review.

**Dependency:** `P0-PB-10A` closes the historical lifecycle exceptions. The
existing Markdown adapter remains the sole owner of the completed Phase 0 IDs
until `P0-PB-07A` completes through this new path. A later `P0-PB-10C` migration
will move those IDs and remove the legacy parser. `P0-PB-10B` is the single
bootstrap record declared through the current Markdown protocol and will move
with that later migration.

**Authority rule:** Each PairBlock ID belongs to exactly one origin. The
controller rejects an ID present in both the typed declaration manifest and the
legacy Markdown inventory. For a manifest-native ID, the controller reads each
requirement, relationship, path, and gate from the typed declaration and reads
each lifecycle state from the declaration or receipt chain. The declaration
supplies `Drafting` before the first receipt. Each later state comes from the
validated receipt chain.

**Revision rule:** The controller computes one canonical fingerprint from a
PairBlock record, its mapped requirements and verifiers, and their transitive
declaration dependencies. Each gate and lifecycle receipt stores that
fingerprint. A candidate manifest is compared with the last accepted manifest
before another operation runs. The user approves the resulting changed-record
and affected-PairBlock sets. A `revise` receipt then binds the previous and
accepted manifest digests, both versions of each changed record digest, the
affected blocks, the approval reference, and each superseded receipt head.
Affected blocks return to `Drafting`; their transitive dependents return to a
waiting state. Unaffected blocks retain their receipts and lifecycle states.
Before acceptance, superseded uncommitted revision plans may be discarded so
one final reviewed plan and one acceptance receipt describe the declaration.
Every completed code-review pass remains preserved by its own Git commit,
including a pass whose verdict requires further changes.

**Declaration record:** `docs/contracts/mantra-rebuild.declarations.toml` will
store these fields:

| Record | Owned values |
|---|---|
| Requirement | `id`, `claim`, `phase`, `order`, `depends_on`, `gate`, `verifier_ids`, and `pair_block_ids` |
| Verifier | `id`, `requirement_ids`, executable conditions, success case, and rejection cases |
| PairBlock | `id`, `requirement_ids`, `depends_on`, checklist section, implementation repository, source paths, test paths, and gate |

The manifest stores repository identifiers and repository-relative paths. The
project profile resolves each repository identifier to its approved checkout.
The declaration schema owns only the initial `Drafting` state. Receipts derive
every later state. A gate stores its owning
repository, working directory, argument vector, and environment variables. The
renderer turns those fields into the displayed shell command; the controller
executes the argument vector.

##### `P0-PB-10B` proposed code

**Code boundary:** The implementation may change only these RICO paths:

- [declaration manifest](mantra-rebuild.declarations.toml)
- [Python dependencies](../../requirements.txt)
- [Phase 0 contract](mantra-rebuild-phase-0.md)
- [master checklist](../checklists/mantra-rebuild.md)
- [typed declaration loader](../../tools/pairblock_status/declaration_manifest.py)
- [Markdown renderer](../../tools/pairblock_status/markdown_renderer.py)
- [project profile](../../tools/pairblock_status/profile.py)
- [legacy bridge](../../tools/pairblock_status/checklist_profile.py)
- [lifecycle controller](../../tools/pairblock_status/pairblock_controller.py)
- [fixture declarations](../../tests/pairblock_status/fixtures/minimal_profile/declarations.toml)
- [fixture builder](../../tests/pairblock_status/conftest.py)
- [declaration tests](../../tests/pairblock_status/test_declaration_manifest.py)
- [renderer tests](../../tests/pairblock_status/test_markdown_renderer.py)
- [controller tests](../../tests/pairblock_status/test_pairblock_controller.py)

**Implementation requirements:**

1. Parse the TOML into frozen typed records and reject unknown fields, duplicate
   IDs, unresolved references, dependency cycles, duplicate path roles, unknown
   repositories, and paths outside their owning repository.
2. Compile manifest-native records directly into schema version 2 of the global
   master-checklist manifest. Preserve the global validator and receipt chain.
3. Render deterministic contract and checklist regions containing the claim,
   verifier conditions, dependencies, status, direct source and test links,
   exact gate command, current receipt, and next legal lifecycle command.
4. Preserve hand-written prose outside the generated regions. A check-only
   render fails when bytes inside a generated region differ from the renderer's
   output.
5. Route controller operations by PairBlock ownership. Manifest-native IDs use
   typed declarations and receipts; legacy IDs use the existing adapter. Reject
   duplicate ownership before a gate runs or a file changes.
6. Keep `P0-PB-07A` as the first real manifest-native execution. Keep the 25
   historical requirements and 29 historical PairBlocks on the legacy path
   until that block completes.
7. Canonically encode each requirement, verifier, and PairBlock record. Compute
   each PairBlock fingerprint from its own record, mapped requirement and
   verifier records, and transitive declaration dependencies.
8. Compare a candidate manifest with the last accepted manifest. Report added,
   changed, and removed records, then traverse reverse declaration dependencies
   to calculate the affected PairBlocks.
9. Require explicit user approval before accepting a declaration revision.
   Persist a `revise` receipt with the prior and accepted manifest digests,
   record-level before and after digests, affected PairBlocks, superseded
   receipt heads, and approval reference.
10. Block gates and lifecycle transitions while the working declaration differs
    from its last accepted revision. After `revise`, render affected blocks as
    `Drafting`, render their transitive dependents as waiting, and preserve every
    unaffected receipt and state.
11. Execute each legacy multi-command gate with fail-fast shell semantics so an
    earlier failed check determines the gate result.
12. Recompute each accepted revision's record changes and affected PairBlock
    closure from its preceding accepted manifest. Validate the receipt schema,
    external approval reference, chain joins, and every referenced superseded
    receipt before using the accepted manifest.
13. Document every active PairBlock-status module, class, function, method,
    test, dataclass field, and persisted `TypedDict` field. Discover active
    Python modules from the source and test directories so a newly added module
    enters the documentation gate automatically.

**Declaration revision workflow:** Run the read-only plan before asking for
approval. The accepted revision command binds that reviewed plan to the user's
approval reference.

```bash
cd /Users/machina/Developer/ChatGPT/RICO
python -m tools.pairblock_status.pairblock_controller plan-revision
python -m tools.pairblock_status.pairblock_controller revise \
  --approval-target 'USER_REVIEW' \
  --approval-revision 'REVIEW_MESSAGE_ID'
```

**Focused check:**

```bash
cd /Users/machina/Developer/ChatGPT/RICO
python_paths=(
  tools/pairblock_status/checklist_profile.py
  tools/pairblock_status/declaration_manifest.py
  tools/pairblock_status/markdown_renderer.py
  tools/pairblock_status/pairblock_controller.py
  tools/pairblock_status/profile.py
  tests/pairblock_status/conftest.py
  tests/pairblock_status/test_declaration_manifest.py
  tests/pairblock_status/test_markdown_renderer.py
  tests/pairblock_status/test_pairblock_controller.py
)
python -m pyright "${python_paths[@]}" &&
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
python -m pytest \
  tests/pairblock_status/test_declaration_manifest.py \
  tests/pairblock_status/test_markdown_renderer.py \
  tests/pairblock_status/test_pairblock_controller.py -q &&
python -m ruff format --check "${python_paths[@]}" &&
python -m ruff check "${python_paths[@]}"
```

**Gate:** Ruff passes, Pyright reports no errors, and the focused tests establish
six results: one manifest edit
creates every machine and human relationship for a new block; equal inputs
render equal bytes; a receipt transition updates every displayed status; a
manual generated-region edit fails check mode; a missing or duplicate reference
fails before execution; and the controller selects the typed adapter directly
for a manifest-native block. The revision tests establish five more results:

- `test_revision_receipt_binds_manifest_and_record_digests` retains the exact
  accepted change and approval.
- `test_changed_verifier_reopens_owner_and_dependents` propagates one semantic
  change through reverse declaration dependencies.
- `test_unrelated_declaration_change_preserves_receipts` keeps an unaffected
  block complete.
- `test_unapproved_declaration_change_blocks_execution` prevents a stale gate
  or lifecycle transition.
- `test_referenced_record_removal_is_rejected` preserves referential integrity.
- `test_revision_receipt_recomputes_or_validates_each_evidence_claim` rejects
  altered change records, affected blocks, approval evidence, and superseded
  receipt heads.
- `test_pairblock_modules_and_definitions_have_documentation` discovers every
  active module and requires documentation for each definition, dataclass
  field, and persisted `TypedDict` field.

**Acceptance case:** A fixture requirement, verifier, and PairBlock advance
through `gate`, `approve`, `accept`, and `register`. Each transition writes one
receipt, updates the normalized manifest, and changes the generated human view.

**Rejection case:** The gate fails before command execution after a test removes
the verifier reference, duplicates the PairBlock in the legacy inventory,
changes a generated link, corrupts the current receipt reference, or changes an
accepted declaration while the latest `revise` receipt identifies the earlier
digest. The revision loader rejects altered derived evidence and an invalid
superseded-receipt reference. The documentation gate discovers a newly added
Python module and rejects any undocumented definition, dataclass field, or
persisted `TypedDict` field. A
legacy command sequence also fails when an earlier command exits unsuccessfully,
even when a later command would pass.

**Stop condition:** Return the proposal for revision if a manifest-native field
can originate in Markdown, a rendered edit can change execution, a receipt-free
status can appear current, the controller can execute an ambiguously owned ID,
an affected block can retain evidence bound to an older fingerprint,
an unrelated block loses valid evidence,
or the bridge requires migration of the historical records before
`P0-PB-07A` succeeds.

### Future work: shared file identity

MANTRA currently defines the same byte-identity fields twice:
`mantra.rebuild.hopfield_replay.FileIdentity` and
`mantra.rebuild.restoration.RestoredFileIdentity` each store `byte_count` and
`sha256`. VIPER's `viper.references.ResolvedFileRef` stores the same content
identity as `bytes` and `sha256`, then adds `stored_at` to identify where VIPER
can retrieve those bytes.

After `P0-PB-07A` completes through the manifest-native workflow, a proposed
`P0-PB-07B` will add `viper.references.FileIdentity` with `sha256: SHA256` and
`bytes: int` constrained to nonnegative values. `ResolvedFileRef`,
`SnapshotFileRef`, and `ReuseFileIdentity` will derive their shared content
identity from that type. MANTRA will consume the VIPER type and remove its two
local identity classes. The restoration parser will continue accepting the
historical `byte_count` field and map it to `FileIdentity.bytes`.

`P0-PB-10B` can close independently because the declaration protocol and the
file-identity hierarchy have separate runtime paths and acceptance tests.
Promotion requires tests
that preserve the serialized fields and validation of existing VIPER reference
types, preserve the restoration manifest's `byte_count` field, reject an
invalid digest or byte count through the shared base type, and rerun the
restoration and Hopfield parity gates.

### Future work: discriminated lifecycle-evidence union

The active declaration and lifecycle records use one closed vocabulary for
`kind` while retaining `target: str` and `revision: str`. Those strings name
different objects: a pytest node ID, command, repository-relative artifact,
external review, Git commit, content digest, or provenance identity. The
current controller validates, serializes, and displays them. No active caller
dispatches a kind-specific operation through either string.

Do not add the full union to `P0-PB-07B`; that block owns byte identity. A
separate proposed PairBlock will introduce these models only after a runtime
consumer needs kind-specific parsing or validation:

```python
@dataclass(frozen=True, slots=True)
class TestRunEvidenceRef:
    kind: Literal["test_run"]
    target: PytestNodeId
    revision: GateReceiptSHA256


@dataclass(frozen=True, slots=True)
class NonTestCommandRunEvidenceRef:
    kind: Literal["command_run"]
    target: CommandIdentity
    revision: GateReceiptSHA256


@dataclass(frozen=True, slots=True)
class ArtifactEvidenceRef:
    kind: Literal["artifact"]
    target: RepositoryArtifactPath
    revision: FileIdentity | ViperContentId | GitCommit


@dataclass(frozen=True, slots=True)
class ApprovalEvidenceRef:
    kind: Literal["approval"]
    target: ReviewRecordLocator
    revision: ReviewRecordIdentity


type GateRunEvidenceRef = TestRunEvidenceRef | NonTestCommandRunEvidenceRef
type LifecycleEvidenceRef = (
    GateRunEvidenceRef | ArtifactEvidenceRef | ApprovalEvidenceRef
)
```

`LifecycleEvidenceRef` is the discriminated union, and each leaf record's
literal `kind` field is its discriminator. The union partitions references by
the thing that supplies evidence: a gate run, an immutable artifact, or a
review decision. `GateRunEvidenceRef` then partitions gate runs into test-run
and non-test command-run references. Origin is metadata on the referenced
record, not a peer classification axis.

Every referenced name other than `Literal` and `FileIdentity` is proposed. The
future contract must define each value type from observed examples before code
is written. It must assign the parser, serializer, CLI adapter, global schema
mapping, and migration reader for every leaf variant. It must increment the
schema version and write only `test_run`, `command_run`, `artifact`, and
`approval` in new records. Existing receipts remain immutable audit evidence;
the migration reader translates their prior tags without rewriting their
bytes.

`P0-PB-10B` implements only the shared `EvidenceKind` literal; it does not
implement or replace the discriminated union. It can close because no active
consumer requires a more specific target or revision type. Promotion requires
at least one real receipt of every kind, a caller that benefits from typed
dispatch, round-trip tests for all four leaf variants, rejection tests for
crossed kind/target/revision combinations, and proof that historical receipts
translate without rewriting their bytes.

## 11. Sources

<!-- generated:manifest-native-contract:start -->
#### Manifest-native block P0-PB-05P

**Status:** Applied

**Requirements:**

- `P0-REQ-35`: A replay declares role-specific typed outputs once, and VIPER restores several selected artifacts beneath one destination using their declared relative paths.

**Verifier conditions:**

- `P0-VR-34`: A multi-artifact restore joins the destination directory to each frozen output path.
- `P0-VR-34`: The restore planner rejects declared paths that overlap beneath the destination.
- `P0-VR-34`: The Hopfield stages expose typed raw-gene prediction, attention-summary, and parity-receipt outputs.
- `P0-VR-34`: The Hopfield runner restores its selected outputs with one execution.restore call and repeats no output filename.

**Dependencies:** `P0-PB-05K`, `P0-PB-10J`

**Implementation:** [_restore.py](../../../viper/src/viper/execution/_restore.py) · [restoration.py](../../../viper/src/viper/restoration.py) · [retry-restore-compare.md](../../../viper/docs/how-to/retry-restore-compare.md) · [test_storage.py](../../../viper/tests/test_storage.py)

**Current receipt:** [receipt](../../evidence/pairblock-lifecycle/p0-pb-05p/20260913T072533.800633Z-accept.json)

**Gate:**

```bash
cd /Users/machina/Developer/ChatGPT/viper
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /bin/zsh -e -c 'python -m pyright src/viper/execution/_restore.py src/viper/restoration.py tests/test_storage.py && python -m pytest tests/test_storage.py -q && python -m ruff format --check src/viper/execution/_restore.py src/viper/restoration.py tests/test_storage.py && python -m ruff check src/viper/execution/_restore.py src/viper/restoration.py tests/test_storage.py'
```

**Next transition:**

```bash
cd /Users/machina/Developer/ChatGPT/RICO
python -m tools.pairblock_status.pairblock_controller advance P0-PB-05P register --evidence-kind KIND --evidence-target TARGET --evidence-revision REVISION
```

#### Manifest-native block P0-PB-07A

**Status:** Review

**Requirements:**

- `P0-REQ-26`: The selected Hopfield replay passes only when its prediction file bytes and hold PearsonDelta exactly match the approved historical result.
- `P0-REQ-35`: A replay declares role-specific typed outputs once, and VIPER restores several selected artifacts beneath one destination using their declared relative paths.

**Verifier conditions:**

- `P0-VR-25`: The evaluation stage consumes both the replayed and historical prediction archives.
- `P0-VR-25`: The receipt records and compares the byte count and SHA-256 of both prediction archives.
- `P0-VR-25`: The parity decision requires equal prediction-file identities and an exactly equal hold PearsonDelta.
- `P0-VR-25`: The receipt retains exact array equality as diagnostic evidence.
- `P0-VR-34`: A multi-artifact restore joins the destination directory to each frozen output path.
- `P0-VR-34`: The restore planner rejects declared paths that overlap beneath the destination.
- `P0-VR-34`: The Hopfield stages expose typed raw-gene prediction, attention-summary, and parity-receipt outputs.
- `P0-VR-34`: The Hopfield runner restores its selected outputs with one execution.restore call and repeats no output filename.

**Dependencies:** `P0-PB-05P`, `P0-PB-07`, `P0-PB-10J`

**Implementation:** [hopfield_replay.py](../../../mantra/src/mantra/rebuild/hopfield_replay.py) · [test_hopfield_replay.py](../../../mantra/src/mantra/rebuild/tests/test_hopfield_replay.py)

**Current receipt:** [receipt](../../evidence/pairblock-gates/p0-pb-07a/20260913T072602.343866Z.json)

**Gate:**

```bash
cd /Users/machina/Developer/ChatGPT/mantra
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=/Users/machina/Developer/ChatGPT/mantra/src:/Users/machina/Developer/ChatGPT/mantra /bin/zsh -e -c 'python -m pyright src/mantra/rebuild/hopfield_replay.py src/mantra/rebuild/tests/test_hopfield_replay.py && python -m pytest --rootdir=/Users/machina/Developer/ChatGPT/mantra/src --confcutdir=/Users/machina/Developer/ChatGPT/mantra/src src/mantra/rebuild/tests/test_hopfield_replay.py -q && python -m ruff format --check src/mantra/rebuild/hopfield_replay.py src/mantra/rebuild/tests/test_hopfield_replay.py && python -m ruff check src/mantra/rebuild/hopfield_replay.py src/mantra/rebuild/tests/test_hopfield_replay.py'
```

**Next transition:**

```bash
cd /Users/machina/Developer/ChatGPT/RICO
python -m tools.pairblock_status.pairblock_controller advance P0-PB-07A approve --evidence-kind KIND --evidence-target TARGET --evidence-revision REVISION
```

#### Manifest-native block P0-PB-10D

**Status:** Applied

**Requirements:**

- `P0-REQ-28`: Each lifecycle event accepts only the evidence category and verified evidence target assigned to that event.

**Verifier conditions:**

- `P0-VR-27`: The lifecycle policy assigns one evidence rule to every executable event.
- `P0-VR-27`: The controller validates the evidence rule before it writes a receipt.

**Dependencies:** `P0-PB-10A`

**Implementation:** [profile.py](../../tools/pairblock_status/profile.py) · [pairblock_controller.py](../../tools/pairblock_status/pairblock_controller.py) · [test_lifecycle_evidence.py](../../tests/pairblock_status/test_lifecycle_evidence.py)

**Current receipt:** [receipt](../../evidence/pairblock-lifecycle/p0-pb-10d/20260913T061220.270166Z-accept.json)

**Gate:**

```bash
cd /Users/machina/Developer/ChatGPT/RICO
PYTHONPATH=. /bin/zsh -e -c 'python -m pyright tools/pairblock_status/profile.py tools/pairblock_status/pairblock_controller.py tests/pairblock_status/test_lifecycle_evidence.py && python -m pytest tests/pairblock_status/test_lifecycle_evidence.py -q && python -m ruff format --check tools/pairblock_status/profile.py tools/pairblock_status/pairblock_controller.py tests/pairblock_status/test_lifecycle_evidence.py && python -m ruff check tools/pairblock_status/profile.py tools/pairblock_status/pairblock_controller.py tests/pairblock_status/test_lifecycle_evidence.py'
```

**Next transition:**

```bash
cd /Users/machina/Developer/ChatGPT/RICO
python -m tools.pairblock_status.pairblock_controller advance P0-PB-10D register --evidence-kind KIND --evidence-target TARGET --evidence-revision REVISION
```

#### Manifest-native block P0-PB-10E

**Status:** Applied

**Requirements:**

- `P0-REQ-29`: A native receipt is authoritative only when its complete schema and recomputed command, output, declaration, repository, and predecessor identities agree with the declared operation.

**Verifier conditions:**

- `P0-VR-28`: Native receipts reject unknown fields and invalid nested values.
- `P0-VR-28`: Gate receipts recompute the command, output, declaration, manifest, drift, and predecessor relationships.
- `P0-VR-28`: Receipts name both the declaration repository and the implementation repository when they differ.

**Dependencies:** `P0-PB-10D`

**Implementation:** [execution_identity.py](../../tools/pairblock_status/execution_identity.py) · [receipt_validation.py](../../tools/pairblock_status/receipt_validation.py) · [pairblock_controller.py](../../tools/pairblock_status/pairblock_controller.py) · [test_receipt_integrity.py](../../tests/pairblock_status/test_receipt_integrity.py)

**Current receipt:** [receipt](../../evidence/pairblock-lifecycle/p0-pb-10e/20260913T061316.251288Z-accept.json)

**Gate:**

```bash
cd /Users/machina/Developer/ChatGPT/RICO
PYTHONPATH=. /bin/zsh -e -c 'python -m pyright tools/pairblock_status/execution_identity.py tools/pairblock_status/receipt_validation.py tools/pairblock_status/pairblock_controller.py tests/pairblock_status/test_receipt_integrity.py && python -m pytest tests/pairblock_status/test_receipt_integrity.py -q && python -m ruff format --check tools/pairblock_status/execution_identity.py tools/pairblock_status/receipt_validation.py tools/pairblock_status/pairblock_controller.py tests/pairblock_status/test_receipt_integrity.py && python -m ruff check tools/pairblock_status/execution_identity.py tools/pairblock_status/receipt_validation.py tools/pairblock_status/pairblock_controller.py tests/pairblock_status/test_receipt_integrity.py'
```

**Next transition:**

```bash
cd /Users/machina/Developer/ChatGPT/RICO
python -m tools.pairblock_status.pairblock_controller advance P0-PB-10E register --evidence-kind KIND --evidence-target TARGET --evidence-revision REVISION
```

#### Manifest-native block P0-PB-10F

**Status:** Applied

**Requirements:**

- `P0-REQ-30`: Declaration acceptance binds the user's approval to one persisted revision plan and accepts only declaration schema version 1.

**Verifier conditions:**

- `P0-VR-29`: plan-revision persists the candidate declaration digest and computed change.
- `P0-VR-29`: revise requires that exact plan and rejects a different candidate manifest.
- `P0-VR-29`: Live manifests and accepted snapshots share one exact schema-version check.

**Dependencies:** `P0-PB-10A`

**Implementation:** [declaration_manifest.py](../../tools/pairblock_status/declaration_manifest.py) · [pairblock_controller.py](../../tools/pairblock_status/pairblock_controller.py) · [test_declaration_revision_integrity.py](../../tests/pairblock_status/test_declaration_revision_integrity.py)

**Current receipt:** [receipt](../../evidence/pairblock-lifecycle/p0-pb-10f/20260913T061221.508549Z-accept.json)

**Gate:**

```bash
cd /Users/machina/Developer/ChatGPT/RICO
PYTHONPATH=. /bin/zsh -e -c 'python -m pyright tools/pairblock_status/declaration_manifest.py tools/pairblock_status/pairblock_controller.py tests/pairblock_status/test_declaration_revision_integrity.py && python -m pytest tests/pairblock_status/test_declaration_revision_integrity.py -q && python -m ruff format --check tools/pairblock_status/declaration_manifest.py tools/pairblock_status/pairblock_controller.py tests/pairblock_status/test_declaration_revision_integrity.py && python -m ruff check tools/pairblock_status/declaration_manifest.py tools/pairblock_status/pairblock_controller.py tests/pairblock_status/test_declaration_revision_integrity.py'
```

**Next transition:**

```bash
cd /Users/machina/Developer/ChatGPT/RICO
python -m tools.pairblock_status.pairblock_controller advance P0-PB-10F register --evidence-kind KIND --evidence-target TARGET --evidence-revision REVISION
```

#### Manifest-native block P0-PB-10G

**Status:** Applied

**Requirements:**

- `P0-REQ-31`: An interrupted state transition converges to one validated receipt-derived contract and checklist projection before another operation runs.

**Verifier conditions:**

- `P0-VR-30`: The controller writes a recoverable prepared record before changing receipt-derived projections.
- `P0-VR-30`: A successful operation publishes its authoritative receipt after both projection files match the prepared bytes and the semantic validator accepts them.
- `P0-VR-30`: The next controller invocation completes an interrupted prepared transition idempotently.

**Dependencies:** `P0-PB-10E`, `P0-PB-10F`

**Implementation:** [projection_transaction.py](../../tools/pairblock_status/projection_transaction.py) · [pairblock_controller.py](../../tools/pairblock_status/pairblock_controller.py) · [test_projection_recovery.py](../../tests/pairblock_status/test_projection_recovery.py)

**Current receipt:** [receipt](../../evidence/pairblock-lifecycle/p0-pb-10g/20260913T061351.350332Z-accept.json)

**Gate:**

```bash
cd /Users/machina/Developer/ChatGPT/RICO
PYTHONPATH=. /bin/zsh -e -c 'python -m pyright tools/pairblock_status/projection_transaction.py tools/pairblock_status/pairblock_controller.py tests/pairblock_status/test_projection_recovery.py && python -m pytest tests/pairblock_status/test_projection_recovery.py -q && python -m ruff format --check tools/pairblock_status/projection_transaction.py tools/pairblock_status/pairblock_controller.py tests/pairblock_status/test_projection_recovery.py && python -m ruff check tools/pairblock_status/projection_transaction.py tools/pairblock_status/pairblock_controller.py tests/pairblock_status/test_projection_recovery.py'
```

**Next transition:**

```bash
cd /Users/machina/Developer/ChatGPT/RICO
python -m tools.pairblock_status.pairblock_controller advance P0-PB-10G register --evidence-kind KIND --evidence-target TARGET --evidence-revision REVISION
```

#### Manifest-native block P0-PB-10H

**Status:** Applied

**Requirements:**

- `P0-REQ-32`: Generated review links encode valid Markdown destinations and each displayed lifecycle command identifies the controlling repository.

**Verifier conditions:**

- `P0-VR-31`: Links escape Markdown control characters while preserving repository-relative targets and fragments.
- `P0-VR-31`: Each generated transition command begins in the controlling repository.

**Dependencies:** `P0-PB-10A`

**Implementation:** [markdown_renderer.py](../../tools/pairblock_status/markdown_renderer.py) · [test_markdown_renderer.py](../../tests/pairblock_status/test_markdown_renderer.py)

**Current receipt:** [receipt](../../evidence/pairblock-lifecycle/p0-pb-10h/20260913T061222.687709Z-accept.json)

**Gate:**

```bash
cd /Users/machina/Developer/ChatGPT/RICO
PYTHONPATH=. /bin/zsh -e -c 'python -m pyright tools/pairblock_status/markdown_renderer.py tests/pairblock_status/test_markdown_renderer.py && python -m pytest tests/pairblock_status/test_markdown_renderer.py -q && python -m ruff format --check tools/pairblock_status/markdown_renderer.py tests/pairblock_status/test_markdown_renderer.py && python -m ruff check tools/pairblock_status/markdown_renderer.py tests/pairblock_status/test_markdown_renderer.py'
```

**Next transition:**

```bash
cd /Users/machina/Developer/ChatGPT/RICO
python -m tools.pairblock_status.pairblock_controller advance P0-PB-10H register --evidence-kind KIND --evidence-target TARGET --evidence-revision REVISION
```

#### Manifest-native block P0-PB-10I

**Status:** Applied

**Requirements:**

- `P0-REQ-33`: A manifest-native PairBlock derives its waiting state from every declared dependency, including a dependency retained in the legacy checklist.

**Verifier conditions:**

- `P0-VR-32`: Waiting-state derivation combines receipt-derived native statuses with parsed legacy statuses.
- `P0-VR-32`: An unresolved dependency produces the same displayed state and gate rejection regardless of declaration origin.
- `P0-VR-32`: The render command regenerates both human views from accepted declarations and receipts without changing lifecycle state.

**Dependencies:** `P0-PB-10H`

**Implementation:** [pairblock_controller.py](../../tools/pairblock_status/pairblock_controller.py) · [test_cross_origin_dependencies.py](../../tests/pairblock_status/test_cross_origin_dependencies.py)

**Current receipt:** [receipt](../../evidence/pairblock-lifecycle/p0-pb-10i/20260913T061319.163029Z-accept.json)

**Gate:**

```bash
cd /Users/machina/Developer/ChatGPT/RICO
PYTHONPATH=. /bin/zsh -e -c 'python -m pyright tools/pairblock_status/pairblock_controller.py tests/pairblock_status/test_cross_origin_dependencies.py && python -m pytest tests/pairblock_status/test_cross_origin_dependencies.py -q && python -m ruff format --check tools/pairblock_status/pairblock_controller.py tests/pairblock_status/test_cross_origin_dependencies.py && python -m ruff check tools/pairblock_status/pairblock_controller.py tests/pairblock_status/test_cross_origin_dependencies.py'
```

**Next transition:**

```bash
cd /Users/machina/Developer/ChatGPT/RICO
python -m tools.pairblock_status.pairblock_controller advance P0-PB-10I register --evidence-kind KIND --evidence-target TARGET --evidence-revision REVISION
```

#### Manifest-native block P0-PB-10J

**Status:** Applied

**Requirements:**

- `P0-REQ-34`: A legacy certification accepts only the profile-declared terminal Phase 0 registration artifact and its exact byte identity.

**Verifier conditions:**

- `P0-VR-33`: A profile that enables legacy certification declares one repository-relative terminal artifact path.
- `P0-VR-33`: The certification transition rejects every other artifact even when that artifact's SHA-256 is valid.
- `P0-VR-33`: Completion validation rechecks both the declared artifact path and its byte identity.

**Dependencies:** `P0-PB-10G`, `P0-PB-10I`

**Implementation:** [profile.py](../../tools/pairblock_status/profile.py) · [pairblock_controller.py](../../tools/pairblock_status/pairblock_controller.py) · [checklist_profile.py](../../tools/pairblock_status/checklist_profile.py) · [conftest.py](../../tests/pairblock_status/conftest.py) · [test_pairblock_controller.py](../../tests/pairblock_status/test_pairblock_controller.py)

**Current receipt:** [receipt](../../evidence/pairblock-lifecycle/p0-pb-10j/20260913T062009.909781Z-accept.json)

**Gate:**

```bash
cd /Users/machina/Developer/ChatGPT/RICO
PYTHONPATH=. /bin/zsh -e -c 'python -m pyright tools/pairblock_status/profile.py tools/pairblock_status/pairblock_controller.py tools/pairblock_status/checklist_profile.py tests/pairblock_status/conftest.py tests/pairblock_status/test_pairblock_controller.py && python -m pytest tests/pairblock_status/test_pairblock_controller.py -q && python -m ruff format --check tools/pairblock_status/profile.py tools/pairblock_status/pairblock_controller.py tools/pairblock_status/checklist_profile.py tests/pairblock_status/conftest.py tests/pairblock_status/test_pairblock_controller.py && python -m ruff check tools/pairblock_status/profile.py tools/pairblock_status/pairblock_controller.py tools/pairblock_status/checklist_profile.py tests/pairblock_status/conftest.py tests/pairblock_status/test_pairblock_controller.py'
```

**Next transition:**

```bash
cd /Users/machina/Developer/ChatGPT/RICO
python -m tools.pairblock_status.pairblock_controller advance P0-PB-10J register --evidence-kind KIND --evidence-target TARGET --evidence-revision REVISION
```
<!-- generated:manifest-native-contract:end -->

- MANTRA: `reinstantiation/README.md`
- MANTRA: `reinstantiation/REINSTANTIATION_ROOT_RELEASE.json`
- MANTRA: `reinstantiation/APPLICATION_VERIFICATION.json`
- MANTRA: `experiments/v1952_direct_mil_control_term_ablation/specs/control_term_ablation.yaml`
- MANTRA: `experiments/v1952_direct_mil_control_term_ablation/diagnostics/CONTROL_TERM_MULTISEED_RESULTS.json`
- MANTRA: `docs/EXPERIMENT_ARCHIVE_AND_DELETE.md`
- MANTRA: `archive_pointers/`
- RICO: [`mantra-viper-rebuild-handoff.md`](../mantra-viper-rebuild-handoff.md)
- Git: [revision verification](https://git-scm.com/docs/git-rev-parse) and [commit comparison](https://git-scm.com/docs/git-diff)
- in-toto: [Statement v1](https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md)
- SLSA: [Provenance v1.2](https://slsa.dev/spec/v1.2/provenance)
- W3C: [PROV-DM](https://www.w3.org/TR/prov-dm/)
- Python: [`sys.addaudithook()`](https://docs.python.org/3/library/sys.html#sys.addaudithook) and the [audit-event table](https://docs.python.org/3/library/audit_events.html)
