@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul 2>nul
title CUMA - Compilar Windows
set "PYTHONDONTWRITEBYTECODE=1"
set "PIP_DISABLE_PIP_VERSION_CHECK=1"

for %%I in ("%~dp0..\..") do set "REPO_ROOT=%%~fI"
set "ZIP_DIR=%REPO_ROOT%\ZIP final\Windows"
set "OUT_DIR=%REPO_ROOT%\dist\CUMA_windows"
set "ZIP_PATH=%ZIP_DIR%\CUMA_windows.zip"
set "VENV_DIR=%REPO_ROOT%\.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "BOOTSTRAP_LOG=%REPO_ROOT%\CUMA_bootstrap.log"
set "BUILD_LOG=%REPO_ROOT%\CUMA_build_windows.log"
set "APP_VERSION=1.100.37"

echo ============================================================
echo CUMA - COMPILACAO WINDOWS
echo Repositorio: "%REPO_ROOT%"
echo Saida:       "%ZIP_PATH%"
echo ============================================================
echo.

if /I "%~1"=="--help" goto :usage
if /I "%~1"=="-h" goto :usage
if /I "%~1"=="/?" goto :usage
if /I "%~1"=="--clean" goto :clean_only
if /I "%~1"=="--diagnostico" goto :diagnostic

call :validate_structure
if errorlevel 1 goto :fail

if /I "%~1"=="--check" (
  call :detect_python_only
  if errorlevel 1 (
    echo [AVISO] Estrutura correta, mas nenhum Python 3.10 ou superior foi encontrado.
    echo O usuario final nao precisa de Python. Apenas a compilacao local precisa.
    exit /b 1
  )
  echo [OK] Estrutura e Python de compilacao localizados corretamente.
  exit /b 0
)

cd /d "%REPO_ROOT%" || (
  echo [ERRO] Nao foi possivel acessar a pasta do repositorio.
  goto :fail
)

call :ensure_venv
if errorlevel 1 goto :fail

echo Validando codigo antes de instalar ou compilar...
"%VENV_PY%" -B "%REPO_ROOT%\scripts\auditoria_integridade.py" --version %APP_VERSION%
if errorlevel 1 (
  echo [ERRO] A auditoria estrutural falhou.
  goto :fail
)

echo Atualizando ferramentas de build...
"%VENV_PY%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
  echo [ERRO] Nao foi possivel atualizar pip/setuptools/wheel.
  goto :fail
)

echo Instalando dependencias...
"%VENV_PY%" -m pip install -r "%REPO_ROOT%\requirements.txt"
if errorlevel 1 (
  echo [ERRO] Nao foi possivel instalar requirements.txt.
  goto :fail
)

echo Conferindo dependencias essenciais...
"%VENV_PY%" -c "import fitz, numpy, PIL, tkinter, PyInstaller"
if errorlevel 1 (
  echo [ERRO] Uma ou mais dependencias essenciais nao podem ser importadas.
  goto :fail
)

call :clean_build_outputs
if errorlevel 1 goto :fail
if not exist "%ZIP_DIR%" mkdir "%ZIP_DIR%"
if errorlevel 1 (
  echo [ERRO] Nao foi possivel criar:
  echo "%ZIP_DIR%"
  goto :fail
)

> "%BUILD_LOG%" echo CUMA %APP_VERSION% - build Windows
>>"%BUILD_LOG%" echo Inicio: %DATE% %TIME%
>>"%BUILD_LOG%" echo Repositorio: "%REPO_ROOT%"
>>"%BUILD_LOG%" echo Python:
"%VENV_PY%" --version >>"%BUILD_LOG%" 2>&1

echo Compilando executaveis autocontidos...
"%VENV_PY%" -m PyInstaller --noconfirm --clean "%REPO_ROOT%\cuma_windows.spec" >>"%BUILD_LOG%" 2>&1
if errorlevel 1 (
  echo [ERRO] O PyInstaller falhou.
  echo Consulte:
  echo "%BUILD_LOG%"
  goto :fail
)

if not exist "%OUT_DIR%\cuma.exe" (
  echo [ERRO] cuma.exe nao foi criado.
  goto :fail
)
if not exist "%OUT_DIR%\cuma_updater.exe" (
  echo [ERRO] cuma_updater.exe nao foi criado.
  goto :fail
)

echo Organizando arquivos da distribuicao...
for %%F in (manual_do_programa.txt LEIA-ME.txt README.md LICENSE NOTAS_RELEASE.md CHANGELOG.md) do (
  if exist "%REPO_ROOT%\%%F" copy /Y "%REPO_ROOT%\%%F" "%OUT_DIR%\%%F" >nul
)

