# FFmpeg build lock

Status: `PARTIAL - NOT STORE FINAL`

## Bundled binary

- Path: `tools/ffmpeg/bin/ffmpeg.exe`
- Observed version: `N-124986-g631ac6d055-20260612`
- Configuration includes:
  - `--enable-shared`
  - `--disable-static`
  - `--disable-libx264`
  - `--disable-libx265`

## Current technical audit

The script `scripts/audit_ffmpeg.py` validates:

- `ffmpeg.exe -version`;
- blocked flags:
  - `--enable-gpl`
  - `--enable-nonfree`
  - `--enable-libx264`
  - `--enable-libx265`
- required flags:
  - `--enable-shared`
  - `--disable-static`
  - `--disable-libx264`
  - `--disable-libx265`
- SHA-256 hashes of files in `tools/ffmpeg`.

## Missing for final Store submission

- exact upstream ZIP/source archive URL;
- SHA-256 of original downloaded archive;
- immutable vendor release identifier;
- source offer/link reviewed by legal counsel;
- confirmation that every enabled external library is compatible with the intended commercial distribution.

Status cannot be raised above `READY FOR PARTNER CENTER IDENTITY` until FFmpeg is fully locked and legally reviewed.
