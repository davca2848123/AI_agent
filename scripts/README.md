# Scripts Directory

This directory contains **batch scripts (.bat)** for managing the RPI AI Agent remotely via SSH.

## Structure

- **Root (`scripts/`)**: Contains only `.bat` files for easy access and execution
- **Internal (`scripts/internal/`)**: Contains Python scripts, shell scripts, and documentation files used by the batch scripts

## Available Scripts

### System Management
- `rpi_restart_service.bat` - Restart the AI agent service
- `rpi_stop_service.bat` - Stop the AI agent service
- `rpi_check_status.bat` - Check system and service status
- `rpi_health_check.bat` - Comprehensive health diagnostics

### Maintenance
- `rpi_cleanup_logs.bat` - Clean up old log files
- `rpi_cleanup_memory.bat` - Clean up memory database
- `rpi_clear_dm.bat` - Clear bot DM messages
- `rpi_task_cleanup_boredom.bat` - Clean up boredom data

### Setup & Configuration
- `rpi_setup_led.bat` - Setup LED indicators
- `rpi_setup_swap.bat` - Configure swap memory
- `setup_rpi_sudoers.bat` - Configure sudo permissions
- `setup_ssh_passwordless.bat` - Setup passwordless SSH
- `rpi_fix_llm.bat` - Fix LLM integration issues
- `rpi_rebuild_python.bat` - Rebuild Python environment

### GitHub Management
- `rpi_delete_todays_releases.bat` - Delete today's GitHub releases
- `rpi_find_releases.bat` - Find releases by date

### Testing
- `rpi_test_led.bat` - Test LED functionality

### SSH Utilities
- `ssh_connect.bat` - Quick SSH connection
- `ssh_config.bat` - SSH configuration variables (sourced by other scripts)

## Usage

All scripts are designed to be run from Windows and connect to the Raspberry Pi via SSH.

Most scripts will:
1. Load SSH configuration from `ssh_config.bat`
2. Connect to the RPI via SSH
3. Execute commands or Python scripts on the remote system
4. Display results and wait for user input (pause)

## Internal Directory

The `internal/` subdirectory contains:
- Python scripts (`.py`) - Backend logic executed on the RPI
- Shell scripts (`.sh`) - Bash scripts for RPI
- Documentation (`.md`) - Guides and references
- Other support files

**Note:** You should not need to directly execute files from `internal/` - use the `.bat` files in the root instead.

---

**Poslední aktualizace:** 2025-12-06  
**Verze:** Beta - CLOSED
