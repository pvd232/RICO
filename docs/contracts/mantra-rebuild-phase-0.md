# Mantra Rebuild Phase 0 Contract

## 1. Status

**Contract status:** Draft — awaiting user review

**Approval state:** Unapproved. This Git-tracked draft preserves the proposed roadmap. Artifact downloads, restoration, implementation, and PairBlock closure each require the user's review and approval.

This contract governs artifact discovery, capacity planning, restoration, and provenance capture before the Hopfield or MIL rebuild begins. The model rebuild remains out of scope until every Phase 0 acceptance condition passes. The user actively reviews each PairBlock's scope, proposed work, observed result, and gate evidence before the next PairBlock begins.

| ID | Implementation obligation |
|---|---|
| `P0-REQ-01` | Define the minimal rebuild dependency graph $B$ for the selected Hopfield and MIL outputs. |
| `P0-REQ-02` | Give every restored file node in $B$ one verified `RestorationBinding`. |
| `P0-REQ-03` | Calculate the maximum simultaneous local storage requirement before downloading an archive. |
| `P0-REQ-04` | Restore verified files to their canonical, Git-ignored paths inside the MANTRA checkout. |
| `P0-REQ-05` | Run restoration from the MANTRA workspace with a released, pinned `viper-provenance` distribution. |
| `P0-REQ-06` | Record and verify $B$ in the VIPER provenance graph. |
| `P0-REQ-07` | Replay the saved MIL application from restored inputs before rebuilding either model. |
| `P0-REQ-08` | Maintain an independent usefulness ledger for VIPER checks, failures, costs, and confirmed findings. |

## 2. Required claim

Before a model rebuild starts, VIPER can trace each selected result through every file the rebuild reads and every producer entrypoint it executes.

The rebuild dependency graph is $B=(F,P,E)$:

- $F$ contains exact file identities. A file enters $F$ only when a selected rebuild stage reads it or an upstream stage produces it.
- $P$ contains exact producer entrypoints. Each entrypoint is identified by repository commit, source path, symbol, source-file byte count, and source-file SHA-256.
- $E$ contains `consumes` edges from files to producer entrypoints and `produces` edges from producer entrypoints to files.

A `consumes` edge requires both a named stage input and an inspected read of that input by the producer. A `produces` edge requires both a declared stage output and a successful run receipt for that output. Every member of $F \cup P$ must lie on a directed path ending at the selected Hopfield or MIL output. Severing any required node or edge must make graph verification fail.

Historical predictions, checkpoints, and reports used only to compare the rebuild form a separate parity-reference graph $Q$. No member of $Q$ may enter a reconstruction or training stage as an input.

This claim establishes byte identity, executed-producer identity, and graph completeness. Historical training reproducibility and scientific correctness remain later acceptance boundaries.

## 3. Current gap

The repository contains restoration controls, artifact pointers, application verification inputs, and historical producer code. The missing rebuild-specific graph must identify the selected result first, then trace only the files and producers required to rebuild it.

The first missing result is therefore the complete rebuild dependency graph. When the signed Hugging Face records identify an absent local file's bytes, Phase 0 classifies that file as a restoration task. An unrecoverable classification requires a failed search of the signed restoration records.

## 4. Restoration and storage contract

### `RestorationBinding`

`RestorationBinding` tells the MANTRA restoration stage where one required file belongs, where its archived bytes reside, and which bytes must result. For a file node $f \in F$:

$$
r=(f,d,s,c),\qquad
s=(repo,revision,archive,member),\qquad
c=(bytes,sha256).
$$

Here $d$ is the destination relative to the MANTRA repository root. The value $s$ identifies one member of one archive at one immutable Hugging Face revision. The value $c$ identifies the extracted file bytes. The binding contains no producer or consumer list; $B$ owns those relationships.

RICO owns this definition and its approval history. The proposed executable type is `experiments/v1954_hopfield_mil_rebuild/src/restoration/models.py::RestorationBinding` in MANTRA. Its reviewed instances belong in `experiments/v1954_hopfield_mil_rebuild/specs/restoration/bindings.json`. VIPER stores each resolved binding with the run evidence that used it.

### Ownership boundary

RICO contains forward-looking contracts and review records. MANTRA contains executable restoration records, restoration code, restored files, rebuild code, and VIPER run evidence. Restoration uses VIPER as an installed external library; this project does not import from or modify the VIPER source checkout.

