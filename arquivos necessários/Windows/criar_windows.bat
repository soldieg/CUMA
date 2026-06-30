@echo off
setlocal EnableExtensions
chcp 65001 >nul
title CUMA - Build Windows autocontido
set "TOOLS_DIR=%~dp0"
set "ROOT_DIR=%~dp0..\.."
set "SRC_DIR=%ROOT_DIR%\GitHub"
set "ZIP_DIR=%ROOT_DIR%\ZIP final\Windows"
set "APP_VERSION=1.100.27"
set "OUT_DIR=dist\CUMA_windows"
set "ZIP_NAME=CUMA_windows.zip"
set "ZIP_PATH=%ZIP_DIR%\%ZIP_NAME%"
set "RELEASE_NOTES=NOTAS_RELEASE_1.100.27_GITHUB.txt"

if not exist "%SRC_DIR%\cuma.py" (
  echo [ERRO] cuma.py nao encontrado em "%SRC_DIR%".
  pause
  exit /b 1
)

if not exist "%ZIP_DIR%" mkdir "%ZIP_DIR%"
cd /d "%SRC_DIR%"

where python >nul 2>nul
if errorlevel 1 (
  echo [ERRO] Python 3.11+ nao encontrado para compilar.
  echo O usuario final NAO precisa de Python, mas o computador de build precisa.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Criando ambiente virtual .venv...
  python -m venv .venv
  if errorlevel 1 exit /b 1
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

if exist build rd /s /q build
if exist dist rd /s /q dist

echo.
echo Gerando CUMA_windows autocontido...
python -m PyInstaller --noconfirm cuma_windows.spec
if errorlevel 1 (
  echo [ERRO] PyInstaller falhou.
  pause
  exit /b 1
)

if not exist "%OUT_DIR%\cuma.exe" (
  echo [ERRO] cuma.exe nao foi criado.
  pause
  exit /b 1
)
if not exist "%OUT_DIR%\cuma_updater.exe" (
  echo [ERRO] cuma_updater.exe nao foi criado.
  pause
  exit /b 1
)

if exist "manual_do_programa.txt" copy /Y "manual_do_programa.txt" "%OUT_DIR%\manual_do_programa.txt" >nul
if exist "LEIA-ME.txt" copy /Y "LEIA-ME.txt" "%OUT_DIR%\LEIA-ME.txt" >nul
if exist "README.md" copy /Y "README.md" "%OUT_DIR%\README.md" >nul
if exist "LICENSE" copy /Y "LICENSE" "%OUT_DIR%\LICENSE" >nul
if exist "NOTAS_RELEASE_1.100.27_GITHUB.txt" copy /Y "NOTAS_RELEASE_1.100.27_GITHUB.txt" "%OUT_DIR%\NOTAS_RELEASE_1.100.27_GITHUB.txt" >nul
if exist "AUDITORIA_DEBUG_1.100.27.txt" copy /Y "AUDITORIA_DEBUG_1.100.27.txt" "%OUT_DIR%\AUDITORIA_DEBUG_1.100.27.txt" >nul

for %%F in (cuma_settings_template.json cuma_logo.png app_icon.ico) do (
  if exist "%OUT_DIR%\%%F" (
    if not exist "%OUT_DIR%\_internal" mkdir "%OUT_DIR%\_internal"
    move /Y "%OUT_DIR%\%%F" "%OUT_DIR%\_internal\%%F" >nul
  )
)

for %%F in (CUMA.log CUMA_update.log erro.txt debug_completo_cuma.txt cuma_settings.json config_cuma.json) do (
  if exist "%OUT_DIR%\%%F" del /f /q "%OUT_DIR%\%%F" >nul 2>nul
)
if exist "%OUT_DIR%\.cuma_user_data" rd /s /q "%OUT_DIR%\.cuma_user_data"
if exist "%OUT_DIR%\limpos" rd /s /q "%OUT_DIR%\limpos"

echo Compactando %ZIP_PATH%...
if exist "%ZIP_PATH%" del /f /q "%ZIP_PATH%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path '%OUT_DIR%\*' -DestinationPath '%ZIP_PATH%' -Force"
if errorlevel 1 exit /b 1

echo Atualizando manifesto para Windows...
python scripts\preparar_manifesto_release.py soldieg CUMA %APP_VERSION% "%ZIP_PATH%" Stable "%RELEASE_NOTES%" windows
if errorlevel 1 echo [AVISO] Nao foi possivel atualizar stable.json.

echo.
echo OK: %ZIP_PATH%
if "%CI%"=="" pause
endlocal
