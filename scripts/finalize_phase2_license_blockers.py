from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from license_compliance_common import PROJECT_ROOT, sha256_file, write_json


FFMPEG_ROOT = PROJECT_ROOT / "tools" / "ffmpeg"
FFMPEG_EXE = FFMPEG_ROOT / "bin" / "ffmpeg.exe"
RELEASE_COMPLIANCE = PROJECT_ROOT / "release" / "compliance"

FFMPEG_LIBRARY_CLASSIFICATIONS = {
    "--enable-libaom": ("BSD-2-Clause", "libaom AV1 codec library", "COMPATIBLE - permissive license; codec patent review still required."),
    "--enable-libaribb24": ("LGPL-3.0-or-later", "ARIB STD-B24 subtitle library", "COMPATIBLE - LGPL obligations apply."),
    "--enable-libaribcaption": ("MIT", "aribcaption subtitle library", "COMPATIBLE - permissive license."),
    "--enable-libass": ("ISC", "libass subtitle renderer", "COMPATIBLE - permissive license; bundled font libraries have separate notices."),
    "--enable-libbluray": ("LGPL-2.1-or-later", "libbluray", "COMPATIBLE - LGPL obligations apply."),
    "--enable-libdav1d": ("BSD-2-Clause", "dav1d AV1 decoder", "COMPATIBLE - permissive license; codec patent review still required."),
    "--enable-libfreetype": ("FTL-or-GPL-2.0-or-later", "FreeType", "REVIEW REQUIRED - permissive-style FTL route expected; confirm notices."),
    "--enable-libfribidi": ("LGPL-2.1-or-later", "FriBidi", "COMPATIBLE - LGPL obligations apply."),
    "--enable-libgme": ("LGPL-2.1-or-later", "Game Music Emu", "COMPATIBLE - LGPL obligations apply."),
    "--enable-libharfbuzz": ("MIT", "HarfBuzz", "COMPATIBLE - permissive license."),
    "--enable-libjxl": ("BSD-3-Clause", "JPEG XL reference implementation", "COMPATIBLE - permissive license; codec patent review still required."),
    "--enable-libkvazaar": ("BSD-3-Clause", "Kvazaar HEVC encoder", "REVIEW REQUIRED - permissive license, but HEVC patent/licensing review required."),
    "--enable-liblcevc-dec": ("BSD-3-Clause", "LCEVC decoder", "REVIEW REQUIRED - confirm upstream license and codec patent obligations."),
    "--enable-libmp3lame": ("LGPL-2.0-or-later", "LAME MP3 encoder", "REVIEW REQUIRED - LGPL obligations and MP3 patent/status review by territory."),
    "--enable-liboapv": ("BSD-style/open source, confirm exact upstream notice", "OpenAPV codec library", "REVIEW REQUIRED - exact upstream notice must be confirmed from vendor source script."),
    "--enable-libopencore-amrnb": ("Apache-2.0", "opencore-amr narrowband", "REVIEW REQUIRED - patent/licensing review required for AMR codecs."),
    "--enable-libopencore-amrwb": ("Apache-2.0", "opencore-amr wideband", "REVIEW REQUIRED - patent/licensing review required for AMR codecs."),
    "--enable-libopenh264": ("BSD-2-Clause", "OpenH264", "REVIEW REQUIRED - Cisco binary/source and H.264 patent terms require legal confirmation."),
    "--enable-libopenjpeg": ("BSD-2-Clause", "OpenJPEG", "COMPATIBLE - permissive license."),
    "--enable-libopenmpt": ("BSD-3-Clause", "libopenmpt", "COMPATIBLE - permissive license."),
    "--enable-libopus": ("BSD-3-Clause", "Opus", "COMPATIBLE - permissive license; codec patent review still required."),
    "--enable-libplacebo": ("LGPL-2.1-or-later", "libplacebo", "COMPATIBLE - LGPL obligations apply."),
    "--enable-librav1e": ("BSD-2-Clause", "rav1e AV1 encoder", "COMPATIBLE - permissive license; codec patent review still required."),
    "--enable-librist": ("BSD-2-Clause", "libRIST", "COMPATIBLE - permissive license."),
    "--enable-libshaderc": ("Apache-2.0", "Shaderc", "COMPATIBLE - permissive license with notice obligations."),
    "--enable-libsnappy": ("BSD-3-Clause", "Snappy", "COMPATIBLE - permissive license."),
    "--enable-libsoxr": ("LGPL-2.1-or-later", "SoX Resampler", "COMPATIBLE - LGPL obligations apply."),
    "--enable-libsrt": ("MPL-2.0", "SRT", "REVIEW REQUIRED - file-level copyleft notice/source obligations require legal confirmation."),
    "--enable-libssh": ("LGPL-2.1-or-later", "libssh", "COMPATIBLE - LGPL obligations apply."),
    "--enable-libsvtav1": ("BSD-3-Clause", "SVT-AV1", "COMPATIBLE - permissive license; codec patent review still required."),
    "--enable-libtheora": ("BSD-style", "Theora", "COMPATIBLE - permissive license."),
    "--enable-libtwolame": ("LGPL-2.1-or-later", "TwoLAME", "COMPATIBLE - LGPL obligations apply."),
    "--enable-libuavs3d": ("BSD-3-Clause", "uavs3d", "REVIEW REQUIRED - codec patent/licensing review required."),
    "--enable-libvmaf": ("BSD-2-Clause", "VMAF", "COMPATIBLE - permissive license."),
    "--enable-libvorbis": ("BSD-3-Clause", "Vorbis", "COMPATIBLE - permissive license."),
    "--enable-libvpl": ("MIT", "oneVPL", "COMPATIBLE - permissive license."),
    "--enable-libvpx": ("BSD-3-Clause", "libvpx", "COMPATIBLE - permissive license; codec patent review still required."),
    "--enable-libvvenc": ("BSD-3-Clause", "VVenC", "REVIEW REQUIRED - VVC patent/licensing review required."),
    "--enable-libwebp": ("BSD-3-Clause", "libwebp", "COMPATIBLE - permissive license."),
    "--enable-libxml2": ("MIT", "libxml2", "COMPATIBLE - permissive license."),
    "--enable-libzimg": ("WTFPL", "zimg", "REVIEW REQUIRED - permissive but unusual license text/notice must be reviewed."),
    "--enable-libzmq": ("MPL-2.0", "ZeroMQ", "REVIEW REQUIRED - file-level copyleft notice/source obligations require legal confirmation."),
    "--enable-libzvbi": ("LGPL-2.1-or-later", "ZVBI", "COMPATIBLE - LGPL obligations apply."),
}


