@echo off
REM Memory Manager Launcher
REM Interactive tool for managing agent memory database

cd /d "%~dp0..\.."
python scripts\internal\memory_manager.py
pause
