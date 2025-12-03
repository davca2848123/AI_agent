@echo off
call ssh_config.bat

echo ========================================================
echo      Raspberry Pi AI Agent - LED Debug
echo ========================================================
echo.
echo This script will test if Python can control the LED.
echo.

ssh -t %RPI_USER%@%RPI_HOST% -p %RPI_PORT% "python3 -u -" < internal/test_led.py

echo.
echo ========================================================
pause
