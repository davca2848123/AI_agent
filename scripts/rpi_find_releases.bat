@echo off
REM ====================================================
REM Find GitHub Releases by Date via SSH
REM ====================================================
REM This script connects to RPI via SSH and searches
REM for GitHub releases matching current date
REM ====================================================

REM Load SSH configuration
call "%~dp0ssh_config.bat"

echo ========================================
echo   Find GitHub Releases by Date
echo ========================================
echo.
echo Connecting to: %RPI_USER%@%RPI_HOST%:%RPI_PORT%
echo Project path: %RPI_PROJECT_PATH%
echo.

REM Connect via SSH and run the find script
ssh %RPI_USER%@%RPI_HOST% -p %RPI_PORT% "cd %RPI_PROJECT_PATH% && python3 scripts/find_releases_by_date.py"

echo.
echo ========================================
echo   Search Complete
echo ========================================
echo.

pause
