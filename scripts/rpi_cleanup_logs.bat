@echo off
REM Log Cleanup on Raspberry Pi (Local Network)
REM This script connects via SSH and runs the cleanup_logs.py script

REM Load SSH configuration
call "%~dp0ssh_config.bat"

echo ========================================
echo   Agent Logs Cleanup
echo ========================================
echo.
echo This will delete log entries older than 2 days.
echo Affected files:
echo   - agent.log
echo   - agent_tools.log
echo.

echo Connecting to: %RPI_USER%@%RPI_HOST%:%RPI_PORT%
echo.

echo Running log cleanup on RPI...
ssh %RPI_USER%@%RPI_HOST% -p %RPI_PORT% "cd %RPI_PROJECT_PATH% && python3 scripts/internal/cleanup_logs.py"

echo.
echo ========================================
echo   Cleanup Complete!
echo ========================================
echo.

pause
