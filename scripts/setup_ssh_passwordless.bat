@echo off
echo Setting up passwordless SSH login...
echo.

:: Check if key exists
if not exist "%USERPROFILE%\.ssh\id_rsa.pub" (
    echo Generating SSH key...
    ssh-keygen -t rsa -b 4096 -f "%USERPROFILE%\.ssh\id_rsa" -N ""
) else (
    echo SSH key already exists.
)

echo.
echo Copying key to Raspberry Pi...
echo -------------------------------------------------------
echo You will be asked for the password ONE LAST TIME.
echo -------------------------------------------------------
echo.
type "%USERPROFILE%\.ssh\id_rsa.pub" | ssh davca@192.168.1.200 "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"

echo.
echo Done! Now try running the other scripts - they should not ask for a password.
pause
