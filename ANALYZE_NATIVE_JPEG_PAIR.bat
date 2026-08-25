@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Analyze-NativeJpegPair.ps1"
set "EXITCODE=%ERRORLEVEL%"
if not "%EXITCODE%"=="0" (
  echo.
  echo Native JPEG analysis exited with code %EXITCODE%.
  pause
)
exit /b %EXITCODE%
