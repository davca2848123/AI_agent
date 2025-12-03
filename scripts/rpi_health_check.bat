@echo off
:: ============================================================
:: RPI AI Agent - SSH Connection and Health Check
:: ============================================================
:: This script connects to the RPI via SSH and runs the health check
:: 
:: Author: Automated Setup
:: Date: 2025-12-01
:: ============================================================

REM Load SSH configuration
call "%~dp0ssh_config.bat"

echo.
echo ========================================
echo   RPI AI Agent - SSH Health Check
echo ========================================
echo.

echo Connecting to %RPI_USER%@%RPI_HOST%...
echo.

:: Connect via SSH and run health check
ssh -p %RPI_PORT% %RPI_USER%@%RPI_HOST% "cd %RPI_PROJECT_PATH% && python scripts/internal/health_check.py"

echo.
echo ========================================
echo   Health Check Complete
echo ========================================
echo.
echo Press any key to close...
pause >nul
