from __future__ import annotations

import ctypes
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from core.json_store import read_json_object, write_json_atomic
from uuid import UUID

from PySide6.QtGui import QColor, QImage

from core.runtime_paths import data_root


SPI_SETDESKWALLPAPER = 0x0014
SPI_GETDESKWALLPAPER = 0x0073
SPIF_UPDATEINIFILE = 0x0001
MAX_PATH = 260
CLSCTX_LOCAL_SERVER = 0x4
COINIT_APARTMENTTHREADED = 0x2

WALLPAPER_POSITIONS = {
    "center": 0,
    "tile": 1,
    "stretch": 2,
    "fit": 3,
    "fill": 4,
    "span": 5,
}
WALLPAPER_POSITION_NAMES = {value: key for key, value in WALLPAPER_POSITIONS.items()}


class Guid(ctypes.Structure):
    _fields_ = [
        ("data1", ctypes.c_ulong),
        ("data2", ctypes.c_ushort),
        ("data3", ctypes.c_ushort),
        ("data4", ctypes.c_ubyte * 8),
    ]

    @classmethod
    def from_text(cls, text: str) -> "Guid":
        value = UUID(text)
        return cls.from_buffer_copy(value.bytes_le)


@dataclass(frozen=True)
class SystemWallpaperResult:
    success: bool
    message: str
    path: Path | None = None


