from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from license_compliance_common import PROJECT_ROOT, RELEASE_COMPLIANCE, ensure_dirs, sha256_file, write_json


COMMANDS = {
    "version": ["-version"],
    "buildconf": ["-buildconf"],
    "formats": ["-formats"],
    "codecs": ["-codecs"],
    "encoders": ["-encoders"],
    "decoders": ["-decoders"],
    "protocols": ["-protocols"],
    "filters": ["-filters"],
    "hwaccels": ["-hwaccels"],
    "libraries": ["-L"],
}

BLOCKED_FLAGS = {
    "--enable-gpl": "GPL is enabled; proprietary distribution needs owner/legal decision.",
    "--enable-nonfree": "Nonfree FFmpeg build cannot be redistributed under normal FFmpeg terms.",
    "--enable-libx264": "x264 commonly makes the resulting FFmpeg build GPL.",
    "--enable-libx265": "x265 commonly makes the resulting FFmpeg build GPL.",
    "--enable-libfdk-aac": "FDK-AAC may create nonfree redistribution constraints.",
}

REVIEW_FLAGS = {
    "--enable-version3": "Version-3 code path enabled; verify LGPLv3/GPLv3 obligations.",
    "--enable-openssl": "OpenSSL has separate license notices and compatibility review.",
    "--enable-gnutls": "GnuTLS has separate LGPL license notices.",
    "--enable-libvpx": "External codec library; include license and patent review.",
    "--enable-libopus": "External codec library; include license and patent review.",
    "--enable-libvorbis": "External codec library; include license and patent review.",
    "--enable-libdav1d": "External codec library; include license and patent review.",
    "--enable-libsvtav1": "External codec library; include license and patent review.",
    "--enable-libaom": "External codec library; include license and patent review.",
    "--enable-libass": "External subtitle library; include license and dependencies.",
}


def ffmpeg_root() -> Path:
    for candidate in (
        PROJECT_ROOT / "tools" / "ffmpeg",
        PROJECT_ROOT / "dist" / "standalone" / "Movaura" / "_internal" / "tools" / "ffmpeg",
    ):
        if (candidate / "bin" / "ffmpeg.exe").is_file():
            return candidate
    return PROJECT_ROOT / "tools" / "ffmpeg"


