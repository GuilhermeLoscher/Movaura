from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from core.runtime_paths import data_root
from core.version import APP_VERSION


@dataclass(frozen=True)
class UpdateResult:
    available: bool
    message: str
    version: str = ""
    download_url: str = ""
    sha256: str = ""


class UpdateChecker:
    def check(self, manifest_url: str) -> UpdateResult:
        if not manifest_url.strip():
            return UpdateResult(
                False,
                "Nenhum servidor de atualizacao foi configurado nesta versao.",
            )
        if not self._safe_manifest_url(manifest_url):
            return UpdateResult(False, "O servidor de atualizacao deve usar HTTPS.")
        request = urllib.request.Request(
            manifest_url,
            headers={"User-Agent": f"Movaura/{APP_VERSION}"},
        )
        try:
            with urllib.request.urlopen(request, timeout=8) as response:
                data = json.load(response)
        except Exception as exc:
            return UpdateResult(False, f"Nao foi possivel consultar atualizacoes: {exc}")
        version = str(data.get("version", "")).strip()
        download_url = str(data.get("download_url", "")).strip()
        sha256 = str(data.get("sha256", "")).strip().upper()
        if (
            not version
            or not self._safe_download_url(download_url)
            or not re.fullmatch(r"[0-9A-F]{64}", sha256)
        ):
            return UpdateResult(False, "O manifesto de atualizacao e invalido.")
        if self._version_tuple(version) <= self._version_tuple(APP_VERSION):
            return UpdateResult(False, f"Voce ja usa a versao mais recente: {APP_VERSION}.")
        return UpdateResult(
            True,
            f"Nova versao disponivel: {version}.",
            version,
            download_url,
            sha256,
        )

    def download(self, result: UpdateResult) -> Path:
        if not result.available or not result.download_url:
            raise ValueError("Nenhuma atualização válida para baixar.")
        if not self._safe_download_url(result.download_url):
            raise ValueError("O link de atualizacao deve usar HTTPS.")
        suffix = Path(urlparse(result.download_url).path).suffix or ".exe"
        target_dir = data_root() / "updates"
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"Movaura-Setup-{result.version}{suffix}"
        request = urllib.request.Request(
            result.download_url,
            headers={"User-Agent": f"Movaura/{APP_VERSION}"},
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            target.write_bytes(response.read())
        if not self.verify_file(target, result.sha256):
            target.unlink(missing_ok=True)
            raise ValueError("O instalador baixado não passou na verificação SHA-256.")
        return target


    @staticmethod
    def _safe_manifest_url(url: str) -> bool:
        scheme = urlparse(url).scheme.lower()
        return scheme in {"https", "file"}

    @staticmethod
    def _safe_download_url(url: str) -> bool:
        return urlparse(url).scheme.lower() == "https"

    @staticmethod
    def verify_file(path: Path, expected_sha256: str) -> bool:
        digest = hashlib.sha256(path.read_bytes()).hexdigest().upper()
        return digest == expected_sha256.upper()

    @staticmethod
    def _version_tuple(version: str) -> tuple[int, ...]:
        try:
            return tuple(int(part) for part in version.split("."))
        except ValueError:
            return (0,)
