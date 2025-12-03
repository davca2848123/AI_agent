@echo off
echo Cleaning up boredom memories...
cd /d "%~dp0.."
python scripts/internal/task_cleanup_memory.py
pause
