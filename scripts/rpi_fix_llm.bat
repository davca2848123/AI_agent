@echo off
REM Load SSH configuration
call "%~dp0ssh_config.bat"

echo Installing LLM dependencies on Raspberry Pi...
echo You will be asked for the password (%RPI_USER%).
echo.
ssh -t %RPI_USER%@%RPI_HOST% -p %RPI_PORT% "bash %RPI_PROJECT_PATH%/scripts/internal/fix_llm.sh"
pause
