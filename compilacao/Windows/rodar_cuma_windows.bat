@echo off
setlocal EnableExtensions DisableDelayedExpansion
call "%~dp0rodar_cuma.bat" %*
set "CUMA_RC=%ERRORLEVEL%"
endlocal & exit /b %CUMA_RC%
