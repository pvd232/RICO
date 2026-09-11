# MANTRA–VIPER Rebuild Phase 0 Contract

## 1. Status

**Contract status:** Draft — awaiting user review

**Approval state:** Unapproved. This Git-tracked draft preserves the proposed roadmap. Artifact downloads, restoration, implementation, and PairBlock closure each require the user's review and approval.

This contract governs artifact discovery, capacity planning, restoration, and provenance capture before the Hopfield or MIL rebuild begins. The model rebuild remains out of scope until every Phase 0 acceptance condition passes. The user actively reviews each PairBlock's scope, proposed work, observed result, and gate evidence before the next PairBlock begins.

| ID | Implementation obligation |
|---|---|
| `P0-REQ-01` | Identify every data-bearing input, fitted transform, checkpoint, configuration, and source file required by the selected Hopfield and MIL pipelines. |
| `P0-REQ-02` | Bind each restorable file to its canonical MANTRA path, immutable Hugging Face location, revision, archive member, byte count, and SHA-256. |
| `P0-REQ-03` | Calculate the maximum simultaneous local storage requirement before downloading an archive. |
| `P0-REQ-04` | Restore verified files to their canonical, Git-ignored paths inside the MANTRA checkout. |
| `P0-REQ-05` | Record every restored file and producing script in the VIPER provenance graph. |
| `P0-REQ-06` | Prove that the graph reaches every file and script required to recompute the selected result. |
| `P0-REQ-07` | Replay the saved MIL application from restored artifacts before rebuilding either model. |
| `P0-REQ-08` | Maintain an independent usefulness ledger for VIPER checks, failures, costs, and confirmed findings. |

## 2. Required claim

Before a model rebuild starts, MANTRA can locate and verify every artifact and source file required by the selected historical pipeline, and VIPER can trace the selected result back through those exact bytes.

Let (A) be the required artifact set, (S) the required source-file set, (H(x)) the SHA-256 of file (x), and (G) the retained VIPER provenance graph. Phase 0 accepts only when:

$$
\forall x \in A \cup S:\ \operatorname{present}(x) \land H(x)=H_{declared}(x) \land \operatorname{reachable}_{G}(result,x).
$$

This claim establishes byte identity and graph completeness. Historical training reproducibility and scientific correctness remain later acceptance boundaries.

## 3. Current gap

The repository contains restoration controls, artifact pointers, application verification inputs, and historical producer code. The missing rebuild-specific inventory must join each required pipeline object to its immutable download location, canonical local path, producer, consumers, and VIPER graph identity.

The first missing result is therefore the complete artifact-and-producer manifest. When the signed Hugging Face records identify an absent local file's bytes, Phase 0 classifies that file as a restoration task. An unrecoverable classification requires a failed search of the signed restoration records.

## 4. Storage contract

Phase 0 uses three storage roles:

| Role | Local path | Retention rule |
|---|---|---|
| Download cache | `/Users/machina/Developer/ChatGPT/mantra-restoration-cache/` | Holds Hugging Face archive chunks during restoration. A cache file may be removed only after its download and extraction evidence is present in VIPER and the user authorizes removal. |
| Canonical restored files | `/Users/machina/Developer/ChatGPT/mantra/` at each documented repository-relative destination | Holds the verified files consumed by MANTRA. Historical names and paths remain unchanged. |
| VIPER evidence | `/Users/machina/Developer/ChatGPT/mantra/.viper/store/` and `/Users/machina/Developer/ChatGPT/mantra/.viper/catalog.sqlite3` | Holds the provenance objects and graph catalog produced by governed runs. |

Phase 0 restores files only to the download cache, their canonical paths in the MANTRA checkout, and the declared VIPER evidence paths. Restoration scripts must receive these current local roots explicitly. The paths `/Users/machina/Developer/RICO`, `/Users/machina/Developer/ChatGPT/RICO`, historical `/home/machina/MANTRA`, and `/dev/shm` are outside the local restoration boundary.

The artifact manifest must record these fields for every required file:

| Field | Meaning |
|---|---|
| `artifact_role` | Stable pipeline role. |
| `canonical_path` | Repository-relative destination under the MANTRA checkout. |
| `hf_repo_id` | Hugging Face repository containing the source archive. |
| `hf_revision` | Immutable revision used for retrieval. |
| `archive_member` | Archive chunk and member that supply the file. |
| `sha256` | Expected digest of the restored file. |
| `compressed_bytes` | Download bytes attributable to the file or containing chunk. |
| `extracted_bytes` | Restored file size. |
| `producer` | Historical script and qualified function when available. |
| `consumers` | Pipeline stages or scripts that read the file. |
| `viper_retained_bytes` | Additional physical bytes VIPER will retain for this file. |
| `restoration_source` | Signed release, manifest, pointer, or restoration record supporting the row. |
| `status` | `identified`, `downloaded`, `verified`, `materialized`, or `graph_registered`. |

### Capacity gate

Before the first archive download, Phase 0 must measure current free space and calculate:

$$
R_{max}=C+D+V+T+H,
$$

where (C) is the maximum compressed cache retained at once, (D) is the extracted canonical footprint, (V) is additional VIPER-retained storage, (T) is peak temporary extraction space, and (H) is 20 GiB of reserved free space. The download gate passes only when observed free space is at least (R_{max}). The manifest must identify shared archive chunks so their bytes are counted once.

## 5. Execution roadmap

