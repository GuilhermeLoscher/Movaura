FFmpeg Compliance Folder

This folder is included with Movaura builds so users and reviewers can see which
FFmpeg component is bundled and under which license.

The commercial build uses an LGPL shared FFmpeg build in `tools/ffmpeg`.
The bundled `tools/ffmpeg/README.txt` must continue to show no `--enable-gpl`
and no `--enable-nonfree`.

For every public commercial release, keep this folder updated with:

1. The FFmpeg license text.
2. The exact source URL or source archive.
3. The build configuration.
4. A notice in the app and EULA mentioning FFmpeg.
5. Confirmation that the build does not use --enable-gpl or --enable-nonfree.
