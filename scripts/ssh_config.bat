@echo off
REM ====================================================
REM SSH Configuration for RPI AI Agent
REM ====================================================
REM This file contains SSH connection settings used by
REM all batch scripts. Edit these values to match your
REM Raspberry Pi configuration.
REM ====================================================

REM Raspberry Pi SSH Settings
set RPI_USER=davca
set RPI_HOST=192.168.1.200
set RPI_PORT=22

REM Path to project on RPI
set RPI_PROJECT_PATH=/home/davca/rpi_ai/rpi_ai

REM Full SSH connection string
set SSH_CONNECT=%RPI_USER%@%RPI_HOST%

REM ====================================================
REM DO NOT EDIT BELOW THIS LINE
REM ====================================================
