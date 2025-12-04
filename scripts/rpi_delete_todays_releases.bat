@echo off
REM ====================================================
REM Delete Today's GitHub Releases via SSH
REM ====================================================
REM This script connects to RPI via SSH and runs the
REM release deletion script to clean up releases created
REM by the restart loop bug.
REM ====================================================

REM Load SSH configuration
call "%~dp0ssh_config.bat"

echo ========================================
echo   Delete Today's GitHub Releases
echo ========================================
echo.
echo This will delete ALL releases from today
echo matching pattern: YYYY.M.D.*
echo.
echo Connecting to: %RPI_USER%@%RPI_HOST%:%RPI_PORT%
echo Project path: %RPI_PROJECT_PATH%
echo.

REM Connect via SSH and run the deletion script
ssh %RPI_USER%@%RPI_HOST% -p %RPI_PORT% "cd %RPI_PROJECT_PATH% && python3 scripts/delete_todays_releases.py"

echo.
echo ========================================
echo   Operation Complete
echo ========================================
echo.

pause
