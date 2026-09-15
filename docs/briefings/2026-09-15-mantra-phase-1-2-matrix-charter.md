# MANTRA Phase 1-2 Matrix Charter

This charter explains how Matrix executes the requirements declared in
[`mantra-hopfield-reconstruction.toml`](../../contracts/mantra-hopfield-reconstruction.toml)
and
[`mantra-mil-reconstruction.toml`](../../contracts/mantra-mil-reconstruction.toml).
Those contract packages remain the authority for requirements, verifiers,
PairBlocks, dependencies, and completion evidence.

## Fixed evidence

Phase 0 is complete and will not run again. Matrix reads its archived files as
immutable comparison inputs. The
[`index.json`](../../archive/mantra-rebuild-phase-0/evidence/phase0/index.json)
resolves the selected Hopfield and MIL receipts, which pin the accepted file
digests, arrays, scores, configurations, and producer history.

## Phase 1: Hopfield reconstruction

| PairBlock | Result required before the next PairBlock starts |
|---|---|
| `H1-PB-01` | The current typed contract and checklist resolve the accepted Phase 0 Hopfield result. |
| `H1-PB-02` | The loader rejects any disagreement among feature, coefficient-target, and truth-row perturbation order. |
| `H1-PB-03` | Rebuilt descriptor-side inputs equal their retained files by keys, labeled axes, shape, dtype, and values. |
| `H1-PB-04` | Rebuilt targets and response transforms equal their retained files by keys, labeled axes, shape, dtype, and values. |
| `H1-PB-05` | The loader assembles the same model input arrays with the same gene order and fit-plus-tune populations. |
| `H1-PB-06` | Training reproduces the selected encoder weights and retains checkpoints, logs, scores, and a VIPER run. |
| `H1-PB-07` | Retrieval and correction reproduce the accepted prediction bytes and hold PearsonDelta exactly. |
| `H1-PB-08` | Contract and VIPER records resolve every accepted Phase 1 producer, input, output, comparison, and commit. |

## Phase 2: MIL reconstruction

| PairBlock | Result required before the next PairBlock starts |
|---|---|
| `M2-PB-01` | The selected standalone configuration resolves its inputs, uses one student query, ignores dormant `proto_count`, and consumes no Hopfield output. |
| `M2-PB-02` | Rebuilt MIL inputs, bags, priors, and conditioning equal their retained counterparts by keys, labeled axes, shape, dtype, and values. |
| `M2-PB-03` | Teacher and student training reproduce the retained identity vectors, checkpoints, and selection records without using hold targets for selection. |
| `M2-PB-04` | Step02 reproduces the accepted predictions, weights, and hold PearsonDelta. |
| `M2-PB-05` | Step03 reproduces the accepted predictions, weights, and final hold PearsonDelta. |
| `M2-PB-06` | Contract and VIPER records resolve every accepted Phase 2 producer, input, output, comparison, checkpoint, and commit. |

## Hopfield input convergence

`H1-PB-09` starts after `H1-PB-08` and `M2-PB-06` close. It runs the unchanged
legacy Hopfield model on the retained MIL descriptor bundle: core83, the
144-value five-source family block, and the matching response40 proxy. The
encoder input changes from 187 to 267 values. The run freezes its checkpoint,
predictions, score, inputs, configuration, runtime, and source commit as a new
bridge baseline. The original 64-value Hopfield result remains the Phase 1
replay baseline.

## Matrix rules

Matrix executes one PairBlock at a time in declared dependency order.

1. Load the current compiled checklist state and select its current PairBlock.
2. Inspect that PairBlock's existing producer, its retained Phase 0 counterpart,
   and the outputs accepted from its dependency.
3. Freeze one `plan.toml` against the current implementation-repository commit.
   The plan names every allowed file action, the observing tests, the gate, and
   the human handoff. Later plans are not guessed before these inputs exist.
4. Reuse the existing producer and persisted artifact boundary. Add a type or
   abstraction only when no current owner can express a required value.
5. Compare structured artifacts in this order: keys, row labels, column labels,
   shapes, dtypes, then values. Require exact bytes or arrays when Phase 0 proves
   exact equality; use a tolerance only when the requirement names it.
6. Execute every implementation PairBlock through VIPER and retain its run and
   file identities. Load the complete numeric training set onto the GPU once.
   Hopfield trains on the full resident tensors; MIL preserves its historical
   128-row steps through GPU indices. The host receives checkpoints, logs, and
   final artifacts. Keep cheap source and fixture checks local.
7. Use the parity execution profile for every replay and the Hopfield bridge.
   Any KMeans call uses seeded scikit-learn Lloyd KMeans on CPU. GPU KMeans
   belongs to a later named throughput run.
8. Stop the current PairBlock when a comparison fails, a required source is
   absent, or a repair would touch an undeclared target. Matrix may choose among
   implementations that preserve the requirement and stay within the frozen
   targets. It may not weaken acceptance, invent a replacement artifact, or
   expand scope without a reviewed contract or plan revision.
9. Finish each PairBlock with its focused gate, self-review, immutable Git
   commit, push, human-readable handoff, implementation review, and required
   VIPER registration. Do not start its dependent before the compiler verifies
   those records.

## First entrypoint

`H1-PB-02` is the first implementation PairBlock. Its source-backed plan lives
at
[`plans/mantra-hopfield-reconstruction/H1-PB-02/plan.toml`](../../plans/mantra-hopfield-reconstruction/H1-PB-02/plan.toml).
Matrix creates `H1-PB-03`'s plan only after `H1-PB-02` closes and the accepted
loader boundary is available as its exact baseline.
