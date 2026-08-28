@echo off
setlocal
cd /d "%~dp0"
python windows_bridge.py %*
if errorlevel 1 pause
