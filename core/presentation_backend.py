from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from core.desktop_probe import DesktopReport


class PresentationBackend(str, Enum):
    WINDOW_HOST = "window-host"
    SYSTEM_WALLPAPER = "system-wallpaper"
    NATIVE_COMPOSITION = "native-composition"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class BackendDecision:
    backend: PresentationBackend
    reason: str

    def to_text(self) -> str:
        return (
            "Backend de apresentação do Movaura:\n"
            f"  backend: {self.backend.value}\n"
            f"  motivo: {self.reason}"
        )


class PresentationPolicy:
    def decide(
        self,
        requested_mode: str,
        report: DesktopReport,
        renderer: str = "color",
    ) -> BackendDecision:
        if requested_mode == PresentationBackend.SYSTEM_WALLPAPER.value:
            return BackendDecision(
                PresentationBackend.SYSTEM_WALLPAPER,
                "fallback seguro explícito: o Windows controla a superfície do wallpaper",
            )

        if requested_mode == PresentationBackend.NATIVE_COMPOSITION.value:
            return BackendDecision(
                PresentationBackend.NATIVE_COMPOSITION,
                "backend DirectComposition selecionado; apresentação isolada do Explorer",
            )

        if requested_mode != "auto":
            return BackendDecision(
                PresentationBackend.WINDOW_HOST,
                f"modo window-host explícito para diagnóstico: {requested_mode}",
            )

        workerw = report.workerw_after_defview
        if workerw and not workerw.parent:
            return BackendDecision(
                PresentationBackend.WINDOW_HOST,
                "host WorkerW clássico de nível superior disponível",
            )

        if renderer == "color":
            return BackendDecision(
                PresentationBackend.SYSTEM_WALLPAPER,
                (
                    "Explorer não expõe um host seguro para animações; "
                    "usando fallback estático de cor controlado pelo Windows"
                ),
            )

        return BackendDecision(
            PresentationBackend.BLOCKED,
            (
                "Explorer não expõe um host seguro para animações; "
                "renderizadores animados exigem um host compatível"
            ),
        )
