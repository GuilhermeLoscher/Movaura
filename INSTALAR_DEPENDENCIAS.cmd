@echo off
setlocal
title Instalador de dependencias do Movaura
set "MOVAURA_ROOT=%~dp0"
cd /d "%MOVAURA_ROOT%"

where python >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_COMMAND=python"
    goto :install
)

where py >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_COMMAND=py -3"
    goto :install
)

echo Python 3 nao foi encontrado.
echo Instale o Python 3.12 ou superior e execute este arquivo novamente.
pause
exit /b 1

:install
echo Criando ambiente local do Movaura...
%PYTHON_COMMAND% -m venv "%MOVAURA_ROOT%.venv"
if %errorlevel% neq 0 goto :error

echo Instalando dependencias...
"%MOVAURA_ROOT%.venv\Scripts\python.exe" -m pip install --upgrade pip
if %errorlevel% neq 0 goto :error
"%MOVAURA_ROOT%.venv\Scripts\python.exe" -m pip install -r "%MOVAURA_ROOT%requirements.txt"
if %errorlevel% neq 0 goto :error

echo.
echo Instalacao concluida. Abra INICIAR_MOVAURA.cmd.
pause
exit /b 0

:error
echo.
echo Nao foi possivel concluir a instalacao.
pause
exit /b 1
