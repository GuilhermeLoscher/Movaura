from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


BLOCKED_CONFIG_FLAGS = (
    "--enable-gpl",
    "--enable-nonfree",
    "--enable-libx264",
    "--enable-libx265",
)
REQUIRED_CONFIG_FLAGS = (
    "--enable-shared",
    "--disable-static",
    "--disable-libx264",
    "--disable-libx265",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit bundled FFmpeg for commercial LGPL-oriented distribution.")
    parser.add_argument("--root", type=Path, default=Path("tools/ffmpeg"))
    parser.add_argument("--report-base", type=Path, default=Path("release/reports/ffmpeg-audit"))
    parser.add_argument("--strict-lock", action="store_true", help="Require a pinned upstream archive hash lock.")
    args = parser.parse_args()

    ffmpeg_root = args.root.resolve()
    ffmpeg_exe = ffmpeg_root / "bin" / "ffmpeg.exe"
    report_base = args.report_base
    report_base.parent.mkdir(parents=True, exist_ok=True)
    findings: list[dict[str, str]] = []
    files: list[dict[str, object]] = []
    version_output = ""
    configuration = ""

    if not ffmpeg_exe.exists():
        findings.append({"severity": "info", "message": "ffmpeg.exe not bundled"})
    else:
        completed = subprocess.run([str(ffmpeg_exe), "-version"], capture_output=True, text=True, check=False)
        version_output = (completed.stdout or "") + (completed.stderr or "")
        for line in version_output.splitlines():
            if line.startswith("configuration:"):
                configuration = line
                break
        config_lower = configuration.lower()
        for flag in BLOCKED_CONFIG_FLAGS:
            if flag in config_lower:
                findings.append({"severity": "critical", "message": f"blocked FFmpeg flag present: {flag}"})
        for flag in REQUIRED_CONFIG_FLAGS:
            if flag not in config_lower:
                findings.append({"severity": "high", "message": f"required FFmpeg flag missing: {flag}"})
        if args.strict_lock:
            findings.append({"severity": "high", "message": "strict upstream archive hash lock is not implemented yet"})
        for path in sorted(ffmpeg_root.rglob("*")):
            if path.is_file():
                files.append(
                    {
                        "path": path.relative_to(ffmpeg_root).as_posix(),
                        "size": path.stat().st_size,
                        "sha256": sha256(path),
                    }
                )

    payload = {
        "status": "failed" if any(item["severity"] in {"critical", "high"} for item in findings) else "ok",
        "ffmpeg_root": str(ffmpeg_root),
        "version_output": version_output,
        "configuration": configuration,
        "files": files,
        "findings": findings,
        "limitations": [
            "This verifies bundled binaries and configuration output.",
            "It does not prove legal compliance or source-code offer completeness.",
            "The current bundled FFmpeg build is a dated git snapshot, not a pinned release archive lock.",
        ],
    }
    report_base.with_suffix(".json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "Movaura FFmpeg audit",
        f"status: {payload['status']}",
        f"root: {ffmpeg_root}",
        "",
        "Configuration:",
        configuration or "not available",
        "",
        "Findings:",
    ]
    for item in findings:
        lines.append(f"- {item['severity']}: {item['message']}")
    lines.extend(["", "Files:"])
    for item in files:
        lines.append(f"- {item['sha256']}  {item['path']} ({item['size']} bytes)")
    report_base.with_suffix(".txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"ffmpeg_audit={payload['status']}")
    for item in findings:
        print(f"{item['severity']}: {item['message']}")
    return 1 if payload["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
