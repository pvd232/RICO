# Workday 09-13

## Day charter

Close Phase 0 with verified historical baselines, exact Hopfield output parity,
connected MANTRA-to-RICO provenance, and a checklist whose status follows retained
lifecycle evidence.

## Outcome

Phase 0 is complete. It restored the historical inputs, replayed the independent
Hopfield and MIL systems, verified their selected results, and registered the
frozen evidence set through VIPER. Model parameters remained frozen throughout
replay and evaluation.

The Hopfield replay loaded the historical encoder and its eleven declared data
inputs, produced a new raw-gene prediction archive on the L4, and compared that
archive with the historical prediction archive. Both files contain 38,397,104
bytes and have SHA-256
`d7180c4669a11b0b2fb184814aafb48ebafe75b02e4bd07998c337aa64dc59b7`.
The replay also reproduced the selected hold-set PearsonDelta exactly:
`0.5861640938949398`.

The standalone MIL replay remained independent of Hopfield. Its retained parity
receipt records the selected MIL result and its own provenance chain.

## What changed

### Phase 0 evidence and replay

- Restored historical MANTRA artifacts were bound to authenticated archive
  members and verified byte identities.
- The Hopfield and MIL replay stages consumed prior-run artifacts through VIPER,
  which connected each copied file to its producing run.
- Hopfield acceptance was strengthened from score equality alone to exact NPZ
  byte equality, array equality, and score equality.
- The Phase 0 evidence index now names the exact Hopfield parity receipt, MIL
  receipt, restoration evidence, graph report, environment receipt, dependency
  graph, and VIPER usefulness ledger.
- The terminal RICO registration run
  `01M2CZF2JEWDPMSDE9083MWR5E` verified the current evidence set and completed at
  `2026-09-13T08:57:35.655652Z`.

### MANTRA implementation

MANTRA gained a typed replay surface for the selected Hopfield result:

- role-specific prediction and evaluation outputs;
- one declaration for every replay input and its provenance source;
- one readable input-assembly path;
- exact file-identity and array-parity checks;
- public VIPER run-reference resolution; and
- focused replay tests and review evidence.

The final MANTRA implementation commit for this replay tranche is
`8f0d705ac8622b8247e02143bbf7023c6b694e72`.

### VIPER implementation

The live replay exposed API and schema gaps that were repaired in VIPER:

- one restore call can restore several selected artifacts under their declared
  filenames;
- terminal local runs have a public reference-resolution API;
- a single-file artifact now retains its author-declared relative path separately
  from its immutable stored file reference;
- reuse, materialization, restoration, and verification preserve that distinction;
  and
- protocol fixtures cover the retained path through serialization.

The current VIPER commits are
`b3c58b501198f8b0516e4a41d63f29ee8e94cf5a` and
`f47bea79f060aa66f76f220c80a3a28d1e969eab`. The retained-path boundary passed
Pyright, Ruff, and 209 tests plus 9 subtests.

### Contract and checklist protocol

The RICO controller now uses structured declarations for new requirements and
PairBlocks. Lifecycle receipts supply observed state; generated Markdown supplies
the human review surface. Today’s work also added or repaired:

- event-specific lifecycle evidence;
- receipt schema and digest validation;
- declaration-revision plans bound to the candidate reviewed by the user;
- separate declaration-repository and implementation-repository identities;
- recoverable projection transactions;
- deterministic Markdown rendering and link validation;
- cross-origin dependency checks;
- explicit certification for the four early Phase 0 blocks whose records predate
  the current receipt vocabulary; and
- commit checkpoints after each completed review cycle.

Every Phase 0 PairBlock and requirement now renders `Complete`. The Phase 0
contract and its checklist summary also render `Complete`.

## Validation evidence

| Boundary | Result |
|---|---|
| Hopfield output file | Exact SHA-256 and byte-count parity |
| Hopfield arrays | Exact key, shape, dtype, and value parity |
| Hopfield score | Exact `0.5861640938949398` parity |
| VIPER retained-path repair | Pyright passed; 209 tests and 9 subtests passed; Ruff passed |
| RICO Phase 0 index | 42 focused tests passed; Pyright passed; Ruff passed |
| Terminal provenance run | VIPER run `01M2CZF2JEWDPMSDE9083MWR5E` succeeded |
| Contract traceability | All Phase 0 requirements and PairBlocks render `Complete` |

The immutable earlier Phase 0 registration receipt remains at its original path
because legacy completion records cite its digest. Today’s registration has new
terminal receipt and run-record paths. This preserves both evidence chains.

## Framework findings

VIPER prevented several real errors: a result selected under the wrong semantic
role, a stale staging link, a cross-workspace provenance break, and an artifact
whose stored path had been mistaken for its declared restoration path.

The same work exposed costs that need follow-up:

- invalid result selection currently reaches execution; plan validation should
  reject it before compute begins;
- repeated producer verification and Git checkout work can dominate a small
  registration stage;
- a fixed materialization path can collide with bytes from an earlier run;
- old run schemas require an explicit compatibility reader after the frozen
  artifact schema changes; and
- review evidence still requires manual assembly; one typed schema and generator
  should emit it.

The terminal registration used a digest-derived input namespace after the first
attempt exposed the fixed-path collision. Hopfield inference ran once.

## Git record

RICO review and acceptance were preserved as separate commits throughout the
day. The principal closing commits before final Phase 0 registration are:

