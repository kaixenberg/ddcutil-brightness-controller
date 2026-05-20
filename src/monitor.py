import subprocess
import re
import threading
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib

class MonitorManager:
    def __init__(self, verbose=False):
        self.verbose = verbose

    def detect_monitors(self, on_success, on_error):
        threading.Thread(
            target=self._detect_monitors_thread,
            args=(on_success, on_error),
            daemon=True
        ).start()

    def _detect_monitors_thread(self, on_success, on_error):
        try:
            if self.verbose:
                print("Executing: ddcutil detect")
            result = subprocess.run(["ddcutil", "detect"], capture_output=True, text=True)
            
            if result.returncode != 0:
                if on_error:
                    GLib.idle_add(on_error, f"Error detecting monitors: {result.stderr}")
                return
            
            monitors = []
            display_pattern = re.compile(r'Display\s+(\d+)')
            model_pattern = re.compile(r'Model:\s+(.+)')
            current_display = None
            
            for line in result.stdout.splitlines():
                display_match = display_pattern.search(line)
                if display_match:
                    current_display = {"id": int(display_match.group(1)), "model": "Unknown", "brightness": 50, "error": None}
                    monitors.append(current_display)
                
                model_match = model_pattern.search(line)
                if model_match and current_display:
                    current_display["model"] = model_match.group(1).strip()
            
            for monitor in monitors:
                try:
                    if self.verbose:
                        print(f"Executing: ddcutil getvcp 10 --display {monitor['id']}")
                    res = subprocess.run(
                        ["ddcutil", "getvcp", "10", "--display", str(monitor["id"])],
                        capture_output=True, text=True
                    )
                    match = re.search(r'current value\s*=\s*(\d+)', res.stdout)
                    if match:
                        monitor["brightness"] = int(match.group(1))
                except Exception as e:
                    monitor["error"] = str(e)
            
            if on_success:
                GLib.idle_add(on_success, monitors)
            
        except Exception as e:
            if on_error:
                GLib.idle_add(on_error, f"Error: {str(e)}")

    def set_brightness(self, monitor_id, brightness, on_success, on_error):
        threading.Thread(
            target=self._set_brightness_thread,
            args=(monitor_id, brightness, on_success, on_error),
            daemon=True
        ).start()

    def _set_brightness_thread(self, monitor_id, brightness, on_success, on_error):
        try:
            if self.verbose:
                print(f"Executing: ddcutil setvcp 10 {brightness} --display {monitor_id}")
            subprocess.run(
                ["ddcutil", "setvcp", "10", str(brightness), "--display", str(monitor_id)],
                check=True
            )
            if on_success:
                GLib.idle_add(on_success, f"Set monitor {monitor_id} brightness to {brightness}%")
        except subprocess.CalledProcessError as e:
            if on_error:
                GLib.idle_add(on_error, f"Error setting brightness: {e}")