def run_ffmpeg(ffmpeg: Path, args: list[str]) -> dict[str, object]:
    try:
        completed = subprocess.run(
            [str(ffmpeg), *args],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        return {
            "argv": [str(ffmpeg), *args],
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    except Exception as exc:
        return {"argv": [str(ffmpeg), *args], "error": f"{type(exc).__name__}: {exc}"}


def parse_configuration(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("configuration:"):
            return line.removeprefix("configuration:").strip()
    return ""


def parse_version(text: str) -> tuple[str, str]:
    first = text.splitlines()[0] if text.splitlines() else ""
    version = first.removeprefix("ffmpeg version ").split(" ")[0] if first.startswith("ffmpeg version ") else ""
    match = re.search(r"g([0-9a-f]{7,40})", version)
    commit = match.group(1) if match else ""
    return version, commit


def enabled_libs(configuration: str) -> list[str]:
    flags = re.findall(r"--enable-[A-Za-z0-9_.+-]+", configuration)
    return sorted(flag for flag in set(flags) if flag.startswith("--enable-lib"))


def main() -> int:
    ensure_dirs()
    root = ffmpeg_root()
    ffmpeg = root / "bin" / "ffmpeg.exe"
    outputs: dict[str, dict[str, object]] = {}
    findings: list[dict[str, str]] = []
    files: list[dict[str, object]] = []

    if not ffmpeg.is_file():
        findings.append({"severity": "critical", "code": "ffmpeg-missing", "message": "ffmpeg.exe was not found."})
    else:
        for name, args in COMMANDS.items():
            outputs[name] = run_ffmpeg(ffmpeg, args)
        text = str(outputs.get("version", {}).get("stdout", "")) + str(outputs.get("version", {}).get("stderr", ""))
        if not text:
            text = str(outputs.get("buildconf", {}).get("stdout", "")) + str(outputs.get("buildconf", {}).get("stderr", ""))
        configuration = parse_configuration(text)
        version, commit = parse_version(text)
        lower_config = configuration.lower()
        for flag, message in BLOCKED_FLAGS.items():
            if flag in lower_config:
                findings.append({"severity": "critical", "code": flag.removeprefix("--"), "message": message})
        for flag, message in REVIEW_FLAGS.items():
            if flag in lower_config:
                findings.append({"severity": "review", "code": flag.removeprefix("--"), "message": message})
        if "master-latest" in (PROJECT_ROOT / "licenses" / "ffmpeg" / "NOTICE.txt").read_text(encoding="utf-8", errors="ignore").lower():
            findings.append(
                {
                    "severity": "high",
                    "code": "master-latest-reference",
                    "message": "FFmpeg is still documented as master-latest; replace with immutable artifact or reproducible source build before release.",
                }
            )
        for path in sorted(root.rglob("*"), key=lambda item: str(item).lower()):
            if path.is_file():
                files.append(
                    {
                        "path": path.relative_to(root).as_posix(),
                        "size": path.stat().st_size,
                        "sha256": sha256_file(path),
                    }
                )
    configuration = parse_configuration(
        str(outputs.get("version", {}).get("stdout", "")) + str(outputs.get("version", {}).get("stderr", ""))
    )
    version, commit = parse_version(str(outputs.get("version", {}).get("stdout", "")))
    external_libs = enabled_libs(configuration)
    lock = {
        "provider": "PENDING OWNER CONFIRMATION",
        "artifact_name": "PENDING - current docs mention master-latest",
        "artifact_url": "PENDING - immutable URL required",
        "downloaded_at_utc": "PENDING",
        "archive_sha256": "PENDING",
        "ffmpeg_version": version,
        "ffmpeg_commit": commit,
        "provider_commit": "PENDING",
        "configuration": configuration,
        "files": files,
        "license_classification": "BLOCKED UNTIL IMMUTABLE SOURCE/ARTIFACT LOCK AND EXTERNAL LIB REVIEW",
        "source_url": "PENDING - corresponding source package required",
        "source_archive_sha256": "PENDING",
        "audit_status": "NOT READY - LICENSE BLOCKERS" if findings else "TECHNICAL AUDIT GENERATED - LEGAL REVIEW REQUIRED",
        "findings": findings,
    }
    payload = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "ffmpeg_root": str(root),
        "outputs": outputs,
        "configuration": configuration,
        "external_libraries": external_libs,
        "files": files,
        "findings": findings,
        "lock": lock,
    }
    write_json(RELEASE_COMPLIANCE / "ffmpeg" / "ffmpeg-audit.json", payload)
    write_json(PROJECT_ROOT / "third_party" / "ffmpeg" / "LOCK.json", lock)
    (PROJECT_ROOT / "licenses" / "ffmpeg").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "licenses" / "ffmpeg" / "BUILD_CONFIGURATION.txt").write_text(configuration + "\n", encoding="utf-8")
    lines = [
        "Movaura FFmpeg compliance audit",
        f"Root: {root}",
        f"Version: {version or 'unknown'}",
        f"Commit: {commit or 'unknown'}",
        "",
        "Configuration:",
        configuration or "not found",
        "",
        "Findings:",
    ]
    lines.extend(f"- {item['severity']}: {item['message']}" for item in findings)
    lines.extend(["", "External --enable-lib* flags:"])
    lines.extend(f"- {flag}" for flag in external_libs)
    (RELEASE_COMPLIANCE / "ffmpeg" / "ffmpeg-audit.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"ffmpeg_findings={len(findings)}")
    return 1 if any(item["severity"] in {"critical", "high"} for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
