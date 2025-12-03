@echo off
REM Load SSH configuration
call "%~dp0ssh_config.bat"

echo 🗑️ Deleting bot messages in Admin DM...
echo Note: This will only delete messages sent BY the bot.
echo.
ssh %RPI_USER%@%RPI_HOST% -p %RPI_PORT% "cd %RPI_PROJECT_PATH% && python scripts/internal/task_clear_dm.py"
pause
