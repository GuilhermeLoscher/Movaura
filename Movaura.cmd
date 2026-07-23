@echo off
setlocal
title Movaura Launcher
set "MOVAURA_ROOT=%~dp0"
cd /d "%MOVAURA_ROOT%"

set "MOVAURA_PYTHON=%MOVAURA_ROOT%.venv\Scripts\python.exe"
if exist "%MOVAURA_PYTHON%" (
    if /i "%~1"=="--startup" (
        "%MOVAURA_PYTHON%" "%MOVAURA_ROOT%\app.py" --startup
    ) else (
        "%MOVAURA_PYTHON%" "%MOVAURA_ROOT%\app.py" --control-panel
    )
    goto :done
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    if /i "%~1"=="--startup" (
        python "%MOVAURA_ROOT%\app.py" --startup
    ) else (
        python "%MOVAURA_ROOT%\app.py" --control-panel
    )
    goto :done
)

where py >nul 2>nul
if %errorlevel% equ 0 (
    if /i "%~1"=="--startup" (
        py -3 "%MOVAURA_ROOT%\app.py" --startup
    ) else (
        py -3 "%MOVAURA_ROOT%\app.py" --control-panel
    )
    goto :done
)

echo Movaura nao encontrou o Python no PATH do Windows.
echo.
echo Abra o PowerShell onde o comando "python app.py" funciona.
echo Execute: where.exe python
echo Envie o resultado para configurarmos o caminho correto.
echo.
pause
exit /b 1

:done
if %errorlevel% neq 0 (
    echo.
    echo Movaura encerrou com erro. Envie a mensagem acima.
    echo.
    pause
)
