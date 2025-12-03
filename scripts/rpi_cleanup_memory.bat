@echo off
REM Memory Cleanup on Raspberry Pi (Local Network)
REM This script connects via SSH and runs the cleanup_memory.py script

REM Load SSH configuration
call "%~dp0ssh_config.bat"

echo ========================================
echo   Memory Database Cleanup
echo ========================================
echo.
echo This will analyze and clean the memory database.
echo.

echo Connecting to: %RPI_USER%@%RPI_HOST%:%RPI_PORT%
echo.

REM Ask user for mode
echo Select mode:
echo [1] Dry-run (analyze only, no changes)
echo [2] Cleanup with backup
echo.
set /p MODE="Enter choice (1 or 2): "

if "%MODE%"=="1" (
    echo.
    echo Running DRY-RUN analysis...
    ssh %RPI_USER%@%RPI_HOST% -p %RPI_PORT% "cd %RPI_PROJECT_PATH% && python3 scripts/internal/cleanup_memory.py --dry-run"
) else if "%MODE%"=="2" (
    echo.
    echo Running CLEANUP with backup...
    ssh %RPI_USER%@%RPI_HOST% -p %RPI_PORT% "cd %RPI_PROJECT_PATH% && python3 scripts/internal/cleanup_memory.py --backup"
) else (
    echo.
    echo Invalid choice. Exiting.
    goto :end
)

echo.
echo ========================================
echo   Cleanup Complete!
echo ========================================
echo.

:end
pause
