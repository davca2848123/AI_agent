@echo off
REM Load SSH configuration
call "%~dp0ssh_config.bat"

echo Starting Python 3.12 rebuild on Raspberry Pi...
echo This process will take 15-30 minutes.
echo You will be asked for the password (%RPI_USER%).
echo.
ssh -t %RPI_USER%@%RPI_HOST% -p %RPI_PORT% "bash %RPI_PROJECT_PATH%/scripts/internal/fix_python_build.sh"
pause
