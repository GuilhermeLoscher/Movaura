# FFmpeg LGPL review

Status: READY FOR PROFESSIONAL LEGAL REVIEW

Movaura uses a pinned BtbN LGPL shared build candidate for local media handling.

- Provider release: https://github.com/BtbN/FFmpeg-Builds/releases/tag/autobuild-2026-06-30-13-34
- Artifact: ffmpeg-N-125365-g9a01c1cb6a-win64-lgpl-shared.zip
- Artifact SHA-256: 52d25fc4711078112ba622d07601f183371af43e2d93cbb6e5eab3e1c05387cb
- FFmpeg commit: 9a01c1cb6a

The build configuration does not include `--enable-gpl`, `--enable-nonfree`, `--enable-libx264`, `--enable-libx265`, or `--enable-libfdk-aac`.
External libraries and codec/patent obligations remain subject to professional review.
