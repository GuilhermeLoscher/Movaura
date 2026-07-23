# Final test report

Status: `AUTOMATED LOCAL TESTS PASS; MANUAL TESTS PENDING`

## Automated tests executed locally in this audit pass

- `python -m compileall -q app.py core renderers ui plugins scripts`: PASS
- `scripts/check_no_pyqt_artifacts.py ... --report-base release/reports/qt-binding-audit`: PASS
- `scripts/audit_ffmpeg.py --root tools/ffmpeg --report-base release/reports/ffmpeg-audit`: PASS
- `scripts/run_product_smoke_tests.py`: PASS
- `scripts/run_ai_generation_tests.py`: PASS
- `app.py --self-test`: PASS

## Important note about AI test output

The AI lifecycle test intentionally prints simulated provider/history/rollback failures. The authoritative result is the final line:

```text
ai_generation_tests=ok
```

## Pending

- GitHub Actions CI run after push.
- Fresh standalone rebuild after all audit changes.
- Fresh MSIX rebuild after all audit changes.
- Fresh WACK on the final regenerated MSIX.
- Human manual test checklist.