- `1ea7403` through `368d885`: structured lifecycle repair and review records;
- `1a1f1dd` through `f8da25c`: legacy certification boundary;
- `4ab77c0` through `8b209a7`: Hopfield parity declaration and review;
- `7a36796` through `bbc655b`: typed restoration and controller-test organization;
- `8f7e70d` through `7eb605b`: exact byte-parity acceptance;
- `a55b2cb` and `95d65e6`: retained-path declaration and gate alignment; and
- `0ae454d` and `cd0eb5b`: closed retained paths, Hopfield parity, and refreshed
  Phase 0 evidence.

## Shutdown state

Phase 0 is closed. Phase 1 begins from two trusted historical baselines and a
connected provenance graph. The first Phase 1 result should be an exact,
identity-bearing reconstruction of Hopfield preprocessing intermediates. Encoder
training follows that reconstruction.

## Post-closure VIPER hardening and release

Phase 0 exposed two costs that would recur throughout reconstruction: prior-run
inputs could collide at one shared materialization path, and separate runs
repeated the same remote retrieval and external Git checkout work. VIPER
`0.1.0a4` now owns both lifecycles.

For prior-run inputs, a new plan records `materialization: attempt_workspace`.
Execution places each verified input beneath the consuming run attempt and gives
that path to the stage. Saved records created before this change continue to use
their recorded declared path. Tests cover distinct retry paths, same-path reuse,
serialization, and verification.

For remote evidence, VIPER now stores verified bytes by SHA-256 beneath
`.viper/cache/verified-objects/`. Each cache hit rechecks byte count and SHA-256;
a corrupt entry is fetched again and replaced atomically. External Git evidence
uses locked persistent checkouts beneath `.viper/cache/git-checkouts/`, with the
remote URL and exact commit checked before every read. Both caches are disposable
performance state and do not replace run evidence.

The implementation was preserved in separate review commits:

- `8a89adc`: isolate stored inputs by run attempt;
- `9d891d3`: cache verified remote evidence across runs;
- `dab5b92`: document the new behavior;
- `48a552a`, `6b69219`, and `eb0f4c3`: align local and CI validation, preserve
  static test inspection, and make the file-access gate portable across Python
  runtimes; and
- `513ba84`: repair executable documentation examples found by the final CI run.

The signed tag `v0.1.0a4` identifies source commit
`513ba8437c47e22fc31847de7cb69cf405dd79a2`. CI run `34751040123` passed on
Python 3.11 through 3.14. Its Python 3.14 boundaries included 455 unit and
contract tests with nine subtests and 132 integration tests with 22 subtests.
Publication run `34751893813` verified the candidate from TestPyPI before
publishing the same wheel and source distribution to PyPI.

The published files are:

| Distribution | Bytes | SHA-256 |
|---|---:|---|
| `viper_provenance-0.1.0a4-py3-none-any.whl` | 245,134 | `a1af45a46e842762a170120e3302cb69e0e0b1c4ba8c68936e6ab0a73ff82612` |
| `viper_provenance-0.1.0a4.tar.gz` | 445,356 | `4ac12023ff7b0ef89ba4829fe48e9ea5a1947ef6abad62990e790770a66b12a5` |

PyPI and TestPyPI serve those exact hashes. The local MANTRA Python 3.13
environment now imports `0.1.0a4` from `site-packages`, rather than from the
editable VIPER checkout.

The L4 base runtime also imports the published `0.1.0a4` wheel from
`site-packages`. Its historical scientific dependencies remain at NumPy 1.26.4,
Click 8.1.8, PyTorch 2.10.0+cu129, and the pre-existing Hugging Face stack. VIPER
was installed there without dependency replacement because the current package
metadata requires NumPy 2 while the preserved MANTRA stack requires NumPy 1.26.
CUDA remained available after installation. Phase 1 should either keep that
explicit compatibility boundary or create a dedicated GPU runtime before adding
new dependencies.

The final CI cycle found three portability defects before release: repository
history was too shallow for Git-backed provenance tests, Python 3.14 did not emit
the thread audit event relied upon by declared file access, and five executable
documentation snippets had drifted from the public API. The fixes request full
history in provenance jobs, wrap `threading.Thread.start` only while the observer
is active, and keep the affected API names inside complete executable examples.
The published documentation retains the existing task-oriented structure and
adds only the new cache, materialization, restoration, and release facts.

VIPER commit `d3b95a6` adds the final release receipt and publication links. The
receipt records the signed tag, CI and publication runs, distribution identities,
registry checks, and installed-package acceptance.

## Local 0.1.0a5 identity cleanup

VIPER commit `44c9fd2` defines `viper.references.FileIdentity` as the shared
SHA-256 and byte-count base for resolved, snapshot, and reuse file references.
MANTRA commit `181e29768` removes its two duplicate identity classes and uses
the VIPER type in restoration and Hopfield replay code. The historical
restoration JSON schema still writes `byte_count`; `RestorationBinding` owns the
translation to and from `FileIdentity.bytes`.

`P0-REQ-37` traces the change through `P0-PB-05R` and `P0-PB-07B`. Their
focused gates passed 60 tests plus five subtests in VIPER and 84 tests in
MANTRA, with clean Pyright and Ruff results. Both blocks are Applied. Their
remaining `register` transition requires new VIPER provenance for these commits;
the earlier Phase 0 terminal registration cannot support that claim.

The discriminated lifecycle-evidence union remains deferred. Current lifecycle
events consume approval and artifact evidence, while test and command execution
has a separate gate-receipt schema. Combining them now would require new receipt
semantics, schema migration, CLI adaptation, and global-manifest mapping without
an active caller that benefits from typed dispatch.
