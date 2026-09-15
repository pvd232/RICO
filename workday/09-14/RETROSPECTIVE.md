# Workday 09-14 retrospective

## Outcome

The contract-package protocol moved from a reviewed architecture into a usable
global implementation, and MANTRA Phase 1 became its first repository-owned
workstream. The protocol now separates four facts that the earlier RICO
controller mixed together:

- a contract package declares what must be true;
- a PairBlock plan declares how one current candidate will be built and tested;
- receipts record what was observed; and
- a compiled execution state joins declarations, plans, and verified receipt
  heads into the status rendered for people.

The day ended with one real Phase 1 plan executed in a reconstructed RICO
checkout. Its gate passed Pyright, two focused tests, the source-documentation
check, and both final Ruff checks. Receipt-last publication wrote the gate
receipt, compiled state, generated contract region, and generated checklist
region. `H1-PB-01` is now in `review`; the later reconstruction blocks remain
`waiting` on declared dependencies.

## Contract protocol delivered

The global implementation in `/Users/machina/.agents/contract_protocol`
contains the complete version-1 execution path:

1. `ContractPackage` loads stable requirements, verifiers, PairBlocks, and
   repository ownership from `<contract_id>.toml`.
2. `PairBlockPlan` binds one current candidate to the package digest, exact Git
   baseline, file actions, and ordered gate.
3. `ChecklistWorkspaceSpec` binds contract packages to their coordination and
   implementation repositories and supplies human presentation order.
4. The shared runner reconstructs the implementation baseline in a temporary
   checkout, applies only declared actions, runs commands through registered
   executables, and records the candidate manifests and results.
5. Typed approval, implementation-review, VIPER-registration, lifecycle, gate,
   revision, and bootstrap records prevent one event from supplying another
   event's evidence.
6. `compile_execution_state()` validates identities and receipt chains, resolves
   dependencies, and derives contract, requirement, and PairBlock progress.
7. The renderer changes only the protected regions of contract and checklist
   Markdown. The surrounding explanation remains authored by a person or LLM.
8. The projection publisher stores every final byte in a recovery journal,
   writes the compiled state and views, validates them, and publishes the
   authoritative receipt last.

The protocol also gained the production operations that its first draft had
omitted. Named functions now create implementation-review evidence,
VIPER-registration evidence, and reviewed declaration-revision plans from
verified inputs. Tests no longer stand in for those operator paths by writing
arbitrary Pydantic objects directly.

## Defects found and repaired

Human review caught several failures that passing construction-oriented tests
had missed. Those findings changed both the implementation and the review
method.

- The first evidence design had readers and validators but no production
  writers for implementation review or VIPER registration. The repair added
  named record operations that derive machine-known fields, accept only the
  human assertion they cannot derive, and persist canonical immutable bytes.
- The initial compiler mixed graph validation, receipt loading, dependency
  admission, aggregation, and serialization in one function. It was split into
  stateless operations with explicit inputs and return values. Shared receipt
  reading replaced duplicated controller/compiler logic.
- Transition code used parallel string dictionaries for current state, event,
  and next state. The lifecycle policy now owns those relationships so typed
  event requests and state transitions cannot drift independently.
- Gate and lifecycle records initially trusted caller-supplied identities too
  broadly. Production operations now derive repository commits, package and
  plan digests, candidate manifests, and evidence references from their owning
  files.
- The initial projection prose implied multi-file filesystem atomicity. The
  implementation and contract now state the real guarantee: each file is
  atomically replaced, the complete projection is validated, and the receipt
  is published last; the durable journal makes interrupted publication
  recoverable.
- Direct preflight commands created Python and Ruff caches beside plan-owned
  files and sometimes ran Pyright from the wrong configuration root. The runner
  now supplies isolated `HOME`, `TMPDIR`, `PYTHONDONTWRITEBYTECODE`, and
  `RUFF_CACHE_DIR` values and executes every step inside the reconstructed
  candidate.
