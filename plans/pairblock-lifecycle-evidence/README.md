# PairBlock Lifecycle Evidence Plan

This directory holds complete production-file candidates for the
[PairBlock lifecycle evidence contract](../../docs/contracts/pairblock-lifecycle-evidence.md).
The `add/` and `replace/` trees mirror each destination beneath the RICO
repository root. `plan.toml` names the immutable Git baseline on which those
actions were reviewed.

`P0-PB-10K` is applied. The checker always materializes the reviewed baseline,
so the same approved plan remains verifiable after its production targets
exist. It does not write production files.

## Start here

1. Review [lifecycle_evidence.py](add/tools/pairblock_status/lifecycle_evidence.py).
2. Review
   [test_lifecycle_evidence_records.py](add/tests/pairblock_status/test_lifecycle_evidence_records.py).
3. Review [requirements.txt](replace/requirements.txt).
4. Run `python plans/pairblock-lifecycle-evidence/check.py P0-PB-10K` from the
   RICO root.
