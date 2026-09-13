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
- [Phase 0G: structured PairBlock declarations](#phase-0g-introduce-structured-pairblock-declarations)
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

**Active tranche:** The accepted Phase 0 restoration and replay evidence remains
frozen. `P0-PB-10B` now introduces a structured origin for future requirements,
verifiers, PairBlocks, paths, and gates before the Hopfield output-parity repair.
The terminal RICO-rooted VIPER [run identity](../../evidence/phase0/rico/phase0_registration_run.json)
and [registration receipt](../../evidence/phase0/rico/phase0_registration_receipt.json)
remain unchanged. The
`certify` receipts for `P0-PB-01`, `P0-PB-04A`, `P0-PB-04B`, and `P0-PB-05A`
preserve their pre-protocol records and bind their completion to the terminal
Phase 0 artifact.

The resolution table identifies the next action. `Review` requires the user's
decision. `Approved` authorizes the user to apply the proposal. `Applied`
means Codex accepted the resulting diff, test evidence, and Git evidence.
`Complete` requires VIPER registration, the final receipt, and a checked box.

**`P0-PB-04B` inspection evidence:** Project release revision
`51cb27990244f1f418e8b7cd11cd98672d18919a` pins control revision
`a3c7405f375ba2f18f856fbfebe6480e98792df0`; both signatures verify with
`reinstantiation/CONTROL_SIGNING_PUBLIC_KEY.pem`.
The signed checksums match `ARCHIVE_INDEX.json`,
`FILESYSTEM_MANIFEST.jsonl.zst`, and the content-object index. Six
missing Hopfield inputs belong to `historical_and_shared_experiments`; the
saved encoder and historical prediction belong to `sota_reproducer`. The
`fit_tune_ctrl19_matched_log1p_cp10k_gene_deltas.npz` destination is an
absolute historical symlink whose target file carries the approved byte count
and SHA-256. The reader must resolve that link inside the historical MANTRA
root and reject links that escape it. Archive payload downloads remain at
zero. The resolver produced the original eight Hopfield bindings from those
controls. The completed set contains 27 Hopfield and MIL destinations in
`historical_and_shared_experiments`, `sota_reproducer`, and
`later_experiments`.

## PairBlock resolution

| PairBlock | Proposal gate | Resolution status | Depends on | Contract block | Proposed code |
|---|---|---|---|---|---|
| `P0-PB-01` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-01/20260913T024518.735984Z-certify.json)) | Complete | None | [Block](../contracts/mantra-rebuild-phase-0.md#p0-pb-01) | [Accepted implementation](../contracts/mantra-rebuild-phase-0.md#p0-pb-01-accepted-implementation) |
| `P0-PB-02` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-02/20260912T184646.515912Z-confirm.json)) | Complete | None | [Block](../contracts/mantra-rebuild-phase-0.md#p0-pb-02) | [Work description](../contracts/mantra-rebuild-phase-0.md#p0-pb-02) |
| `P0-PB-03` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-03/20260912T203922.293506Z-confirm.json)) | Complete | None | [Block](../contracts/mantra-rebuild-phase-0.md#p0-pb-03) | [Work description](../contracts/mantra-rebuild-phase-0.md#p0-pb-03) |
| `P0-PB-04` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-04/20260913T024520.405075Z-confirm.json)) | Complete | `P0-PB-04A`, `P0-PB-04B` | [Block](../contracts/mantra-rebuild-phase-0.md#p0-pb-04) | [Child blocks](../contracts/mantra-rebuild-phase-0.md#p0-pb-04) |
| `P0-PB-04A` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-04a/20260913T024519.074399Z-certify.json)) | Complete | None | [Block](../contracts/mantra-rebuild-phase-0.md#p0-pb-04a) | [Source](../../../mantra/src/mantra/rebuild/restoration.py) · [Tests](../../../mantra/src/mantra/rebuild/tests/test_restoration.py) |
| `P0-PB-04B` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-04b/20260913T024519.409010Z-certify.json)) | Complete | None | [Block](../contracts/mantra-rebuild-phase-0.md#p0-pb-04b) | [Source](../../../mantra/src/mantra/rebuild/restoration.py) · [Base tests](../../../mantra/src/mantra/rebuild/tests/test_restoration.py) · [Resolver tests](../../../mantra/src/mantra/rebuild/tests/test_control_resolution.py) |
| `P0-PB-05` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-05/20260913T024521.071472Z-confirm.json)) | Complete | `P0-PB-05A`, `P0-PB-05B` | [Block](../contracts/mantra-rebuild-phase-0.md#p0-pb-05) | [Child blocks](../contracts/mantra-rebuild-phase-0.md#p0-pb-05) |
| `P0-PB-05A` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-05a/20260913T024519.741712Z-certify.json)) | Complete | None | [Block](../contracts/mantra-rebuild-phase-0.md#p0-pb-05a) | [Source](../../../mantra/src/mantra/rebuild/capacity.py) · [Tests](../../../mantra/src/mantra/rebuild/tests/test_capacity.py) |
| `P0-PB-05B` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-05b/20260913T023138.391261Z-register.json)) | Complete | `P0-PB-04B` | [Block](../contracts/mantra-rebuild-phase-0.md#p0-pb-05b) | [Source](../../../mantra/src/mantra/rebuild/archive_plan.py) · [Tests](../../../mantra/src/mantra/rebuild/tests/test_archive_plan.py) |
| `P0-PB-05C` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-05c/20260913T001013.278571Z-register.json)) | Complete | None | [Block](../contracts/mantra-rebuild-phase-0.md#p0-pb-05c) | [Observer](../../../viper/src/viper/_workers/file_access.py) · [Tests](../../../viper/tests/test_stage_file_access.py) |
| `P0-PB-05D` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-05d/20260913T023138.819375Z-register.json)) | Complete | None | [Block](../contracts/mantra-rebuild-phase-0.md#p0-pb-05d) | [Verifier](../../../viper/src/viper/_verification/plan.py) · [Tests](../../../viper/tests/test_verification.py) · [Test map](../../../viper/tests/declaration_observers.toml) |
| `P0-PB-05E` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-05e/20260913T023139.133182Z-register.json)) | Complete | `P0-PB-05D` | [Block](../contracts/mantra-rebuild-phase-0.md#p0-pb-05e) | [Run model](../../../viper/src/viper/runs.py) · [Protocol tests](../../../viper/tests/test_protocol.py) · [Relationship tests](../../../viper/tests/test_verification.py) · [Test map](../../../viper/tests/declaration_observers.toml) |
| `P0-PB-05F` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-05f/20260913T001013.563488Z-register.json)) | Complete | `P0-PB-05C` | [Block](../contracts/mantra-rebuild-phase-0.md#p0-pb-05f) | [Observer](../../../viper/src/viper/_workers/file_access.py) · [Tests](../../../viper/tests/test_stage_file_access.py) · [Test map](../../../viper/tests/declaration_observers.toml) |
| `P0-PB-05G` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-05g/20260913T001013.825215Z-register.json)) | Complete | `P0-PB-05C` | [Block](../contracts/mantra-rebuild-phase-0.md#p0-pb-05g) | [Loader](../../../viper/src/viper/stages.py) · [Worker](../../../viper/src/viper/_workers/stages.py) · [Tests](../../../viper/tests/test_stage_invocation.py) · [Test map](../../../viper/tests/declaration_observers.toml) |
| `P0-PB-05H` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-05h/20260913T001014.084630Z-register.json)) | Complete | `P0-PB-05C` | [Block](../contracts/mantra-rebuild-phase-0.md#p0-pb-05h) | [Observer](../../../viper/src/viper/_workers/file_access.py) · [Worker](../../../viper/src/viper/_workers/stages.py) · [Tests](../../../viper/tests/test_stage_file_access.py) · [Test map](../../../viper/tests/declaration_observers.toml) |
| `P0-PB-05I` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-05i/20260913T005528.163327Z-register.json)) | Complete | None | [Block](../contracts/mantra-rebuild-phase-0.md#p0-pb-05i) | [Attempt](../../../viper/src/viper/execution/_attempt.py) · [Publication](../../../viper/src/viper/execution/_publication.py) · [Tests](../../../viper/tests/test_run_execution.py) |
| `P0-PB-05J` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-05j/20260913T023139.443978Z-register.json)) | Complete | None | [Block](../contracts/mantra-rebuild-phase-0.md#p0-pb-05j) | [Public execution](../../../viper/src/viper/execution/__init__.py) · [Attempt](../../../viper/src/viper/execution/_attempt.py) · [Run dispatch](../../../viper/src/viper/execution/_run.py) · [Tests](../../../viper/tests/test_run_execution.py) |
| `P0-PB-05K` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-05k/20260913T022908.195769Z-register.json)) | Complete | None | [Block](../contracts/mantra-rebuild-phase-0.md#p0-pb-05k) | [Fetcher](../../../viper/src/viper/execution/_source.py) · [Storage](../../../viper/src/viper/_verification/storage.py) · [Tests](../../../viper/tests/test_storage.py) |
| `P0-PB-05L` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-05l/20260913T022908.498098Z-register.json)) | Complete | None | [Block](../contracts/mantra-rebuild-phase-0.md#p0-pb-05l) | [Input model](../../../viper/src/viper/inputs.py) · [Draft model](../../../viper/src/viper/benchmark.py) · [Tests](../../../viper/tests/test_prior_run_inputs.py) |
| `P0-PB-05M` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-05m/20260913T022908.801225Z-register.json)) | Complete | None | [Block](../contracts/mantra-rebuild-phase-0.md#p0-pb-05m) | [Verifier](../../../viper/src/viper/verification.py) · [Tests](../../../viper/tests/test_verification_acceptance.py) |
| `P0-PB-05N` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-05n/20260913T022909.106493Z-register.json)) | Complete | None | [Block](../contracts/mantra-rebuild-phase-0.md#p0-pb-05n) | [Selector](../../../viper/tools/select_impacted_tests.py) · [Tests](../../../viper/tests/test_impacted_test_selection.py) |
| `P0-PB-05O` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-05o/20260913T022909.413777Z-register.json)) | Complete | None | [Block](../contracts/mantra-rebuild-phase-0.md#p0-pb-05o) | [Worker](../../../viper/src/viper/_workers/stages.py) · [Policy test](../../../viper/tests/test_process_startup.py) · [File-access tests](../../../viper/tests/test_stage_file_access.py) |
| `P0-PB-06` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-06/20260913T023139.758509Z-register.json)) | Complete | `P0-PB-04A`, `P0-PB-04B`, `P0-PB-05A`, `P0-PB-05B`, `P0-PB-05C`, `P0-PB-05D`, `P0-PB-05K`, `P0-PB-05L`, `P0-PB-05M` | [Block](../contracts/mantra-rebuild-phase-0.md#p0-pb-06) | [Bindings](../../../mantra/src/mantra/rebuild/restoration.py) · [VIPER](../../../mantra/src/mantra/rebuild/viper_restore.py) · [Tests](../../../mantra/src/mantra/rebuild/tests/test_viper_restore.py) |
| `P0-PB-07` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-07/20260913T023140.070651Z-register.json)) | Complete | `P0-PB-06` | [Block](../contracts/mantra-rebuild-phase-0.md#p0-pb-07) | [Source](../../../mantra/src/mantra/rebuild/hopfield_replay.py) · [Tests](../../../mantra/src/mantra/rebuild/tests/test_hopfield_replay.py) |
| `P0-PB-08` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-08/20260913T023140.383343Z-register.json)) | Complete | `P0-PB-06` | [Block](../contracts/mantra-rebuild-phase-0.md#p0-pb-08) | [Source](../../../mantra/src/mantra/rebuild/mil_replay.py) · [Tests](../../../mantra/src/mantra/rebuild/tests/test_mil_replay.py) |
| `P0-PB-09` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-09/20260913T023141.025582Z-register.json)) | Complete | `P0-PB-07`, `P0-PB-08`, `P0-PB-10` | [Block](../contracts/mantra-rebuild-phase-0.md#p0-pb-09) | [Source](../../tools/freeze_phase0.py) · [Tests](../../tests/test_freeze_phase0.py) |
| `P0-PB-09A` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-09a/20260913T023141.344319Z-register.json)) | Complete | `P0-PB-07`, `P0-PB-08`, `P0-PB-09` | [Block](../contracts/mantra-rebuild-phase-0.md#p0-pb-09a) | [Source](../../tools/register_phase0.py) · [Loader](../../tools/artifact_loaders.py) · [Tests](../../tests/test_register_phase0.py) · [Terminal receipt](../../evidence/phase0/rico/phase0_registration_receipt.json) |
| `P0-PB-10` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-10/20260913T023140.710312Z-register.json)) | Complete | None | [Block](../contracts/mantra-rebuild-phase-0.md#p0-pb-10) | [Controller](../../tools/pairblock_status/pairblock_controller.py) · [Tests](../../tests/pairblock_status/test_pairblock_controller.py) |
| `P0-PB-10A` | Lifecycle ([receipt](../../evidence/pairblock-lifecycle/p0-pb-10a/20260913T024518.399844Z-register.json)) | Complete | `P0-PB-10` | [Block](../contracts/mantra-rebuild-phase-0.md#p0-pb-10a) | [Profile](../../tools/pairblock_status/profile.py) · [Controller](../../tools/pairblock_status/pairblock_controller.py) · [Validator](../../tools/pairblock_status/checklist_profile.py) · [Fixtures](../../tests/pairblock_status/conftest.py) · [Tests](../../tests/pairblock_status/test_pairblock_controller.py) |
| `P0-PB-10B` | Passed: `90` tests ([receipt](../../evidence/pairblock-gates/p0-pb-10b/20260913T051841.974521Z.json)) | Review | `P0-PB-10A` | [Block](../contracts/mantra-rebuild-phase-0.md#p0-pb-10b) | [Source and tests](../contracts/mantra-rebuild-phase-0.md#p0-pb-10b-proposed-code) · [Dependencies](../../requirements.txt) · [Declarations](../contracts/mantra-rebuild.declarations.toml) · [Loader](../../tools/pairblock_status/declaration_manifest.py) · [Renderer](../../tools/pairblock_status/markdown_renderer.py) · [Controller](../../tools/pairblock_status/pairblock_controller.py) · [Declaration tests](../../tests/pairblock_status/test_declaration_manifest.py) · [Renderer tests](../../tests/pairblock_status/test_markdown_renderer.py) · [Controller tests](../../tests/pairblock_status/test_pairblock_controller.py) |

<!-- generated:manifest-native-checklist:start -->
| PairBlock | Status | Depends on | Contract | Source | Tests | Receipt |
|---|---|---|---|---|---|---|
| `P0-PB-10D` | Applied | `P0-PB-10A` | [P0-PB-10D](../contracts/mantra-rebuild-phase-0.md#manifest-native-block-p0-pb-10d) | [profile.py](../../tools/pairblock_status/profile.py) · [pairblock_controller.py](../../tools/pairblock_status/pairblock_controller.py) | [test_lifecycle_evidence.py](../../tests/pairblock_status/test_lifecycle_evidence.py) | [receipt](../../evidence/pairblock-lifecycle/p0-pb-10d/20260913T061220.270166Z-accept.json) |
| `P0-PB-10E` | Applied | `P0-PB-10D` | [P0-PB-10E](../contracts/mantra-rebuild-phase-0.md#manifest-native-block-p0-pb-10e) | [execution_identity.py](../../tools/pairblock_status/execution_identity.py) · [receipt_validation.py](../../tools/pairblock_status/receipt_validation.py) · [pairblock_controller.py](../../tools/pairblock_status/pairblock_controller.py) | [test_receipt_integrity.py](../../tests/pairblock_status/test_receipt_integrity.py) | [receipt](../../evidence/pairblock-lifecycle/p0-pb-10e/20260913T061316.251288Z-accept.json) |
| `P0-PB-10F` | Applied | `P0-PB-10A` | [P0-PB-10F](../contracts/mantra-rebuild-phase-0.md#manifest-native-block-p0-pb-10f) | [declaration_manifest.py](../../tools/pairblock_status/declaration_manifest.py) · [pairblock_controller.py](../../tools/pairblock_status/pairblock_controller.py) | [test_declaration_revision_integrity.py](../../tests/pairblock_status/test_declaration_revision_integrity.py) | [receipt](../../evidence/pairblock-lifecycle/p0-pb-10f/20260913T061221.508549Z-accept.json) |
| `P0-PB-10G` | Applied | `P0-PB-10E`, `P0-PB-10F` | [P0-PB-10G](../contracts/mantra-rebuild-phase-0.md#manifest-native-block-p0-pb-10g) | [projection_transaction.py](../../tools/pairblock_status/projection_transaction.py) · [pairblock_controller.py](../../tools/pairblock_status/pairblock_controller.py) | [test_projection_recovery.py](../../tests/pairblock_status/test_projection_recovery.py) | [receipt](../../evidence/pairblock-lifecycle/p0-pb-10g/20260913T061351.350332Z-accept.json) |
| `P0-PB-10H` | Applied | `P0-PB-10A` | [P0-PB-10H](../contracts/mantra-rebuild-phase-0.md#manifest-native-block-p0-pb-10h) | [markdown_renderer.py](../../tools/pairblock_status/markdown_renderer.py) | [test_markdown_renderer.py](../../tests/pairblock_status/test_markdown_renderer.py) | [receipt](../../evidence/pairblock-lifecycle/p0-pb-10h/20260913T061222.687709Z-accept.json) |
| `P0-PB-10I` | Applied | `P0-PB-10H` | [P0-PB-10I](../contracts/mantra-rebuild-phase-0.md#manifest-native-block-p0-pb-10i) | [pairblock_controller.py](../../tools/pairblock_status/pairblock_controller.py) | [test_cross_origin_dependencies.py](../../tests/pairblock_status/test_cross_origin_dependencies.py) | [receipt](../../evidence/pairblock-lifecycle/p0-pb-10i/20260913T061319.163029Z-accept.json) |
| `P0-PB-10J` | Drafting | `P0-PB-10G`, `P0-PB-10I` | [P0-PB-10J](../contracts/mantra-rebuild-phase-0.md#manifest-native-block-p0-pb-10j) | [profile.py](../../tools/pairblock_status/profile.py) · [pairblock_controller.py](../../tools/pairblock_status/pairblock_controller.py) · [checklist_profile.py](../../tools/pairblock_status/checklist_profile.py) | [conftest.py](../../tests/pairblock_status/conftest.py) · [test_pairblock_controller.py](../../tests/pairblock_status/test_pairblock_controller.py) | None |
<!-- generated:manifest-native-checklist:end -->

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
The `accept` transition also replaces the row's staging links with active
source and test links in the same checklist write.
A block without runnable code uses external review evidence: `submit` advances
`Drafting` to `Review`, and `confirm` advances `Review` to `Complete`. A failed
gate or illegal transition preserves the checklist.

The contract is the only authority for required behavior and gates. The
checklist is the only authority for current lifecycle status. Staging files
hold proposals through `Approved`; after acceptance, the active source at the
cited Git commit is authoritative. Review findings may identify contract gaps,
but they do not become blockers until the contract declares them.

For each review cycle, Codex updates this file in the same RICO commit that
records any changed contract status. MANTRA implementation commits remain in
MANTRA. The RICO checklist cites their commit IDs and gate outputs.

Each completed review pass ends in a commit before the next pass or
implementation block begins. Codex freezes the exact working-tree diff, records
the verdict and findings, runs the applicable focused checks, rereads the diff,
and commits only that pass's owned paths. A `Request changes` commit preserves
the rejected checkpoint; its repair receives a later review-cycle commit.
Codex verifies that each commit contains the reviewed diff. Publication follows
the repository's synchronization schedule. The review receipt records the base
and result commits, owned paths, canonical diff digest, checked invariants,
findings, mechanical evidence, exclusions, and verdict.

A task-created branch closes before its PairBlock closes. The owning
repository's default branch must contain the accepted commit, the configured
upstream must identify the same default-branch commit, and no worktree may
retain the task branch. Codex then removes that merged local branch. This gate
applies only to branches and worktrees created for this rebuild.

## Governing sources

| Work unit | Current state | Owning phase | Completion evidence |
|---|---|---|---|
| [Phase 0 contract](../contracts/mantra-rebuild-phase-0.md) | In progress | Phase 0 | The accepted restoration and replay baseline remains closed; `P0-PB-10B` closes the structured-authoring maintenance requirement. |
| Hopfield reconstruction contract | Pending | Phase 1A | User-approved contract with exact intermediate and final parity gates. |
| MIL reconstruction contract | Pending | Phase 2A | User-approved contract with exact intermediate and final parity gates. |
| Graph encoder contract | Design complete; contract pending | Phase 3A | User-approved contract covering identity, topology, features, training, evaluation, and VIPER evidence. |

The checklist uses the Phase 0 contract stored in RICO commit `929a1d2` with
SHA-256
`ca016cf7ba2f5a1c4ee88cc42c1bad3127124a256288c19710ef12fd5c5fc94c`.

<!-- contract-baseline: P0 path=docs/contracts/mantra-rebuild-phase-0.md revision=929a1d2 sha256=ca016cf7ba2f5a1c4ee88cc42c1bad3127124a256288c19710ef12fd5c5fc94c -->

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
| `P0-REQ-01` | Complete | 0B | None | The approved Hopfield and MIL portions of graph $B$ contain every required file, producer, and edge and exclude parity graph $Q$. |
| `P0-REQ-02` | Complete | 0C | `P0-REQ-01` | Every absent file in $B$ resolves through exactly one valid `RestorationBinding`. |
| `P0-REQ-03` | Complete | 0C | `P0-REQ-01` | The capacity receipt records every term in $R_{max}$ and measured free space is at least $R_{max}$. |
| `P0-REQ-04` | Complete | 0D | `P0-REQ-02`, `P0-REQ-03` | Every restored canonical file matches its approved byte count and SHA-256. |
| `P0-REQ-05` | Complete | 0D | `P0-REQ-02`, `P0-REQ-03` | Restoration runs from the MANTRA root through the verified `mantra` environment, and VIPER retains the environment receipt. |
| `P0-REQ-06` | Complete | 0D | `P0-REQ-04`, `P0-REQ-05` | VIPER verifies graph $B$; deleting one required node or edge makes verification fail. |
| `P0-REQ-07` | Complete | 0E | `P0-REQ-06` | Hopfield replay reproduces `0.5861640938949398` within the approved tolerance and retains its predictions. |
| `P0-REQ-08` | Complete | 0E | `P0-REQ-06` | Standalone v1952 seed-123460 `without_control` replay reproduces `0.6025499488874759` and the approved prediction hashes. |
| `P0-REQ-09` | Complete | 0F | `P0-REQ-07`, `P0-REQ-08` | Every assessed VIPER check has a usefulness-ledger entry and independently confirmed findings. |
| `P0-REQ-10` | Complete | 0C | None | A declared proposal gate retains its result and applies only its legal checklist transition; traceability validation rejects broken IDs, dependencies, owners, code links, tests, or gates. |
| `P0-REQ-11` | Complete | 0C | None | A governed VIPER stage rejects undeclared CPython-visible file-open attempts and retains each successful Python file open, including one read-open for every declared input. |
| `P0-REQ-12` | Complete | 0C | None | An unbenchmarked VIPER run may select a `model` artifact produced by a non-training stage; a benchmarked run still selects its model from a training stage. |
| `P0-REQ-13` | Complete | 0C | `P0-REQ-02` | An absent runtime destination binds only to its approved digest in its approved signed archive; a present destination also matches its filesystem-manifest row. |
| `P0-REQ-14` | Complete | 0C | `P0-REQ-12` | An unbenchmarked run selects any artifact declared by one of its stages; a benchmarked run still selects `model` from a training stage. |
| `P0-REQ-15` | Complete | 0C | `P0-REQ-11` | A governed stage may use the exact operating-system null device without creating a provenance edge or satisfying a declared-input read. |
| `P0-REQ-16` | Complete | 0C | `P0-REQ-11` | Runtime module lookup uses the workspace module objects loaded with the frozen stage callable and restores the prior module registry afterward. |
| `P0-REQ-17` | Complete | 0C | `P0-REQ-11` | A governed stage may read exact Python sources in its frozen Git commit without opening the declared data boundary to untracked or non-Python files. |
| `P0-REQ-18` | Complete | 0C | None | A result-verification failure finalizes one failed attempt without masking the verification error. |
| `P0-REQ-19` | Complete | 0C | None | An execution caller may explicitly trust additional source repositories whose artifact loaders must run while verifying prior-run inputs. |
| `P0-REQ-20` | Complete | 0C | None | A stored-input path outside `inputs/` fails during authoring and publishes no pointer. |
| `P0-REQ-21` | Complete | 0C | None | One execution reuses the authenticated checkout for equal external repository and commit identities. |
| `P0-REQ-22` | Complete | 0C | None | Equal producer-run references share one verified producer result while artifact checks remain per pointer. |
| `P0-REQ-23` | Complete | 0C | None | Import bindings do not cause domain widening when CodeQL already identifies the runtime callers. |
| `P0-REQ-24` | Complete | 0C | None | Repository-owned stage process calls use the spawn-safe subprocess facade. |
| `P0-REQ-25` | Complete | 0C | `P0-REQ-10` | A named pre-protocol PairBlock closes only from a reasoned certification receipt bound to the terminal Phase 0 artifact. |
| `P0-REQ-27` | In progress | 0G | `P0-REQ-25` | Typed declarations and lifecycle receipts generate every machine and human surface for a newly authored PairBlock. |

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

- [x] Approve the complete Hopfield path from its eleven data inputs and saved
      encoder to the selected raw-gene prediction.
      <!-- pair-block: P0-PB-02 -->
      <!-- pair-block-contract: P0-PB-02 contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [x] Approve the complete MIL path for v1952 seed 123460
      `without_control`, excluding every Hopfield output from its inputs.
      <!-- pair-block: P0-PB-03 -->
      <!-- pair-block-contract: P0-PB-03 contract=docs/contracts/mantra-rebuild-phase-0.md -->

**Gate:** Review the graph tables and source traces in the Phase 0 contract;
then confirm that each required file and producer reaches its selected output.
The Hopfield and MIL artifact tables are approved.

**Commit boundary:** Commit the approved MIL artifact table and both graph
definitions in RICO.

## Phase 0C. Implement restoration bindings and capacity planning

**Depends on:** Phase 0B

- [x] Implement and test the strict `RestorationBinding` value type proposed in
      `P0-PB-04A`.
      <!-- pair-block: P0-PB-04A -->
      <!-- pair-block-contract: P0-PB-04A contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [x] Implement and test the control-record resolver proposed in `P0-PB-04B` so
      one approved MANTRA path resolves to one archive member.
      <!-- pair-block: P0-PB-04B -->
      <!-- pair-block-contract: P0-PB-04B contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [x] Validate one binding record for every absent file in graph $B$.
      <!-- pair-block: P0-PB-04 -->
      <!-- pair-block-contract: P0-PB-04 contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [x] Implement and test the `CapacityPlan` and `CapacityReceipt` proposed in
      `P0-PB-05A`.
      <!-- pair-block: P0-PB-05A -->
      <!-- pair-block-contract: P0-PB-05A contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [x] Produce the ordered archive-chunk plan in `P0-PB-05B` and obtain the
      user's approval for cache retention and deletion timing.
      <!-- pair-block: P0-PB-05B -->
      <!-- pair-block-contract: P0-PB-05B contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [x] Add and verify the governed VIPER file-access mode in `P0-PB-05C`.
      <!-- pair-block: P0-PB-05C -->
      <!-- pair-block-contract: P0-PB-05C contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [x] Permit an unbenchmarked VIPER restoration run to select its restored
      `model` output in `P0-PB-05D`.
      <!-- pair-block: P0-PB-05D -->
      <!-- pair-block-contract: P0-PB-05D contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [x] Permit an unbenchmarked VIPER replay to select its declared terminal
      receipt in `P0-PB-05E`.
      <!-- pair-block: P0-PB-05E -->
      <!-- pair-block-contract: P0-PB-05E contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [x] Exclude the operating system's null device from governed data-access
      evidence in `P0-PB-05F`.
      <!-- pair-block: P0-PB-05F -->
      <!-- pair-block-contract: P0-PB-05F contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [x] Preserve the frozen stage callable's workspace modules during invocation
      in `P0-PB-05G`.
      <!-- pair-block: P0-PB-05G -->
      <!-- pair-block-contract: P0-PB-05G contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [x] Permit governed reads of exact Python files captured by the frozen source
      commit in `P0-PB-05H`.
      <!-- pair-block: P0-PB-05H -->
      <!-- pair-block-contract: P0-PB-05H contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [x] Finalize a failed attempt after result verification rejects it in
      `P0-PB-05I`.
      <!-- pair-block: P0-PB-05I -->
      <!-- pair-block-contract: P0-PB-05I contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [x] Permit a caller to approve prior-run source repositories for loader
      execution in `P0-PB-05J`.
      <!-- pair-block: P0-PB-05J -->
      <!-- pair-block-contract: P0-PB-05J contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [x] Reuse one authenticated checkout for files from the same external Git
      revision in `P0-PB-05K`.
      <!-- pair-block: P0-PB-05K -->
      <!-- pair-block-contract: P0-PB-05K contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [x] Reject stored-input destinations outside `inputs/` during authoring in
      `P0-PB-05L`.
      <!-- pair-block: P0-PB-05L -->
      <!-- pair-block-contract: P0-PB-05L contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [x] Verify each exact producer run once per verification pass in
      `P0-PB-05M`.
      <!-- pair-block: P0-PB-05M -->
      <!-- pair-block-contract: P0-PB-05M contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [x] Exclude imported local names from runtime one-hop callers in
      `P0-PB-05N`.
      <!-- pair-block: P0-PB-05N -->
      <!-- pair-block-contract: P0-PB-05N contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [x] Route stage-worker process launches through the spawn-safe facade in
      `P0-PB-05O`.
      <!-- pair-block: P0-PB-05O -->
      <!-- pair-block-contract: P0-PB-05O contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [x] Measure free space and save a passing capacity receipt before download.
      <!-- pair-block: P0-PB-05 -->
      <!-- pair-block-contract: P0-PB-05 contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [x] Register the active `P0-PB-10` controller and its acceptance evidence in
      VIPER.
      <!-- pair-block: P0-PB-10 -->
      <!-- pair-block-contract: P0-PB-10 contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [x] Certify the four named pre-protocol PairBlocks from the terminal Phase 0
      artifact in `P0-PB-10A`.
      <!-- pair-block: P0-PB-10A -->
      <!-- pair-block-contract: P0-PB-10A contract=docs/contracts/mantra-rebuild-phase-0.md -->

**Gate:** Run the MANTRA restoration and capacity tests and the separate
`P0-PB-05C` VIPER focused check. The tests must reject malformed paths,
identities, duplicate or absent control mappings, insufficient free space, and
undeclared governed file-open access.

```bash
PYTHONPATH="$PWD/src" PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
python -m pytest \
  --rootdir="$PWD/src" \
  --confcutdir="$PWD/src" \
  src/mantra/rebuild/tests/test_restoration.py \
  src/mantra/rebuild/tests/test_control_resolution.py \
  src/mantra/rebuild/tests/test_capacity.py -q
```

**Commit boundaries:** Commit the reviewed binding reader and tests first.
Commit the reviewed capacity calculator, bindings, and approved download plan
after the full Phase 0 artifact set is known.

## Phase 0D. Restore files and verify graph B in VIPER

**Depends on:** Phase 0C

- [x] Verify the 27 approved files on the restored MANTRA disk, publish their
      exact bytes as named VIPER outputs, and persist the disk-import receipt.
- [x] Run restoration from the MANTRA root through the Conda environment named
      `mantra` and register the environment receipt in VIPER.
      <!-- pair-block: P0-PB-01 -->
      <!-- pair-block-contract: P0-PB-01 contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [x] Register graph $B$, the environment receipt, the capacity receipt, and
      every restoration receipt in VIPER.
- [x] Verify the complete graph and demonstrate failure after removing one
      required node or edge.
      <!-- pair-block: P0-PB-06 -->
      <!-- pair-block-contract: P0-PB-06 contract=docs/contracts/mantra-rebuild-phase-0.md -->

**Gate:** `P0-VR-04` and `P0-VR-06` pass against the restored MANTRA checkout.

**Commit boundary:** Commit the MANTRA restoration code and checked-in receipts
after the focused tests and graph rejection test pass.

## Phase 0E. Replay Hopfield and MIL

**Depends on:** Phase 0D

- [x] Replay the selected Hopfield raw-gene readout and compare the generated
      predictions and score with parity graph $Q_H$.
      <!-- pair-block: P0-PB-07 -->
      <!-- pair-block-contract: P0-PB-07 contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [x] Replay v1952 seed 123460 `without_control` on the historical
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

- [x] Complete the VIPER usefulness ledger, register every Phase 0 evidence
      artifact, and obtain the user's approval to begin reconstruction.
      <!-- pair-block: P0-PB-09 -->
      <!-- pair-block-contract: P0-PB-09 contract=docs/contracts/mantra-rebuild-phase-0.md -->
- [x] Verify the frozen evidence index in one RICO-rooted VIPER run.
      <!-- pair-block: P0-PB-09A -->
      <!-- pair-block-contract: P0-PB-09A contract=docs/contracts/mantra-rebuild-phase-0.md -->

**Gate:** `P0-VR-09` passes, the user approves the evidence set, and all 25
Phase 0 requirements are complete.

**Commit boundary:** Update the Phase 0 contract status and this checklist in
RICO; record the closing RICO and MANTRA commit IDs in VIPER.

## Phase 0G. Introduce structured PairBlock declarations

**Depends on:** Phase 0F

- [ ] Implement and review the typed declaration loader, deterministic Markdown
      renderer, and controller ownership router in `P0-PB-10B`.
      <!-- pair-block: P0-PB-10B -->
      <!-- pair-block-contract: P0-PB-10B contract=docs/contracts/mantra-rebuild-phase-0.md -->

**Gate:** `P0-VR-26` passes. The implementation accepts one manifest-native
fixture through its full lifecycle, rejects every severed or duplicate
connector before execution, reopens the exact affected closure after an
approved declaration revision, recomputes the revision receipt's derived
evidence, preserves unaffected receipts, discovers every active Python module
for semantic documentation coverage, and leaves the completed legacy inventory
on its current authority path.

**Commit boundary:** Commit the reviewed declaration protocol, renderer,
controller routing, tests, contract, and checklist as one RICO increment. Record
its VIPER result before authoring `P0-PB-07A`.

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

**Execution order:** Begin after Phase 1C so each reconstruction receives a
separate review cycle. The standalone MIL input graph ends at its own
artifacts.

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
| Provide or authorize L4-class compute when an approved reconstruction block requires training or exceeds the local execution threshold. | Phase 1C onward | Training, embeddings, large matrix operations, and repeated sweeps. |
| Approve each reconstruction contract and its PairBlocks. | Phases 1A, 2A, and 3 | Implementation of each model generation. |

## Deferred scope

| Item | Scope basis |
|---|---|
| CPU-only MIL acceptance | The historical acceptance run used an L4-class CUDA environment. A CPU portability probe measures feasibility only. |
| [Shared file identity](../contracts/mantra-rebuild-phase-0.md#future-work-shared-file-identity) | After `P0-PB-07A`, promote proposed `P0-PB-07B` to add `viper.references.FileIdentity`, derive VIPER's file-reference types from it, and remove MANTRA's duplicate byte-identity classes. |
| [Discriminated lifecycle-evidence union](../contracts/mantra-rebuild-phase-0.md#future-work-discriminated-lifecycle-evidence-union) | Retain the shared `EvidenceKind` literal until a real caller needs kind-specific parsing; then charter a separate PairBlock for the discriminated union, schema revision, and historical-receipt reader. |
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
