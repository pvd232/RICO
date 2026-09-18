# VIPER Cloud Persistence

The [single governing contract](../contracts/viper-cloud-persistence.md) owns
the gap, impact analysis, design, requirements, and PairBlocks. This checklist
only compiles execution order and evidence state. It closes when a fresh
workspace consumes a promoted producer artifact through ViperCloud without
access to the producer path or storage-provider configuration.

<!-- contract-protocol:generated:start -->
**Resume here:** [Resume at VC-PB-01](../contracts/viper-cloud-persistence.md#vc-pb-01)


### Phase 1: Durable cloud run root

| Requirement | Status | Contract | PairBlocks | Dependencies |
|---|---|---|---|---|
| <nobr><code>VC-REQ-01</code></nobr> | in_progress | [viper-cloud-persistence](../contracts/viper-cloud-persistence.md#vc-req-01) | <nobr><code>VC-PB-01</code></nobr> | None |
| <nobr><code>VC-REQ-02</code></nobr> | in_progress | [viper-cloud-persistence](../contracts/viper-cloud-persistence.md#vc-req-02) | <nobr><code>VC-PB-01</code></nobr> | <nobr><code>VC-REQ-01</code></nobr> |

### Phase 2: Explicit verified promotion

| Requirement | Status | Contract | PairBlocks | Dependencies |
|---|---|---|---|---|
| <nobr><code>VC-REQ-03</code></nobr> | planned | [viper-cloud-persistence](../contracts/viper-cloud-persistence.md#vc-req-03) | <nobr><code>VC-PB-02</code></nobr> | None |

### Phase 3: Identity and lineage preservation

| Requirement | Status | Contract | PairBlocks | Dependencies |
|---|---|---|---|---|
| <nobr><code>VC-REQ-04</code></nobr> | planned | [viper-cloud-persistence](../contracts/viper-cloud-persistence.md#vc-req-04) | <nobr><code>VC-PB-03</code></nobr> | <nobr><code>VC-REQ-03</code></nobr> |

### Phase 4: Fresh-workspace acceptance

| Requirement | Status | Contract | PairBlocks | Dependencies |
|---|---|---|---|---|
| <nobr><code>VC-REQ-05</code></nobr> | planned | [viper-cloud-persistence](../contracts/viper-cloud-persistence.md#vc-req-05) | <nobr><code>VC-PB-04</code></nobr> | <nobr><code>VC-REQ-01</code></nobr>, <nobr><code>VC-REQ-02</code></nobr>, <nobr><code>VC-REQ-03</code></nobr>, <nobr><code>VC-REQ-04</code></nobr> |
<!-- contract-protocol:generated:end -->