The MANTRA execution environment will live at `experiments/v1954_hopfield_mil_rebuild/.venv`. Its checked-in lock file will live at `experiments/v1954_hopfield_mil_rebuild/specs/runtime/requirements.lock`. The lock must select `viper-provenance==0.1.0a3` by released distribution hash. An editable VIPER installation fails the environment gate.

### Local storage

Phase 0 uses three storage roles:

| Role | Local path | Retention rule |
|---|---|---|
| Download cache | `/Users/machina/Developer/ChatGPT/mantra-restoration-cache/` | Holds Hugging Face archive chunks during restoration. A cache file may be removed only after its download and extraction evidence is present in VIPER and the user authorizes removal. |
| Canonical restored files | `/Users/machina/Developer/ChatGPT/mantra/` at each documented repository-relative destination | Holds the verified files consumed by MANTRA. Historical names and paths remain unchanged. |
| VIPER evidence | `/Users/machina/Developer/ChatGPT/mantra/.viper/store/` and `/Users/machina/Developer/ChatGPT/mantra/.viper/catalog.sqlite3` | Holds the provenance objects and graph catalog produced by governed runs. |

Phase 0 restores files only to the download cache, their canonical paths in the MANTRA checkout, and the declared VIPER evidence paths. Restoration scripts receive these roots explicitly. The RICO repositories, historical `/home/machina/MANTRA`, and `/dev/shm` are outside the local restoration boundary.

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
| $H$ | 20 GiB reserved free space. |

The download gate passes only when observed free space is at least $R_{max}$. Shared archive chunks count once.

## 5. Execution roadmap

```mermaid
flowchart TB
    scope_review["User approves Phase 0 contract"]
    contract["RICO Phase 0 contract"]
    environment["MANTRA environment<br/>released VIPER distribution"]
    trace["Trace selected results<br/>into rebuild graph B"]
    binding["RestorationBinding<br/>for each absent file"]
    parity["Parity-reference graph Q<br/>comparison only"]
    capacity["Capacity gate<br/>free space ≥ Rmax"]
    restore["MANTRA-rooted<br/>VIPER restoration run"]
    verify["Verified VIPER graph B<br/>including severed-edge rejection"]
    replay["Saved MIL application replay"]
    evidence_review["User reviews Phase 0 evidence"]
    hopfield["Approval to begin<br/>Hopfield reconstruction"]

    scope_review --> contract
    contract --> environment
    contract --> trace
    trace --> binding
    trace --> parity
    trace --> capacity
    binding --> capacity
    environment --> restore
    capacity --> restore
    restore --> verify
    trace --> verify
    verify --> replay
    parity --> replay
    replay --> evidence_review
    evidence_review --> hopfield

    classDef contractNode fill:#0b5fff,color:#ffffff,stroke:#052e8a,stroke-width:2px
    classDef workNode fill:#f3f7ff,color:#111827,stroke:#315a8a,stroke-width:1.5px
    classDef gateNode fill:#fff4d6,color:#111827,stroke:#9a6700,stroke-width:2px
    classDef outcomeNode fill:#e8f7ee,color:#111827,stroke:#237a44,stroke-width:2px
    class contract contractNode
    class environment,trace,binding,parity,restore workNode
    class scope_review,capacity,verify,replay,evidence_review gateNode
    class hopfield outcomeNode
```

1. Confirm the selected Hopfield and MIL result files that terminate $B$.
2. Create the MANTRA development environment and prove that it uses the released VIPER distribution.
3. Trace the Hopfield result backward to its required file nodes, producer entrypoints, and edges.
4. Trace the MIL result backward through its required file nodes, producer entrypoints, and edges.
5. Classify historical comparison files in $Q$ so they cannot feed the rebuild.
6. Write one `RestorationBinding` for each absent file node in $B$.
7. Calculate $R_{max}$ and stop if the capacity gate fails.
8. Download and extract the required archive members through MANTRA-rooted VIPER stages.
9. Verify $B$, including a rejection case with one required relationship severed.
10. Replay the saved MIL application, freeze Phase 0 evidence, and request approval to begin Hopfield reconstruction.

## 6. Persisted evidence

