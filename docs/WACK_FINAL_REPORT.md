# WACK final report

Status: `PASS WITH OPTIONAL WARNING`

Final WACK result for the regenerated MSIX from this audit pass:

- Report: `release/certification/wack-20260723-172615.xml`
- XML SHA-256: `3514D8567FE5D421C2E5E805158006CA745FC1C6C3FFCE01E29F3DDDC53B77C2`
- Package: `release/msix/Movaura-0.9.0.0.msix`
- Package SHA-256: `0E8E821E7533A4C1D40D8E29ECB3CA14063F0BE4775E95C5C9D5930A49CC8330`
- Overall result: `PASS`
- WACK version: `10.0.28000.1839`
- OS reported by WACK: `Microsoft Windows 11 Pro`
- OS version reported by WACK: `10.0.26200.0`
- PASS count: `23`
- FAIL count: `1`
- Optional FAIL count: `1`

## Optional FAIL

- Test: `Executáveis bloqueados`
- Optional: `TRUE`
- Area: runtime binaries from the packaged desktop app, including Python, Qt/PySide6 and FFmpeg components.
- Decision: documented and preserved. The overall WACK result is `PASS`; runtime DLLs were not modified unsafely only to silence an optional warning.

Do not treat WACK PASS as proof of full product functionality. Manual product testing and Partner Center identity/signing are still required.
