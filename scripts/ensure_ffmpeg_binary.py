from __future__ import annotations

import json
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from license_compliance_common import PROJECT_ROOT, sha256_file


LOCK_PATH = PROJECT_ROOT / "third_party" / "ffmpeg" / "LOCK.json"
FFMPEG_ROOT = PROJECT_ROOT / "tools" / "ffmpeg"


def download(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=300) as response, target.open("wb") as handle:
        shutil.copyfileobj(response, handle)


def main() -> int:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    artifact_url = lock["artifact_url"]
    artifact_name = lock["artifact_name"]
    expected_sha = lock["archive_sha256"].lower()
    ffmpeg_exe = FFMPEG_ROOT / "bin" / "ffmpeg.exe"
    if ffmpeg_exe.is_file():
        source_meta = FFMPEG_ROOT / "MOVAURA_LOCK_SOURCE.json"
        if not source_meta.is_file():
            source_meta.write_text(
                json.dumps(
                    {
                        "tag": lock["provider_release_tag"],
                        "artifact": artifact_name,
                        "artifact_url": artifact_url,
                        "archive_sha256": expected_sha,
                        "downloaded_at_utc": lock.get("downloaded_at_utc", ""),
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        print(f"ffmpeg_present={ffmpeg_exe}")
        return 0
    with tempfile.TemporaryDirectory(prefix="movaura-ffmpeg-") as tmp_name:
        tmp = Path(tmp_name)
        archive = tmp / artifact_name
        download(artifact_url, archive)
        actual_sha = sha256_file(archive).lower()
        if actual_sha != expected_sha:
            raise SystemExit(f"FFmpeg archive SHA mismatch: {actual_sha} != {expected_sha}")
        with zipfile.ZipFile(archive) as package:
            package.extractall(tmp)
        extracted = tmp / artifact_name.removesuffix(".zip")
        if not (extracted / "bin" / "ffmpeg.exe").is_file():
            raise SystemExit(f"ffmpeg.exe not found inside {artifact_name}")
        if FFMPEG_ROOT.exists():
            shutil.rmtree(FFMPEG_ROOT)
        shutil.copytree(extracted, FFMPEG_ROOT)
        (FFMPEG_ROOT / "MOVAURA_LOCK_SOURCE.json").write_text(
            json.dumps(
                {
                    "tag": lock["provider_release_tag"],
                    "artifact": artifact_name,
                    "artifact_url": artifact_url,
                    "archive_sha256": expected_sha,
                    "downloaded_at_utc": lock.get("downloaded_at_utc", ""),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    print(f"ffmpeg_downloaded={FFMPEG_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
