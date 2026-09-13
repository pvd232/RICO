# PairBlock Lifecycle Evidence Plan

This directory holds complete production-file candidates for the
[PairBlock lifecycle evidence contract](../../docs/contracts/pairblock-lifecycle-evidence.md).
The `add/` tree mirrors each destination beneath the RICO repository root.

`P0-PB-10K` is ready for pair implementation. Copy or type each candidate into
the target named by `plan.toml`, then run the listed gate from the RICO root.
The plan does not write production files.

## Start here

1. Review
   [lifecycle_evidence.py](add/tools/pairblock_status/lifecycle_evidence.py).
2. Create `tools/pairblock_status/lifecycle_evidence.py` from that candidate.
3. Review
   [test_lifecycle_evidence_records.py](add/tests/pairblock_status/test_lifecycle_evidence_records.py).
4. Create `tests/pairblock_status/test_lifecycle_evidence_records.py` from that
   candidate.
5. Run the four `P0-PB-10K` gate commands in `plan.toml`.
