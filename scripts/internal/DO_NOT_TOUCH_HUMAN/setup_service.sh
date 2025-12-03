#!/bin/bash

# Define variables
SERVICE_NAME="rpi_ai.service"
# Determine the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# Assume the service file is in the same directory as this script
SERVICE_SOURCE_PATH="$SCRIPT_DIR/$SERVICE_NAME"
SERVICE_DEST_PATH="/etc/systemd/system/$SERVICE_NAME"

if [ ! -f "$SERVICE_SOURCE_PATH" ]; then
    echo "Error: Could not find $SERVICE_NAME in $SCRIPT_DIR"
    exit 1
fi

echo "Installing $SERVICE_NAME..."

# Copy the service file to /etc/systemd/system/
echo "Copying service file to $SERVICE_DEST_PATH..."
sudo cp "$SERVICE_SOURCE_PATH" "$SERVICE_DEST_PATH"

# Reload systemd to recognize the new service
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable the service to start on boot
echo "Enabling service..."
sudo systemctl enable "$SERVICE_NAME"

# Start the service immediately
echo "Starting service..."
sudo systemctl restart "$SERVICE_NAME"

echo "---------------------------------------------------"
echo "Service installed, enabled, and started."
echo "Check status with: sudo systemctl status $SERVICE_NAME"
echo "View logs with: sudo journalctl -u $SERVICE_NAME -f"
echo "---------------------------------------------------"
