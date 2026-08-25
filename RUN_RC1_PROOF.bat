@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Invoke-ProofContract.ps1" -Stage All -GameRoot "S:\Unity_Games\PC3 - Pizza Creator"
set "RESULT=%ERRORLEVEL%"
echo.
if not "%RESULT%"=="0" echo One or more selected proof gates failed. Review the newest evidence\runs folder.
if "%RESULT%"=="0" echo No selected gate failed. BLOCKED and NOT RUN gates still require retained evidence before certification.
pause
exit /b %RESULT%
