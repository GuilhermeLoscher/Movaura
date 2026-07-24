# Final license audit

Status: NOT READY - LICENSE BLOCKERS

This is a technical compliance preparation report, not legal advice.

## Blockers

- FFmpeg immutable archive/source lock is pending.
- FFmpeg external libraries require official per-library review.
- Qt module licensing still requires official module-by-module confirmation.
- LGPLv3 and MSIX replacement/relink strategy requires owner/legal decision.
- Patent/codecs review requires territory-specific legal review.

## Evidence

- `release/compliance/`
- `docs/audit-evidence/movaura-beta-baseline.json`
- `third_party/ffmpeg/LOCK.json`
- `THIRD_PARTY_NOTICES.txt`

## Official sources checked

- Qt licensing: https://doc.qt.io/qt-6/licensing.html
- Qt for Python commercial use: https://doc.qt.io/qtforpython-6.10/commercial/index.html
- FFmpeg legal/license documentation: https://ffmpeg.org/legal.html
- FFmpeg license documentation snapshot: https://ffmpeg.org/doxygen/7.0/md_LICENSE.html
- MSIX package signing: https://learn.microsoft.com/en-us/windows/msix/package/signing-package-overview
- MSIX package identity/runtime context: https://learn.microsoft.com/en-us/windows/msix/detect-package-identity
- PyInstaller license: https://pyinstaller.org/en/stable/license.html

## License text blocker

The local PySide6 wheels did not expose full LGPL/GPL text files under names such as `LGPL*.txt` or `GPL*.txt` during this audit.
Existing short notices must not be treated as complete license texts. Full official license texts and Qt third-party notices remain required before commercial publication.
