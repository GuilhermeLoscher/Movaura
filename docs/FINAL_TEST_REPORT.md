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

## Build and package validation executed locally

- `scripts/build_standalone.ps1 -PythonExe C:\NovaWall\.build-venv\Scripts\python.exe`: PASS
- Standalone self-test from `dist\standalone\Movaura\Movaura.exe`: PASS
- Standalone path-with-spaces self-test: PASS
- `scripts/build_msix_package.ps1 -StandalonePath dist\standalone\Movaura -PythonExe C:\NovaWall\.build-venv\Scripts\python.exe`: PASS
- `scripts/validate_msix_layout.py`: PASS, 300 files validated
- Final MSIX SHA-256: `0E8E821E7533A4C1D40D8E29ECB3CA14063F0BE4775E95C5C9D5930A49CC8330`
- `scripts/run_wack.ps1 -PackagePath release\msix\Movaura-0.9.0.0.msix`: PASS overall, 1 optional warning documented in `docs/WACK_FINAL_REPORT.md`

## Pending

- GitHub Actions CI run for the PR/final branch commit.
- Human manual test checklist.
- Partner Center real identity build/signing.
- Professional legal review for final commercial distribution.
