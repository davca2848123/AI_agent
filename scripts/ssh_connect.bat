@echo off
REM SSH Connect to Raspberry Pi (Local Network)
REM This script connects to the Raspberry Pi via local network

REM Load SSH configuration
call "%~dp0ssh_config.bat"

echo ========================================
echo   SSH Connection to Raspberry Pi
echo ========================================
echo.

echo Connecting to: %RPI_USER%@%RPI_HOST%:%RPI_PORT%
echo.

ssh %RPI_USER%@%RPI_HOST% -p %RPI_PORT%

pause