| Evidence | Required content |
|---|---|
| Rebuild dependency graph | Every required member of $F$, $P$, and $E$, with the selected result as its terminal node. |
| Restoration bindings | One reviewed $r=(f,d,s,c)$ record for every absent restored file in $F$. |
| Environment receipt | Python executable, installed VIPER version, installed distribution identity, lock-file identity, and editable-install rejection result. |
| Capacity receipt | The measured terms in $R_{max}=C+D+V+T+H$, the measurement time, and the gate result. |
| Restoration receipt | The resolved `RestorationBinding` and outcome for each restored file. |
| VIPER graph | The verified runtime representation of $B$. |
| Graph-completeness report | Missing members of $F$, $P$, or $E$, plus the pass or fail result. |
| MIL replay receipt | Exact command, environment, input digests, output digests, metrics, tolerances, and comparison result. |
| VIPER usefulness ledger | Claimed check, real defect detected, independent confirmation, ordinary-test coverage, false alarms, infrastructure failures, time cost, and later reuse. |

The dependency graph, restoration bindings, environment receipt, capacity receipt, restoration receipts, completeness report, replay receipt, and usefulness ledger must themselves be registered in VIPER. Each checked-in evidence file requires a corresponding graph record.

## 7. Verification

| Rule | Executable condition |
|---|---|
| `P0-VR-01` | Every member of $F \cup P$ lies on a path ending at a selected result, and every edge in $E$ has its required evidence. |
| `P0-VR-02` | Every absent restored file in $F$ has exactly one valid `RestorationBinding`. |
| `P0-VR-03` | The measured free space is greater than or equal to $R_{max}$ before download begins. |
| `P0-VR-04` | Every materialized file exists at its canonical path and matches its declared byte count and SHA-256. |
| `P0-VR-05` | The active Python environment contains the released `viper-provenance==0.1.0a3` distribution selected by the checked-in lock file. |
| `P0-VR-06` | The VIPER graph contains every member of $B$, and severing one required node or edge makes verification fail. |
| `P0-VR-07` | The saved MIL application reproduces the hashes and metrics declared by `reinstantiation/APPLICATION_VERIFICATION.json` within its stated tolerances. |
| `P0-VR-08` | Every assessed VIPER check has a usefulness-ledger row and independent evidence for any confirmed defect. |

## 8. Acceptance boundary

### Success

Phase 0 passes when `P0-VR-01` through `P0-VR-08` pass, every required provenance record exists in VIPER, the user reviews the complete evidence set, and the repository contains a synced commit recording the approved contract and Phase 0 receipts.

### Rejection

Phase 0 fails when $B$ contains an unnecessary node, omits a required node or edge, admits a parity reference as a rebuild input, lacks a `RestorationBinding`, exceeds available storage, uses an editable VIPER checkout, restores different bytes, or exceeds a MIL replay tolerance.

## 9. PairBlock order

| PairBlock | Bounded deliverable | Gate |
|---|---|---|
| `P0-PB-01` | Selected result roots and external-VIPER development environment | User approves both roots; `P0-VR-05` passes. |
| `P0-PB-02` | Complete Hopfield subgraph of $B$ | `P0-VR-01` for Hopfield. |
| `P0-PB-03` | Complete MIL subgraph of $B$ | `P0-VR-01` for MIL. |
| `P0-PB-04` | `RestorationBinding` implementation and reviewed records | `P0-VR-02`. |
| `P0-PB-05` | Capacity receipt and download plan | `P0-VR-03`. |
| `P0-PB-06` | Verified restoration and graph-completeness rejection test | `P0-VR-04` and `P0-VR-06`. |
| `P0-PB-07` | Saved MIL application replay | `P0-VR-07`. |
| `P0-PB-08` | Phase 0 evidence freeze and usefulness assessment | `P0-VR-08` and user approval. |

For each PairBlock, Codex drafts the proposed contract or source, the user reviews it, Codex performs the agreed code review, the user implements approved code, and Codex reviews the applied diff and focused gate. A PairBlock closes only when the implementation, test result, Git evidence, and VIPER evidence agree.

## 10. Sources

- MANTRA: `reinstantiation/README.md`
- MANTRA: `reinstantiation/REINSTANTIATION_ROOT_RELEASE.json`
- MANTRA: `reinstantiation/APPLICATION_VERIFICATION.json`
- MANTRA: `docs/EXPERIMENT_ARCHIVE_AND_DELETE.md`
- MANTRA: `archive_pointers/`
- RICO: [`mantra-viper-rebuild-handoff.md`](../mantra-viper-rebuild-handoff.md)
