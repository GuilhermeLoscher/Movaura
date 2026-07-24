# LGPL and MSIX technical assessment

Status: OWNER DECISION REQUIRED.

This is a technical assessment, not legal advice. MSIX packages are installed into protected app package locations and are signature-bound. That can complicate the user's ability to replace LGPL libraries with modified versions without rebuilding/repackaging the application.

Options for owner/legal review:

1. Qt Community/LGPLv3: keep DLLs separate, provide notices/source/rebuild materials, and have counsel confirm the MSIX replacement/relink strategy.
2. Qt commercial license: obtain and keep proof of license coverage for distributed Qt modules.
3. Framework replacement: analyze only if Qt obligations cannot be satisfied.

Security constraints: do not load DLLs from the current directory, global PATH, user-writable untrusted folders, or unsigned paths.

## Official sources checked

- Qt licensing: https://doc.qt.io/qt-6/licensing.html
- Qt for Python commercial distribution guidance: https://doc.qt.io/qtforpython-6.10/commercial/index.html
- Microsoft MSIX package signing: https://learn.microsoft.com/en-us/windows/msix/package/signing-package-overview
- Microsoft MSIX package identity/runtime context: https://learn.microsoft.com/en-us/windows/msix/detect-package-identity

## Technical conclusion

No secure implementation was added to allow loading replacement Qt DLLs from user-writable locations. That would increase DLL search-order and tampering risk.
For a Store/MSIX commercial release, the owner must choose either a legally reviewed LGPLv3 compliance strategy with reproducible rebuild/repackage materials, or a Qt commercial license path.
