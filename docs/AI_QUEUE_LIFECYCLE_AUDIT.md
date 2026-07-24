# AI queue lifecycle audit

Status: `AUTOMATED TESTS PASS LOCALLY`

## Covered by `scripts/run_ai_generation_tests.py`

- success path;
- provider failure;
- history result failure;
- history failure failure;
- rollback;
- rollback cleanup failure;
- cancellation;
- shutdown timeout;
- repeated shutdown;
- provider hang simulation;
- no premature QThread destruction in tested lifecycle;
- terminal state handling.

The test intentionally prints stack traces for simulated failures, then exits with:

```text
ai_generation_tests=ok
```

## Not covered

- Real external AI provider.
- Network provider cancellation.
- GPU-backed generation.

Real API integration is intentionally out of scope for this audit.
