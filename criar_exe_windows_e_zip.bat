@echo off
setlocal EnableExtensions DisableDelayedExpansion
call "%~dp0compilacao\Windows\criar_windows.bat" %*
set "CUMA_RC=%ERRORLEVEL%"
endlocal & exit /b %CUMA_RC%
