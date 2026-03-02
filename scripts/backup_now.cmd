@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "PS_SCRIPT=%SCRIPT_DIR%backup_now.ps1"

if not exist "%PS_SCRIPT%" (
  echo [ERROR] Script not found: "%PS_SCRIPT%"
  pause
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%"
set "EC=%ERRORLEVEL%"

if not "%EC%"=="0" (
  echo.
  echo [ERROR] Backup failed with code %EC%.
  pause
  exit /b %EC%
)

echo.
echo [OK] Backup completed.
pause
exit /b 0
