# MANTRA Rebuild

This checklist is the execution authority for the Hopfield reconstruction, the
MIL reconstruction, and the first biologically grounded graph encoder. The
registered contracts own requirements and verification. This checklist owns
their phase and execution order; the compiler derives current status from
retained evidence.

<!-- contract-protocol:generated:start -->
**Resume here:** [Resume at H1-PB-02](../contracts/mantra-hopfield-reconstruction.md#h1-pb-02)


### Phase 1: Hopfield reconstruction

| PairBlock | Status | Contract | Dependencies | Receipt |
|---|---|---|---|---|
| <nobr><code>H1-PB-01</code></nobr> | bootstrap-complete | [mantra-hopfield-reconstruction](../contracts/mantra-hopfield-reconstruction.md#h1-pb-01) | None | [receipt](../evidence/mantra-rebuild/bootstrap.json) |
| <nobr><code>H1-PB-02</code></nobr> | drafting | [mantra-hopfield-reconstruction](../contracts/mantra-hopfield-reconstruction.md#h1-pb-02) | <nobr><code>H1-PB-01</code></nobr> | None |
| <nobr><code>H1-PB-03</code></nobr> | waiting | [mantra-hopfield-reconstruction](../contracts/mantra-hopfield-reconstruction.md#h1-pb-03) | <nobr><code>H1-PB-02</code></nobr> | None |
| <nobr><code>H1-PB-04</code></nobr> | waiting | [mantra-hopfield-reconstruction](../contracts/mantra-hopfield-reconstruction.md#h1-pb-04) | <nobr><code>H1-PB-03</code></nobr> | None |
| <nobr><code>H1-PB-05</code></nobr> | waiting | [mantra-hopfield-reconstruction](../contracts/mantra-hopfield-reconstruction.md#h1-pb-05) | <nobr><code>H1-PB-04</code></nobr> | None |
| <nobr><code>H1-PB-06</code></nobr> | waiting | [mantra-hopfield-reconstruction](../contracts/mantra-hopfield-reconstruction.md#h1-pb-06) | <nobr><code>H1-PB-05</code></nobr> | None |

### Phase 2: MIL reconstruction

| PairBlock | Status | Contract | Dependencies | Receipt |
|---|---|---|---|---|
| <nobr><code>M2-PB-01</code></nobr> | waiting | [mantra-mil-reconstruction](../contracts/mantra-mil-reconstruction.md#m2-pb-01) | <nobr><code>H1-PB-06</code></nobr> | None |
| <nobr><code>M2-PB-02</code></nobr> | waiting | [mantra-mil-reconstruction](../contracts/mantra-mil-reconstruction.md#m2-pb-02) | <nobr><code>M2-PB-01</code></nobr> | None |
| <nobr><code>M2-PB-03</code></nobr> | waiting | [mantra-mil-reconstruction](../contracts/mantra-mil-reconstruction.md#m2-pb-03) | <nobr><code>M2-PB-02</code></nobr> | None |
| <nobr><code>M2-PB-04</code></nobr> | waiting | [mantra-mil-reconstruction](../contracts/mantra-mil-reconstruction.md#m2-pb-04) | <nobr><code>M2-PB-03</code></nobr> | None |

### Phase 3: Graph identities and baselines

| PairBlock | Status | Contract | Dependencies | Receipt |
|---|---|---|---|---|
| <nobr><code>GE-PB-01</code></nobr> | waiting | [mantra-graph-encoder-v1](../contracts/mantra-graph-encoder-v1.md#ge-pb-01) | <nobr><code>M2-PB-04</code></nobr> | None |

### Phase 4: Topology and V1 features

| PairBlock | Status | Contract | Dependencies | Receipt |
|---|---|---|---|---|
| <nobr><code>GE-PB-02</code></nobr> | waiting | [mantra-graph-encoder-v1](../contracts/mantra-graph-encoder-v1.md#ge-pb-02) | <nobr><code>GE-PB-01</code></nobr> | None |
| <nobr><code>GE-PB-03</code></nobr> | waiting | [mantra-graph-encoder-v1](../contracts/mantra-graph-encoder-v1.md#ge-pb-03) | <nobr><code>GE-PB-02</code></nobr> | None |

### Phase 5: V1 graph encoder

| PairBlock | Status | Contract | Dependencies | Receipt |
|---|---|---|---|---|
| <nobr><code>GE-PB-04</code></nobr> | waiting | [mantra-graph-encoder-v1](../contracts/mantra-graph-encoder-v1.md#ge-pb-04) | <nobr><code>GE-PB-03</code></nobr> | None |
| <nobr><code>GE-PB-05</code></nobr> | waiting | [mantra-graph-encoder-v1](../contracts/mantra-graph-encoder-v1.md#ge-pb-05) | <nobr><code>GE-PB-04</code></nobr> | None |
| <nobr><code>GE-PB-06</code></nobr> | waiting | [mantra-graph-encoder-v1](../contracts/mantra-graph-encoder-v1.md#ge-pb-06) | <nobr><code>GE-PB-05</code></nobr> | None |
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
