# Movaura Native Host

This is the experimental Win32 desktop-host layer for Movaura. It is a C ABI
DLL so Python can call it through `ctypes` without binding the project to one
Python version.

## Why This Exists

On some Windows 11 Explorer layouts, `SHELLDLL_DefView` lives directly under
`Progman` and no desktop-sized `WorkerW` exists. In that state, PySide6 plus
`SetParent` can attach windows, but they either render above icons or remain
hidden behind Explorer's icon host.

This module moves the host detection and attach logic into native Win32 code so
we can continue experimenting closer to the shell without rewriting the whole
engine.

## Build

From a "Developer PowerShell for VS" or another shell with MSVC and CMake:

```powershell
cd <pasta-do-projeto>\Movaura\native_host
cmake -S . -B build -G "Visual Studio 17 2022" -A x64
cmake --build build --config Release
```

Expected DLL:

```text
<pasta-do-projeto>\Movaura\native_host\bin\movaura_native_host.dll
```

## Test From Python

```powershell
cd <pasta-do-projeto>\Movaura
python app.py --native-diagnose
```

If the DLL is not built yet, the command prints the missing expected path.

## Current Native API

- `nw_probe_desktop`: native Explorer/WorkerW/Progman probe.
- `nw_send_workerw_messages`: sends the known `0x052C` WorkerW messages.
- `nw_attach_to_workerw_after_defview`: attaches a child window only to the
  safe `WorkerW after DefView` topology.

## Design Rule

The native layer must stay conservative. It should not force tiny WorkerW
windows into fake desktop hosts for automatic mode, because testing showed that
those become ordinary windows above the icons rather than true wallpaper
layers.
