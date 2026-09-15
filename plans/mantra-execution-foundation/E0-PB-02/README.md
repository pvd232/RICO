# E0-PB-02

## What changed

- The Spot launcher tries lower-demand regions in order and treats quota failures like capacity failures.
- A verified cloud probe is mandatory before launch. The launch records the worker, disk, and network resources it created.
- The same script tears down the worker and disk only after an artifact restore probe succeeds.
- Failed launches clean their own partial resources without deleting reused network infrastructure.

## Plan deviations

Live worker execution identity moved to E0-PB-12 because CUDA, driver, RNG, and runtime facts can only be measured after the worker boots. Everything else went according to plan.

## Review these files

- [Complete diff](patches/gpu-lifecycle.patch)
- [Launcher and teardown entrypoint](../../../mantra-deploy-spot.sh#L39)
- [Regional fallback and cleanup tests](../../../tests/infrastructure/test_mantra_gpu_lifecycle.py#L190)

## Decision

Approve E0-PB-02, or return it with findings.
