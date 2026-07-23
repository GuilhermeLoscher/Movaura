from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from threading import Thread
from urllib.request import Request, urlopen

from core.runtime_paths import data_root


class TelemetryClient:
    def __init__(self, enabled: bool, endpoint: str = "") -> None:
        self.enabled = enabled
        self.endpoint = endpoint.strip()
        self.path = data_root() / "telemetry.jsonl"

    def record(self, event: str, properties: dict[str, object] | None = None) -> None:
        if not self.enabled:
            return
        payload = {"event": event, "timestamp": datetime.now().isoformat(timespec="seconds"), "properties": properties or {}}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, ensure_ascii=False) + "\n")
        if self.endpoint:
            Thread(target=self._post, args=(payload,), daemon=True).start()

    def _post(self, payload: dict[str, object]) -> None:
        try:
            body = json.dumps(payload).encode("utf-8")
            urlopen(Request(self.endpoint, data=body, headers={"Content-Type": "application/json"}), timeout=4).close()
        except OSError:
            pass