- A late top-down review found that declaration revisions followed reverse
  dependencies only inside the revised contract. `CP-PB-07` now snapshots the
  other registered packages and computes the affected closure across contract
  boundaries. Its final isolated gate passed.
- The same review removed `coordination_repository_commit` from lifecycle
  receipts. That commit predated the receipt and no verifier used it, so the
  field asserted ownership it could not establish.
- Gate documentation previously said verification recomputed command results.
  The verifier validates the retained declared commands and zero exit codes;
  it recomputes candidate manifests and the diff. The contract now makes that
  narrower claim.

## Minimal-design rule

The repeated design lesson became the global `minimal-sufficient-design`
skill. At an architecture fork it requires this order:

1. reuse an existing primitive whose invariant already matches;
2. extend that primitive when one contained change closes the gap;
3. add a new abstraction only when it owns a distinct invariant or removes
   more machinery than it introduces; and
4. stop when the named proof obligations pass.

The rule counts public models, persisted fields, states, paths, validators,
migrations, and cleanup obligations. It therefore turns simplicity into a
reviewable decision rather than a stylistic preference. Its rationale is
grounded in economy of mechanism, information hiding, explicit security
requirements, and digest-bound attestations.

## Git and evidence record

The global protocol work was divided into review-cycle commits rather than one
opaque final rewrite. The major boundaries are:

- `7bfea55`: typed lifecycle evidence;
- `48a2196`: compiled execution state;
- `d9ea132`: deterministic generated views;
- `90bd030`: recoverable receipt-last publication;
- `69f4c85`: completed CP-PB-04 self-review;
- `6a28eb1`: protocol migration;
- `9a1dfc3`: production evidence creation and verification boundary;
- `f3bf902`: minimal-sufficient-design skill;
- `57e5e54`: cross-contract revision closure; and
- `c2d1a15`: skill evaluation index alignment;
- `579221c`: bootstrap declaration-binding repair; and
- `8860737`: formal bootstrap history and current generated state.

Each listed global review cycle was pushed, followed by an upstream equality
check. Superseded uncommitted CP-PB-07 gate attempts were removed; the retained
directory contains the final passing receipt. The bootstrap receipt now marks
CP-PB-01 through CP-PB-06 complete against their retained historical plans and
implementation commits. CP-PB-07 remains in Review pending user approval.

## Phase 1 handoff

RICO now owns:

- `contracts/mantra-hopfield-reconstruction.toml`, the typed declaration;
- `contracts/mantra-hopfield-reconstruction.md`, the human contract;
- `checklists/mantra-rebuild-phase-1.toml`, repository bindings and roadmap
  placement;
- `checklists/mantra-rebuild-phase-1.md`, the generated progress view; and
- `plans/mantra-hopfield-reconstruction/H1-PB-01/plan.toml`, the first executed
  implementation plan.

The package declares six blocks. `H1-PB-01` establishes the Phase 0 handoff.
`H1-PB-02` owns ordered array identities. `H1-PB-03` owns preprocessing
reconstruction. `H1-PB-04` owns encoder training. `H1-PB-05` owns retrieval,
reference correction, and exact final parity. `H1-PB-06` owns terminal
provenance registration. Only `H1-PB-01` has a current plan; this avoids
freezing downstream implementation details before their predecessors reveal
the actual boundary.

RICO commit `e5743f4` preserves this review cycle. Its retained
`gate-review-06.json` reports five successful steps, and the repository matched
`origin/main` after the push.

## First missing result

The next missing result is not another framework component. It is the approved
`H1-PB-01` review transition followed by an exact source-and-artifact map for
`H1-PB-02`. That map must identify the selected historical producers, row and
gene axes, fitting populations, shapes, dtypes, and normalization populations
before any preprocessing array is rebuilt.

The main pace lesson is equally concrete: schema work must stop when the live
vertical slice succeeds. Tomorrow's time belongs to Hopfield reconstruction.
