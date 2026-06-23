@echo off
setlocal EnableExtensions
chcp 65001 >nul
title CUMA - Compilar Windows
cd /d "%~dp0"

if not exist "cuma.py" (
  echo [ERRO] cuma.py nao encontrado nesta pasta.
  pause
  exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
  echo [ERRO] Python nao encontrado. Instale Python 3.11+ e marque "Add Python to PATH".
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Criando ambiente virtual .venv...
  python -m venv .venv
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

if exist build rd /s /q build
if exist dist rd /s /q dist

echo.
echo Gerando executavel com PyInstaller...
python -m PyInstaller --noconfirm cuma.spec
if errorlevel 1 (
  echo [ERRO] Falha ao criar executavel.
  pause
  exit /b 1
)

echo.
echo Organizando pasta final...
if not exist "dist\cuma\_internal" mkdir "dist\cuma\_internal"

if exist "manual_do_programa.txt" copy /Y "manual_do_programa.txt" "dist\cuma\manual_do_programa.txt" >nul
if exist "LEIA-ME.txt" copy /Y "LEIA-ME.txt" "dist\cuma\LEIA-ME.txt" >nul

for %%F in (cuma_settings_template.json cuma_logo.png app_icon.ico) do (
  if exist "dist\cuma\%%F" move /Y "dist\cuma\%%F" "dist\cuma\_internal\%%F" >nul
)

for %%F in (
  config_cuma.json
  cuma_interface_colors.json
  cuma_device_profiles.json
  version.json
  cuma_version_state.json
  cuma_version_history.json
  CUMA.log
  erro.txt
  debug_completo_cuma.txt
  debug_patch_mesclado.json
  debug_patch_final_devices_languages.json
  RELATORIO_RELEASE_1_081_1.txt
) do (
  if exist "dist\cuma\%%F" del /f /q "dist\cuma\%%F" >nul 2>nul
  if exist "dist\cuma\_internal\%%F" del /f /q "dist\cuma\_internal\%%F" >nul 2>nul
)

if exist "dist\cuma\limpos" rd /s /q "dist\cuma\limpos"

echo.
echo Compactando release...
if exist CUMA_windows.zip del /f /q CUMA_windows.zip
powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path 'dist\cuma\*' -DestinationPath 'CUMA_windows.zip' -Force"

echo.
echo OK. Executavel em: dist\cuma\cuma.exe
echo ZIP em: CUMA_windows.zip
echo.
echo Observacao: as configuracoes do usuario serao criadas em %%APPDATA%%\CUMA\cuma_settings.json.
pause
endlocal