for %%F in (CUMA.log CUMA_update.log erro.txt CUMA_bootstrap.log CUMA_build_windows.log debug_completo_cuma.txt cuma_settings.json config_cuma.json) do (
  if exist "%OUT_DIR%\%%F" del /f /q "%OUT_DIR%\%%F" >nul 2>nul
)
if exist "%OUT_DIR%\.cuma_user_data" rd /s /q "%OUT_DIR%\.cuma_user_data"
if exist "%OUT_DIR%\limpos" rd /s /q "%OUT_DIR%\limpos"
if exist "%OUT_DIR%\__pycache__" rd /s /q "%OUT_DIR%\__pycache__"

if exist "%ZIP_PATH%" del /f /q "%ZIP_PATH%"
set "CUMA_ZIP_SOURCE=%OUT_DIR%"
set "CUMA_ZIP_TARGET=%ZIP_PATH%"

echo Compactando pacote...
powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $source=$env:CUMA_ZIP_SOURCE; $target=$env:CUMA_ZIP_TARGET; if(-not (Test-Path -LiteralPath $source -PathType Container)){throw 'Pasta de saida ausente: ' + $source}; $items=Get-ChildItem -LiteralPath $source -Force; if(-not $items){throw 'Pasta de saida vazia: ' + $source}; if(Test-Path -LiteralPath $target){Remove-Item -LiteralPath $target -Force}; Compress-Archive -Path (Join-Path $source '*') -DestinationPath $target -CompressionLevel Optimal -Force"
if errorlevel 1 (
  echo [ERRO] O PowerShell nao conseguiu criar o ZIP.
  goto :fail
)

if not exist "%ZIP_PATH%" (
  echo [ERRO] O ZIP final nao foi criado.
  goto :fail
)

for %%A in ("%ZIP_PATH%") do set "ZIP_SIZE=%%~zA"
if "%ZIP_SIZE%"=="0" (
  echo [ERRO] O ZIP final foi criado vazio.
  goto :fail
)

echo Validando o pacote final...
"%VENV_PY%" -B "%REPO_ROOT%\scripts\release_pipeline.py" verify-asset --platform windows --path "%ZIP_PATH%"
if errorlevel 1 (
  echo [ERRO] O ZIP foi criado, mas nao passou na validacao interna.
  goto :fail
)

if /I "%CUMA_SKIP_MANIFEST%"=="1" (
  echo Manifesto local ignorado pelo pipeline de release.
) else (
  echo Atualizando manifesto local...
  "%VENV_PY%" -B "%REPO_ROOT%\scripts\preparar_manifesto_release.py" soldieg CUMA %APP_VERSION% "%ZIP_PATH%" Stable "%REPO_ROOT%\NOTAS_RELEASE.md" windows
  if errorlevel 1 echo [AVISO] O pacote foi criado, mas o stable.json nao foi atualizado.
)

>>"%BUILD_LOG%" echo Fim: %DATE% %TIME%
>>"%BUILD_LOG%" echo Pacote: "%ZIP_PATH%"

echo.
echo [OK] Compilacao concluida:
echo "%ZIP_PATH%"
echo Log:
echo "%BUILD_LOG%"
if "%CI%"=="" pause
exit /b 0

:validate_structure
set "STRUCTURE_ERROR=0"
for %%F in (cuma.py cuma_updater.py requirements.txt cuma_build_info.json cuma_windows.spec) do (
  if not exist "%REPO_ROOT%\%%F" (
    echo [ERRO] Arquivo obrigatorio nao encontrado:
    echo "%REPO_ROOT%\%%F"
    set "STRUCTURE_ERROR=1"
  )
)
for %%F in (auditoria_integridade.py preparar_manifesto_release.py release_pipeline.py testar_bats_windows.py) do (
  if not exist "%REPO_ROOT%\scripts\%%F" (
    echo [ERRO] Script obrigatorio nao encontrado:
    echo "%REPO_ROOT%\scripts\%%F"
    set "STRUCTURE_ERROR=1"
  )
)
if "%STRUCTURE_ERROR%"=="1" exit /b 1
exit /b 0

:clean_build_outputs
echo Limpando saidas anteriores...
if exist "%REPO_ROOT%\build" rd /s /q "%REPO_ROOT%\build"
if exist "%REPO_ROOT%\dist" rd /s /q "%REPO_ROOT%\dist"
if exist "%ZIP_PATH%" del /f /q "%ZIP_PATH%"
if exist "%REPO_ROOT%\__pycache__" rd /s /q "%REPO_ROOT%\__pycache__"
if exist "%REPO_ROOT%\scripts\__pycache__" rd /s /q "%REPO_ROOT%\scripts\__pycache__"
if exist "%REPO_ROOT%\tests\__pycache__" rd /s /q "%REPO_ROOT%\tests\__pycache__"
exit /b 0

