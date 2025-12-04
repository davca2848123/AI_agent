@echo off
REM ====================================================
REM STOP AI Agent Service on RPI (Emergency)
REM ====================================================
REM This script stops the agent service on RPI via SSH
REM Use this to stop the restart loop
REM ====================================================

REM Load SSH configuration
call "%~dp0ssh_config.bat"

echo ========================================
echo   EMERGENCY: Stop AI Agent Service
echo ========================================
echo.
echo This will STOP the agent service on RPI
echo to prevent restart loop.
echo.
echo Connecting to: %RPI_USER%@%RPI_HOST%:%RPI_PORT%
echo.

REM Connect via SSH and stop the service
ssh %RPI_USER%@%RPI_HOST% -p %RPI_PORT% "sudo systemctl stop rpi_ai.service && echo 'Service stopped successfully' || echo 'Failed to stop service'"

echo.
echo ========================================
echo   Operation Complete
echo ========================================
echo.
echo To start again: sudo systemctl start rpi_ai.service
echo.

pause
