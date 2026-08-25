@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Launch-JpegResearchLab.ps1"
set "EXITCODE=%ERRORLEVEL%"
if not "%EXITCODE%"=="0" (
  echo.
  echo PC3 Native JPEG Research Lab exited with code %EXITCODE%.
  pause
)
exit /b %EXITCODE%
