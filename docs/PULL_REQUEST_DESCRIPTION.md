# Migrate Movaura to PySide6 and finalize Store audit readiness

## Summary

This PR migrates Movaura from PyQt6 to PySide6 and completes the current Microsoft Store technical readiness audit for the `migration/pyside6` branch.

## Main changes

- Replaced active Qt imports with PySide6.
- Added checks to detect PyQt6 residue in source and packaged artifacts.
- Added pinned build dependencies in `requirements-build.txt`.
- Hardened scene package import validation against unsafe archive contents.
- Hardened plugin loading path validation.
- Added UTF-8/mojibake validation.
- Added reproducible build reports, inventories, SHA-256 hashes and simple SBOM outputs.
- Added MSIX layout validation.
- Added Partner Center identity safeguards for Store builds.
- Added Microsoft Store readiness, security, licensing, WACK, CI and manual-test documentation.

## Local validation

- Standalone local build: PASS
- MSIX local build: PASS
- Internal MSIX validation: PASS
- WACK local result: PASS overall
- WACK PASS count: 23
- WACK FAIL count: 1
- WACK optional FAIL count: 1
- Optional WACK warning: `Executáveis bloqueados`, documented in `docs/WACK_FINAL_REPORT.md`

## Hashes

- MSIX SHA-256: `0E8E821E7533A4C1D40D8E29ECB3CA14063F0BE4775E95C5C9D5930A49CC8330`
- WACK XML SHA-256: `3514D8567FE5D421C2E5E805158006CA745FC1C6C3FFCE01E29F3DDDC53B77C2`

## Status and limitations

Current status: `READY FOR PARTNER CENTER IDENTITY`

Do not merge until:

- GitHub Actions CI is green for this PR.
- CI artifacts are reviewed.
- Manual tests are completed.
- Partner Center real identity is applied.
- Store-signed MSIX is generated with the real identity.
- WACK is rerun on the final Store identity package.
- Licensing/FFmpeg/Qt/PySide6 review is completed.

## Explicitly not included

- No merge to `main`.
- No Store publication.
- No Partner Center submission.
- No real AI provider integration.
- No telemetry.
- No private certificate.
- No secret or service-role key.
- No changes to `C:\NovaWall\Movaura Beta`.
