# Final license audit

Status: READY FOR PROFESSIONAL LEGAL REVIEW

This is a technical compliance preparation report, not legal advice. It must not be treated as approval for commercial release.

## What was resolved

- FFmpeg no longer depends on a floating `latest` artifact in the compliance lock.
- FFmpeg is pinned to a retained BtbN monthly release with immutable tag URL and archive SHA-256.
- FFmpeg binary hashes are recorded in `third_party/ffmpeg/LOCK.json` and `docs/FFMPEG_BUILD_LOCK.md`.
- FFmpeg source and provider source URLs/SHA-256 are recorded without vendoring large source archives into Git.
- Every enabled `--enable-lib*` flag has a technical license classification or legal-review classification.
- Qt/PySide6 artifact inventory was regenerated after removing Qt Virtual Keyboard from the local artifact.
- The build script now excludes Qt Virtual Keyboard and fails if it reappears.
- Official GPL/LGPL license texts were added for Qt/PySide6/Shiboken6 review packages.

## Still requiring professional review

- LGPLv3 compliance strategy for MSIX and standalone distribution.
- Codec and patent review by sale/distribution territory.
- Final third-party notice wording and EULA/privacy alignment.
- Owner decision on whether to use Qt commercial licensing or LGPLv3 compliance materials.

## Evidence

- `third_party/ffmpeg/LOCK.json`
- `docs/FFMPEG_BUILD_LOCK.md`
- `docs/FFMPEG_EXTERNAL_LIBRARY_MATRIX.md`
- `docs/QT_MODULE_LICENSE_MATRIX.md`
- `docs/LGPL_MSIX_TECHNICAL_ASSESSMENT.md`
- `THIRD_PARTY_NOTICES.txt`
- `release/compliance/`

## Official sources checked

- BtbN FFmpeg-Builds README/release retention and variants: https://github.com/BtbN/FFmpeg-Builds
- BtbN pinned release: https://github.com/BtbN/FFmpeg-Builds/releases/tag/autobuild-2026-06-30-13-34
- FFmpeg legal/license documentation: https://ffmpeg.org/legal.html
- Qt licensing: https://doc.qt.io/qt-6/licensing.html
- Qt for Python commercial use: https://doc.qt.io/qtforpython-6.10/commercial/index.html
- Qt Virtual Keyboard licensing: https://doc.qt.io/qt-6/qtvirtualkeyboard-index.html
- GNU GPL/LGPL license texts: https://www.gnu.org/licenses/
