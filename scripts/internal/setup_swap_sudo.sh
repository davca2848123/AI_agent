#!/bin/bash
# Setup script for passwordless sudo for swap management
# Run this script with: sudo bash setup_swap_sudo.sh

echo "Setting up passwordless sudo for swap management..."

# Get the current user
CURRENT_USER=$(logname 2>/dev/null || echo $SUDO_USER)

if [ -z "$CURRENT_USER" ]; then
    echo "Error: Cannot determine current user"
    exit 1
fi

echo "Configuring sudo for user: $CURRENT_USER"

# Create sudoers.d file for swap commands
SUDOERS_FILE="/etc/sudoers.d/ai-swap-nopasswd"

cat > "$SUDOERS_FILE" << EOF
# Allow AI agent to manage swap without password
$CURRENT_USER ALL=(ALL) NOPASSWD: /usr/sbin/swapoff
$CURRENT_USER ALL=(ALL) NOPASSWD: /usr/bin/dd
$CURRENT_USER ALL=(ALL) NOPASSWD: /usr/bin/chmod
$CURRENT_USER ALL=(ALL) NOPASSWD: /usr/sbin/mkswap
$CURRENT_USER ALL=(ALL) NOPASSWD: /usr/sbin/swapon
EOF

# Set proper permissions
chmod 0440 "$SUDOERS_FILE"

# Validate the sudoers file
if ! visudo -c -f "$SUDOERS_FILE"; then
    echo "Error: Invalid sudoers configuration"
    rm -f "$SUDOERS_FILE"
    exit 1
fi

echo "✅ Sudo configuration complete!"
echo ""
echo "The following commands can now run without password:"
echo "  - sudo swapoff"
echo "  - sudo dd"
echo "  - sudo chmod"
echo "  - sudo mkswap"
echo "  - sudo swapon"
echo ""
echo "Test it with: sudo -n swapoff -a"
