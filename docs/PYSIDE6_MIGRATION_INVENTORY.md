# Inventario de migracao PyQt6 para PySide6 - Movaura

Base: `81f91e2491abe4f5d26ad75f11bd496caf7c3f59`.
Branch: `migration/pyside6`.

Este inventario foi produzido antes das alteracoes de codigo da migracao. Ele mapeia usos de Qt/PyQt6, risco, acao e teste esperado.

## Resumo

- Ocorrencias inventariadas: 236.
- Arquivos Python/config com Qt/PyQt6: 29.
- Areas de maior risco: `core/ai_generation/queue.py`, `ui/ai_generation_page.py`, `core/thumbnail_cache.py`, `renderers/video_renderer.py`, `core/tray.py`, `ui/control_panel.py`.

## Mapa tecnico

| Arquivo | Linha | Simbolo | Risco | Acao necessaria | Teste de cobertura |
|---|---:|---|---|---|---|
| `app.py` | 8 | `PyQt6, QTimer, QtCore` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `app.py` | 9 | `PyQt6, QIcon, QtGui` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `app.py` | 10 | `PyQt6, QApplication, QtWidgets` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `app.py` | 206 | `QApplication` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `app.py` | 211 | `.exec(` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `app.py` | 218 | `QApplication` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `app.py` | 222 | `QIcon` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `app.py` | 225 | `QTimer` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `app.py` | 240 | `.exec(` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `app.py` | 262 | `.exec(` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `app.py` | 267 | `.exec(` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `app.py` | 288 | `.exec(` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `core/ai_generation/providers.py` | 12 | `PyQt6, QtCore` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `core/ai_generation/providers.py` | 13 | `PyQt6, QImage, QtGui` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `core/ai_generation/providers.py` | 90 | `QImage` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `core/ai_generation/providers.py` | 179 | `QImage` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `core/ai_generation/providers.py` | 185 | `QImage` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `core/ai_generation/providers.py` | 233 | `QImage` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `core/ai_generation/providers.py` | 277 | `AlignmentFlag` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `core/ai_generation/providers.py` | 284 | `QImage` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `core/ai_generation/providers.py` | 292 | `QImage` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `core/ai_generation/providers.py` | 294 | `QImage` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `core/ai_generation/queue.py` | 7 | `PyQt6, QObject, QThread, QtCore, pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `core/ai_generation/queue.py` | 17 | `QObject` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `core/ai_generation/queue.py` | 18 | `pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `core/ai_generation/queue.py` | 19 | `pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `core/ai_generation/queue.py` | 20 | `pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `core/ai_generation/queue.py` | 21 | `pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `core/ai_generation/queue.py` | 22 | `pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `core/ai_generation/queue.py` | 129 | `QObject` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `core/ai_generation/queue.py` | 130 | `pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `core/ai_generation/queue.py` | 131 | `pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `core/ai_generation/queue.py` | 132 | `pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `core/ai_generation/queue.py` | 133 | `pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `core/ai_generation/queue.py` | 134 | `pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `core/ai_generation/queue.py` | 141 | `QObject` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `core/ai_generation/queue.py` | 147 | `QThread` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `core/ai_generation/queue.py` | 194 | `QThread` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `core/ai_generation/storage.py` | 10 | `PyQt6, QtCore` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `core/ai_generation/storage.py` | 11 | `PyQt6, QImage, QtGui` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `core/ai_generation/storage.py` | 146 | `QImage` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `core/ai_generation/storage.py` | 147 | `QImage` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `core/ai_generation/storage.py` | 161 | `QImage` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `core/ai_generation/storage.py` | 175 | `QImage` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `core/ai_generation/storage.py` | 177 | `QImage` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `core/engine.py` | 9 | `PyQt6, QTimer, QtCore` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `core/engine.py` | 10 | `PyQt6, QApplication, QtWidgets` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `core/engine.py` | 37 | `QApplication` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `core/engine.py` | 77 | `QTimer` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `core/engine.py` | 80 | `QTimer` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `core/engine.py` | 86 | `QTimer` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `core/engine.py` | 89 | `QTimer` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `core/engine.py` | 92 | `QTimer` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `core/engine.py` | 95 | `QTimer` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `core/engine.py` | 654 | `winId` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `core/hotkey_manager.py` | 7 | `PyQt6, QObject, QTimer, QtCore` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `core/hotkey_manager.py` | 19 | `QObject` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `core/hotkey_manager.py` | 25 | `QTimer` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `core/media_analyzer.py` | 10 | `PyQt6, QImage, QImageReader, QtGui` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `core/media_analyzer.py` | 100 | `QImage, QImageReader` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `core/monitor_manager.py` | 7 | `PyQt6, QtCore` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `core/plugin_manager.py` | 61 | `exec_` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `core/screensaver.py` | 10 | `PyQt6, QTimer, QtCore` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `core/screensaver.py` | 11 | `PyQt6, QApplication, QtWidgets` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `core/screensaver.py` | 48 | `QApplication` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `core/screensaver.py` | 54 | `QTimer` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `core/system_wallpaper.py` | 11 | `PyQt6, QImage, QtGui` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `core/system_wallpaper.py` | 97 | `QImage` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `core/thumbnail_cache.py` | 8 | `PyQt6, QObject, QTimer, QtCore, pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `core/thumbnail_cache.py` | 9 | `PyQt6, QIcon, QImage, QImageReader, QPixmap, QtGui` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `core/thumbnail_cache.py` | 10 | `PyQt6, QMediaPlayer, QVideoSink, QtMultimedia` | alto | Migrar imports multimedia e validar sinais/status/loop/thumbnail. | self-test; smoke de renderer video/gif/thumbnail; teste manual preview |
| `core/thumbnail_cache.py` | 15 | `QObject` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `core/thumbnail_cache.py` | 16 | `pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `core/thumbnail_cache.py` | 28 | `QMediaPlayer` | alto | Migrar imports multimedia e validar sinais/status/loop/thumbnail. | self-test; smoke de renderer video/gif/thumbnail; teste manual preview |
| `core/thumbnail_cache.py` | 29 | `QVideoSink` | alto | Migrar imports multimedia e validar sinais/status/loop/thumbnail. | self-test; smoke de renderer video/gif/thumbnail; teste manual preview |
| `core/thumbnail_cache.py` | 33 | `QTimer` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `core/thumbnail_cache.py` | 99 | `QTimer` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `core/thumbnail_cache.py` | 103 | `QImage, QImageReader` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `core/thumbnail_cache.py` | 110 | `QIcon` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `core/thumbnail_cache.py` | 111 | `QPixmap` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `core/thumbnail_cache.py` | 114 | `QIcon` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `core/tray.py` | 3 | `PyQt6, QAction, QIcon, QtGui` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `core/tray.py` | 4 | `PyQt6, QApplication, QMenu, QSystemTrayIcon, QtWidgets` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `core/tray.py` | 9 | `QApplication` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `core/tray.py` | 12 | `QIcon` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `core/tray.py` | 15 | `QIcon, QSystemTrayIcon` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `core/tray.py` | 21 | `QSystemTrayIcon` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `core/tray.py` | 31 | `QSystemTrayIcon` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `core/tray.py` | 35 | `QSystemTrayIcon` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `core/tray.py` | 36 | `QSystemTrayIcon` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `core/tray.py` | 39 | `QMenu` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `core/tray.py` | 40 | `QMenu` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `core/tray.py` | 41 | `QAction` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `core/tray.py` | 46 | `QAction` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `core/tray.py` | 50 | `QAction` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `core/tray.py` | 53 | `QAction` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `core/tray.py` | 56 | `QAction` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `core/tray.py` | 59 | `QAction` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `core/tray.py` | 63 | `QAction` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `core/wallpaper_window.py` | 3 | `PyQt6, QTimer, QtCore` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `core/wallpaper_window.py` | 4 | `PyQt6, QtWidgets` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `core/wallpaper_window.py` | 12 | `QTimer` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `core/wallpaper_window.py` | 16 | `WindowType` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `core/wallpaper_window.py` | 17 | `WindowType` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `core/wallpaper_window.py` | 18 | `WindowType` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `core/wallpaper_window.py` | 30 | `WindowType` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `core/wallpaper_window.py` | 31 | `WindowType` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `core/wallpaper_window.py` | 54 | `winId` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `LEIA-ME-PRIMEIRO.txt` | 41 | `PyQt6` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `native_host/README.md` | 10 | `PyQt6` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `plugins/sample_pulse/plugin.py` | 1 | `PyQt6, QTimer, QtCore` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `plugins/sample_pulse/plugin.py` | 10 | `QTimer` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `README.md` | 194 | `PyQt6` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `README.md` | 218 | `PyQt6` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `README.md` | 253 | `PyQt6` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `renderers/base.py` | 7 | `PyQt6, QtWidgets` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `renderers/color_renderer.py` | 1 | `PyQt6, QtGui` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `renderers/color_renderer.py` | 2 | `PyQt6, QtWidgets` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `renderers/factory.py` | 5 | `PyQt6, QtWidgets` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `renderers/gif_renderer.py` | 3 | `PyQt6, QtCore` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `renderers/gif_renderer.py` | 4 | `PyQt6, QMovie, QtGui` | alto | Migrar imports multimedia e validar sinais/status/loop/thumbnail. | self-test; smoke de renderer video/gif/thumbnail; teste manual preview |
| `renderers/gif_renderer.py` | 5 | `PyQt6, QtWidgets` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `renderers/gif_renderer.py` | 14 | `QMovie` | alto | Migrar imports multimedia e validar sinais/status/loop/thumbnail. | self-test; smoke de renderer video/gif/thumbnail; teste manual preview |
| `renderers/gif_renderer.py` | 15 | `AlignmentFlag` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `renderers/gif_renderer.py` | 19 | `QMovie` | alto | Migrar imports multimedia e validar sinais/status/loop/thumbnail. | self-test; smoke de renderer video/gif/thumbnail; teste manual preview |
| `renderers/gif_renderer.py` | 20 | `QMovie` | alto | Migrar imports multimedia e validar sinais/status/loop/thumbnail. | self-test; smoke de renderer video/gif/thumbnail; teste manual preview |
| `renderers/opengl_renderer.py` | 5 | `PyQt6, QTimer, QtCore` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `renderers/opengl_renderer.py` | 6 | `PyQt6, QtGui` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `renderers/opengl_renderer.py` | 7 | `PyQt6, QtOpenGL, QtOpenGLWidgets` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `renderers/opengl_renderer.py` | 17 | `QTimer` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `renderers/video_renderer.py` | 3 | `PyQt6, QtCore` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `renderers/video_renderer.py` | 4 | `PyQt6, QAudioOutput, QMediaPlayer, QtMultimedia` | alto | Migrar imports multimedia e validar sinais/status/loop/thumbnail. | self-test; smoke de renderer video/gif/thumbnail; teste manual preview |
| `renderers/video_renderer.py` | 5 | `PyQt6, QVideoWidget, QtMultimedia, QtMultimediaWidgets` | alto | Migrar imports multimedia e validar sinais/status/loop/thumbnail. | self-test; smoke de renderer video/gif/thumbnail; teste manual preview |
| `renderers/video_renderer.py` | 10 | `QVideoWidget` | alto | Migrar imports multimedia e validar sinais/status/loop/thumbnail. | self-test; smoke de renderer video/gif/thumbnail; teste manual preview |
| `renderers/video_renderer.py` | 14 | `QMediaPlayer` | alto | Migrar imports multimedia e validar sinais/status/loop/thumbnail. | self-test; smoke de renderer video/gif/thumbnail; teste manual preview |
| `renderers/video_renderer.py` | 15 | `QAudioOutput` | alto | Migrar imports multimedia e validar sinais/status/loop/thumbnail. | self-test; smoke de renderer video/gif/thumbnail; teste manual preview |
| `renderers/video_renderer.py` | 35 | `QMediaPlayer` | alto | Migrar imports multimedia e validar sinais/status/loop/thumbnail. | self-test; smoke de renderer video/gif/thumbnail; teste manual preview |
| `renderers/video_renderer.py` | 36 | `QMediaPlayer` | alto | Migrar imports multimedia e validar sinais/status/loop/thumbnail. | self-test; smoke de renderer video/gif/thumbnail; teste manual preview |
| `requirements.txt` | 1 | `PyQt6` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `requirements.txt` | 2 | `PyQt6` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `requirements.txt` | 3 | `PyQt6, sip` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `scripts/run_ai_generation_tests.py` | 13 | `PyQt6, QThread, QTimer, QtCore` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `scripts/run_ai_generation_tests.py` | 14 | `PyQt6, QImage, QtGui` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `scripts/run_ai_generation_tests.py` | 15 | `PyQt6, QApplication, QtWidgets` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `scripts/run_ai_generation_tests.py` | 94 | `QApplication` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `scripts/run_ai_generation_tests.py` | 98 | `QTimer` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `scripts/run_ai_generation_tests.py` | 100 | `QTimer` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `scripts/run_ai_generation_tests.py` | 114 | `.exec(` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `scripts/run_ai_generation_tests.py` | 155 | `QImage` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `scripts/run_ai_generation_tests.py` | 254 | `QThread` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `scripts/run_ai_generation_tests.py` | 269 | `QThread` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `scripts/run_ai_generation_tests.py` | 270 | `QThread` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `scripts/run_ai_generation_tests.py` | 280 | `QThread` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `scripts/run_ai_generation_tests.py` | 423 | `QImage` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `scripts/run_ai_generation_tests.py` | 500 | `QImage` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `scripts/run_ai_generation_tests.py` | 545 | `QImage` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `scripts/run_ai_generation_tests.py` | 566 | `QApplication` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `scripts/run_product_smoke_tests.py` | 12 | `PyQt6, QtCore` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `scripts/run_product_smoke_tests.py` | 13 | `PyQt6, QApplication, QtWidgets` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `scripts/run_product_smoke_tests.py` | 295 | `QApplication` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `ui/activation_dialog.py` | 3 | `PyQt6, QtWidgets` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `ui/ai_generation_page.py` | 7 | `PyQt6, QtCore, pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `ui/ai_generation_page.py` | 8 | `PyQt6, QIcon, QPixmap, QtGui` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `ui/ai_generation_page.py` | 9 | `PyQt6, QtWidgets` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `ui/ai_generation_page.py` | 10 | `QApplication` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `ui/ai_generation_page.py` | 45 | `pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `ui/ai_generation_page.py` | 46 | `pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `ui/ai_generation_page.py` | 47 | `pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `ui/ai_generation_page.py` | 48 | `pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `ui/ai_generation_page.py` | 49 | `pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `ui/ai_generation_page.py` | 50 | `pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `ui/ai_generation_page.py` | 261 | `AlignmentFlag` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/ai_generation_page.py` | 355 | `QApplication` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `ui/ai_generation_page.py` | 469 | `QIcon, QPixmap` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `ui/ai_generation_page.py` | 608 | `ItemDataRole` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/ai_generation_page.py` | 612 | `ItemDataRole` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/ai_generation_page.py` | 648 | `ItemDataRole` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/control_panel.py` | 10 | `PyQt6, QObject, QTimer, QtCore, pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `ui/control_panel.py` | 11 | `PyQt6, QIcon, QPixmap, QtGui` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `ui/control_panel.py` | 12 | `PyQt6, QtWidgets` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `ui/control_panel.py` | 13 | `QApplication` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `ui/control_panel.py` | 17 | `QFileDialog` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/control_panel.py` | 113 | `QObject` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `ui/control_panel.py` | 114 | `pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `ui/control_panel.py` | 118 | `QApplication` | medio | Migrar imports e validar event loop/tray/menu/quit. | scripts/run_product_smoke_tests.py; teste manual tray |
| `ui/control_panel.py` | 143 | `QTimer` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/control_panel.py` | 147 | `QTimer` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/control_panel.py` | 152 | `QIcon` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `ui/control_panel.py` | 159 | `QTimer` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/control_panel.py` | 163 | `QTimer` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/control_panel.py` | 174 | `QTimer` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/control_panel.py` | 175 | `QTimer` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/control_panel.py` | 187 | `QTimer` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/control_panel.py` | 188 | `QTimer` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/control_panel.py` | 229 | `QPixmap` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `ui/control_panel.py` | 844 | `.exec(` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/control_panel.py` | 857 | `.exec(` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/control_panel.py` | 870 | `.exec(` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/control_panel.py` | 893 | `.exec(` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/control_panel.py` | 900 | `.exec(` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/control_panel.py` | 905 | `.exec(` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/control_panel.py` | 922 | `.exec(` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/control_panel.py` | 942 | `QFileDialog` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/library_dialog.py` | 5 | `PyQt6, QtCore, pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `ui/library_dialog.py` | 6 | `PyQt6, QIcon, QPixmap, QtGui` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `ui/library_dialog.py` | 7 | `PyQt6, QtWidgets` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `ui/library_dialog.py` | 10 | `QFileDialog` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/library_dialog.py` | 45 | `pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `ui/library_dialog.py` | 46 | `pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `ui/library_dialog.py` | 145 | `ItemDataRole` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/library_dialog.py` | 160 | `QFileDialog` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/library_dialog.py` | 168 | `QFileDialog` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/library_dialog.py` | 207 | `QFileDialog` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/library_dialog.py` | 249 | `ItemDataRole` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/library_dialog.py` | 281 | `QIcon` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `ui/library_dialog.py` | 283 | `QPixmap` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `ui/library_dialog.py` | 285 | `QIcon` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `ui/library_dialog.py` | 297 | `QPixmap` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `ui/library_dialog.py` | 299 | `QIcon` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `ui/library_dialog.py` | 308 | `QPixmap` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `ui/library_dialog.py` | 310 | `QIcon` | medio | Migrar imports e validar carregamento/salvamento de imagens/icons. | scripts/run_ai_generation_tests.py; library smoke; screenshots UI |
| `ui/product_dialogs.py` | 5 | `PyQt6, QtCore, pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `ui/product_dialogs.py` | 6 | `PyQt6, QtWidgets` | baixo | Trocar import/dependencia/documentacao para PySide6 ou marcar historico. | busca final por PyQt6; build standalone sem PyQt6 |
| `ui/product_dialogs.py` | 11 | `QFileDialog` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/product_dialogs.py` | 38 | `pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `ui/product_dialogs.py` | 98 | `QFileDialog` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/product_dialogs.py` | 164 | `QFileDialog` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/product_dialogs.py` | 185 | `pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `ui/product_dialogs.py` | 238 | `pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `ui/product_dialogs.py` | 278 | `QFileDialog` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/product_dialogs.py` | 334 | `pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `ui/product_dialogs.py` | 335 | `pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |
| `ui/product_dialogs.py` | 482 | `QFileDialog` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/product_dialogs.py` | 678 | `QFileDialog` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/product_dialogs.py` | 683 | `QFileDialog` | baixo | Substituir referencia/documentacao conforme contexto. | compileall; busca final PyQt6 |
| `ui/product_dialogs.py` | 701 | `pyqtSignal` | alto | Migrar pyqtSignal para Signal e validar ciclo QThread/worker/parent/deleteLater. | scripts/run_ai_generation_tests.py; smoke tests de shutdown |

## Observacoes de migracao

- `pyqtSignal` deve virar `Signal` importado de `PySide6.QtCore`.
- Nao ha ocorrencias de `pyqtSlot`, `pyqtProperty`, `sip.delete` ou `sip.isdeleted` no codigo de producao inventariado.
- `QAction` permanece em `QtGui`, compativel com PySide6.
- `QMediaPlayer`, `QAudioOutput`, `QVideoWidget` e `QVideoSink` exigem validacao manual alem de smoke tests offscreen.
- `file://` em update checker e manifestos locais de teste nao devem ser confundidos com provider real de IA.
- O Movaura Beta nao foi lido nem modificado para produzir este inventario.
