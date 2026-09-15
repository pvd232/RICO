# MANTRA Biological Data Foundation

This contract gives every downstream MANTRA stage one biological identity map
and one cell population. It preserves the raw perturbation label while keeping
gene, transcript, guide, protein, response-coordinate, and graph-node identities
distinct.

The raw atlas is downloaded once and filtered once. The QC pass combines a
mitochondrial percentage at or below 15 with the declared five-MAD rules. Its
ordered cell set becomes one minimal H5AD read by every later producer. A
separate stage regenerates two gene panels. The control-program panel applies
the documented highly-variable-gene procedure and excludes mitochondrial,
ribosomal, globin, and core immediate-early genes. The ordered GEARS 5,000-gene
response panel retains any immediate-early genes present because response is a
prediction target. Downstream stages use the panel declared for their role.

<!-- contract-protocol:generated:start -->
**Planned.** [Jump to current PairBlock](#d3-pb-01)

**Checklist:** [MANTRA rebuild](../checklists/mantra-rebuild.md)

### PairBlocks

<a id="d3-pb-01"></a>

#### <nobr><code>D3-PB-01</code></nobr>

**Status:** waiting

**Requirement contribution:** Freeze the perturbation row key and the distinct fields used to join biological and experimental identities.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>H1-PB-09</code></nobr>, <nobr><code>M2-PB-06</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="d3-pb-02"></a>

#### <nobr><code>D3-PB-02</code></nobr>

**Status:** waiting

**Requirement contribution:** Download and register the immutable raw K562 atlas through VIPER.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>D3-PB-01</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="d3-pb-03"></a>

#### <nobr><code>D3-PB-03</code></nobr>

**Status:** waiting

**Requirement contribution:** Build the versioned perturbation identity table from the pinned atlas and source snapshots.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>D3-PB-02</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="d3-pb-04"></a>

#### <nobr><code>D3-PB-04</code></nobr>

**Status:** waiting

**Requirement contribution:** Apply the fixed 15 percent mitochondrial ceiling and five-MAD rules once, then freeze one ordered cell set for every downstream stage.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>D3-PB-03</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="d3-pb-05"></a>

#### <nobr><code>D3-PB-05</code></nobr>

**Status:** waiting

**Requirement contribution:** Build the canonical slim H5AD from the selected cells and retain only fields with downstream consumers.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>D3-PB-04</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="d3-pb-06"></a>

#### <nobr><code>D3-PB-06</code></nobr>

**Status:** waiting

**Requirement contribution:** Verify FastH5ADLoader against the canonical slim file and retain correctness and timing evidence.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>D3-PB-05</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="d3-pb-07"></a>

#### <nobr><code>D3-PB-07</code></nobr>

**Status:** waiting

**Requirement contribution:** Regenerate and freeze the IEG-excluded control-program panel and the distinct ordered GEARS 5,000-gene response panel.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>D3-PB-06</code></nobr>

**Next action:** Wait for the declared dependencies.


### Requirements

| Requirement | Claim | Progress | Verifiers | PairBlocks |
|---|---|---|---|---|
| <nobr><code>D3-REQ-01</code></nobr> | The model-facing perturbation ID must remain the raw label in the canonical split contract. One declared identity schema must attach current HGNC, Ensembl gene, transcript, guide-pair, locus-type, and source-snapshot fields without substituting any of those identities for the perturbation ID or the separate response-gene key. | planned | <nobr><code>D3-VR-01</code></nobr> | <nobr><code>D3-PB-01</code></nobr> |
| <nobr><code>D3-REQ-02</code></nobr> | The raw K562 perturbation atlas must be downloaded from a pinned source into immutable source bytes with the request, source revision, byte count, SHA-256, and retrieval result retained through VIPER. | planned | <nobr><code>D3-VR-02</code></nobr> | <nobr><code>D3-PB-02</code></nobr> |
| <nobr><code>D3-REQ-03</code></nobr> | One versioned perturbation identity table must preserve every raw perturbation label from the pinned atlas and materialize the declared HGNC, Ensembl gene, transcript, guide-pair, locus-type, resolution-result, and source-snapshot fields, with explicit missingness for identities that do not exist. | planned | <nobr><code>D3-VR-03</code></nobr> | <nobr><code>D3-PB-03</code></nobr> |
| <nobr><code>D3-REQ-04</code></nobr> | One QC pass must retain cells with mitochondrial percentage at or below 15 and within five median absolute deviations for the declared count, detected-gene, top-20-gene-fraction, and mitochondrial covariates, then produce one ordered cell set for every downstream consumer. | planned | <nobr><code>D3-VR-04</code></nobr> | <nobr><code>D3-PB-04</code></nobr> |
| <nobr><code>D3-REQ-05</code></nobr> | One deterministic builder must create the canonical slim H5AD from the pinned atlas and selected cell set, retaining the expression matrix, cell and perturbation identity fields, mitochondrial fraction, and gene-axis identifiers while omitting unused derived annotations, layers, embeddings, graphs, and analysis state. | planned | <nobr><code>D3-VR-05</code></nobr> | <nobr><code>D3-PB-05</code></nobr> |
| <nobr><code>D3-REQ-06</code></nobr> | FastH5ADLoader must read the canonical slim H5AD with the same requested rows, columns, order, dtypes, and values as the reference AnnData path, and the VIPER run must retain the input, output, timing, and comparison evidence. | planned | <nobr><code>D3-VR-06</code></nobr> | <nobr><code>D3-PB-06</code></nobr> |
| <nobr><code>D3-REQ-07</code></nobr> | One deterministic gene-panel stage must derive the control-program panel by the documented Seurat v3 highly-variable-gene procedure from an eligible gene universe that excludes mitochondrial, ribosomal, globin, and core immediate-early genes, and must reproduce the exact ordered GEARS 5,000-gene response panel while retaining the core immediate-early genes present in that target surface. The stage must retain each selection rule, fitted population, source gene axis, ordered output, overlap, and digest; the two panels must remain distinct inputs to their named downstream consumers. | planned | <nobr><code>D3-VR-07</code></nobr> | <nobr><code>D3-PB-07</code></nobr> |

### Verification rules

| Rule | Requirements | Acceptance conditions | Success case | Rejection cases |
|---|---|---|---|---|
| <nobr><code>D3-VR-01</code></nobr> | <nobr><code>D3-REQ-01</code></nobr> | The declared schema uses the raw split-contract label as the perturbation row key, uses the resolved gene key only for response columns, and gives every other biological or experimental identity its own named field and pinned source. | [test_declares_distinct_perturbation_and_response_identities](../../mantra/src/mantra/rebuild/tests/test_biological_identity.py) | [test_rejects_cross_axis_identity_substitution](../../mantra/src/mantra/rebuild/tests/test_biological_identity.py) |
| <nobr><code>D3-VR-02</code></nobr> | <nobr><code>D3-REQ-02</code></nobr> | A clean restoration resolves the exact atlas bytes from the retained source record, and changed or partial bytes fail before QC or transformation. | [test_restores_pinned_raw_atlas](../../mantra/src/mantra/rebuild/tests/test_atlas_acquisition.py) | [test_rejects_partial_or_changed_atlas](../../mantra/src/mantra/rebuild/tests/test_atlas_acquisition.py) |
| <nobr><code>D3-VR-03</code></nobr> | <nobr><code>D3-REQ-03</code></nobr> | Every atlas perturbation retains its raw label; unambiguous current gene records are attached with the resolution kind and source snapshots; unresolved or biologically absent identities remain explicit missing values. | [test_builds_perturbation_identity_table](../../mantra/src/mantra/rebuild/tests/test_biological_identity.py) | [test_rejects_ambiguous_resolution_or_implicit_missingness](../../mantra/src/mantra/rebuild/tests/test_biological_identity.py) |
| <nobr><code>D3-VR-04</code></nobr> | <nobr><code>D3-REQ-04</code></nobr> | The QC record reports the median, median absolute deviation, bounds, rejected cells, retained perturbation coverage, and fixed 15 percent mitochondrial ceiling; every downstream builder consumes the same ordered cell-set identity. | [test_builds_one_fifteen_percent_five_mad_cell_set](../../mantra/src/mantra/rebuild/tests/test_cell_qc.py) | [test_rejects_changed_threshold_or_downstream_cell_set](../../mantra/src/mantra/rebuild/tests/test_cell_qc.py) |
| <nobr><code>D3-VR-05</code></nobr> | <nobr><code>D3-REQ-05</code></nobr> | Rebuilding twice from the same atlas and QC record produces the same H5AD identity, every retained field has a named consumer, and legacy derived fields are absent. | [test_builds_minimal_canonical_slim_atlas](../../mantra/src/mantra/rebuild/tests/test_slim_atlas.py) | [test_rejects_missing_identity_or_extra_derived_fields](../../mantra/src/mantra/rebuild/tests/test_slim_atlas.py) |
| <nobr><code>D3-VR-06</code></nobr> | <nobr><code>D3-REQ-06</code></nobr> | Fast and reference readers return equal arrays for dense and sparse fixtures, explicit row selections, repeated genes, missing genes, and the canonical slim-file schema. | [test_fast_reader_matches_reference_reader](../../mantra/src/mantra/rebuild/tests/test_fast_h5ad_contract.py) | [test_rejects_unsupported_or_misaligned_h5ad](../../mantra/src/mantra/rebuild/tests/test_fast_h5ad_contract.py) |
| <nobr><code>D3-VR-07</code></nobr> | <nobr><code>D3-REQ-07</code></nobr> | The control-panel record identifies the documented Seurat v3 procedure, fitted population, per-gene statistics, eligible-gene exclusions, core immediate-early-gene blacklist, ordered output, and realized count. The response panel equals the ordered GEARS 5,000-gene surface and retains any core immediate-early genes present in that target surface. Changing either source population, selection rule, membership, order, exclusion policy, or downstream role fails. | [test_builds_distinct_control2k_and_gears5k_panels](../../mantra/src/mantra/rebuild/tests/test_gene_panels.py) | [test_rejects_changed_or_interchanged_gene_panels](../../mantra/src/mantra/rebuild/tests/test_gene_panels.py) |
<!-- contract-protocol:generated:end -->
