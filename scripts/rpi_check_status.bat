@echo off
REM ====================================================
REM Check AI Agent Status and Logs on RPI
REM ====================================================
REM This script checks service status and shows recent logs
REM ====================================================

REM Load SSH configuration
call "%~dp0ssh_config.bat"

echo ========================================
echo   AI Agent Status Check
echo ========================================
echo.
echo Connecting to: %RPI_USER%@%RPI_HOST%:%RPI_PORT%
echo.

REM Connect via SSH and check status
ssh %RPI_USER%@%RPI_HOST% -p %RPI_PORT% "echo '=== SERVICE STATUS ==='; sudo systemctl status rpi_ai.service | head -20; echo ''; echo '=== RECENT ERRORS ==='; journalctl -u rpi_ai.service -n 50 | grep -i error; echo ''; echo '=== LAST 10 RESTARTS ==='; journalctl -u rpi_ai.service | grep 'Starting\|Started\|Failed' | tail -20"

echo.
pause
