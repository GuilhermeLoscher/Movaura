# Movaura final audit baseline

Date: 2026-07-23

## Repository safety gate

- Active directory: `C:\NovaWall\Movaura`
- Required branch: `migration/pyside6`
- Current branch observed: `migration/pyside6`
- Remote observed: `https://github.com/GuilhermeLoscher/Movaura.git`
- Repository root observed: `C:/NovaWall/Movaura`
- Protected backup project: `C:\NovaWall\Movaura Beta`
- `Movaura Beta` inside repository: `false`
- Reparse points/junctions observed under `C:\NovaWall`: none reported
- Reparse points/junctions observed inside repository: none reported
- Git status before this audit phase: clean on `migration/pyside6...origin/migration/pyside6`

## Initial commit

- Commit-base audited: `fa94245d7a2b1dde9eb0bec1a458d41db0a7001f`
- Local branch tip before new corrections: `fa94245`

## Recent commits

```text
fa94245 Report PySide6 migration validation
bcf5efa Document PySide6 third-party licensing
67f8b4f Add PySide6 residue checks
a023076 Migrate Qt bindings to PySide6
3b7196e Inventory Qt usage for PySide6 migration
81f91e2 Audit Microsoft Store release compliance
f6c9c78 Validate standalone and MSIX release flow
d7a689e Guarantee AI history failure termination
22ca589 Harden AI generation lifecycle
20c354e Harden AI generation workflow
```

## Submodules

- `.gitmodules`: absent.
- `git submodule status`: not executed successfully because the local Git installation could not find Unix helper commands (`basename`, `sed`, `git-sh-setup`).
- Impact: no submodule configuration is present, but the command failure is recorded as a local tooling issue.

## Environment

- Windows product name observed: Windows 10 Pro
- Windows version observed: 2009
- OS build observed: 26200
- Architecture observed: 64 bits
- PowerShell: 5.1.26100.8875
- Python: 3.12.13
- PySide6: 6.10.0
- shiboken6: 6.10.0
- pywin32: 311
- PyInstaller: 6.20.0
- Windows SDK candidates observed: 10.0.28000.0, 10.0.26100.0, 10.0.22621.0 and older kits
- WACK help/version query: not executed because `appcert.exe` required elevation for that query

## FFmpeg baseline

Bundled executable observed:

- `tools/ffmpeg/bin/ffmpeg.exe`

Version output:

```text
ffmpeg version N-124986-g631ac6d055-20260612
```

Configuration summary:

```text
--enable-shared --disable-static --disable-libx264 --disable-libx265
```

Risk:

- The current FFmpeg is a dated git snapshot build, not a fully locked release archive with original ZIP hash.
- Commercial release remains blocked until source/build lock and legal review are completed.

## Large local artifacts observed

These are ignored or local release/data artifacts, not necessarily intended for Git:

- `msix/Movaura-0.9.0.0.msix` - 241,553,292 bytes
- `installer/Movaura-Setup-0.9.0.exe` - 154,721,976 bytes
- `tools/ffmpeg/bin/avfilter-11.dll` - 90,659,328 bytes
- `tools/ffmpeg/bin/avcodec-62.dll` - 70,587,904 bytes
- `data/optimized_videos/6a670451c7c3d2191161_1600x900_30fps.mp4` - 37,194,409 bytes
- `data/optimized_videos/66aa4738e383eedc2c98_1280x720_15fps.mp4` - 23,373,240 bytes

## Versioned native binaries

- `native_compositor_app/bin/movaura_native_compositor.exe`
- `native_host_app/bin/movaura_host_probe.exe`
- `native_host/bin/movaura_native_host.dll`
- `native_host/novawall_native_host.dll`

Native binary SHA-256 values were collected during the baseline command output and should be regenerated in release reports for every final build.

## Potential secrets scan

No real service role, private key or JWT token was found in source scan.

Expected placeholders/documentation found:

- `SUA_ANON_KEY`
- error text mentioning anon key/RLS

Local test certificate note:

- `release/msix/Movaura-TestCertificate.cer` exists as a local ignored test certificate for developer installation.
- No PFX/private key should be committed.

## Ignored/generated content observed

- `__pycache__` directories exist locally.
- `build/`, `dist/`, `release/`, `tools/`, generated data and installer/MSIX outputs are ignored by `.gitignore`.

## Baseline conclusion

Repository safety gate passed for continuing work on `C:\NovaWall\Movaura`.

Status after baseline: `READY FOR CI REVIEW` only after the new CI/build corrections pass locally and are pushed. This is not a Store approval.
