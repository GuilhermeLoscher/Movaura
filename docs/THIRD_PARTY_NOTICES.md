# Third-party notices

Status: READY FOR PROFESSIONAL LEGAL REVIEW. This notice summarizes technical inventory and must be reviewed against official license texts before publication.

Movaura includes third-party runtime components. The complete audit evidence is under `release/compliance/` and the human review documents are under `docs/`.

## Qt / PySide6 / Shiboken6

- PySide6 6.10.0 / Qt runtime modules are distributed as dynamic files in the standalone artifact.
- Official GPL/LGPL texts are included under `licenses/qt`, `licenses/pyside6`, and `licenses/shiboken6`.
- Qt Virtual Keyboard was removed from the local artifact and is guarded against re-collection because official Qt documentation lists it as commercial/GPLv3 for open-source users.
- See `docs/QT_MODULE_LICENSE_MATRIX.md` and `docs/LGPL_MSIX_TECHNICAL_ASSESSMENT.md`.

## FFmpeg

- FFmpeg is bundled for local video decoding/inspection/optimization.
- Provider: BtbN/FFmpeg-Builds.
- Release tag: autobuild-2026-06-30-13-34.
- Artifact: ffmpeg-N-125365-g9a01c1cb6a-win64-lgpl-shared.zip.
- Artifact SHA-256: 52d25fc4711078112ba622d07601f183371af43e2d93cbb6e5eab3e1c05387cb.
- FFmpeg source URL/SHA and provider source URL/SHA are recorded in `third_party/ffmpeg/LOCK.json`.
- See `docs/FFMPEG_BUILD_LOCK.md` and `docs/FFMPEG_EXTERNAL_LIBRARY_MATRIX.md`.

## Python runtime and packages

- Python/PyInstaller/Pillow/pywin32 and related package notices are inventoried under `licenses/` and `release/compliance/python/`.
- See `docs/PYTHON_DEPENDENCY_LICENSE_MATRIX.md` and `docs/THIRD_PARTY_COMPONENTS_LOCK.md`.
