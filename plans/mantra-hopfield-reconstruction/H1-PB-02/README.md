# H1-PB-02: Truth-row alignment

## What changes

The Hopfield loader currently verifies that descriptor features and coefficient
targets use the same ordered perturbations, then loads fit and tune truth arrays
without reading their labels. The retained patch makes the loader read those
labels and reject disagreement before it pairs any truth row with a feature row.

## Start here

- [Complete diff](patches/truth-perturbation-order.patch)
- [Executable plan](plan.toml)
- [Current loader join](../../../../mantra/experiments/v1938_sota_clean_repro/src/step01/hopfield/loader.py#L265)
- [Current observing fixture](../../../../mantra/experiments/v1938_sota_clean_repro/tests/step01/test_hopfield_direct_family_contract.py#L451)

The focused preflight passed Pyright, three selected test cases, Ruff lint, and
range-limited Ruff formatting checks in an isolated checkout of the declared
MANTRA baseline. The range limit avoids rewriting unrelated historical lines
that were already outside the current formatter's output.
