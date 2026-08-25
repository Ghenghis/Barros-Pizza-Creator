@echo off
setlocal
cd /d "%~dp0"
echo PC3 Pizza Creator - Native JPEG Research Tool Setup
echo ----------------------------------------------------
echo This downloads pinned official research tools, verifies SHA-256,
echo creates an isolated Python analysis environment, and then offers
echo optional RenderDoc/ImageMagick installation.
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Setup-JpegResearchTools.ps1" -PromptOptional
set "EXITCODE=%ERRORLEVEL%"
if not "%EXITCODE%"=="0" (
  echo.
  echo Research-tool setup exited with code %EXITCODE%.
  pause
)
exit /b %EXITCODE%