:clean_only
call :clean_build_outputs
echo [OK] Saidas de build e caches do projeto foram removidos.
if "%CI%"=="" pause
exit /b 0

:diagnostic
> "%BOOTSTRAP_LOG%" echo CUMA - diagnostico de build Windows
>>"%BOOTSTRAP_LOG%" echo Data: %DATE% %TIME%
>>"%BOOTSTRAP_LOG%" echo Repositorio: "%REPO_ROOT%"
>>"%BOOTSTRAP_LOG%" echo Venv: "%VENV_DIR%"
>>"%BOOTSTRAP_LOG%" echo Saida: "%ZIP_PATH%"
>>"%BOOTSTRAP_LOG%" echo.
>>"%BOOTSTRAP_LOG%" echo === WHERE ===
where py >>"%BOOTSTRAP_LOG%" 2>&1
where python >>"%BOOTSTRAP_LOG%" 2>&1
where python3 >>"%BOOTSTRAP_LOG%" 2>&1
where powershell >>"%BOOTSTRAP_LOG%" 2>&1
if exist "%VENV_PY%" (
  >>"%BOOTSTRAP_LOG%" echo.
  >>"%BOOTSTRAP_LOG%" echo === PYTHON DO VENV ===
  "%VENV_PY%" --version >>"%BOOTSTRAP_LOG%" 2>&1
  "%VENV_PY%" -m pip --version >>"%BOOTSTRAP_LOG%" 2>&1
  "%VENV_PY%" -m PyInstaller --version >>"%BOOTSTRAP_LOG%" 2>&1
)
echo Diagnostico salvo em:
echo "%BOOTSTRAP_LOG%"
type "%BOOTSTRAP_LOG%"
if "%CI%"=="" pause
exit /b 0

:ensure_venv
if exist "%VENV_PY%" (
  "%VENV_PY%" -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
  if not errorlevel 1 exit /b 0
  echo [AVISO] Ambiente virtual existente esta invalido. Recriando...
  rd /s /q "%VENV_DIR%" >nul 2>nul
)

echo Criando ambiente virtual...
call :create_venv
if exist "%VENV_PY%" exit /b 0

call :offer_python_install
if exist "%VENV_PY%" exit /b 0

echo.
echo [ERRO] Nao foi possivel criar o ambiente virtual.
echo Consulte:
echo "%BOOTSTRAP_LOG%"
echo.
echo Instale o Python 3.11 para compilar:
echo winget install --id Python.Python.3.11 -e --scope user
exit /b 1

:create_venv
if exist "%VENV_DIR%" rd /s /q "%VENV_DIR%" >nul 2>nul
> "%BOOTSTRAP_LOG%" echo CUMA %APP_VERSION% - diagnostico de Python

call :try_direct_python "%LocalAppData%\Programs\Python\Python314\python.exe"
if exist "%VENV_PY%" exit /b 0
call :try_direct_python "%LocalAppData%\Programs\Python\Python313\python.exe"
if exist "%VENV_PY%" exit /b 0
call :try_direct_python "%LocalAppData%\Programs\Python\Python312\python.exe"
if exist "%VENV_PY%" exit /b 0
call :try_direct_python "%LocalAppData%\Programs\Python\Python311\python.exe"
if exist "%VENV_PY%" exit /b 0
call :try_direct_python "%LocalAppData%\Programs\Python\Python310\python.exe"
if exist "%VENV_PY%" exit /b 0

call :try_direct_python "%ProgramFiles%\Python314\python.exe"
if exist "%VENV_PY%" exit /b 0
call :try_direct_python "%ProgramFiles%\Python313\python.exe"
if exist "%VENV_PY%" exit /b 0
call :try_direct_python "%ProgramFiles%\Python312\python.exe"
if exist "%VENV_PY%" exit /b 0
call :try_direct_python "%ProgramFiles%\Python311\python.exe"
if exist "%VENV_PY%" exit /b 0
call :try_direct_python "%ProgramFiles%\Python310\python.exe"
if exist "%VENV_PY%" exit /b 0

for %%V in (3.14 3.13 3.12 3.11 3.10 3) do (
  call :try_py_launcher %%V
  if exist "%VENV_PY%" exit /b 0
)

call :try_command_python python
if exist "%VENV_PY%" exit /b 0
call :try_command_python python3
if exist "%VENV_PY%" exit /b 0
exit /b 1

