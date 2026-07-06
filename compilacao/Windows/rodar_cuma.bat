@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul 2>nul
title CUMA - Rodar aplicativo
set "PYTHONDONTWRITEBYTECODE=1"
set "PIP_DISABLE_PIP_VERSION_CHECK=1"

for %%I in ("%~dp0..\..") do set "REPO_ROOT=%%~fI"
set "VENV_DIR=%REPO_ROOT%\.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "COMPILED_DIR=%REPO_ROOT%\dist\CUMA_windows"
set "COMPILED_EXE=%COMPILED_DIR%\cuma.exe"
set "BOOTSTRAP_LOG=%REPO_ROOT%\CUMA_bootstrap.log"
set "RUN_MODE=auto"

if /I "%~1"=="--fonte" set "RUN_MODE=source"
if /I "%~1"=="--source" set "RUN_MODE=source"
if /I "%~1"=="--compilado" set "RUN_MODE=compiled"
if /I "%~1"=="--compiled" set "RUN_MODE=compiled"

echo ============================================================
echo CUMA - EXECUCAO LOCAL
echo Repositorio: "%REPO_ROOT%"
echo Modo:        %RUN_MODE%
echo ============================================================
echo.

if /I "%~1"=="--help" goto :usage
if /I "%~1"=="-h" goto :usage
if /I "%~1"=="/?" goto :usage
if /I "%~1"=="--diagnostico" goto :diagnostic
if /I "%~1"=="--check" goto :check

if /I "%RUN_MODE%"=="compiled" goto :run_compiled
if /I "%RUN_MODE%"=="auto" if exist "%COMPILED_EXE%" goto :run_compiled

call :validate_source
if errorlevel 1 goto :fail

cd /d "%REPO_ROOT%" || (
  echo [ERRO] Nao foi possivel acessar a pasta do repositorio.
  goto :fail
)

call :ensure_venv
if errorlevel 1 goto :fail

call :ensure_runtime_dependencies
if errorlevel 1 goto :fail

echo Validando sintaxe e estrutura...
"%VENV_PY%" -B "%REPO_ROOT%\scripts\auditoria_integridade.py"
if errorlevel 1 (
  echo [ERRO] A auditoria do codigo falhou.
  goto :fail
)

echo Iniciando CUMA pelo codigo-fonte...
echo.
"%VENV_PY%" -B "%REPO_ROOT%\cuma.py"
set "CUMA_RC=%ERRORLEVEL%"
if not "%CUMA_RC%"=="0" (
  echo.
  echo [ERRO] O CUMA terminou com codigo %CUMA_RC%.
  echo Consulte os logs em %%APPDATA%%\CUMA e:
  echo "%BOOTSTRAP_LOG%"
  if "%CI%"=="" pause
)
exit /b %CUMA_RC%

:run_compiled
if not exist "%COMPILED_EXE%" (
  echo [ERRO] Executavel compilado nao encontrado:
  echo "%COMPILED_EXE%"
  echo.
  echo Compile primeiro com:
  echo "%REPO_ROOT%\criar_exe_windows_e_zip.bat"
  goto :fail
)
echo Executavel compilado encontrado. Iniciando...
pushd "%COMPILED_DIR%" >nul 2>nul
if errorlevel 1 (
  echo [ERRO] Nao foi possivel acessar a pasta do executavel.
  goto :fail
)
start "" "%COMPILED_EXE%"
set "CUMA_RC=%ERRORLEVEL%"
popd >nul 2>nul
if not "%CUMA_RC%"=="0" (
  echo [ERRO] O Windows nao conseguiu iniciar:
  echo "%COMPILED_EXE%"
  goto :fail
)
exit /b 0

:check
call :validate_source
set "SOURCE_RC=%ERRORLEVEL%"
call :detect_python_only
set "PYTHON_RC=%ERRORLEVEL%"

if exist "%COMPILED_EXE%" (
  echo [OK] Executavel compilado:
  echo "%COMPILED_EXE%"
) else (
  echo [INFO] Nenhum executavel compilado foi encontrado.
)

if "%SOURCE_RC%"=="0" (
  echo [OK] Estrutura do codigo-fonte valida.
) else (
  echo [AVISO] Codigo-fonte incompleto.
)

if "%PYTHON_RC%"=="0" (
  echo [OK] Python 3.10 ou superior encontrado.
) else (
  echo [AVISO] Python funcional nao encontrado.
)

if exist "%COMPILED_EXE%" exit /b 0
if "%SOURCE_RC%"=="0" if "%PYTHON_RC%"=="0" exit /b 0
exit /b 1

