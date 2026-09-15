# Workday 09-14

## Twenty-hour charter

Run one sustained Phase 1 reconstruction day from 08:00 to 04:00. The plan
assigns 16 hours and 45 minutes to focused work, 2 hours and 15 minutes to
meals and breaks, and the final hour to integration slack and shutdown. Preserve
the order and durations if the start time moves.

## Primary outcome

By shutdown, the Hopfield reconstruction has an approved identity boundary,
the earliest preprocessing producers have run through VIPER, and the encoder
training block is either executing on the L4 or has a retained blocker that
names the failed input, operation, and evidence.

## Hard stop

Stop at 04:00. Do not spend the final hour opening another implementation
surface. Use it to finish the active gate, retain evidence, synchronize Git, and
write the next command.

## Execution plan

| Time | Budget | Work block | Deliverable | Done condition |
|---|---:|---|---|---|
| 08:00–09:00 | 1 hr | Review and admit `H1-PB-01` | User-reviewed contract, checklist, gate receipt, and lifecycle decision | The reviewed candidate and current Git commit match; any requested repair receives its own validated review-cycle commit. |
| 09:00–12:00 | 3 hr | `H1-PB-02`: historical identity map | Exact historical producers, row and gene axes, fitting populations, shapes, dtypes, and normalization populations | Every identity has one source, consumer, comparison rule, observing test, and retained reference. |
| 12:00–12:45 | 45 min | Lunch | Step away | Return with the identity boundary frozen. |
| 12:45–16:15 | 3 hr 30 min | `H1-PB-03`: first preprocessing producers | Reconstructed matched-control and coefficient-target artifacts | A changed row, gene, fitting population, shape, dtype, or value fails before downstream execution. |
| 16:15–17:00 | 45 min | Break and midpoint replan | Compare actual results with the replan rule | Continue downstream only if `H1-PB-02` is accepted and one preprocessing producer passes. |
| 17:00–20:30 | 3 hr 30 min | `H1-PB-03`: remaining preprocessing chain | Control programs, response representations, biological descriptors, and reference shifts | Each accepted artifact records its producer, ordered inputs, file identity, array comparison, and VIPER run. |
| 20:30–21:15 | 45 min | Dinner | Step away | Return with the preprocessing diff frozen. |
| 21:15–01:15 | 4 hr | `H1-PB-04`: encoder training boundary | Approved training plan and launched L4 run, or completed short run if runtime permits | Architecture, objective, seed, inputs, checkpoint rule, logs, and GPU environment are declared before compute begins. |
| 01:15–03:00 | 1 hr 45 min | Review and integration | Self-review, focused gates, review-cycle commits, pushes, and current generated views | Every changed claim has an observing check; every repository equals its upstream after the cycle. |
| 03:00–04:00 | 1 hr | Slack and shutdown | Resolve the earliest active failure or prepare the exact restart handoff | No unexplained dirty files, idle paid compute, unlinked receipts, or undocumented next step remain. |

## Midpoint replan

At 16:15, continue to downstream preprocessing only if both conditions hold:

1. `H1-PB-02` has an accepted identity boundary; and
2. at least one historical preprocessing artifact has been independently
   rebuilt and compared.

If either condition is missing, stop adding producers. Spend the remaining
preprocessing time on the earliest unresolved identity or source edge. Launch
encoder training only after every input it consumes has an accepted identity
and producer.

## Compute policy

Use the local machine for contract compilation, hashing, focused unit tests,
Pyright, Ruff, and small array checks. Use the L4 for training, embeddings,
large matrix operations, repeated sweeps, or an inference estimate above 10–15
minutes. Validate the plan before starting paid compute. Disposable instances
use `autoDelete=True`; retained evidence belongs in Git or VIPER, not on the
instance disk.

## Review and Git policy

Each coherent implementation cycle ends with:

1. Ruff import and format fixes;
2. Pyright over the changed Python boundary;
3. the smallest tests that observe the changed claims;
4. final non-mutating Ruff format and lint checks;
5. a frozen-diff self-review for correctness, duplication, stateful coupling,
   source documentation, and unsupported guarantees;
6. a task-scoped commit and normal push; and
7. a fetch and equality check between `HEAD` and its upstream.

Candidate files remain duplicated under the active PairBlock plan because that
copy is the reviewed, replayable input. Do not create plans for later blocks
until their dependencies reveal the required implementation.

## Pace rule

At every design fork, reuse an existing proven primitive first, extend it only
to close a named invariant, and add a new abstraction only when it owns a
distinct guarantee or removes more machinery than it adds. Stop protocol work
when the active vertical slice passes. Record non-blocking framework ideas for
later instead of interrupting Hopfield reconstruction.

## Shutdown handoff

Record the current PairBlock, exact next command, gate and lifecycle receipts,
implementation commits, GPU state, observed runtime, and any failed comparison.
The next session must be able to resume without reconstructing intent from chat.
