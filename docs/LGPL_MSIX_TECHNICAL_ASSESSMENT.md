# LGPL and MSIX technical assessment

Status: READY FOR PROFESSIONAL LEGAL REVIEW

This is a technical assessment, not legal advice. MSIX packages are installed into protected package locations and are signature-bound. That can complicate the user ability to replace LGPL libraries without rebuilding or repackaging. The app should not load DLLs from writable or untrusted paths as a workaround because that creates DLL search-order and tampering risk.

## Real technical checks performed

- Confirmed standalone Qt/PySide6 files are physically distributed as separate DLL/plugin files, not statically linked into `Movaura.exe`.
- Removed detected Qt Virtual Keyboard files from the local standalone artifact and added a build-time guard to fail if they are collected again.
- Added official GPL/LGPL license texts to the local license payload.
- Updated CI validation to fail on missing FFmpeg lock fields, floating FFmpeg artifact URLs, missing required license texts, and GPL-only Qt VirtualKeyboard artifacts.

## Owner/legal decision still required

1. Use Qt/PySide6 under LGPLv3 with a documented source/rebuild/repackage path and notices.
2. Or obtain a Qt commercial license and preserve proof of coverage for all distributed modules.
3. Confirm whether MSIX distribution plus supplied rebuild/repackage materials satisfies LGPLv3 for the target distribution model.

## Security decision

No code was added to load replacement Qt DLLs from current directory, PATH, or user-writable folders. That keeps the package safer, but means the LGPL replacement/relink path must be handled by documented rebuild/repackage materials or commercial licensing.
