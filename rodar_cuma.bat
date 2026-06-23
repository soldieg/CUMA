@echo off
setlocal EnableExtensions
chcp 65001 >nul
title CUMA - Rodar aplicativo
cd /d "%~dp0"

if not exist "cuma.py" (
  echo [ERRO] cuma.py nao encontrado nesta pasta.
  pause
  exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
  where py >nul 2>nul
  if errorlevel 1 (
    echo [ERRO] Python nao encontrado. Instale Python 3.11+ e marque "Add Python to PATH".
    pause
    exit /b 1
  )
)

if not exist ".venv\Scripts\python.exe" (
  echo Criando ambiente virtual .venv...
  py -3 -m venv .venv 2>nul
  if errorlevel 1 python -m venv .venv
  if errorlevel 1 (
    echo [ERRO] Falha ao criar ambiente virtual.
    pause
    exit /b 1
  )
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo [ERRO] Falha ao instalar dependencias.
  pause
  exit /b 1
)

python cuma.py
pause
endlocal