1. Read the handoff, architecture appendices, restoration controls, archive pointers, historical configurations, and producer scripts.
2. Trace the selected Hopfield result backward from its prediction and score to every input, fitted object, configuration, and producer.
3. Trace the selected MIL result backward through calibration, correction, retrieval, student training, teacher training, preprocessing, and raw inputs.
4. Write the combined artifact-and-producer manifest before downloading data.
5. Resolve each manifest row to an immutable Hugging Face revision, archive member, expected digest, and byte count.
6. Calculate (R_{max}), inspect VIPER duplication behavior, and stop if the capacity gate fails.
7. Download only the required archive chunks into the download cache.
8. Verify archive and member identities, then materialize each file at its canonical MANTRA path.
9. Register each restored file, source file, configuration, and relationship in VIPER.
10. Run graph-completeness checks, including a rejection case with one required relationship severed.
11. Replay the saved MIL application and compare its declared outputs, hashes, and metrics.
12. Freeze the Phase 0 evidence and authorize the first Hopfield reconstruction PairBlock.

## 6. Persisted evidence

| Evidence | Required content |
|---|---|
| Artifact-and-producer manifest | Every field defined in the storage contract, one row per required file. |
| Capacity receipt | Free bytes, (C), (D), (V), (T), (H), (R_{max}), measurement time, and gate result. |
| Restoration receipt | Download identity, extraction identity, canonical destination, byte count, digest, and outcome for each file. |
| VIPER graph | Nodes and relationships for sources, archive records, restored artifacts, producers, configurations, stages, outputs, measurements, and the selected result. |
| Graph-completeness report | Required nodes, missing nodes, required relationships, missing relationships, and pass or fail. |
| MIL replay receipt | Exact command, environment, input digests, output digests, metrics, tolerances, and comparison result. |
| VIPER usefulness ledger | Claimed check, real defect detected, independent confirmation, ordinary-test coverage, false alarms, infrastructure failures, time cost, and later reuse. |

The artifact-and-producer manifest, capacity receipt, restoration receipts, completeness report, replay receipt, and usefulness ledger must themselves be registered in VIPER. Each checked-in document requires a corresponding graph record.

## 7. Verification

| Rule | Executable condition |
|---|---|
| `P0-VR-01` | Every required pipeline input and persisted fitted object has exactly one manifest row. |
| `P0-VR-02` | Every restorable manifest row has an immutable Hugging Face revision, archive member, expected SHA-256, and canonical destination. |
| `P0-VR-03` | The measured free space is greater than or equal to (R_{max}) before download begins. |
| `P0-VR-04` | Every materialized file exists at its canonical path and matches its declared byte count and SHA-256. |
| `P0-VR-05` | The VIPER graph reaches every member of (A \cup S) from the selected result. |
| `P0-VR-06` | Removing one required producer-to-artifact or artifact-to-consumer relationship causes graph-completeness verification to fail. |
| `P0-VR-07` | The saved MIL application reproduces the hashes and metrics declared by `reinstantiation/APPLICATION_VERIFICATION.json` within its stated tolerances. |
| `P0-VR-08` | Every assessed VIPER check has a usefulness-ledger row and independent evidence for any confirmed defect. |

## 8. Acceptance boundary

### Success

Phase 0 passes when `P0-VR-01` through `P0-VR-08` pass, every required provenance record exists in VIPER, the user reviews the complete evidence set, and the repository contains a synced commit recording the approved contract and Phase 0 receipts.

### Rejection

Phase 0 fails when a required file lacks an immutable source or expected digest, the capacity calculation omits simultaneous storage, a restored file differs from its declared bytes, the VIPER trace omits a required input or producer, or the saved MIL application exceeds a declared tolerance.

## 9. PairBlock order

| PairBlock | Bounded deliverable | Gate |
|---|---|---|
| `P0-PB-01` | Artifact-and-producer manifest schema and documentation-source inventory | User approves scope and fields. |
| `P0-PB-02` | Complete Hopfield dependency rows | `P0-VR-01` and `P0-VR-02` for Hopfield. |
| `P0-PB-03` | Complete MIL dependency rows | `P0-VR-01` and `P0-VR-02` for MIL. |
| `P0-PB-04` | Capacity receipt and download plan | `P0-VR-03`. |
| `P0-PB-05` | Verified restoration and canonical materialization | `P0-VR-04`. |
| `P0-PB-06` | VIPER registration and completeness verifier | `P0-VR-05` and `P0-VR-06`. |
| `P0-PB-07` | Saved MIL application replay | `P0-VR-07`. |
| `P0-PB-08` | Phase 0 evidence freeze and usefulness assessment | `P0-VR-08` and user approval. |

For each PairBlock, Codex drafts the proposed contract or source, the user reviews it, Codex performs the agreed code review, the user implements approved code, and Codex reviews the applied diff and focused gate. A PairBlock closes only when the implementation, test result, Git evidence, and VIPER evidence agree.

## 10. Sources

- MANTRA: `reinstantiation/README.md`
- MANTRA: `reinstantiation/REINSTANTIATION_ROOT_RELEASE.json`
- MANTRA: `reinstantiation/APPLICATION_VERIFICATION.json`
- MANTRA: `docs/EXPERIMENT_ARCHIVE_AND_DELETE.md`
- MANTRA: `archive_pointers/`
- RICO: [`mantra-viper-rebuild-handoff.md`](mantra-viper-rebuild-handoff.md)
