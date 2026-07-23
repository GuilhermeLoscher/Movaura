# Third-party notices - Movaura

Last updated: 2026-07-23.

This document summarizes third-party components redistributed or expected in the Movaura standalone/MSIX build. It is a technical compliance aid, not legal advice.

## PySide6 / Qt for Python

- Package: PySide6 6.10.0, PySide6_Essentials 6.10.0, PySide6_Addons 6.10.0.
- License declared by wheel metadata: LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only.
- Official docs: https://doc.qt.io/qtforpython-6
- Source: https://code.qt.io/cgit/pyside/pyside-setup.git/
- Distribution method: dynamic DLLs and Python extension modules collected by PyInstaller.
- Movaura does not intentionally statically link Qt.

## Qt runtime

- Version: Qt 6.10.0 runtime files bundled by PySide6 wheels.
- License: module-dependent; Qt documents LGPLv3/GPLv3/commercial options and GPL-only modules separately.
- Official licensing page: https://doc.qt.io/qt-6/licensing.html
- LGPL obligations overview: https://www.qt.io/development/open-source-lgpl-obligations
- Distribution note: Qt DLLs are separate files inside `_internal/PySide6` in the standalone build, allowing replacement/debugging review consistent with LGPL planning.

## shiboken6

- Package: shiboken6 6.10.0.
- License declared by wheel metadata: LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only.
- Official docs: https://doc.qt.io/qtforpython/shiboken6
- Source: https://code.qt.io/cgit/pyside/pyside-setup.git/

## Python runtime

- Runtime: Python 3.12.x bundled by PyInstaller.
- License: Python Software Foundation License.
- Official license docs: https://docs.python.org/3/license.html

## pywin32

- Package: pywin32 311.
- Project: https://github.com/mhammond/pywin32
- Used for Win32 desktop integration.

## FFmpeg

- FFmpeg is used for optional video optimization.
- See `licenses/ffmpeg/` and `docs/FFMPEG_LGPL_REVIEW.md`.
- Commercial builds must continue using LGPL-clean FFmpeg without `--enable-gpl` or `--enable-nonfree`.

## LGPL planning notes

- Qt/PySide6 libraries are distributed dynamically, not statically linked by project code.
- License notices are included under `licenses/` and are packaged by `scripts/build_standalone.ps1`.
- A final commercial release should keep exact component versions, source links, license texts/notices, and a replacement/debugging policy for LGPL components.
- This project should receive professional legal review before paid distribution.
