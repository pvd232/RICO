# MANTRA Rebuild

This checklist is the execution authority for the Hopfield reconstruction, the
MIL reconstruction, and the first biologically grounded graph encoder. The
registered contracts own requirements and verification. This checklist owns
their phase and execution order; the compiler derives current status from
retained evidence.

The [Phase 1-2 Matrix charter](../docs/briefings/2026-09-15-mantra-phase-1-2-matrix-charter.md)
fixes the autonomous execution rules, stop conditions, and result required from
each PairBlock. Phase 0 remains an immutable comparison source and never runs
again.

<!-- contract-protocol:generated:start -->
**Resume here:** [Resume at H1-PB-02](../contracts/mantra-hopfield-reconstruction.md#h1-pb-02)


### Phase 1: Hopfield reconstruction

| Requirement | Status | Contract | PairBlocks | Dependencies |
|---|---|---|---|---|
| <nobr><code>H1-REQ-01</code></nobr> | complete | [mantra-hopfield-reconstruction](../contracts/mantra-hopfield-reconstruction.md#h1-req-01) | <nobr><code>H1-PB-01</code></nobr> | None |
| <nobr><code>H1-REQ-02</code></nobr> | in_progress | [mantra-hopfield-reconstruction](../contracts/mantra-hopfield-reconstruction.md#h1-req-02) | <nobr><code>H1-PB-02</code></nobr> | <nobr><code>H1-REQ-01</code></nobr> |
| <nobr><code>H1-REQ-03</code></nobr> | planned | [mantra-hopfield-reconstruction](../contracts/mantra-hopfield-reconstruction.md#h1-req-03) | <nobr><code>H1-PB-03</code></nobr> | <nobr><code>H1-REQ-02</code></nobr> |
| <nobr><code>H1-REQ-04</code></nobr> | planned | [mantra-hopfield-reconstruction](../contracts/mantra-hopfield-reconstruction.md#h1-req-04) | <nobr><code>H1-PB-04</code></nobr> | <nobr><code>H1-REQ-03</code></nobr> |
| <nobr><code>H1-REQ-05</code></nobr> | planned | [mantra-hopfield-reconstruction](../contracts/mantra-hopfield-reconstruction.md#h1-req-05) | <nobr><code>H1-PB-05</code></nobr> | <nobr><code>H1-REQ-04</code></nobr> |
| <nobr><code>H1-REQ-06</code></nobr> | planned | [mantra-hopfield-reconstruction](../contracts/mantra-hopfield-reconstruction.md#h1-req-06) | <nobr><code>H1-PB-06</code></nobr> | <nobr><code>H1-REQ-05</code></nobr> |
| <nobr><code>H1-REQ-07</code></nobr> | planned | [mantra-hopfield-reconstruction](../contracts/mantra-hopfield-reconstruction.md#h1-req-07) | <nobr><code>H1-PB-07</code></nobr> | <nobr><code>H1-REQ-06</code></nobr> |
| <nobr><code>H1-REQ-08</code></nobr> | planned | [mantra-hopfield-reconstruction](../contracts/mantra-hopfield-reconstruction.md#h1-req-08) | <nobr><code>H1-PB-08</code></nobr> | <nobr><code>H1-REQ-07</code></nobr> |

### Phase 2: MIL reconstruction

| Requirement | Status | Contract | PairBlocks | Dependencies |
|---|---|---|---|---|
| <nobr><code>M2-REQ-01</code></nobr> | planned | [mantra-mil-reconstruction](../contracts/mantra-mil-reconstruction.md#m2-req-01) | <nobr><code>M2-PB-01</code></nobr> | <nobr><code>H1-REQ-08</code></nobr> |
| <nobr><code>M2-REQ-02</code></nobr> | planned | [mantra-mil-reconstruction](../contracts/mantra-mil-reconstruction.md#m2-req-02) | <nobr><code>M2-PB-02</code></nobr> | <nobr><code>M2-REQ-01</code></nobr> |
| <nobr><code>M2-REQ-03</code></nobr> | planned | [mantra-mil-reconstruction](../contracts/mantra-mil-reconstruction.md#m2-req-03) | <nobr><code>M2-PB-03</code></nobr> | <nobr><code>M2-REQ-02</code></nobr> |
| <nobr><code>M2-REQ-04</code></nobr> | planned | [mantra-mil-reconstruction](../contracts/mantra-mil-reconstruction.md#m2-req-04) | <nobr><code>M2-PB-04</code></nobr> | <nobr><code>M2-REQ-03</code></nobr> |
| <nobr><code>M2-REQ-05</code></nobr> | planned | [mantra-mil-reconstruction](../contracts/mantra-mil-reconstruction.md#m2-req-05) | <nobr><code>M2-PB-05</code></nobr> | <nobr><code>M2-REQ-04</code></nobr> |
| <nobr><code>M2-REQ-06</code></nobr> | planned | [mantra-mil-reconstruction](../contracts/mantra-mil-reconstruction.md#m2-req-06) | <nobr><code>M2-PB-06</code></nobr> | <nobr><code>M2-REQ-05</code></nobr> |

### Phase 3: Graph identities and baselines

| Requirement | Status | Contract | PairBlocks | Dependencies |
|---|---|---|---|---|
| <nobr><code>GE-REQ-01</code></nobr> | planned | [mantra-graph-encoder-v1](../contracts/mantra-graph-encoder-v1.md#ge-req-01) | <nobr><code>GE-PB-01</code></nobr> | <nobr><code>M2-REQ-06</code></nobr> |
| <nobr><code>GE-REQ-02</code></nobr> | planned | [mantra-graph-encoder-v1](../contracts/mantra-graph-encoder-v1.md#ge-req-02) | <nobr><code>GE-PB-01</code></nobr> | <nobr><code>GE-REQ-01</code></nobr> |

### Phase 4: Topology and V1 features

| Requirement | Status | Contract | PairBlocks | Dependencies |
|---|---|---|---|---|
| <nobr><code>GE-REQ-03</code></nobr> | planned | [mantra-graph-encoder-v1](../contracts/mantra-graph-encoder-v1.md#ge-req-03) | <nobr><code>GE-PB-02</code></nobr> | <nobr><code>GE-REQ-02</code></nobr> |
| <nobr><code>GE-REQ-04</code></nobr> | planned | [mantra-graph-encoder-v1](../contracts/mantra-graph-encoder-v1.md#ge-req-04) | <nobr><code>GE-PB-03</code></nobr> | <nobr><code>GE-REQ-03</code></nobr> |

### Phase 5: V1 graph encoder

| Requirement | Status | Contract | PairBlocks | Dependencies |
|---|---|---|---|---|
| <nobr><code>GE-REQ-05</code></nobr> | planned | [mantra-graph-encoder-v1](../contracts/mantra-graph-encoder-v1.md#ge-req-05) | <nobr><code>GE-PB-04</code></nobr> | <nobr><code>GE-REQ-04</code></nobr> |
| <nobr><code>GE-REQ-06</code></nobr> | planned | [mantra-graph-encoder-v1](../contracts/mantra-graph-encoder-v1.md#ge-req-06) | <nobr><code>GE-PB-05</code></nobr> | <nobr><code>GE-REQ-05</code></nobr> |
| <nobr><code>GE-REQ-07</code></nobr> | planned | [mantra-graph-encoder-v1](../contracts/mantra-graph-encoder-v1.md#ge-req-07) | <nobr><code>GE-PB-06</code></nobr> | <nobr><code>GE-REQ-06</code></nobr> |
<!-- contract-protocol:generated:end -->

## Terminal outcome

The rebuild is complete when the selected Hopfield and MIL results reproduce
from their source inputs, the V1 graph encoder passes its frozen comparison
gates, and VIPER can resolve every accepted input, output, run, and producer.

## Owner actions

- Approve each PairBlock after reviewing its tested Git comparison.
- Provide or authorize L4-class compute when training or matrix workload exceeds
  the local execution threshold.

## Deferred scope

- CPU-only MIL acceptance remains outside the accepted CUDA reconstruction.
- Relation-specific message passing begins after V1 passes.
- Learned edge weights begin after relation-specific message passing establishes
  a comparison baseline.
- Perturbation-conditioned node selection begins after the earlier graph versions
  establish its necessity.

## Historical source

The pre-protocol roadmap and completed Phase 0 execution history are retained in
the [legacy master checklist](../archive/mantra-rebuild-master-checklist-legacy.md)
and the [Phase 0 archive](../archive/mantra-rebuild-phase-0/).
