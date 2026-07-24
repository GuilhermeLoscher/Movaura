# Legal review handoff

- Product: Movaura
- Commit: ad18ee50a9672ecf93a8d2a04372f88c2199a8cc
- Created UTC: 2026-07-24T14:39:03.693319+00:00
- Distribution: Windows standalone/MSIX, Microsoft Store candidate
- Countries: OWNER DECISION REQUIRED
- Business model: OWNER DECISION REQUIRED

## Questions for counsel

1. Does the proposed LGPLv3 strategy satisfy standalone and MSIX distribution obligations?
2. Are the provided LGPL/GPL texts, FFmpeg source URLs/SHA-256, and notices sufficient?
3. Does the EULA preserve third-party license rights?
4. Which codec/patent licenses are required in the selected sale territories?
5. Is the FFmpeg source offer/package strategy sufficient if source archives are not vendored into Git?
6. Is excluding Qt Virtual Keyboard sufficient, or should owner obtain Qt commercial licensing anyway?
7. Do sales, activation, and update flows create additional legal/privacy obligations?
8. Is the privacy policy adequate for Microsoft Store review?

## Evidence package

- `release/compliance/`
- `docs/QT_MODULE_LICENSE_MATRIX.md`
- `docs/FFMPEG_EXTERNAL_LIBRARY_MATRIX.md`
- `docs/FFMPEG_BUILD_LOCK.md`
- `third_party/ffmpeg/LOCK.json`
- `THIRD_PARTY_NOTICES.txt`
