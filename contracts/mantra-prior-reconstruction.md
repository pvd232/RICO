# MANTRA Prior Reconstruction

This contract rebuilds every biological prior consumed by the first-principles
models from pinned source bytes. Each prior reports source consumption,
identifier resolution, perturbation coverage, missing modalities, transformation
parameters, and its ordered output arrays.

The interaction build must consume the complete IntAct source. The experimental
`ALG1L` perturbation remains on the model row axis, resolves to the current
`ALG1L1P` pseudogene record, and carries no fabricated protein-derived values.

<!-- contract-protocol:generated:start -->
**Planned.** [Jump to current PairBlock](#p4-pb-01)

**Checklist:** [MANTRA rebuild](../checklists/mantra-rebuild.md)

### PairBlocks

<a id="p4-pb-01"></a>

#### <nobr><code>P4-PB-01</code></nobr>

**Status:** waiting

**Requirement contribution:** Inventory every prior consumed by the parity models and connect it to sources, builders, arrays, and historical evidence.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>D3-PB-06</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="p4-pb-02"></a>

#### <nobr><code>P4-PB-02</code></nobr>

**Status:** waiting

**Requirement contribution:** Run each selected prior source through a complete, atomic, VIPER-recorded acquisition and ingest path.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>P4-PB-01</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="p4-pb-03"></a>

#### <nobr><code>P4-PB-03</code></nobr>

**Status:** waiting

**Requirement contribution:** Preserve pseudogene perturbations while marking unsupported protein-derived modalities missing.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>P4-PB-02</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="p4-pb-04"></a>

#### <nobr><code>P4-PB-04</code></nobr>

**Status:** waiting

**Requirement contribution:** Rebuild the interaction prior from complete pinned sources and reject the historical truncated IntAct input.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>P4-PB-03</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="p4-pb-05"></a>

#### <nobr><code>P4-PB-05</code></nobr>

**Status:** waiting

**Requirement contribution:** Rebuild and audit every other selected prior against the canonical perturbation identities.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>P4-PB-04</code></nobr>

**Next action:** Wait for the declared dependencies.

<a id="p4-pb-06"></a>

#### <nobr><code>P4-PB-06</code></nobr>

**Status:** waiting

**Requirement contribution:** Freeze one corrected, provenance-complete prior bundle for both model rebuilds.

**Plan:** None

**Current receipt:** None

**Dependencies:** <nobr><code>P4-PB-05</code></nobr>

**Next action:** Wait for the declared dependencies.


### Requirements

| Requirement | Claim | Progress | Verifiers | PairBlocks |
|---|---|---|---|---|
| <nobr><code>P4-REQ-01</code></nobr> | Before corrected reconstruction begins, the inventory must distinguish raw biological sources, transformed prior blocks, and final model inputs. It must account explicitly for the eleven arrays in the retained compressed prior bundle—corum, depmap_essentiality, dorothea_grn, gene_family, mechanistic256, motif, pathway_hallmark, ppi_spectral, ptm, regulatory256, and subcellular—and resolve every model-consumed prior to its raw sources, typed ingest, biological identity joins, transformation parameters, output arrays, historical counterpart, and demonstrated reconstruction boundary. | planned | <nobr><code>P4-VR-01</code></nobr> | <nobr><code>P4-PB-01</code></nobr> |
| <nobr><code>P4-REQ-02</code></nobr> | Each selected prior source must be reacquired or restored through one VIPER stage that retains the exact request, source version, raw bytes, parser inputs, typed output, and failures without writing partial downloads to final paths. | planned | <nobr><code>P4-VR-02</code></nobr> | <nobr><code>P4-PB-02</code></nobr> |
| <nobr><code>P4-REQ-03</code></nobr> | A perturbation that resolves to a current pseudogene must remain on the experimental row axis, retain its current gene identity and locus type, and mark protein-derived modalities missing instead of dropping the row or fabricating protein evidence. | planned | <nobr><code>P4-VR-03</code></nobr> | <nobr><code>P4-PB-03</code></nobr> |
| <nobr><code>P4-REQ-04</code></nobr> | The interaction prior must parse every byte of each pinned source, preserve source attribution for every accepted edge, report per-source and union coverage, and reject a truncated or concurrently changing source before dimensional reduction. | planned | <nobr><code>P4-VR-04</code></nobr> | <nobr><code>P4-PB-04</code></nobr> |
| <nobr><code>P4-REQ-05</code></nobr> | Every non-interaction prior selected for the rebuilt models must be reconstructed from its pinned typed sources and report unresolved perturbations, missing modalities, duplicate identities, row order, dimensions, dtypes, and transformation parameters. | planned | <nobr><code>P4-VR-05</code></nobr> | <nobr><code>P4-PB-05</code></nobr> |
| <nobr><code>P4-REQ-06</code></nobr> | One corrected prior bundle must preserve the canonical perturbation order, distinguish observed values from missing modalities, and bind every array to its source and build evidence for downstream model stages. | planned | <nobr><code>P4-VR-06</code></nobr> | <nobr><code>P4-PB-06</code></nobr> |

### Verification rules

| Rule | Requirements | Acceptance conditions | Success case | Rejection cases |
|---|---|---|---|---|
| <nobr><code>P4-VR-01</code></nobr> | <nobr><code>P4-REQ-01</code></nobr> | The inventory accounts for every model-consumed prior; separately names the eleven retained compressed-bundle arrays; and records each source, producer, transformation, historical identity, current reconstruction status, and first unresolved connector without treating an assembled block as a raw source. | [test_inventory_accounts_for_every_consumed_prior](../../mantra/src/mantra/rebuild/tests/test_prior_inventory.py) | [test_rejects_unowned_or_unresolved_prior](../../mantra/src/mantra/rebuild/tests/test_prior_inventory.py) |
| <nobr><code>P4-VR-02</code></nobr> | <nobr><code>P4-REQ-02</code></nobr> | Each download or restoration publishes only verified complete bytes and the VIPER record reaches the request, source identity, parser, typed output, and failure state. | [test_acquires_and_ingests_prior_sources](../../mantra/src/mantra/rebuild/tests/test_prior_sources.py) | [test_rejects_partial_or_unpinned_prior_source](../../mantra/src/mantra/rebuild/tests/test_prior_sources.py) |
| <nobr><code>P4-VR-03</code></nobr> | <nobr><code>P4-REQ-03</code></nobr> | The ALG1L experimental row resolves to the current ALG1L1P gene record and carries explicit missingness for protein-derived inputs while remaining present in every split and output axis. | [test_preserves_pseudogene_perturbation_with_modality_masks](../../mantra/src/mantra/rebuild/tests/test_pseudogene_policy.py) | [test_rejects_dropped_row_or_fabricated_protein_identity](../../mantra/src/mantra/rebuild/tests/test_pseudogene_policy.py) |
| <nobr><code>P4-VR-04</code></nobr> | <nobr><code>P4-REQ-04</code></nobr> | The parser consumes the complete pinned IntAct bytes, reports accepted pairs and covered perturbations, and rejects the known 1,170,222,081-byte historical prefix as incomplete. | [test_rebuilds_interactions_from_complete_sources](../../mantra/src/mantra/rebuild/tests/test_interaction_prior.py) | [test_rejects_historical_intact_prefix](../../mantra/src/mantra/rebuild/tests/test_interaction_prior.py) |
| <nobr><code>P4-VR-05</code></nobr> | <nobr><code>P4-REQ-05</code></nobr> | Each selected prior rebuild preserves canonical row order and emits complete identity, coverage, missingness, source, and transformation reports before model fitting. | [test_rebuilds_selected_noninteraction_priors](../../mantra/src/mantra/rebuild/tests/test_prior_reconstruction.py) | [test_rejects_missing_or_misaligned_prior_rows](../../mantra/src/mantra/rebuild/tests/test_prior_reconstruction.py) |
| <nobr><code>P4-VR-06</code></nobr> | <nobr><code>P4-REQ-06</code></nobr> | The frozen bundle contains one ordered row per perturbation, one observation mask per modality, and a verified provenance path from every array to its raw source and builder. | [test_freezes_corrected_prior_bundle](../../mantra/src/mantra/rebuild/tests/test_prior_bundle.py) | [test_rejects_unattributed_or_implicit_missing_values](../../mantra/src/mantra/rebuild/tests/test_prior_bundle.py) |
<!-- contract-protocol:generated:end -->