class SystemWallpaperBackend:
    def __init__(self) -> None:
        self.root = data_root()
        self.generated_dir = self.root / "generated"
        self.state_path = self.root / "system_wallpaper_state.json"
        self.user32 = ctypes.windll.user32
        self.user32.SystemParametersInfoW.argtypes = [
            ctypes.c_uint,
            ctypes.c_uint,
            ctypes.c_void_p,
            ctypes.c_uint,
        ]
        self.user32.SystemParametersInfoW.restype = ctypes.c_int

    def apply(
        self,
        renderer: str,
        color_text: str,
        media_path: str,
        position: str = "fill",
    ) -> SystemWallpaperResult:
        self._save_original_wallpaper()
        position_result = self._set_position(position)
        if position_result is not None:
            return position_result
        if renderer == "image":
            return self.apply_image(media_path)
        if renderer == "color":
            return self.apply_color(color_text)
        return SystemWallpaperResult(
            False,
            f"O papel de parede estático não aceita o renderizador: {renderer}",
        )

    def apply_color(self, color_text: str) -> SystemWallpaperResult:
        started = perf_counter()
        color = QColor(color_text)
        if not color.isValid():
            return SystemWallpaperResult(False, f"Cor inválida: {color_text}")

        self.generated_dir.mkdir(parents=True, exist_ok=True)
        output = self.generated_dir / "movaura-color.bmp"
        image = QImage(32, 32, QImage.Format.Format_RGB32)
        image.fill(color)
        if not image.save(str(output), "BMP"):
            return SystemWallpaperResult(False, f"Não foi possível salvar o papel de parede gerado: {output}")

        if not self._set_wallpaper(output):
            error = ctypes.get_last_error()
            return SystemWallpaperResult(False, f"Falha em SystemParametersInfoW; último erro={error}")

        return SystemWallpaperResult(
            True,
            (
                "Papel de parede estático aplicado com segurança; "
                f"ícones e barra de tarefas continuam sob controle do Explorer ({perf_counter() - started:.2f}s)"
            ),
            output,
        )

    def apply_image(self, image_path: str) -> SystemWallpaperResult:
        started = perf_counter()
        source = Path(image_path).expanduser()
        if not source.exists():
            return SystemWallpaperResult(False, f"Imagem do papel de parede não encontrada: {source}")
        if source.suffix.lower() not in {".bmp", ".jpg", ".jpeg", ".png"}:
            return SystemWallpaperResult(
                False,
                f"Formato de imagem não aceito: {source.suffix or '(nenhum)'}",
            )

        if not self._set_wallpaper(source):
            error = ctypes.get_last_error()
            return SystemWallpaperResult(False, f"Falha em SystemParametersInfoW; último erro={error}")

        return SystemWallpaperResult(
            True,
            f"Imagem aplicada como papel de parede com segurança ({perf_counter() - started:.2f}s)",
            source,
        )

    def restore(self) -> SystemWallpaperResult:
        started = perf_counter()
        if not self.state_path.exists():
            return SystemWallpaperResult(False, "Não existe um papel de parede anterior salvo.")

        state = read_json_object(self.state_path)
        if state is None:
            return SystemWallpaperResult(False, "Não foi possível ler o papel de parede salvo.")
        original = Path(str(state.get("wallpaper", "")))

        if not original.exists():
            return SystemWallpaperResult(False, f"O papel de parede salvo não existe mais: {original}")
        original_position = str(state.get("wallpaper_position", ""))
        if original_position:
            position_result = self._set_position(original_position)
            if position_result is not None:
                return position_result
        if not self._set_wallpaper(original):
            error = ctypes.get_last_error()
            return SystemWallpaperResult(False, f"Falha ao restaurar o papel de parede; último erro={error}")

        return SystemWallpaperResult(
            True,
            f"Papel de parede anterior restaurado ({perf_counter() - started:.2f}s)",
            original,
        )

    def _save_original_wallpaper(self) -> None:
        if self.state_path.exists():
            self._save_original_position_if_missing()
            return

        buffer = ctypes.create_unicode_buffer(MAX_PATH)
        ok = self.user32.SystemParametersInfoW(
            SPI_GETDESKWALLPAPER,
            len(buffer),
            ctypes.cast(buffer, ctypes.c_void_p),
            0,
        )
        if not ok or not buffer.value:
            return

        write_json_atomic(
            self.state_path,
            {
                "wallpaper": buffer.value,
                "wallpaper_position": self._get_position(),
            },
        )

    def _save_original_position_if_missing(self) -> None:
        state = read_json_object(self.state_path)
        if state is None:
            return
        if state.get("wallpaper_position"):
            return
        state["wallpaper_position"] = self._get_position()
        write_json_atomic(self.state_path, state)

    def _set_wallpaper(self, path: Path) -> bool:
        return bool(
            self.user32.SystemParametersInfoW(
                SPI_SETDESKWALLPAPER,
                0,
                ctypes.cast(ctypes.c_wchar_p(str(path.resolve())), ctypes.c_void_p),
                SPIF_UPDATEINIFILE,
            )
        )

    def _set_position(self, position: str) -> SystemWallpaperResult | None:
        position_value = WALLPAPER_POSITIONS.get(position)
        if position_value is None:
            return SystemWallpaperResult(False, f"Posição de papel de parede inválida: {position}")

        ole32 = ctypes.windll.ole32
        ole32.CoInitializeEx.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        ole32.CoInitializeEx.restype = ctypes.c_long
        ole32.CoCreateInstance.argtypes = [
            ctypes.POINTER(Guid),
            ctypes.c_void_p,
            ctypes.c_ulong,
            ctypes.POINTER(Guid),
            ctypes.POINTER(ctypes.c_void_p),
        ]
        ole32.CoCreateInstance.restype = ctypes.c_long
        ole32.CoUninitialize.argtypes = []
        ole32.CoUninitialize.restype = None

        initialized = ole32.CoInitializeEx(None, COINIT_APARTMENTTHREADED) >= 0
        instance = ctypes.c_void_p()
        clsid = Guid.from_text("C2CF3110-460E-4FC1-B9D0-8A1C0C9CC4BD")
        iid = Guid.from_text("B92B56A9-8B55-4E14-9A89-0199BBB6F93B")
        try:
            result = ole32.CoCreateInstance(
                ctypes.byref(clsid),
                None,
                CLSCTX_LOCAL_SERVER,
                ctypes.byref(iid),
                ctypes.byref(instance),
            )
            if result < 0:
                return SystemWallpaperResult(
                    False,
                    f"IDesktopWallpaper não está disponível; hresult=0x{result & 0xFFFFFFFF:08X}",
                )

            vtable = ctypes.cast(
                instance,
                ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)),
            ).contents
            set_position = ctypes.WINFUNCTYPE(
                ctypes.c_long,
                ctypes.c_void_p,
                ctypes.c_int,
            )(vtable[10])
            release = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)(vtable[2])
            try:
                result = set_position(instance, position_value)
                if result < 0:
                    return SystemWallpaperResult(
                        False,
                        f"Falha em IDesktopWallpaper.SetPosition; hresult=0x{result & 0xFFFFFFFF:08X}",
                    )
            finally:
                release(instance)
        finally:
            if initialized:
                ole32.CoUninitialize()
        return None

    def _get_position(self) -> str:
        ole32 = ctypes.windll.ole32
        ole32.CoInitializeEx.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        ole32.CoInitializeEx.restype = ctypes.c_long
        ole32.CoCreateInstance.argtypes = [
            ctypes.POINTER(Guid),
            ctypes.c_void_p,
            ctypes.c_ulong,
            ctypes.POINTER(Guid),
            ctypes.POINTER(ctypes.c_void_p),
        ]
        ole32.CoCreateInstance.restype = ctypes.c_long
        ole32.CoUninitialize.argtypes = []
        ole32.CoUninitialize.restype = None

        initialized = ole32.CoInitializeEx(None, COINIT_APARTMENTTHREADED) >= 0
        instance = ctypes.c_void_p()
        clsid = Guid.from_text("C2CF3110-460E-4FC1-B9D0-8A1C0C9CC4BD")
        iid = Guid.from_text("B92B56A9-8B55-4E14-9A89-0199BBB6F93B")
        try:
            result = ole32.CoCreateInstance(
                ctypes.byref(clsid),
                None,
                CLSCTX_LOCAL_SERVER,
                ctypes.byref(iid),
                ctypes.byref(instance),
            )
            if result < 0:
                return ""

            vtable = ctypes.cast(
                instance,
                ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)),
            ).contents
            get_position = ctypes.WINFUNCTYPE(
                ctypes.c_long,
                ctypes.c_void_p,
                ctypes.POINTER(ctypes.c_int),
            )(vtable[11])
            release = ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)(vtable[2])
            try:
                value = ctypes.c_int()
                result = get_position(instance, ctypes.byref(value))
                if result < 0:
                    return ""
                return WALLPAPER_POSITION_NAMES.get(value.value, "")
            finally:
                release(instance)
        finally:
            if initialized:
                ole32.CoUninitialize()
