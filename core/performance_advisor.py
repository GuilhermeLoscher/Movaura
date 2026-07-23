"""User-friendly performance guidance for Movaura. Desenvolvido por Guilherme Loscher (GL)."""

from __future__ import annotations

from dataclasses import dataclass

from core.performance_monitor import PerformanceSnapshot


@dataclass(frozen=True)
class PerformanceAdvice:
    level: str
    title: str
    message: str
    action: str


class PerformanceAdvisor:
    def advice(
        self,
        snapshot: PerformanceSnapshot,
        renderer: str,
        fps: int,
        optimize_videos: bool,
    ) -> PerformanceAdvice:
        if snapshot.processes == 0:
            return PerformanceAdvice(
                "idle",
                "Pronto para aplicar",
                "Escolha um wallpaper, pré-visualize e aplique na área de trabalho.",
                "Aplicar na área de trabalho",
            )
        if snapshot.average_cpu_percent >= 16 or snapshot.memory_mb >= 280:
            return PerformanceAdvice(
                "high",
                "Consumo alto detectado",
                "Ative o perfil Leve, limite o FPS e mantenha a otimização automática de vídeos ligada.",
                "Corrigir desempenho",
            )
        if renderer == "video" and not optimize_videos:
            return PerformanceAdvice(
                "warning",
                "Vídeo sem otimização",
                "A otimização automática reduz bastante CPU/RAM em vídeos grandes e mantém o arquivo original intacto.",
                "Ativar otimização",
            )
        if renderer == "video" and fps > 30:
            return PerformanceAdvice(
                "warning",
                "FPS alto para vídeo",
                "Vídeos costumam ficar suaves em 30 FPS. Use 15 FPS no perfil Leve para notebooks.",
                "Usar recomendado",
            )
        return PerformanceAdvice(
            "ok",
            "Desempenho saudável",
            "O compositor está dentro de uma faixa boa para uso diário.",
            "Manter configuração",
        )

    @staticmethod
    def beginner_summary(renderer: str, media_name: str, screen: object, profile_name: str) -> str:
        wallpaper = media_name or {
            "color": "cor sólida",
            "particles": "partículas leves",
            "rain": "chuva",
            "fog": "neblina",
            "glow": "brilho suave",
            "vignette": "vinheta",
        }.get(renderer, renderer)
        screen_label = "todos os monitores" if screen == "all" else f"monitor {screen}"
        return f"{wallpaper} | {screen_label} | perfil {profile_name}"
