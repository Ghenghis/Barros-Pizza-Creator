@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0INSTALL_Barros_AI_Designer.ps1"
if errorlevel 1 pause

