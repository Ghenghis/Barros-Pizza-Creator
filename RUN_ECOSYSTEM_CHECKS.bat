@echo off
setlocal
cd /d "%~dp0"

set "PY=python"
if exist "%~dp0.venv\Scripts\python.exe" set "PY=%~dp0.venv\Scripts\python.exe"

"%PY%" "%~dp0tools\run_ecosystem_checks.py" --run-tests %*
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
  echo Portable ecosystem audit PASS. Live GUI/game gates still require real retained runtime evidence.
) else (
  echo Ecosystem audit found unresolved paths, sync drift, or test failures. See the evidence JSON path printed above.
)
pause
exit /b %RC%
