from __future__ import annotations

import hashlib
import json
import os
import platform
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from core.json_store import read_json_object, write_json_atomic
from core.runtime_paths import data_root
from core.settings import MovauraSettings


@dataclass(frozen=True)
class LicenseStatus:
    required: bool
    active: bool
    message: str
    key: str = ""
    email: str = ""


@dataclass(frozen=True)
class ActivationResult:
    success: bool
    message: str


class LicenseManager:
    """Beta activation through Supabase REST."""

    def __init__(self, settings: MovauraSettings) -> None:
        self.settings = settings
        self.license_path = data_root() / "license.json"

    def is_required(self) -> bool:
        env_value = os.environ.get("MOVAURA_LICENSE_REQUIRED", "").strip().lower()
        if env_value in {"1", "true", "yes", "sim"}:
            return True
        if env_value in {"0", "false", "no", "nao", "não"}:
            return False
        return self.settings.get_bool("license_required")

    def status(self) -> LicenseStatus:
        if not self.is_required():
            return LicenseStatus(False, True, "Ativacao desativada nesta build.")
        local = self._read_local_license()
        if not local:
            return LicenseStatus(True, False, "Ative o Movaura Beta para continuar.")
        if local.get("machine_hash") != self.machine_hash():
            return LicenseStatus(True, False, "Esta ativacao pertence a outro computador.")
        expires_at = str(local.get("expires_at") or "").strip()
        if expires_at and self._is_expired(expires_at):
            return LicenseStatus(True, False, "Esta chave beta expirou.")
        key = str(local.get("key") or "")
        email = str(local.get("email") or "")
        return LicenseStatus(True, True, "Movaura Beta ativado.", key=key, email=email)

    def activate(self, key: str, email: str, name: str = "") -> ActivationResult:
        key = key.strip().upper()
        email = email.strip().lower()
        name = name.strip()
        if not key:
            return ActivationResult(False, "Informe a chave beta.")
        if "@" not in email or "." not in email:
            return ActivationResult(False, "Informe um e-mail valido.")
        endpoint = self._endpoint()
        anon_key = self._anon_key()
        if not endpoint or not anon_key:
            return ActivationResult(False, "Supabase ainda nao foi configurado nesta build beta.")

        rpc_name = self.settings.get_str("license_activation_rpc").strip()
        if rpc_name:
            try:
                return self._activate_via_rpc(endpoint, anon_key, rpc_name, key, email, name)
            except HTTPError as exc:
                if exc.code != 404:
                    return ActivationResult(False, self._friendly_network_error(exc))
            except Exception as exc:
                return ActivationResult(False, self._friendly_network_error(exc))

        try:
            rows = self._supabase_get_key(endpoint, anon_key, key)
        except Exception as exc:
            return ActivationResult(False, self._friendly_network_error(exc))
        if not rows:
            return ActivationResult(False, "Chave beta nao encontrada.")

        row = rows[0]
        row_status = str(row.get("status") or "available").lower()
        current_machine = self.machine_hash()
        row_machine = str(row.get("machine_hash") or "")
        row_email = str(row.get("assigned_email") or "").lower()
        expires_at = str(row.get("expires_at") or "")

        if expires_at and self._is_expired(expires_at):
            return ActivationResult(False, "Esta chave beta expirou.")
        if row_status == "used":
            if row_machine == current_machine and (not row_email or row_email == email):
                self._write_local_license(key, email, expires_at)
                return ActivationResult(True, "Ativacao restaurada neste computador.")
            return ActivationResult(False, "Esta chave beta ja foi usada em outro computador.")
        if row_status not in {"available", "new", "pending", ""}:
            return ActivationResult(False, f"Esta chave beta esta com status: {row_status}.")

        payload = {
            "status": "used",
            "assigned_email": email,
            "assigned_name": name,
            "machine_hash": current_machine,
            "activated_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            self._supabase_patch_key(endpoint, anon_key, key, payload)
        except Exception as exc:
            return ActivationResult(False, self._friendly_network_error(exc))
        self._write_local_license(key, email, expires_at)
        return ActivationResult(True, "Movaura Beta ativado com sucesso.")

    def _activate_via_rpc(
        self,
        endpoint: str,
        anon_key: str,
        rpc_name: str,
        key: str,
        email: str,
        name: str,
    ) -> ActivationResult:
        url = f"{endpoint}/rest/v1/rpc/{quote(rpc_name, safe='')}"
        payload = {
            "p_key": key,
            "p_email": email,
            "p_name": name,
            "p_machine_hash": self.machine_hash(),
        }
        body = json.dumps(payload).encode("utf-8")
        request = Request(url, data=body, headers=self._headers(anon_key), method="POST")
        with urlopen(request, timeout=12) as response:
            decoded = json.loads(response.read().decode("utf-8") or "{}")
        if isinstance(decoded, list) and decoded:
            decoded = decoded[0]
        if not isinstance(decoded, dict):
            return ActivationResult(False, "Resposta invalida do servidor de ativacao.")
        success = bool(decoded.get("success"))
        message = str(decoded.get("message") or "")
        if success:
            self._write_local_license(key, email, str(decoded.get("expires_at") or ""))
        return ActivationResult(success, message or "Ativacao concluida.")

    def machine_hash(self) -> str:
        raw = "|".join(
            [
                str(uuid.getnode()),
                os.environ.get("COMPUTERNAME", ""),
                os.environ.get("USERNAME", ""),
                platform.machine(),
            ]
        )
        return hashlib.sha256(raw.encode("utf-8", errors="ignore")).hexdigest()

    def _read_local_license(self) -> dict[str, Any]:
        return read_json_object(self.license_path) or {}

    def _write_local_license(self, key: str, email: str, expires_at: str = "") -> None:
        write_json_atomic(
            self.license_path,
            {
                "product": "Movaura Beta",
                "key": key,
                "email": email,
                "machine_hash": self.machine_hash(),
                "activated_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": expires_at,
            },
        )

    def _endpoint(self) -> str:
        return (
            os.environ.get("MOVAURA_SUPABASE_URL")
            or self.settings.get_str("license_supabase_url")
        ).strip().rstrip("/")

    def _anon_key(self) -> str:
        return (
            os.environ.get("MOVAURA_SUPABASE_ANON_KEY")
            or self.settings.get_str("license_supabase_anon_key")
        ).strip()

    def _table(self) -> str:
        return quote(self.settings.get_str("license_table") or "beta_keys", safe="")

    def _supabase_get_key(self, endpoint: str, anon_key: str, key: str) -> list[dict[str, Any]]:
        url = (
            f"{endpoint}/rest/v1/{self._table()}?"
            f"key=eq.{quote(key, safe='')}&select=key,status,assigned_email,"
            "machine_hash,expires_at"
        )
        request = Request(url, headers=self._headers(anon_key), method="GET")
        with urlopen(request, timeout=12) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data if isinstance(data, list) else []

    def _supabase_patch_key(
        self,
        endpoint: str,
        anon_key: str,
        key: str,
        payload: dict[str, Any],
    ) -> None:
        url = f"{endpoint}/rest/v1/{self._table()}?key=eq.{quote(key, safe='')}"
        body = json.dumps(payload).encode("utf-8")
        request = Request(
            url,
            data=body,
            headers={**self._headers(anon_key), "Prefer": "return=minimal"},
            method="PATCH",
        )
        with urlopen(request, timeout=12):
            return

    def _headers(self, anon_key: str) -> dict[str, str]:
        return {
            "apikey": anon_key,
            "Authorization": f"Bearer {anon_key}",
            "Content-Type": "application/json",
        }

    def _friendly_network_error(self, exc: Exception) -> str:
        if isinstance(exc, HTTPError):
            if exc.code in {401, 403}:
                return "Supabase recusou a ativacao. Verifique anon key e politicas RLS."
            if exc.code == 404:
                return "Tabela beta_keys nao encontrada no Supabase."
            return f"Falha no servidor de ativacao: HTTP {exc.code}."
        if isinstance(exc, URLError):
            return "Nao foi possivel conectar ao servidor de ativacao."
        return f"Falha ao ativar: {exc}"

    def _is_expired(self, value: str) -> bool:
        try:
            normalized = value.replace("Z", "+00:00")
            expires_at = datetime.fromisoformat(normalized)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
        except ValueError:
            return False
        return datetime.now(timezone.utc) > expires_at
