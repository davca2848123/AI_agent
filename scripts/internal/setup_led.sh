#!/bin/bash

# Script to setup permissions for RPi ACT LED
# This allows the agent (running as non-root) to control the LED

echo "💡 Setting up LED permissions..."

# 1. Identify LED path
LED_PATH=""
if [ -e "/sys/class/leds/ACT/brightness" ]; then
    LED_PATH="/sys/class/leds/ACT/brightness"
elif [ -e "/sys/class/leds/led0/brightness" ]; then
    LED_PATH="/sys/class/leds/led0/brightness"
fi

if [ -z "$LED_PATH" ]; then
    echo "❌ Could not find ACT LED path. Your RPi model might be different."
    exit 1
fi

echo "✅ Found LED at: $LED_PATH"

# 2. Create udev rule for persistence
RULE_FILE="/etc/udev/rules.d/99-agent-led.rules"
echo "📝 Creating udev rule at $RULE_FILE..."

# We use chmod 666 to allow any user to write to it. 
# For higher security, we could create a group, but this is a dedicated agent device.
cat <<EOF | sudo tee $RULE_FILE
SUBSYSTEM=="leds", KERNEL=="ACT", ACTION=="add", RUN+="/bin/chmod 666 /sys/class/leds/ACT/brightness"
SUBSYSTEM=="leds", KERNEL=="led0", ACTION=="add", RUN+="/bin/chmod 666 /sys/class/leds/led0/brightness"
EOF

# 3. Apply changes immediately
echo "🔄 Reloading udev rules..."
sudo udevadm control --reload-rules
sudo udevadm trigger

# 4. Manual chmod for current session (just in case trigger didn't catch it)
echo "🔓 Applying immediate permissions..."
sudo chmod 666 "$LED_PATH"

# Verify
if [ -w "$LED_PATH" ]; then
    echo "✅ Success! Current user can write to LED."
    # Test blink
    echo "✨ Testing blink..."
    echo 1 > "$LED_PATH"
    sleep 0.2
    echo 0 > "$LED_PATH"
    sleep 0.2
    echo 1 > "$LED_PATH"
    sleep 0.2
    echo 0 > "$LED_PATH"
    # Restore default (usually 0 or 255 depending on trigger)
    echo 0 > "$LED_PATH" 
else
    echo "❌ Failed to set write permissions."
    exit 1
fi

echo "🎉 LED setup complete. The agent can now use the LED."
