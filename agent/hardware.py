import logging
import psutil
import subprocess
import sys
import platform
import os

logger = logging.getLogger(__name__)

class HardwareMonitor:
    def __init__(self):
        self.is_rpi = False
        self._check_platform()
        
        # Thresholds
        self.MAX_TEMP = 80.0 # Celsius
        self.MAX_RAM_PERCENT = 90.0
        
    def _check_platform(self):
        """Checks if running on Raspberry Pi."""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                if 'Raspberry Pi' in f.read():
                    self.is_rpi = True
        except FileNotFoundError:
            pass
            
    def get_cpu_temp(self) -> float:
        """Gets CPU temperature."""
        if self.is_rpi:
            try:
                # Try vcgencmd first
                output = subprocess.check_output(['vcgencmd', 'measure_temp']).decode('utf-8')
                return float(output.replace('temp=', '').replace('\'C\n', ''))
            except Exception:
                # Fallback to sysfs
                try:
                    with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                        return float(f.read()) / 1000.0
                except Exception:
                    pass
        
        # Mock for Windows/Non-RPi
        return 45.0

    def get_ram_usage(self) -> float:
        """Gets RAM usage percentage."""
        return psutil.virtual_memory().percent

    def is_safe_to_run(self) -> bool:
        """Checks if system is within safe operating limits."""
        temp = self.get_cpu_temp()
        ram = self.get_ram_usage()
        
        if temp > self.MAX_TEMP:
            logger.warning(f"OVERHEATING: CPU Temp {temp}°C exceeds limit {self.MAX_TEMP}°C")
            return False
            
        if ram > self.MAX_RAM_PERCENT:
            logger.warning(f"OOM RISK: RAM Usage {ram}% exceeds limit {self.MAX_RAM_PERCENT}%")
            return False
            
        return True

    def get_status(self) -> str:
        """Returns a status string."""
        return f"Temp: {self.get_cpu_temp():.1f}°C, RAM: {self.get_ram_usage():.1f}%"

class LedIndicator:
    def __init__(self):
        self.led_path = "/sys/class/leds/ACT/brightness"
        self.state = "IDLE"  # IDLE, BUSY, ERROR
        self.running = True
        self._thread = None
        # Only start thread if on RPi or if forced for testing (logic handled in _loop)
        # But to be safe and avoid errors on Windows, we check existence or platform
        if os.path.exists(self.led_path) or platform.system() == 'Linux':
             import threading
             self._thread = threading.Thread(target=self._loop, daemon=True)
             self._thread.start()

    def set_state(self, state):
        """Nastaví stav LED: 'IDLE' (vypnuto), 'BUSY' (rychlé blikání), 'ERROR' (pomalé blikání)"""
        self.state = state

    def _write_led(self, value):
        try:
            # 0 = vypnuto, 1 (nebo 255) = zapnuto
            if os.path.exists(self.led_path):
                with open(self.led_path, 'w') as f:
                    f.write(str(value))
        except Exception:
            pass # Ignorovat chyby pokud nebeží na RPi nebo nemá práva

    def _loop(self):
        import time
        while self.running:
            if self.state == "IDLE":
                self._write_led(0)
                time.sleep(0.5)
            
            elif self.state == "BUSY":
                # Rychlé blikání (např. 100ms interval)
                self._write_led(255)
                time.sleep(0.1)
                self._write_led(0)
                time.sleep(0.1)
                
            elif self.state == "ERROR":
                # Pomalé blikání (dlouhý svit, krátká pauza nebo naopak)
                self._write_led(255)
                time.sleep(1.0)
                self._write_led(0)
                time.sleep(1.0)

