@echo off
REM Fix RPI Sudoers for Passwordless Access
REM This script configures the RPI to allow 'davca' to run sudo commands without a password.
REM You will be asked for the password ONE LAST TIME during this script.

set RPI_USER=davca
set RPI_HOST=192.168.1.200

echo ================================================
echo   Fixing RPI Sudoers (Passwordless Setup)
echo ================================================
echo.
echo This will create /etc/sudoers.d/rpi_agent on the RPi.
echo You may be asked for your password one last time.
echo.

ssh -t %RPI_USER%@%RPI_HOST% "echo 'davca ALL=(ALL) NOPASSWD: ALL' | sudo tee /etc/sudoers.d/rpi_agent > /dev/null && sudo chmod 0440 /etc/sudoers.d/rpi_agent && echo '✅ Success! Passwordless sudo configured.'"

echo.
echo ================================================
echo   Verification
echo ================================================
echo.
echo Testing passwordless sudo (should NOT ask for password)...
ssh %RPI_USER%@%RPI_HOST% "sudo systemctl status rpi_agent --no-pager -n 1"

echo.
if %errorlevel% equ 0 (
    echo ✅ Verification Successful! You can now use !cmd sudo and the restart script.
) else (
    echo ❌ Verification Failed. Something went wrong.
)
echo.
pause
