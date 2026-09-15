# MANTRA Graph Encoder V1

This contract freezes the identities and baselines used by the first
biologically grounded graph encoder, selects its topology and features, and
then reserves held-out responses for final evaluation after model selection.

<!-- contract-protocol:generated:start -->
**Planned.** [Jump to current PairBlock](#ge-pb-01)

**Checklist:** [MANTRA rebuild](../checklists/mantra-rebuild.md)

### PairBlocks

<a id="ge-pb-01"></a>

#### <nobr><code>GE-PB-01</code></nobr>

**Status:** waiting

**Requirement contribution:** Freeze graph-encoder row, column, split, and source identities and reproduce the corrected ridge and fusion-only baselines on that surface.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>M2-PB-06</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="ge-pb-02"></a>

#### <nobr><code>GE-PB-02</code></nobr>

**Status:** waiting

**Requirement contribution:** Build the candidate biological graphs and retain the topology measurements and edge provenance used to choose message depth.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>GE-PB-01</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="ge-pb-03"></a>

#### <nobr><code>GE-PB-03</code></nobr>

**Status:** waiting

**Requirement contribution:** Build and validate the AlphaGenome feature pipeline and reproduce the frozen fusion-only baseline.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>GE-PB-02</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="ge-pb-04"></a>

#### <nobr><code>GE-PB-04</code></nobr>

**Status:** waiting

**Requirement contribution:** Train the first graph encoder and replace the legacy student representation at every inference-time consumer.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>GE-PB-03</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="ge-pb-05"></a>

#### <nobr><code>GE-PB-05</code></nobr>

**Status:** waiting

**Requirement contribution:** Run the provenance-preserving graph and message-depth study and freeze the selection using tune data only.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>GE-PB-04</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="ge-pb-06"></a>

#### <nobr><code>GE-PB-06</code></nobr>

**Status:** waiting

**Requirement contribution:** Apply the V1 comparison gates and reproduce the selected graph-encoder result from retained VIPER records.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>GE-PB-05</code></nobr>

**Next action:** Wait for the declared dependencies.


### Requirements

| Requirement | Claim | Progress | Verifiers | PairBlocks |
|---|---|---|---|---|
| <nobr><code>GE-REQ-01</code></nobr> | The graph-encoder path must preserve the ordered identities and source releases for all 2,057 perturbation rows, all 5,000 resolved response-gene columns, train, tune, and hold memberships, response-target computation, and held-out-data exclusion. | planned | <nobr><code>GE-VR-01</code></nobr> | <nobr><code>GE-PB-01</code></nobr> |
| <nobr><code>GE-REQ-02</code></nobr> | The corrected ridge and fusion-only baselines must reproduce on the same frozen evaluation surface used to assess the graph encoder, and VIPER must retain the identity records, manifests, producer commands, splits, baselines, and checks. | planned | <nobr><code>GE-VR-02</code></nobr> | <nobr><code>GE-PB-01</code></nobr> |
| <nobr><code>GE-REQ-03</code></nobr> | PPI, regulatory, and signaling graph candidates must retain edge provenance and report perturbation coverage, response coverage, response mass by message-passing depth, top-K differentially expressed gene recall, graph density, and per-perturbation failure modes. | planned | <nobr><code>GE-VR-03</code></nobr> | <nobr><code>GE-PB-02</code></nobr> |
| <nobr><code>GE-REQ-04</code></nobr> | Every graph node must receive a validated, modality-normalized AlphaGenome feature row; the feature pipeline must reject missing nodes, invalid rows, and collapsed fused embeddings and must reproduce the frozen fusion-only baseline. | planned | <nobr><code>GE-VR-04</code></nobr> | <nobr><code>GE-PB-03</code></nobr> |
| <nobr><code>GE-REQ-05</code></nobr> | The V1 encoder must build the binary PPI graph, apply one-hop mean aggregation, gather perturbation rows, replace the legacy student identity at every inference consumer, train under the unchanged downstream objective, and produce valid non-collapsed embeddings for all 2,057 perturbations without using hold responses in graph construction or node features. | planned | <nobr><code>GE-VR-05</code></nobr> | <nobr><code>GE-PB-04</code></nobr> |
| <nobr><code>GE-REQ-06</code></nobr> | The graph-construction study must union approved prior edges with provenance, rank unique neighbors by AlphaGenome cosine similarity, sweep top-K under fixed topology and evaluation gates, and select graph construction and message depth using tune data only. | planned | <nobr><code>GE-VR-06</code></nobr> | <nobr><code>GE-PB-05</code></nobr> |
| <nobr><code>GE-REQ-07</code></nobr> | The selected V1 graph encoder must beat fusion-only on at least one primary unseen-perturbation metric, remain competitive with or exceed the corrected ridge baseline, and reproduce the accepted result from retained VIPER records. | planned | <nobr><code>GE-VR-07</code></nobr> | <nobr><code>GE-PB-06</code></nobr> |

### Verification rules

| Rule | Requirements | Acceptance conditions | Success case | Rejection cases |
|---|---|---|---|---|
| <nobr><code>GE-VR-01</code></nobr> | <nobr><code>GE-REQ-01</code></nobr> | Every required perturbation and response column has one ordered identity, an approved split membership, and a retained source release; held-out responses are excluded from training inputs. | [test_freezes_graph_encoder_identities](../../mantra/src/mantra/rebuild/tests/test_graph_identities.py) | [test_rejects_changed_identity_or_hold_leakage](../../mantra/src/mantra/rebuild/tests/test_graph_identities.py) |
| <nobr><code>GE-VR-02</code></nobr> | <nobr><code>GE-REQ-02</code></nobr> | The corrected ridge and fusion-only predictions and metrics reproduce from the frozen identity surface. | [test_reproduces_corrected_graph_baselines](../../mantra/src/mantra/rebuild/tests/test_graph_baselines.py) | [test_rejects_baseline_on_another_evaluation_surface](../../mantra/src/mantra/rebuild/tests/test_graph_baselines.py) |
| <nobr><code>GE-VR-03</code></nobr> | <nobr><code>GE-REQ-03</code></nobr> | The topology report retains every candidate edge source and reports the declared reachability, response-mass, recall, density, and failure measurements. | [test_reports_candidate_graph_topology](../../mantra/src/mantra/rebuild/tests/test_graph_topology.py) | [test_rejects_unattributed_or_incomplete_topology](../../mantra/src/mantra/rebuild/tests/test_graph_topology.py) |
| <nobr><code>GE-VR-04</code></nobr> | <nobr><code>GE-REQ-04</code></nobr> | Every graph node has one valid fused feature row, each modality follows the approved normalization, and the fusion-only baseline reproduces. | [test_builds_complete_v1_feature_matrix](../../mantra/src/mantra/rebuild/tests/test_graph_features.py) | [test_rejects_missing_invalid_or_collapsed_features](../../mantra/src/mantra/rebuild/tests/test_graph_features.py) |
| <nobr><code>GE-VR-05</code></nobr> | <nobr><code>GE-REQ-05</code></nobr> | The V1 encoder produces one finite non-collapsed embedding for every perturbation and no graph or feature input contains hold response data. | [test_trains_v1_graph_encoder](../../mantra/src/mantra/rebuild/tests/test_graph_encoder.py) | [test_rejects_missing_embeddings_or_hold_leakage](../../mantra/src/mantra/rebuild/tests/test_graph_encoder.py) |
| <nobr><code>GE-VR-06</code></nobr> | <nobr><code>GE-REQ-06</code></nobr> | Every candidate edge retains its source, the top-K sweep uses fixed gates, and graph and depth selection consume tune results without reading hold results. | [test_selects_graph_and_depth_on_tune_data](../../mantra/src/mantra/rebuild/tests/test_graph_construction.py) | [test_rejects_unattributed_edges_or_hold_selection](../../mantra/src/mantra/rebuild/tests/test_graph_construction.py) |
| <nobr><code>GE-VR-07</code></nobr> | <nobr><code>GE-REQ-07</code></nobr> | The selected encoder beats fusion-only on a primary unseen-perturbation metric, satisfies the corrected-ridge comparison, and reproduces from resolved VIPER records. | [test_accepts_reproducible_v1_graph_encoder](../../mantra/src/mantra/rebuild/tests/test_graph_acceptance.py) | [test_rejects_uncompetitive_or_unresolved_v1_result](../../mantra/src/mantra/rebuild/tests/test_graph_acceptance.py) |
<!-- contract-protocol:generated:end -->
