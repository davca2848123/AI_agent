@echo off
REM Setup SWAP Sudo on Raspberry Pi (Local Network)
REM This script connects via SSH and runs the setup_swap_sudo.sh script

REM Load SSH configuration
call "%~dp0ssh_config.bat"

echo ========================================
echo   SWAP Sudo Setup on Raspberry Pi
echo ========================================
echo.

echo Connecting to: %RPI_USER%@%RPI_HOST%:%RPI_PORT%
echo Running: sudo bash setup_swap_sudo.sh
echo.

REM Upload and execute the script
ssh %RPI_USER%@%RPI_HOST% -p %RPI_PORT% "cd %RPI_PROJECT_PATH%/scripts/internal && sudo bash setup_swap_sudo.sh"

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.

pause
