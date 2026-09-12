# Workday 09-11

This journal records the continuous workday that began September 11 and crossed midnight.

## Day charter

Close the Phase 0 implementation tranche, then prepare the archive plan that unlocks restoration and parity replay.

## Capacity

The next focused session budgets three hours of planned work and thirty minutes of slack. Hard stop: unspecified.

## Completed today

- RICO now separates the historical MANTRA oracle from the new implementation: Phase 0 restoration and replay run against MANTRA, while Phase 1 and later model development belong in RICO.
- VIPER 0.1.0a4 carries producer-workspace identity across the MANTRA-to-RICO stored-input boundary, and the local cross-workspace probe passes.
- `P0-PB-10` now drives PairBlock lifecycle transitions and retained receipts through the master checklist.
- MANTRA commit `2304674e1fc9730801d1afe39edc7585c81081f4` applies `P0-PB-04A`, `P0-PB-04B`, and `P0-PB-05A`. The focused boundary passed Ruff, the docstring prose check, and 55 tests.
- RICO commit `f3dddf1` records those three blocks as `Applied` and links each state to its lifecycle receipt.
- The global Python prose check now reads real docstrings through the abstract syntax tree and enforces affirmative source documentation.

## Execution plan

| Budget | Work block | Deliverable | Done condition |
|---:|---|---|---|
| 35 min | `P0-PB-05B` | Ordered archive-part plan and measured capacity receipt | Every required part has an immutable identity, the capacity calculation passes, and the plan identifies the first part to fetch. |
| 90 min | `P0-PB-06` | Eight restored Hopfield artifacts and VIPER graph $B$ | Each restored file matches its approved byte identity; VIPER reaches every binding; the severed-edge test fails as required. |
| 40 min | `P0-PB-07` and `P0-PB-08` probes | Separate Hopfield and MIL replay decisions | Local inference and evaluation either produce retained results or identify the exact CUDA operation and inputs for an L4 run. |
| 15 min | Closure | Updated checklist, receipts, Git evidence, and usefulness ledger | The checklist links every new result and names the next unresolved block. |
| 30 min | Slack | Restoration debugging, download variance, and transition loss | Used only when a planned block overruns. |

## Replan rule

If `P0-PB-06` has restored fewer than eight artifacts after 125 minutes of planned work, finish the immutable archive plan and capacity receipt, record the last verified archive part, and move both replay probes to the next session.

## Not today <!-- direct-prose: allow -->

Phase 1 Hopfield reconstruction, Phase 2 MIL reconstruction, the graph-encoder build, and the public VIPER release remain outside this restoration tranche.

## Shutdown

Record completed PairBlocks, unresolved archive parts, validation results, and commit identities. The next session starts by generating the `P0-PB-05B` archive-part table from the eight approved restoration bindings and the authenticated archive controls.
