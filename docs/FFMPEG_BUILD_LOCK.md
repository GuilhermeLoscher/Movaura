# FFmpeg build lock

Status: NOT READY - LICENSE BLOCKERS.

The current package still needs an immutable FFmpeg artifact/source lock before commercial release.

- Version: N-124986-g631ac6d055-20260612
- Commit: 631ac6d055
- Archive SHA-256: PENDING
- Audit status: NOT READY - LICENSE BLOCKERS

See `third_party/ffmpeg/LOCK.json` and `release/compliance/ffmpeg/ffmpeg-audit.json`.

## Official sources checked

- FFmpeg legal/license documentation: https://ffmpeg.org/legal.html
- FFmpeg license documentation snapshot: https://ffmpeg.org/doxygen/7.0/md_LICENSE.html

## Release blocker

The current audit found a real FFmpeg binary and recorded its configuration and file hashes, but the original archive URL, original archive SHA-256, provider commit and corresponding source archive are still pending.
The current `master-latest` reference is not acceptable for a final commercial release because it is not an immutable provenance lock.
