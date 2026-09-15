# MANTRA Rebuild

This checklist is the execution authority for the Hopfield reconstruction, the
MIL reconstruction, and the first biologically grounded graph encoder. The
registered contracts own requirements and verification. This checklist owns
their phase and execution order; the compiler derives current status from
retained evidence.

The [pre-graph Matrix charter](../docs/briefings/2026-09-15-mantra-pregraph-matrix-charter.md)
fixes the compute allocation, artifact ownership, variant policy, stop
conditions, and result required from each PairBlock through Phase 9. Phase 0
remains an immutable comparison source and never runs again.

<!-- contract-protocol:generated:start -->
**Resume here:** [Resume at E0-PB-04](../contracts/mantra-execution-foundation.md#e0-pb-04)


### Phase 1: GPU foundation and Hopfield reconstruction

| Requirement | Status | Contract | PairBlocks | Dependencies |
|---|---|---|---|---|
| <nobr><code>E0-REQ-01</code></nobr> | complete | [mantra-execution-foundation](../contracts/mantra-execution-foundation.md#e0-req-01) | <nobr><code>E0-PB-01</code></nobr> | <nobr><code>E0-REQ-02</code></nobr> |
| <nobr><code>E0-REQ-02</code></nobr> | complete | [mantra-execution-foundation](../contracts/mantra-execution-foundation.md#e0-req-02) | <nobr><code>E0-PB-02</code></nobr> | None |
| <nobr><code>E0-REQ-03</code></nobr> | complete | [mantra-execution-foundation](../contracts/mantra-execution-foundation.md#e0-req-03) | <nobr><code>E0-PB-03</code></nobr> | <nobr><code>E0-REQ-01</code></nobr> |
| <nobr><code>E0-REQ-12</code></nobr> | in_progress | [mantra-execution-foundation](../contracts/mantra-execution-foundation.md#e0-req-12) | <nobr><code>E0-PB-12</code></nobr> | <nobr><code>E0-REQ-01</code></nobr>, <nobr><code>E0-REQ-02</code></nobr> |
| <nobr><code>E0-REQ-09</code></nobr> | in_progress | [mantra-execution-foundation](../contracts/mantra-execution-foundation.md#e0-req-09) | <nobr><code>E0-PB-09</code></nobr> | <nobr><code>E0-REQ-03</code></nobr> |
| <nobr><code>H1-REQ-01</code></nobr> | complete | [mantra-hopfield-reconstruction](../contracts/mantra-hopfield-reconstruction.md#h1-req-01) | <nobr><code>H1-PB-01</code></nobr> | None |
| <nobr><code>H1-REQ-02</code></nobr> | in_progress | [mantra-hopfield-reconstruction](../contracts/mantra-hopfield-reconstruction.md#h1-req-02) | <nobr><code>H1-PB-02</code></nobr> | <nobr><code>H1-REQ-01</code></nobr> |
| <nobr><code>H1-REQ-03</code></nobr> | planned | [mantra-hopfield-reconstruction](../contracts/mantra-hopfield-reconstruction.md#h1-req-03) | <nobr><code>H1-PB-03</code></nobr> | <nobr><code>H1-REQ-02</code></nobr> |
| <nobr><code>H1-REQ-04</code></nobr> | planned | [mantra-hopfield-reconstruction](../contracts/mantra-hopfield-reconstruction.md#h1-req-04) | <nobr><code>H1-PB-04</code></nobr> | <nobr><code>H1-REQ-03</code></nobr> |
| <nobr><code>H1-REQ-05</code></nobr> | planned | [mantra-hopfield-reconstruction](../contracts/mantra-hopfield-reconstruction.md#h1-req-05) | <nobr><code>H1-PB-05</code></nobr> | <nobr><code>H1-REQ-04</code></nobr> |
| <nobr><code>H1-REQ-06</code></nobr> | planned | [mantra-hopfield-reconstruction](../contracts/mantra-hopfield-reconstruction.md#h1-req-06) | <nobr><code>H1-PB-06</code></nobr> | <nobr><code>H1-REQ-05</code></nobr>, <nobr><code>E0-REQ-09</code></nobr>, <nobr><code>E0-REQ-12</code></nobr> |
| <nobr><code>H1-REQ-07</code></nobr> | planned | [mantra-hopfield-reconstruction](../contracts/mantra-hopfield-reconstruction.md#h1-req-07) | <nobr><code>H1-PB-07</code></nobr> | <nobr><code>H1-REQ-06</code></nobr> |
| <nobr><code>H1-REQ-08</code></nobr> | planned | [mantra-hopfield-reconstruction](../contracts/mantra-hopfield-reconstruction.md#h1-req-08) | <nobr><code>H1-PB-08</code></nobr> | <nobr><code>H1-REQ-07</code></nobr> |

### Phase 2: MIL reconstruction and Hopfield input convergence

| Requirement | Status | Contract | PairBlocks | Dependencies |
|---|---|---|---|---|
| <nobr><code>E0-REQ-10</code></nobr> | in_progress | [mantra-execution-foundation](../contracts/mantra-execution-foundation.md#e0-req-10) | <nobr><code>E0-PB-10</code></nobr> | <nobr><code>E0-REQ-03</code></nobr> |
| <nobr><code>M2-REQ-01</code></nobr> | in_progress | [mantra-mil-reconstruction](../contracts/mantra-mil-reconstruction.md#m2-req-01) | <nobr><code>M2-PB-01</code></nobr> | None |
| <nobr><code>M2-REQ-02</code></nobr> | planned | [mantra-mil-reconstruction](../contracts/mantra-mil-reconstruction.md#m2-req-02) | <nobr><code>M2-PB-02</code></nobr> | <nobr><code>M2-REQ-01</code></nobr> |
| <nobr><code>M2-REQ-03</code></nobr> | planned | [mantra-mil-reconstruction](../contracts/mantra-mil-reconstruction.md#m2-req-03) | <nobr><code>M2-PB-03</code></nobr> | <nobr><code>M2-REQ-02</code></nobr>, <nobr><code>E0-REQ-10</code></nobr>, <nobr><code>E0-REQ-12</code></nobr> |
| <nobr><code>M2-REQ-04</code></nobr> | planned | [mantra-mil-reconstruction](../contracts/mantra-mil-reconstruction.md#m2-req-04) | <nobr><code>M2-PB-04</code></nobr> | <nobr><code>M2-REQ-03</code></nobr> |
| <nobr><code>M2-REQ-05</code></nobr> | planned | [mantra-mil-reconstruction](../contracts/mantra-mil-reconstruction.md#m2-req-05) | <nobr><code>M2-PB-05</code></nobr> | <nobr><code>M2-REQ-04</code></nobr> |
| <nobr><code>M2-REQ-06</code></nobr> | planned | [mantra-mil-reconstruction](../contracts/mantra-mil-reconstruction.md#m2-req-06) | <nobr><code>M2-PB-06</code></nobr> | <nobr><code>M2-REQ-05</code></nobr> |
| <nobr><code>H1-REQ-09</code></nobr> | planned | [mantra-hopfield-reconstruction](../contracts/mantra-hopfield-reconstruction.md#h1-req-09) | <nobr><code>H1-PB-09</code></nobr> | <nobr><code>H1-REQ-08</code></nobr>, <nobr><code>M2-REQ-06</code></nobr>, <nobr><code>E0-REQ-08</code></nobr>, <nobr><code>E0-REQ-09</code></nobr> |

### Phase 3: Biological identities and canonical atlas

| Requirement | Status | Contract | PairBlocks | Dependencies |
|---|---|---|---|---|
| <nobr><code>D3-REQ-01</code></nobr> | planned | [mantra-data-foundation](../contracts/mantra-data-foundation.md#d3-req-01) | <nobr><code>D3-PB-01</code></nobr> | <nobr><code>H1-REQ-09</code></nobr>, <nobr><code>M2-REQ-06</code></nobr> |
| <nobr><code>D3-REQ-02</code></nobr> | planned | [mantra-data-foundation](../contracts/mantra-data-foundation.md#d3-req-02) | <nobr><code>D3-PB-02</code></nobr> | <nobr><code>D3-REQ-01</code></nobr> |
| <nobr><code>D3-REQ-03</code></nobr> | planned | [mantra-data-foundation](../contracts/mantra-data-foundation.md#d3-req-03) | <nobr><code>D3-PB-03</code></nobr> | <nobr><code>D3-REQ-02</code></nobr> |
| <nobr><code>D3-REQ-04</code></nobr> | planned | [mantra-data-foundation](../contracts/mantra-data-foundation.md#d3-req-04) | <nobr><code>D3-PB-04</code></nobr> | <nobr><code>D3-REQ-03</code></nobr> |
| <nobr><code>D3-REQ-05</code></nobr> | planned | [mantra-data-foundation](../contracts/mantra-data-foundation.md#d3-req-05) | <nobr><code>D3-PB-05</code></nobr> | <nobr><code>D3-REQ-04</code></nobr> |
| <nobr><code>D3-REQ-06</code></nobr> | planned | [mantra-data-foundation](../contracts/mantra-data-foundation.md#d3-req-06) | <nobr><code>D3-PB-06</code></nobr> | <nobr><code>D3-REQ-05</code></nobr> |
| <nobr><code>D3-REQ-07</code></nobr> | planned | [mantra-data-foundation](../contracts/mantra-data-foundation.md#d3-req-07) | <nobr><code>D3-PB-07</code></nobr> | <nobr><code>D3-REQ-06</code></nobr> |

### Phase 4: Prior reconstruction

| Requirement | Status | Contract | PairBlocks | Dependencies |
|---|---|---|---|---|
| <nobr><code>E0-REQ-11</code></nobr> | in_progress | [mantra-execution-foundation](../contracts/mantra-execution-foundation.md#e0-req-11) | <nobr><code>E0-PB-11</code></nobr> | <nobr><code>E0-REQ-03</code></nobr> |
| <nobr><code>P4-REQ-01</code></nobr> | planned | [mantra-prior-reconstruction](../contracts/mantra-prior-reconstruction.md#p4-req-01) | <nobr><code>P4-PB-01</code></nobr> | <nobr><code>D3-REQ-06</code></nobr> |
| <nobr><code>P4-REQ-02</code></nobr> | planned | [mantra-prior-reconstruction](../contracts/mantra-prior-reconstruction.md#p4-req-02) | <nobr><code>P4-PB-02</code></nobr> | <nobr><code>P4-REQ-01</code></nobr> |
| <nobr><code>P4-REQ-03</code></nobr> | planned | [mantra-prior-reconstruction](../contracts/mantra-prior-reconstruction.md#p4-req-03) | <nobr><code>P4-PB-03</code></nobr> | <nobr><code>P4-REQ-02</code></nobr> |
| <nobr><code>P4-REQ-04</code></nobr> | planned | [mantra-prior-reconstruction](../contracts/mantra-prior-reconstruction.md#p4-req-04) | <nobr><code>P4-PB-04</code></nobr> | <nobr><code>P4-REQ-03</code></nobr> |
| <nobr><code>P4-REQ-05</code></nobr> | planned | [mantra-prior-reconstruction](../contracts/mantra-prior-reconstruction.md#p4-req-05) | <nobr><code>P4-PB-05</code></nobr> | <nobr><code>P4-REQ-04</code></nobr> |
| <nobr><code>P4-REQ-06</code></nobr> | planned | [mantra-prior-reconstruction](../contracts/mantra-prior-reconstruction.md#p4-req-06) | <nobr><code>P4-PB-06</code></nobr> | <nobr><code>P4-REQ-05</code></nobr> |

### Phase 5: Response reconstruction

| Requirement | Status | Contract | PairBlocks | Dependencies |
|---|---|---|---|---|
| <nobr><code>E0-REQ-04</code></nobr> | in_progress | [mantra-execution-foundation](../contracts/mantra-execution-foundation.md#e0-req-04) | <nobr><code>E0-PB-04</code></nobr> | <nobr><code>E0-REQ-03</code></nobr> |
| <nobr><code>E0-REQ-05</code></nobr> | in_progress | [mantra-execution-foundation](../contracts/mantra-execution-foundation.md#e0-req-05) | <nobr><code>E0-PB-05</code></nobr> | <nobr><code>E0-REQ-03</code></nobr> |
| <nobr><code>E0-REQ-06</code></nobr> | in_progress | [mantra-execution-foundation](../contracts/mantra-execution-foundation.md#e0-req-06) | <nobr><code>E0-PB-06</code></nobr> | <nobr><code>E0-REQ-03</code></nobr> |
| <nobr><code>E0-REQ-08</code></nobr> | planned | [mantra-execution-foundation](../contracts/mantra-execution-foundation.md#e0-req-08) | <nobr><code>E0-PB-08</code></nobr> | <nobr><code>E0-REQ-04</code></nobr> |
| <nobr><code>R5-REQ-01</code></nobr> | planned | [mantra-response-reconstruction](../contracts/mantra-response-reconstruction.md#r5-req-01) | <nobr><code>R5-PB-01</code></nobr> | <nobr><code>R5-REQ-02</code></nobr>, <nobr><code>E0-REQ-04</code></nobr>, <nobr><code>E0-REQ-08</code></nobr> |
| <nobr><code>R5-REQ-02</code></nobr> | planned | [mantra-response-reconstruction](../contracts/mantra-response-reconstruction.md#r5-req-02) | <nobr><code>R5-PB-02</code></nobr> | <nobr><code>P4-REQ-06</code></nobr>, <nobr><code>D3-REQ-07</code></nobr> |
| <nobr><code>R5-REQ-03</code></nobr> | planned | [mantra-response-reconstruction](../contracts/mantra-response-reconstruction.md#r5-req-03) | <nobr><code>R5-PB-03</code></nobr> | <nobr><code>R5-REQ-02</code></nobr>, <nobr><code>E0-REQ-06</code></nobr> |
| <nobr><code>R5-REQ-04</code></nobr> | planned | [mantra-response-reconstruction](../contracts/mantra-response-reconstruction.md#r5-req-04) | <nobr><code>R5-PB-04</code></nobr> | <nobr><code>R5-REQ-03</code></nobr>, <nobr><code>E0-REQ-05</code></nobr> |
| <nobr><code>R5-REQ-05</code></nobr> | planned | [mantra-response-reconstruction](../contracts/mantra-response-reconstruction.md#r5-req-05) | <nobr><code>R5-PB-05</code></nobr> | <nobr><code>R5-REQ-04</code></nobr>, <nobr><code>E0-REQ-11</code></nobr> |
| <nobr><code>R5-REQ-06</code></nobr> | planned | [mantra-response-reconstruction](../contracts/mantra-response-reconstruction.md#r5-req-06) | <nobr><code>R5-PB-06</code></nobr> | <nobr><code>R5-REQ-01</code></nobr>, <nobr><code>R5-REQ-07</code></nobr> |
| <nobr><code>R5-REQ-07</code></nobr> | planned | [mantra-response-reconstruction](../contracts/mantra-response-reconstruction.md#r5-req-07) | <nobr><code>R5-PB-07</code></nobr> | <nobr><code>R5-REQ-05</code></nobr> |

### Phase 6: Shared perturbation representation

| Requirement | Status | Contract | PairBlocks | Dependencies |
|---|---|---|---|---|
| <nobr><code>E0-REQ-07</code></nobr> | in_progress | [mantra-execution-foundation](../contracts/mantra-execution-foundation.md#e0-req-07) | <nobr><code>E0-PB-07</code></nobr> | <nobr><code>E0-REQ-03</code></nobr> |
| <nobr><code>S6-REQ-01</code></nobr> | planned | [mantra-first-principles-models](../contracts/mantra-first-principles-models.md#s6-req-01) | <nobr><code>S6-PB-01</code></nobr> | <nobr><code>R5-REQ-06</code></nobr> |
| <nobr><code>S6-REQ-02</code></nobr> | planned | [mantra-first-principles-models](../contracts/mantra-first-principles-models.md#s6-req-02) | <nobr><code>S6-PB-02</code></nobr> | <nobr><code>S6-REQ-01</code></nobr>, <nobr><code>E0-REQ-11</code></nobr> |
| <nobr><code>S6-REQ-03</code></nobr> | planned | [mantra-first-principles-models](../contracts/mantra-first-principles-models.md#s6-req-03) | <nobr><code>S6-PB-03</code></nobr> | <nobr><code>S6-REQ-02</code></nobr> |
| <nobr><code>S6-REQ-04</code></nobr> | planned | [mantra-first-principles-models](../contracts/mantra-first-principles-models.md#s6-req-04) | <nobr><code>S6-PB-04</code></nobr> | <nobr><code>S6-REQ-03</code></nobr>, <nobr><code>E0-REQ-07</code></nobr> |
| <nobr><code>S6-REQ-05</code></nobr> | planned | [mantra-first-principles-models](../contracts/mantra-first-principles-models.md#s6-req-05) | <nobr><code>S6-PB-05</code></nobr> | <nobr><code>S6-REQ-01</code></nobr>, <nobr><code>E0-REQ-02</code></nobr> |
| <nobr><code>S6-REQ-06</code></nobr> | planned | [mantra-first-principles-models](../contracts/mantra-first-principles-models.md#s6-req-06) | <nobr><code>S6-PB-06</code></nobr> | <nobr><code>S6-REQ-04</code></nobr>, <nobr><code>R5-REQ-07</code></nobr> |
| <nobr><code>S6-REQ-07</code></nobr> | planned | [mantra-first-principles-models](../contracts/mantra-first-principles-models.md#s6-req-07) | <nobr><code>S6-PB-07</code></nobr> | <nobr><code>S6-REQ-05</code></nobr>, <nobr><code>S6-REQ-06</code></nobr> |
| <nobr><code>S6-REQ-08</code></nobr> | planned | [mantra-first-principles-models](../contracts/mantra-first-principles-models.md#s6-req-08) | <nobr><code>S6-PB-08</code></nobr> | <nobr><code>S6-REQ-07</code></nobr>, <nobr><code>E0-REQ-08</code></nobr> |
| <nobr><code>S6-REQ-09</code></nobr> | planned | [mantra-first-principles-models](../contracts/mantra-first-principles-models.md#s6-req-09) | <nobr><code>S6-PB-09</code></nobr> | <nobr><code>S6-REQ-08</code></nobr>, <nobr><code>E0-REQ-09</code></nobr>, <nobr><code>E0-REQ-10</code></nobr> |

### Phase 7: First-principles Hopfield

| Requirement | Status | Contract | PairBlocks | Dependencies |
|---|---|---|---|---|
| <nobr><code>H7-REQ-01</code></nobr> | planned | [mantra-first-principles-models](../contracts/mantra-first-principles-models.md#h7-req-01) | <nobr><code>H7-PB-01</code></nobr> | <nobr><code>S6-REQ-09</code></nobr>, <nobr><code>E0-REQ-09</code></nobr> |
| <nobr><code>H7-REQ-02</code></nobr> | planned | [mantra-first-principles-models](../contracts/mantra-first-principles-models.md#h7-req-02) | <nobr><code>H7-PB-02</code></nobr> | <nobr><code>H7-REQ-01</code></nobr> |
| <nobr><code>H7-REQ-03</code></nobr> | planned | [mantra-first-principles-models](../contracts/mantra-first-principles-models.md#h7-req-03) | <nobr><code>H7-PB-03</code></nobr> | <nobr><code>H7-REQ-02</code></nobr> |
| <nobr><code>H7-REQ-04</code></nobr> | planned | [mantra-first-principles-models](../contracts/mantra-first-principles-models.md#h7-req-04) | <nobr><code>H7-PB-04</code></nobr> | <nobr><code>H7-REQ-03</code></nobr> |
| <nobr><code>H7-REQ-05</code></nobr> | planned | [mantra-first-principles-models](../contracts/mantra-first-principles-models.md#h7-req-05) | <nobr><code>H7-PB-05</code></nobr> | <nobr><code>H7-REQ-04</code></nobr> |

### Phase 8: First-principles MIL

| Requirement | Status | Contract | PairBlocks | Dependencies |
|---|---|---|---|---|
| <nobr><code>M8-REQ-01</code></nobr> | planned | [mantra-first-principles-models](../contracts/mantra-first-principles-models.md#m8-req-01) | <nobr><code>M8-PB-01</code></nobr> | <nobr><code>S6-REQ-09</code></nobr>, <nobr><code>E0-REQ-10</code></nobr> |
| <nobr><code>M8-REQ-02</code></nobr> | planned | [mantra-first-principles-models](../contracts/mantra-first-principles-models.md#m8-req-02) | <nobr><code>M8-PB-02</code></nobr> | <nobr><code>M8-REQ-01</code></nobr> |
| <nobr><code>M8-REQ-03</code></nobr> | planned | [mantra-first-principles-models](../contracts/mantra-first-principles-models.md#m8-req-03) | <nobr><code>M8-PB-03</code></nobr> | <nobr><code>M8-REQ-02</code></nobr> |
| <nobr><code>M8-REQ-04</code></nobr> | planned | [mantra-first-principles-models](../contracts/mantra-first-principles-models.md#m8-req-04) | <nobr><code>M8-PB-04</code></nobr> | <nobr><code>M8-REQ-03</code></nobr> |
| <nobr><code>M8-REQ-05</code></nobr> | planned | [mantra-first-principles-models](../contracts/mantra-first-principles-models.md#m8-req-05) | <nobr><code>M8-PB-05</code></nobr> | <nobr><code>M8-REQ-04</code></nobr> |
| <nobr><code>M8-REQ-06</code></nobr> | planned | [mantra-first-principles-models](../contracts/mantra-first-principles-models.md#m8-req-06) | <nobr><code>M8-PB-06</code></nobr> | <nobr><code>M8-REQ-05</code></nobr> |

### Phase 9: Pre-graph baseline freeze

| Requirement | Status | Contract | PairBlocks | Dependencies |
|---|---|---|---|---|
| <nobr><code>B9-REQ-01</code></nobr> | planned | [mantra-first-principles-models](../contracts/mantra-first-principles-models.md#b9-req-01) | <nobr><code>B9-PB-01</code></nobr> | <nobr><code>H7-REQ-05</code></nobr>, <nobr><code>M8-REQ-06</code></nobr> |
| <nobr><code>B9-REQ-02</code></nobr> | planned | [mantra-first-principles-models](../contracts/mantra-first-principles-models.md#b9-req-02) | <nobr><code>B9-PB-02</code></nobr> | <nobr><code>B9-REQ-01</code></nobr> |

### Phase 10: Graph identities and baselines

| Requirement | Status | Contract | PairBlocks | Dependencies |
|---|---|---|---|---|
| <nobr><code>GE-REQ-01</code></nobr> | planned | [mantra-graph-encoder-v1](../contracts/mantra-graph-encoder-v1.md#ge-req-01) | <nobr><code>GE-PB-01</code></nobr> | <nobr><code>B9-REQ-02</code></nobr> |
| <nobr><code>GE-REQ-02</code></nobr> | planned | [mantra-graph-encoder-v1](../contracts/mantra-graph-encoder-v1.md#ge-req-02) | <nobr><code>GE-PB-01</code></nobr> | <nobr><code>GE-REQ-01</code></nobr> |

### Phase 11: Topology and V1 features

| Requirement | Status | Contract | PairBlocks | Dependencies |
|---|---|---|---|---|
| <nobr><code>GE-REQ-03</code></nobr> | planned | [mantra-graph-encoder-v1](../contracts/mantra-graph-encoder-v1.md#ge-req-03) | <nobr><code>GE-PB-02</code></nobr> | <nobr><code>GE-REQ-02</code></nobr> |
| <nobr><code>GE-REQ-04</code></nobr> | planned | [mantra-graph-encoder-v1](../contracts/mantra-graph-encoder-v1.md#ge-req-04) | <nobr><code>GE-PB-03</code></nobr> | <nobr><code>GE-REQ-03</code></nobr> |

### Phase 12: V1 graph encoder

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

## Later work

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