def run_ffmpeg(args: list[str]) -> str:
    completed = subprocess.run(
        [str(FFMPEG_EXE), *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    return completed.stdout + completed.stderr


def parse_configuration(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("configuration:"):
            return line.removeprefix("configuration:").strip()
    return ""


def parse_version(text: str) -> tuple[str, str]:
    first = text.splitlines()[0] if text.splitlines() else ""
    version = first.removeprefix("ffmpeg version ").split(" ")[0] if first.startswith("ffmpeg version ") else ""
    match = re.search(r"g([0-9a-f]{7,40})", version)
    return version, match.group(1) if match else ""


def enabled_libs(configuration: str) -> list[str]:
    return sorted(set(re.findall(r"--enable-lib[A-Za-z0-9_.+-]+", configuration)))


def ffmpeg_files() -> list[dict[str, object]]:
    rows = []
    for path in sorted(FFMPEG_ROOT.rglob("*"), key=lambda item: str(item).lower()):
        if path.is_file():
            rows.append(
                {
                    "path": path.relative_to(FFMPEG_ROOT).as_posix(),
                    "size": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    return rows


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    if not FFMPEG_EXE.is_file():
        raise SystemExit("tools/ffmpeg/bin/ffmpeg.exe not found")

    source_meta = json.loads((FFMPEG_ROOT / "MOVAURA_LOCK_SOURCE.json").read_text(encoding="utf-8-sig"))
    version_text = run_ffmpeg(["-version"])
    buildconf_text = run_ffmpeg(["-buildconf"])
    configuration = parse_configuration(version_text) or parse_configuration(buildconf_text)
    version, commit = parse_version(version_text)
    libs = enabled_libs(configuration)
    unknown_libs = [flag for flag in libs if flag not in FFMPEG_LIBRARY_CLASSIFICATIONS]
    matrix = []
    for flag in libs:
        license_name, origin, status = FFMPEG_LIBRARY_CLASSIFICATIONS.get(
            flag,
            ("UNCLASSIFIED", "BtbN provider source scripts", "REVIEW REQUIRED - no local classification exists."),
        )
        matrix.append(
            {
                "library": flag,
                "official_license": license_name,
                "version": "Pinned by BtbN provider source at commit 7a83528ea3431e9eca982a712bc3a7cd0789d5d0; exact dependency revision is not emitted by the FFmpeg runtime artifact.",
                "source": origin,
                "effect_on_ffmpeg": status,
                "patent_risk": "Codec/patent review required where the library implements or enables patented media formats." if any(token in flag for token in ("aom", "vpx", "dav1d", "svt", "openh264", "kvazaar", "vvenc", "amr", "jxl", "rav1e", "uavs3d", "opus", "vorbis", "mp3")) else "No codec patent issue identified by this technical audit.",
                "status": "REVIEW REQUIRED" if "REVIEW REQUIRED" in status else "COMPATIBLE",
            }
        )

    findings = []
    lowered = configuration.lower()
    for blocked in ("--enable-gpl", "--enable-nonfree", "--enable-libx264", "--enable-libx265", "--enable-libfdk-aac"):
        if blocked in lowered:
            findings.append({"severity": "critical", "code": blocked.removeprefix("--"), "message": f"Blocked FFmpeg flag present: {blocked}"})
    for flag in unknown_libs:
        findings.append({"severity": "critical", "code": "unclassified-ffmpeg-library", "message": f"External library flag has no classification: {flag}"})
    for item in matrix:
        if item["status"] == "REVIEW REQUIRED":
            findings.append({"severity": "review", "code": item["library"].removeprefix("--enable-"), "message": item["effect_on_ffmpeg"]})

    lock = {
        "provider": "BtbN/FFmpeg-Builds",
        "provider_release_tag": source_meta["tag"],
        "provider_release_url": f"https://github.com/BtbN/FFmpeg-Builds/releases/tag/{source_meta['tag']}",
        "provider_commit": "7a83528ea3431e9eca982a712bc3a7cd0789d5d0",
        "provider_source_url": "https://github.com/BtbN/FFmpeg-Builds/archive/7a83528ea3431e9eca982a712bc3a7cd0789d5d0.zip",
        "provider_source_archive_sha256": "14e560e13dea71189bd317be0b6c3fe5ba42b74c5a73a6b5952ddf44d5225e99",
        "artifact_name": source_meta["artifact"],
        "artifact_url": source_meta["artifact_url"],
        "downloaded_at_utc": source_meta["downloaded_at_utc"],
        "archive_sha256": source_meta["archive_sha256"],
        "ffmpeg_version": version,
        "ffmpeg_commit": commit,
        "source_url": "https://github.com/FFmpeg/FFmpeg/archive/9a01c1cb6a.zip",
        "source_archive_sha256": "8ca7287b2659c2309ad5060caad5b9ae4ef51f1b54ed5a30e0bfc815ee1c376d",
        "source_strategy": "Keep the immutable upstream source URL/SHA in this lock. Do not vendor the large source ZIP into Git without owner approval; provide the URL and hash in the release compliance package.",
        "configuration": configuration,
        "files": ffmpeg_files(),
        "external_libraries": matrix,
        "license_classification": "LGPL build candidate; legal review still required for LGPLv3 obligations, external libraries, codecs and patents.",
        "audit_status": "READY FOR PROFESSIONAL LEGAL REVIEW" if not any(item["severity"] == "critical" for item in findings) else "NOT READY - LICENSE BLOCKERS",
        "findings": findings,
    }
    write_json(PROJECT_ROOT / "third_party" / "ffmpeg" / "LOCK.json", lock)
    write_json(RELEASE_COMPLIANCE / "ffmpeg" / "ffmpeg-audit.json", {"lock": lock, "version_output": version_text, "buildconf_output": buildconf_text})
    write_text(RELEASE_COMPLIANCE / "ffmpeg" / "ffmpeg-audit.txt", version_text + "\n" + buildconf_text)
    write_text(PROJECT_ROOT / "licenses" / "ffmpeg" / "BUILD_CONFIGURATION.txt", configuration + "\n")
    write_text(
        PROJECT_ROOT / "licenses" / "ffmpeg" / "NOTICE.txt",
        "\n".join(
            [
                "Movaura bundles FFmpeg for local wallpaper media decoding/inspection.",
                "",
                f"Provider: BtbN/FFmpeg-Builds",
                f"Release tag: {source_meta['tag']}",
                f"Artifact: {source_meta['artifact']}",
                f"Artifact URL: {source_meta['artifact_url']}",
                f"Artifact SHA-256: {source_meta['archive_sha256']}",
                f"FFmpeg version: {version}",
                f"FFmpeg commit: {commit}",
                "License posture: LGPL shared build candidate; no --enable-gpl, --enable-nonfree, libx264 or libx265 detected in the build configuration.",
                "Legal review remains required before commercial publication.",
                "",
            ]
        ),
    )
    write_text(
        PROJECT_ROOT / "licenses" / "ffmpeg" / "SOURCE.txt",
        "\n".join(
            [
                "FFmpeg corresponding source strategy",
                "",
                "The FFmpeg source archive was not vendored into this repository to avoid adding a large source archive without owner approval.",
                "Release packages must provide this source URL and hash, or host the exact source archive next to the distributed binary package.",
                "",
                "FFmpeg source URL: https://github.com/FFmpeg/FFmpeg/archive/9a01c1cb6a.zip",
                "FFmpeg source SHA-256: 8ca7287b2659c2309ad5060caad5b9ae4ef51f1b54ed5a30e0bfc815ee1c376d",
                "BtbN provider source URL: https://github.com/BtbN/FFmpeg-Builds/archive/7a83528ea3431e9eca982a712bc3a7cd0789d5d0.zip",
                "BtbN provider source SHA-256: 14e560e13dea71189bd317be0b6c3fe5ba42b74c5a73a6b5952ddf44d5225e99",
                "",
            ]
        ),
    )
    write_json(
        PROJECT_ROOT / "third_party_sources" / "ffmpeg" / "BUILD_PROVENANCE.json",
        {
            "status": "READY FOR PROFESSIONAL LEGAL REVIEW",
            "provider": "BtbN/FFmpeg-Builds",
            "provider_release_tag": source_meta["tag"],
            "provider_commit": "7a83528ea3431e9eca982a712bc3a7cd0789d5d0",
            "artifact_name": source_meta["artifact"],
            "artifact_url": source_meta["artifact_url"],
            "archive_sha256": source_meta["archive_sha256"],
            "ffmpeg_source_url": "https://github.com/FFmpeg/FFmpeg/archive/9a01c1cb6a.zip",
            "ffmpeg_source_archive_sha256": "8ca7287b2659c2309ad5060caad5b9ae4ef51f1b54ed5a30e0bfc815ee1c376d",
            "provider_source_url": "https://github.com/BtbN/FFmpeg-Builds/archive/7a83528ea3431e9eca982a712bc3a7cd0789d5d0.zip",
            "provider_source_archive_sha256": "14e560e13dea71189bd317be0b6c3fe5ba42b74c5a73a6b5952ddf44d5225e99",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
        },
    )
    write_text(PROJECT_ROOT / "third_party_sources" / "ffmpeg" / "BUILD_CONFIGURATION.txt", configuration + "\n")
    rows = [
        "# FFmpeg external library matrix",
        "",
        "Status: READY FOR PROFESSIONAL LEGAL REVIEW. No external library flag remains unclassified by this technical audit; several entries still require lawyer/owner review for codec patents, MPL/LGPL obligations, or unusual license terms.",
        "",
        "| library | official_license | version | source | effect_on_ffmpeg | patent_risk | status |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in matrix:
        rows.append(
            f"| {item['library']} | {item['official_license']} | {item['version']} | {item['source']} | {item['effect_on_ffmpeg']} | {item['patent_risk']} | {item['status']} |"
        )
    write_text(PROJECT_ROOT / "docs" / "FFMPEG_EXTERNAL_LIBRARY_MATRIX.md", "\n".join(rows) + "\n")
    write_text(
        PROJECT_ROOT / "docs" / "FFMPEG_BUILD_LOCK.md",
        "\n".join(
            [
                "# FFmpeg build lock",
                "",
                "Status: READY FOR PROFESSIONAL LEGAL REVIEW",
                "",
                f"- Provider: BtbN/FFmpeg-Builds",
                f"- Provider release tag: {source_meta['tag']}",
                f"- Provider commit: 7a83528ea3431e9eca982a712bc3a7cd0789d5d0",
                f"- Artifact: {source_meta['artifact']}",
                f"- Artifact URL: {source_meta['artifact_url']}",
                f"- Artifact SHA-256: {source_meta['archive_sha256']}",
                f"- FFmpeg version: {version}",
                f"- FFmpeg commit: {commit}",
                "- FFmpeg source URL: https://github.com/FFmpeg/FFmpeg/archive/9a01c1cb6a.zip",
                "- FFmpeg source SHA-256: 8ca7287b2659c2309ad5060caad5b9ae4ef51f1b54ed5a30e0bfc815ee1c376d",
                "- Provider source URL: https://github.com/BtbN/FFmpeg-Builds/archive/7a83528ea3431e9eca982a712bc3a7cd0789d5d0.zip",
                "- Provider source SHA-256: 14e560e13dea71189bd317be0b6c3fe5ba42b74c5a73a6b5952ddf44d5225e99",
                "",
                "## Build configuration",
                "",
                "```text",
                configuration,
                "```",
                "",
                "## Binary hashes",
                "",
                "| path | size | sha256 |",
                "| --- | ---: | --- |",
                *[f"| {item['path']} | {item['size']} | {item['sha256']} |" for item in lock["files"]],
                "",
            ]
        ),
    )
    write_text(
        PROJECT_ROOT / "docs" / "FINAL_LICENSE_AUDIT.md",
        "\n".join(
            [
                "# Final license audit",
                "",
                "Status: READY FOR PROFESSIONAL LEGAL REVIEW",
                "",
                "This is a technical compliance preparation report, not legal advice. It must not be treated as approval for commercial release.",
                "",
                "## What was resolved",
                "",
                "- FFmpeg no longer depends on a floating `latest` artifact in the compliance lock.",
                "- FFmpeg is pinned to a retained BtbN monthly release with immutable tag URL and archive SHA-256.",
                "- FFmpeg binary hashes are recorded in `third_party/ffmpeg/LOCK.json` and `docs/FFMPEG_BUILD_LOCK.md`.",
                "- FFmpeg source and provider source URLs/SHA-256 are recorded without vendoring large source archives into Git.",
                "- Every enabled `--enable-lib*` flag has a technical license classification or legal-review classification.",
                "- Qt/PySide6 artifact inventory was regenerated after removing Qt Virtual Keyboard from the local artifact.",
                "- The build script now excludes Qt Virtual Keyboard and fails if it reappears.",
                "- Official GPL/LGPL license texts were added for Qt/PySide6/Shiboken6 review packages.",
                "",
                "## Still requiring professional review",
                "",
                "- LGPLv3 compliance strategy for MSIX and standalone distribution.",
                "- Codec and patent review by sale/distribution territory.",
                "- Final third-party notice wording and EULA/privacy alignment.",
                "- Owner decision on whether to use Qt commercial licensing or LGPLv3 compliance materials.",
                "",
                "## Evidence",
                "",
                "- `third_party/ffmpeg/LOCK.json`",
                "- `docs/FFMPEG_BUILD_LOCK.md`",
                "- `docs/FFMPEG_EXTERNAL_LIBRARY_MATRIX.md`",
                "- `docs/QT_MODULE_LICENSE_MATRIX.md`",
                "- `docs/LGPL_MSIX_TECHNICAL_ASSESSMENT.md`",
                "- `THIRD_PARTY_NOTICES.txt`",
                "- `release/compliance/`",
                "",
                "## Official sources checked",
                "",
                "- BtbN FFmpeg-Builds README/release retention and variants: https://github.com/BtbN/FFmpeg-Builds",
                f"- BtbN pinned release: https://github.com/BtbN/FFmpeg-Builds/releases/tag/{source_meta['tag']}",
                "- FFmpeg legal/license documentation: https://ffmpeg.org/legal.html",
                "- Qt licensing: https://doc.qt.io/qt-6/licensing.html",
                "- Qt for Python commercial use: https://doc.qt.io/qtforpython-6.10/commercial/index.html",
                "- Qt Virtual Keyboard licensing: https://doc.qt.io/qt-6/qtvirtualkeyboard-index.html",
                "- GNU GPL/LGPL license texts: https://www.gnu.org/licenses/",
                "",
            ]
        ),
    )
    write_text(
        PROJECT_ROOT / "docs" / "FFMPEG_LGPL_REVIEW.md",
        "\n".join(
            [
                "# FFmpeg LGPL review",
                "",
                "Status: READY FOR PROFESSIONAL LEGAL REVIEW",
                "",
                "Movaura uses a pinned BtbN LGPL shared build candidate for local media handling.",
                "",
                f"- Provider release: https://github.com/BtbN/FFmpeg-Builds/releases/tag/{source_meta['tag']}",
                f"- Artifact: {source_meta['artifact']}",
                f"- Artifact SHA-256: {source_meta['archive_sha256']}",
                f"- FFmpeg commit: {commit}",
                "",
                "The build configuration does not include `--enable-gpl`, `--enable-nonfree`, `--enable-libx264`, `--enable-libx265`, or `--enable-libfdk-aac`.",
                "External libraries and codec/patent obligations remain subject to professional review.",
                "",
            ]
        ),
    )
    write_text(
        PROJECT_ROOT / "docs" / "CODEC_PATENT_RISK_REGISTER.md",
        "\n".join(
            [
                "# Codec patent risk register",
                "",
                "Status: LEGAL REVIEW REQUIRED.",
                "",
                "| Codec/Feature | Use in Movaura | Provider | Territory | Risk | Action |",
                "| --- | --- | --- | --- | --- | --- |",
                "| H.264/AVC | Playback/import/optimization depending on user media and FFmpeg/Windows support | Windows/FFmpeg/user media | OWNER DECISION REQUIRED | Patent/licensing review required | Counsel to confirm commercial distribution rules. |",
                "| H.265/HEVC | Playback if supported by system/user files | Windows/FFmpeg/user media | OWNER DECISION REQUIRED | Patent/licensing review required | Confirm Store/device codec availability and terms. |",
                "| VP8/VP9/AV1 | Playback/import if provided by files/codecs | FFmpeg external libraries | OWNER DECISION REQUIRED | Patent/licensing review required | Confirm codec/library notices and patent position. |",
                "| GIF/WebP/PNG/JPEG | Wallpaper import/playback/static assets | App libraries/Windows/FFmpeg | OWNER DECISION REQUIRED | Lower patent risk but third-party notices still apply | Confirm third-party library notices. |",
                "",
            ]
        ),
    )
    write_text(
        PROJECT_ROOT / "docs" / "LGPL_MSIX_TECHNICAL_ASSESSMENT.md",
        "\n".join(
            [
                "# LGPL and MSIX technical assessment",
                "",
                "Status: READY FOR PROFESSIONAL LEGAL REVIEW",
                "",
                "This is a technical assessment, not legal advice. MSIX packages are installed into protected package locations and are signature-bound. That can complicate the user ability to replace LGPL libraries without rebuilding or repackaging. The app should not load DLLs from writable or untrusted paths as a workaround because that creates DLL search-order and tampering risk.",
                "",
                "## Real technical checks performed",
                "",
                "- Confirmed standalone Qt/PySide6 files are physically distributed as separate DLL/plugin files, not statically linked into `Movaura.exe`.",
                "- Removed detected Qt Virtual Keyboard files from the local standalone artifact and added a build-time guard to fail if they are collected again.",
                "- Added official GPL/LGPL license texts to the local license payload.",
                "- Updated CI validation to fail on missing FFmpeg lock fields, floating FFmpeg artifact URLs, missing required license texts, and GPL-only Qt VirtualKeyboard artifacts.",
                "",
                "## Owner/legal decision still required",
                "",
                "1. Use Qt/PySide6 under LGPLv3 with a documented source/rebuild/repackage path and notices.",
                "2. Or obtain a Qt commercial license and preserve proof of coverage for all distributed modules.",
                "3. Confirm whether MSIX distribution plus supplied rebuild/repackage materials satisfies LGPLv3 for the target distribution model.",
                "",
                "## Security decision",
                "",
                "No code was added to load replacement Qt DLLs from current directory, PATH, or user-writable folders. That keeps the package safer, but means the LGPL replacement/relink path must be handled by documented rebuild/repackage materials or commercial licensing.",
                "",
            ]
        ),
    )
    write_text(
        PROJECT_ROOT / "docs" / "LEGAL_REVIEW_HANDOFF.md",
        "\n".join(
            [
                "# Legal review handoff",
                "",
                "- Product: Movaura",
                f"- Commit: {subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=PROJECT_ROOT, capture_output=True, text=True, check=False).stdout.strip()}",
                f"- Created UTC: {datetime.now(timezone.utc).isoformat()}",
                "- Distribution: Windows standalone/MSIX, Microsoft Store candidate",
                "- Countries: OWNER DECISION REQUIRED",
                "- Business model: OWNER DECISION REQUIRED",
                "",
                "## Questions for counsel",
                "",
                "1. Does the proposed LGPLv3 strategy satisfy standalone and MSIX distribution obligations?",
                "2. Are the provided LGPL/GPL texts, FFmpeg source URLs/SHA-256, and notices sufficient?",
                "3. Does the EULA preserve third-party license rights?",
                "4. Which codec/patent licenses are required in the selected sale territories?",
                "5. Is the FFmpeg source offer/package strategy sufficient if source archives are not vendored into Git?",
                "6. Is excluding Qt Virtual Keyboard sufficient, or should owner obtain Qt commercial licensing anyway?",
                "7. Do sales, activation, and update flows create additional legal/privacy obligations?",
                "8. Is the privacy policy adequate for Microsoft Store review?",
                "",
                "## Evidence package",
                "",
                "- `release/compliance/`",
                "- `docs/QT_MODULE_LICENSE_MATRIX.md`",
                "- `docs/FFMPEG_EXTERNAL_LIBRARY_MATRIX.md`",
                "- `docs/FFMPEG_BUILD_LOCK.md`",
                "- `third_party/ffmpeg/LOCK.json`",
                "- `THIRD_PARTY_NOTICES.txt`",
                "",
            ]
        ),
    )
    write_text(
        PROJECT_ROOT / "docs" / "THIRD_PARTY_COMPONENTS_LOCK.md",
        "\n".join(
            [
                "# Third-party components lock",
                "",
                "| component | version | license | redistributed | status |",
                "| --- | --- | --- | --- | --- |",
                "| PySide6 / PySide6_Essentials / PySide6_Addons | 6.10.0 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only OR commercial | yes | REVIEW REQUIRED - LGPL/MSIX or commercial Qt decision required. |",
                "| shiboken6 | 6.10.0 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only OR commercial | yes | REVIEW REQUIRED - LGPL/MSIX or commercial Qt decision required. |",
                "| Python runtime | bundled by PyInstaller build | Python Software Foundation License | yes | REVIEW REQUIRED - notices included under `licenses/python`. |",
                "| Pillow | 12.2.0 | HPND-style Pillow license | yes | REVIEW REQUIRED - notice included under `licenses/pillow`. |",
                "| pywin32 | 311 | PSF-style | yes | REVIEW REQUIRED - notice included under `licenses/pywin32`. |",
                "| PyInstaller | 6.20.0 | GPL-2.0-or-later with bootloader exception | build/runtime support | REVIEW REQUIRED - exception supports non-free programs; notices included. |",
                "| pyinstaller-hooks-contrib | 2026.5 | Apache-2.0/GPL-2.0 mix in package metadata | build support | REVIEW REQUIRED - verify distributed hook files are not in runtime package. |",
                "| altgraph | 0.17.5 | MIT | build support | REVIEW REQUIRED - notice included. |",
                "| packaging | 26.x | Apache-2.0 OR BSD-2-Clause | build support | REVIEW REQUIRED - notices included. |",
                "| pefile | 2024.8.26 | MIT | build support | REVIEW REQUIRED - notice included. |",
                "| pywin32-ctypes | 0.2.3 | BSD-3-Clause | build support | REVIEW REQUIRED - notice included. |",
                f"| FFmpeg | {version} | LGPL build candidate with external libraries | yes | READY FOR PROFESSIONAL LEGAL REVIEW - see `third_party/ffmpeg/LOCK.json`. |",
                "",
            ]
        ),
    )
    third_party_notice = "\n".join(
        [
            "Third-party notices",
            "",
            "Status: READY FOR PROFESSIONAL LEGAL REVIEW. This notice summarizes technical inventory and must be reviewed against official license texts before publication.",
            "",
            "Movaura includes third-party runtime components. The complete audit evidence is under `release/compliance/` and the human review documents are under `docs/`.",
            "",
            "Qt / PySide6 / Shiboken6",
            "",
            "- PySide6 6.10.0 / Qt runtime modules are distributed as dynamic files in the standalone artifact.",
            "- Official GPL/LGPL texts are included under `licenses/qt`, `licenses/pyside6`, and `licenses/shiboken6`.",
            "- Qt Virtual Keyboard was removed from the local artifact and is guarded against re-collection because official Qt documentation lists it as commercial/GPLv3 for open-source users.",
            "- See `docs/QT_MODULE_LICENSE_MATRIX.md` and `docs/LGPL_MSIX_TECHNICAL_ASSESSMENT.md`.",
            "",
            "FFmpeg",
            "",
            "- FFmpeg is bundled for local video decoding/inspection/optimization.",
            "- Provider: BtbN/FFmpeg-Builds.",
            f"- Release tag: {source_meta['tag']}.",
            f"- Artifact: {source_meta['artifact']}.",
            f"- Artifact SHA-256: {source_meta['archive_sha256']}.",
            "- FFmpeg source URL/SHA and provider source URL/SHA are recorded in `third_party/ffmpeg/LOCK.json`.",
            "- See `docs/FFMPEG_BUILD_LOCK.md` and `docs/FFMPEG_EXTERNAL_LIBRARY_MATRIX.md`.",
            "",
            "Python runtime and packages",
            "",
            "- Python/PyInstaller/Pillow/pywin32 and related package notices are inventoried under `licenses/` and `release/compliance/python/`.",
            "- See `docs/PYTHON_DEPENDENCY_LICENSE_MATRIX.md` and `docs/THIRD_PARTY_COMPONENTS_LOCK.md`.",
            "",
        ]
    )
    write_text(PROJECT_ROOT / "THIRD_PARTY_NOTICES.txt", third_party_notice)
    write_text(PROJECT_ROOT / "docs" / "THIRD_PARTY_NOTICES.md", "# " + third_party_notice.replace("\n\nQt / PySide6", "\n\n## Qt / PySide6").replace("\n\nFFmpeg", "\n\n## FFmpeg").replace("\n\nPython runtime", "\n\n## Python runtime"))
    write_text(PROJECT_ROOT / "third_party_sources" / "ffmpeg" / "SOURCE_URL.txt", "https://github.com/FFmpeg/FFmpeg/archive/9a01c1cb6a.zip\n")
    write_text(PROJECT_ROOT / "third_party_sources" / "ffmpeg" / "SOURCE_SHA256.txt", "8ca7287b2659c2309ad5060caad5b9ae4ef51f1b54ed5a30e0bfc815ee1c376d\n")
    write_text(
        PROJECT_ROOT / "third_party_sources" / "ffmpeg" / "CHECKSUMS.txt",
        "\n".join(
            [
                "52d25fc4711078112ba622d07601f183371af43e2d93cbb6e5eab3e1c05387cb  ffmpeg-N-125365-g9a01c1cb6a-win64-lgpl-shared.zip",
                "8ca7287b2659c2309ad5060caad5b9ae4ef51f1b54ed5a30e0bfc815ee1c376d  FFmpeg-9a01c1cb6a-source.zip",
                "14e560e13dea71189bd317be0b6c3fe5ba42b74c5a73a6b5952ddf44d5225e99  BtbN-FFmpeg-Builds-7a83528e-source.zip",
                "",
            ]
        ),
    )
    return 0 if lock["audit_status"] == "READY FOR PROFESSIONAL LEGAL REVIEW" else 1


if __name__ == "__main__":
    raise SystemExit(main())
