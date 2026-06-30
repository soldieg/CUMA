@echo off
setlocal EnableExtensions
chcp 65001 >nul
title CUMA - Criar pacotes multiplataforma

echo.
echo Este arquivo organiza a criacao dos pacotes do CUMA.
echo.
echo IMPORTANTE:
echo - PyInstaller nao gera executavel Linux/macOS corretamente a partir do Windows.
echo - O Windows sera criado localmente.
echo - Linux e macOS devem ser criados na propria plataforma ou pelo GitHub Actions incluído.
echo.

call "%~dp0Windows\criar_windows.bat"
if errorlevel 1 exit /b 1

echo.
echo Windows criado.
echo Para criar Linux/macOS automaticamente sem ter esses sistemas, use:
echo GitHub ^> Actions ^> Build CUMA Multiplataforma
echo.
if "%CI%"=="" pause
endlocal
