@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Convert-BarrosMusic.ps1" -SourceDirectory "S:\Unity_Games\PC3 - Pizza Creator\Barros_Music"
set "BARROS_RC=%ERRORLEVEL%"
echo.
if not "%BARROS_RC%"=="0" echo Music conversion did not complete successfully.
pause
exit /b %BARROS_RC%
