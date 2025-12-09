import time
import os
import sys

LED_PATH = "/sys/class/leds/ACT/brightness"

print(f"🔍 Testing LED control at: {LED_PATH}")

if not os.path.exists(LED_PATH):
    print(f"❌ Error: Path {LED_PATH} does not exist!")
    # Try alternate
    LED_PATH = "/sys/class/leds/led0/brightness"
    print(f"🔄 Trying alternate path: {LED_PATH}")
    if not os.path.exists(LED_PATH):
        print(f"❌ Error: Alternate path also not found.")
        sys.exit(1)

print(f"✅ Found LED path.")

try:
    print("🔓 Testing write permissions...")
    with open(LED_PATH, 'w') as f:
        f.write("0")
    print("✅ Write permission OK.")
except PermissionError:
    print("❌ Error: Permission denied! Run the setup script again or check sudoers.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error writing to LED: {e}")
    sys.exit(1)

print("✨ Blinking LED (5 times)...")
try:
    for i in range(5):
        print(f"   Blink {i+1}/5...")
        with open(LED_PATH, 'w') as f:
            f.write("255")
        time.sleep(0.2)
        with open(LED_PATH, 'w') as f:
            f.write("0")
        time.sleep(0.2)
    print("✅ Blink test complete.")
except Exception as e:
    print(f"❌ Error during blink loop: {e}")
