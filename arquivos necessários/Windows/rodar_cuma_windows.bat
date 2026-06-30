@echo off
setlocal EnableExtensions
chcp 65001 >nul
set "SRC_DIR=%~dp0..\..\GitHub"
cd /d "%SRC_DIR%"
where python >nul 2>nul
if errorlevel 1 (
  echo [ERRO] Python nao encontrado para modo desenvolvimento.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" python -m venv .venv
call ".venv\Scripts\activate.bat"
python -m pip install -r requirements.txt
python cuma.py
endlocal
