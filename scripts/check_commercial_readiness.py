from __future__ import annotations

import sys
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    checks: list[tuple[str, bool, str]] = []
    installer = ROOT / "release" / "installer" / "Movaura-Setup-0.9.0.exe"
    notices = ROOT / "licenses" / "ffmpeg" / "NOTICE.txt"
    ffmpeg_readme = ROOT / "tools" / "ffmpeg" / "README.txt"
    app_license = ROOT / "licenses" / "ffmpeg" / "SOURCE.txt"
    msix_script = ROOT / "scripts" / "build_msix_package.ps1"
    wack_script = ROOT / "scripts" / "run_wack.ps1"
    store_notes = ROOT / "docs" / "STORE_SUBMISSION.md"
    privacy_policy = ROOT / "docs" / "PRIVACY_POLICY.md"
    certification_notes = ROOT / "docs" / "CERTIFICATION_NOTES.md"

    checks.append(("installer", installer.is_file(), str(installer)))
    checks.append(("ffmpeg_notice", notices.is_file(), str(notices)))
    checks.append(("ffmpeg_source_note", app_license.is_file(), str(app_license)))
    checks.append(("msix_build_flow", msix_script.is_file(), str(msix_script)))
    checks.append(("wack_flow", wack_script.is_file(), str(wack_script)))
    checks.append(("store_submission_materials", store_notes.is_file(), str(store_notes)))
    checks.append(("privacy_policy_draft", privacy_policy.is_file(), str(privacy_policy)))
    checks.append(("certification_notes", certification_notes.is_file(), str(certification_notes)))

    readme_text = ""
    if ffmpeg_readme.is_file():
        readme_text = ffmpeg_readme.read_text(encoding="utf-8", errors="ignore").lower()
    ffmpeg_version_text = ""
    for ffmpeg in (
        ROOT / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe",
        ROOT / "tools" / "ffmpeg" / "ffmpeg.exe",
    ):
        if ffmpeg.is_file():
            completed = subprocess.run(
                [str(ffmpeg), "-version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=15,
            )
            ffmpeg_version_text = (completed.stdout + "\n" + completed.stderr).lower()
            break
    config_text = ""
    for line in ffmpeg_version_text.splitlines():
        if line.startswith("configuration:"):
            config_text = line
            break
    ffmpeg_is_lgpl_clean = (
        ("license: lgpl" in readme_text or "lgpl" in readme_text)
        and config_text
        and "--enable-gpl" not in config_text
        and "--enable-nonfree" not in config_text
        and "--disable-libx264" in config_text
        and "--disable-libx265" in config_text
    )
    checks.append(
        (
            "ffmpeg_lgpl_clean",
            ffmpeg_is_lgpl_clean,
            "FFmpeg LGPL compartilhado, sem GPL/nonfree na configuracao reportada.",
        )
    )

    ok = True
    for name, passed, detail in checks:
        status = "OK" if passed else "ATENCAO"
        print(f"{status}: {name} - {detail}")
        ok = ok and passed
    if ok:
        print("commercial_readiness=ok")
        return 0
    print("commercial_readiness=needs_review")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
