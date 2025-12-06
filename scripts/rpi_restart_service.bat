@echo off
REM SSH Connect to RPI and Restart Agent Service
REM This script connects to the Raspberry Pi and restarts the agent service

REM Load SSH configuration
call "%~dp0ssh_config.bat"

set SERVICE_NAME=rpi_ai.service

echo ================================================
echo   SSH + Restart RPI Agent Service
echo ================================================
echo.
echo Connecting to: %RPI_USER%@%RPI_HOST%
echo Service: %SERVICE_NAME%
echo.
echo This will:
echo   1. Connect via SSH
echo   2. Restart the agent service
echo   3. Show service status
echo.
pause

echo.
echo [1/3] Connecting to RPI...
ssh -p %RPI_PORT% %RPI_USER%@%RPI_HOST% "echo 'Connected successfully!'"

if %errorlevel% neq 0 (
    echo ERROR: SSH connection failed!
    pause
    exit /b 1
)

echo.
echo [2/3] Restarting agent service...
ssh -p %RPI_PORT% %RPI_USER%@%RPI_HOST% "rm -f /home/davca/rpi_ai/rpi_ai/.startup_failures && sudo systemctl restart %SERVICE_NAME%"

echo.
echo [3/3] Checking service status...
ssh -p %RPI_PORT% %RPI_USER%@%RPI_HOST% "sudo systemctl status %SERVICE_NAME% --no-pager -l"

echo.
echo ================================================
echo   Service restart completed!
echo ================================================
echo.
echo To view live logs, run:
echo   ssh -p %RPI_PORT% %RPI_USER%@%RPI_HOST% "sudo journalctl -u %SERVICE_NAME% -f"
echo.
pause
