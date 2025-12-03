@echo off
call ssh_config.bat

echo ========================================================
echo      Raspberry Pi AI Agent - LED Setup
echo ========================================================
echo.
echo This script will configure permissions to allow the agent
echo to control the ACT LED (green light) on your Raspberry Pi.
echo.

ssh -t %RPI_USER%@%RPI_HOST% -p %RPI_PORT% "bash -s" < internal/setup_led.sh

echo.
echo ========================================================
if %errorlevel% equ 0 (
    echo ✅ Setup completed successfully!
) else (
    echo ❌ Setup failed.
)
pause