:try_direct_python
set "PY_CANDIDATE=%~1"
if not exist "%PY_CANDIDATE%" exit /b 1
"%PY_CANDIDATE%" -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
if errorlevel 1 exit /b 1
echo Tentando "%PY_CANDIDATE%"...
>>"%BOOTSTRAP_LOG%" echo Tentando "%PY_CANDIDATE%"
"%PY_CANDIDATE%" -m venv "%VENV_DIR%" >>"%BOOTSTRAP_LOG%" 2>&1
if exist "%VENV_PY%" exit /b 0
if exist "%VENV_DIR%" rd /s /q "%VENV_DIR%" >nul 2>nul
exit /b 1

:try_py_launcher
where py >nul 2>nul
if errorlevel 1 exit /b 1
py -%~1 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
if errorlevel 1 exit /b 1
echo Tentando py -%~1...
>>"%BOOTSTRAP_LOG%" echo Tentando py -%~1
py -%~1 -m venv "%VENV_DIR%" >>"%BOOTSTRAP_LOG%" 2>&1
if exist "%VENV_PY%" exit /b 0
if exist "%VENV_DIR%" rd /s /q "%VENV_DIR%" >nul 2>nul
exit /b 1

:try_command_python
where %~1 >nul 2>nul
if errorlevel 1 exit /b 1
%~1 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
if errorlevel 1 exit /b 1
echo Tentando %~1...
>>"%BOOTSTRAP_LOG%" echo Tentando %~1
%~1 -m venv "%VENV_DIR%" >>"%BOOTSTRAP_LOG%" 2>&1
if exist "%VENV_PY%" exit /b 0
if exist "%VENV_DIR%" rd /s /q "%VENV_DIR%" >nul 2>nul
exit /b 1

:detect_python_only
if exist "%VENV_PY%" (
  "%VENV_PY%" -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
  if not errorlevel 1 exit /b 0
)
for %%P in (
  "%LocalAppData%\Programs\Python\Python314\python.exe"
  "%LocalAppData%\Programs\Python\Python313\python.exe"
  "%LocalAppData%\Programs\Python\Python312\python.exe"
  "%LocalAppData%\Programs\Python\Python311\python.exe"
  "%LocalAppData%\Programs\Python\Python310\python.exe"
  "%ProgramFiles%\Python314\python.exe"
  "%ProgramFiles%\Python313\python.exe"
  "%ProgramFiles%\Python312\python.exe"
  "%ProgramFiles%\Python311\python.exe"
  "%ProgramFiles%\Python310\python.exe"
) do (
  if exist "%%~P" (
    "%%~P" -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
    if not errorlevel 1 exit /b 0
  )
)
where py >nul 2>nul
if not errorlevel 1 (
  for %%V in (3.14 3.13 3.12 3.11 3.10 3) do (
    py -%%V -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
    if not errorlevel 1 exit /b 0
  )
)
where python >nul 2>nul
if not errorlevel 1 (
  python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
  if not errorlevel 1 exit /b 0
)
where python3 >nul 2>nul
if not errorlevel 1 (
  python3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
  if not errorlevel 1 exit /b 0
)
exit /b 1

:offer_python_install
if not "%CI%"=="" exit /b 1
where winget >nul 2>nul
if errorlevel 1 exit /b 1

echo.
choice /C SN /N /M "Python 3.11 nao foi encontrado. Instalar automaticamente pelo winget? [S/N]: "
if errorlevel 2 exit /b 1

echo Instalando Python 3.11...
winget install --id Python.Python.3.11 -e --scope user --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
  echo [ERRO] O winget nao conseguiu instalar o Python.
  exit /b 1
)

call :create_venv
if exist "%VENV_PY%" exit /b 0

echo [AVISO] O Python foi instalado, mas o terminal atual ainda nao o reconheceu.
echo Feche esta janela e execute o BAT novamente.
exit /b 1

:usage
echo Uso:
echo   criar_windows.bat             Compila, valida e gera o ZIP
echo   criar_windows.bat --check     Verifica estrutura e Python
echo   criar_windows.bat --clean     Remove build, dist, ZIP e caches
echo   criar_windows.bat --diagnostico Gera CUMA_bootstrap.log
exit /b 0

:fail
echo.
echo [FALHA] A compilacao nao foi concluida.
echo Verifique as mensagens acima.
if exist "%BUILD_LOG%" (
  echo Log de build:
  echo "%BUILD_LOG%"
)
if exist "%BOOTSTRAP_LOG%" (
  echo Log de diagnostico:
  echo "%BOOTSTRAP_LOG%"
)
if "%CI%"=="" pause
exit /b 1
