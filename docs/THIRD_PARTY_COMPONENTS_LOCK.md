# Third-party components lock

Status: `TECHNICAL LOCK PARTIAL`

This file records components known in the current build path. It is not a legal opinion.

| Component | Version | License | Official URL | Source URL | Link form | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Python | 3.12.13 | PSF License | https://www.python.org/ | https://github.com/python/cpython | embedded runtime via PyInstaller | Include full license text before final Store release. |
| PySide6 | 6.10.0 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only | https://doc.qt.io/qtforpython-6/ | https://download.qt.io/official_releases/QtForPython/pyside6/ | dynamic DLL/modules in package | LGPL technical compliance prepared; legal review required. |
| PySide6_Addons | 6.10.0 | Qt module-dependent | https://doc.qt.io/qtforpython-6/ | https://download.qt.io/official_releases/QtForPython/pyside6/ | dynamic DLL/modules in package | Inventory generated from final artifact required. |
| PySide6_Essentials | 6.10.0 | Qt module-dependent | https://doc.qt.io/qtforpython-6/ | https://download.qt.io/official_releases/QtForPython/pyside6/ | dynamic DLL/modules in package | Inventory generated from final artifact required. |
| shiboken6 | 6.10.0 | LGPL/GPL options | https://doc.qt.io/qtforpython-6/ | https://download.qt.io/official_releases/QtForPython/pyside6/ | dynamic DLL/modules in package | Required by PySide6. |
| pywin32 | 311 | Python-style open source license | https://github.com/mhammond/pywin32 | https://github.com/mhammond/pywin32 | Python extension modules | Include license text before final release. |
| PyInstaller | 6.20.0 | GPL with bootloader exception | https://pyinstaller.org/ | https://github.com/pyinstaller/pyinstaller | build tool/bootloader | Verify bootloader notice in final legal review. |
| FFmpeg | N-124986-g631ac6d055-20260612 | LGPL-oriented build claimed by configuration | https://ffmpeg.org/ | https://ffmpeg.org/download.html | shared binaries in package | Not fully locked to immutable archive yet. |

## Required final action

Generate final inventories from:

- `release/reports/standalone-file-inventory.csv`
- `release/reports/msix-file-inventory.csv`
- `release/reports/standalone-sbom.json`
- `release/reports/msix-sbom.json`

Then update this file with final hashes and exact redistributed files.