:diagnostic
> "%BOOTSTRAP_LOG%" echo CUMA - diagnostico do launcher Windows
>>"%BOOTSTRAP_LOG%" echo Data: %DATE% %TIME%
>>"%BOOTSTRAP_LOG%" echo Repositorio: "%REPO_ROOT%"
>>"%BOOTSTRAP_LOG%" echo Venv: "%VENV_DIR%"
>>"%BOOTSTRAP_LOG%" echo Executavel: "%COMPILED_EXE%"
>>"%BOOTSTRAP_LOG%" echo.
>>"%BOOTSTRAP_LOG%" echo === WHERE ===
where py >>"%BOOTSTRAP_LOG%" 2>&1
where python >>"%BOOTSTRAP_LOG%" 2>&1
where python3 >>"%BOOTSTRAP_LOG%" 2>&1
where powershell >>"%BOOTSTRAP_LOG%" 2>&1
>>"%BOOTSTRAP_LOG%" echo.
>>"%BOOTSTRAP_LOG%" echo === ARQUIVOS ===
if exist "%REPO_ROOT%\cuma.py" (>>"%BOOTSTRAP_LOG%" echo [OK] cuma.py) else (>>"%BOOTSTRAP_LOG%" echo [FALTA] cuma.py)
if exist "%REPO_ROOT%\requirements.txt" (>>"%BOOTSTRAP_LOG%" echo [OK] requirements.txt) else (>>"%BOOTSTRAP_LOG%" echo [FALTA] requirements.txt)
if exist "%COMPILED_EXE%" (>>"%BOOTSTRAP_LOG%" echo [OK] cuma.exe) else (>>"%BOOTSTRAP_LOG%" echo [FALTA] cuma.exe)
if exist "%VENV_PY%" (
  >>"%BOOTSTRAP_LOG%" echo.
  >>"%BOOTSTRAP_LOG%" echo === PYTHON DO VENV ===
  "%VENV_PY%" --version >>"%BOOTSTRAP_LOG%" 2>&1
  "%VENV_PY%" -c "import sys; print(sys.executable); print(sys.version)" >>"%BOOTSTRAP_LOG%" 2>&1
  "%VENV_PY%" -c "import fitz, numpy, PIL, tkinter; print('dependencias principais: OK')" >>"%BOOTSTRAP_LOG%" 2>&1
)
echo Diagnostico salvo em:
echo "%BOOTSTRAP_LOG%"
type "%BOOTSTRAP_LOG%"
if "%CI%"=="" pause
exit /b 0

:validate_source
set "SOURCE_ERROR=0"
for %%F in (cuma.py cuma_updater.py requirements.txt cuma_build_info.json) do (
  if not exist "%REPO_ROOT%\%%F" (
    echo [ERRO] Arquivo obrigatorio nao encontrado:
    echo "%REPO_ROOT%\%%F"
    set "SOURCE_ERROR=1"
  )
)
if not exist "%REPO_ROOT%\scripts\auditoria_integridade.py" (
  echo [ERRO] Auditoria nao encontrada:
  echo "%REPO_ROOT%\scripts\auditoria_integridade.py"
  set "SOURCE_ERROR=1"
)
if "%SOURCE_ERROR%"=="1" exit /b 1
exit /b 0

:ensure_runtime_dependencies
"%VENV_PY%" -c "import fitz, numpy, PIL, tkinter" >nul 2>nul
if not errorlevel 1 exit /b 0

echo Instalando dependencias necessarias...
"%VENV_PY%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
  echo [ERRO] Falha ao atualizar pip/setuptools/wheel.
  exit /b 1
)
"%VENV_PY%" -m pip install -r "%REPO_ROOT%\requirements.txt"
if errorlevel 1 (
  echo [ERRO] Falha ao instalar requirements.txt.
  exit /b 1
)
"%VENV_PY%" -c "import fitz, numpy, PIL, tkinter"
if errorlevel 1 (
  echo [ERRO] As dependencias principais continuam indisponiveis.
  exit /b 1
)
exit /b 0

:ensure_venv
if exist "%VENV_PY%" (
  "%VENV_PY%" -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
  if not errorlevel 1 exit /b 0
  echo [AVISO] Ambiente virtual existente esta invalido. Recriando...
  rd /s /q "%VENV_DIR%" >nul 2>nul
)

echo Criando ambiente virtual para executar o codigo...
call :create_venv
if exist "%VENV_PY%" exit /b 0

call :offer_python_install
if exist "%VENV_PY%" exit /b 0

echo.
echo [ERRO] Nenhum Python 3.10 ou superior funcional foi encontrado.
echo.
echo Para rodar sem Python, compile primeiro ou use uma Release pronta.
echo Para instalar o Python 3.11:
echo winget install --id Python.Python.3.11 -e --scope user
echo.
echo Log de diagnostico:
echo "%BOOTSTRAP_LOG%"
exit /b 1

:create_venv
if exist "%VENV_DIR%" rd /s /q "%VENV_DIR%" >nul 2>nul
> "%BOOTSTRAP_LOG%" echo CUMA - diagnostico de Python

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
echo   rodar_cuma.bat                 Usa o EXE se existir; senao usa o fonte
echo   rodar_cuma.bat --fonte         Forca a execucao pelo Python
echo   rodar_cuma.bat --compilado     Forca a execucao do EXE
echo   rodar_cuma.bat --check         Verifica estrutura, Python e EXE
echo   rodar_cuma.bat --diagnostico   Gera CUMA_bootstrap.log
exit /b 0

:fail
echo.
echo [FALHA] Nao foi possivel iniciar o CUMA.
if exist "%BOOTSTRAP_LOG%" (
  echo Log de diagnostico:
  echo "%BOOTSTRAP_LOG%"
)
if "%CI%"=="" pause
exit /b 1
