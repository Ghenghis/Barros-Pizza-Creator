@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Sync-GitLabSafe.ps1" %*
exit /b %ERRORLEVEL%
