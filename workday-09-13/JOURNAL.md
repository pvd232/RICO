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
