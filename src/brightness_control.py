#!/usr/bin/env python3
import gi
import subprocess
import re
import threading

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk

class MonitorBrightnessControl(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.example.MonitorBrightnessControl")
        self.connect("activate", self.on_activate)
        self.monitors = []
        
    def on_activate(self, app):
        self.window = Gtk.ApplicationWindow(application=app, title="Monitor Brightness Control")
        self.window.set_default_size(400, 300)
        self.window.set_border_width(10)
        
        # Set up the main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.window.add(main_box)
        
        # Header with app name
        header = Gtk.Label()
        header.set_markup("<b>Monitor Brightness Controller</b>")
        header.set_margin_bottom(10)
        main_box.pack_start(header, False, False, 0)
        
        # Status bar for messages
        self.status_label = Gtk.Label(label="Detecting monitors...")
        main_box.pack_start(self.status_label, False, False, 0)
        
        # Container for monitor controls
        self.monitors_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        main_box.pack_start(self.monitors_box, True, True, 0)
        
        # Refresh button
        refresh_button = Gtk.Button(label="Refresh Monitors")
        refresh_button.connect("clicked", self.detect_monitors)
        main_box.pack_end(refresh_button, False, False, 0)
        
        # Show all components
        self.window.show_all()
        
        # Start monitor detection in a separate thread
        threading.Thread(target=self.detect_monitors, daemon=True).start()
    
    def detect_monitors(self, widget=None):
        # Clear existing monitor controls
        for child in self.monitors_box.get_children():
            self.monitors_box.remove(child)
        
        self.status_label.set_text("Detecting monitors...")
        
        # Run this in the main thread if called from the refresh button
        if widget:
            self._detect_monitors_impl()
        else:
            # Otherwise run it in a background thread and update UI in main thread
            GLib.idle_add(self._detect_monitors_impl)
    
    def _detect_monitors_impl(self):
        try:
            # Get list of monitors using ddcutil
            result = subprocess.run(["ddcutil", "detect"], capture_output=True, text=True)
            
            if result.returncode != 0:
                self.status_label.set_text(f"Error detecting monitors: {result.stderr}")
                return
            
            # Parse monitor information
            self.monitors = []
            display_pattern = re.compile(r'Display\s+(\d+)')
            model_pattern = re.compile(r'Model:\s+(.+)')
            current_display = None
            
            for line in result.stdout.splitlines():
                display_match = display_pattern.search(line)
                if display_match:
                    current_display = {"id": int(display_match.group(1)), "model": "Unknown"}
                    self.monitors.append(current_display)
                
                model_match = model_pattern.search(line)
                if model_match and current_display:
                    current_display["model"] = model_match.group(1).strip()
            
            # Create controls for each monitor
            if self.monitors:
                for monitor in self.monitors:
                    self._create_monitor_control(monitor)
                self.status_label.set_text(f"Found {len(self.monitors)} monitor(s)")
            else:
                self.status_label.set_text("No monitors detected with DDC support")
            
        except Exception as e:
            self.status_label.set_text(f"Error: {str(e)}")
        
        # Ensure all new widgets are shown
        self.window.show_all()
    
    def _create_monitor_control(self, monitor):
        # Get current brightness
        try:
            result = subprocess.run(
                ["ddcutil", "getvcp", "10", "--display", str(monitor["id"])],
                capture_output=True, text=True
            )
            
            # Parse the current brightness value
            brightness = 50  # Default value
            match = re.search(r'current value\s*=\s*(\d+)', result.stdout)
            if match:
                brightness = int(match.group(1))
                
            # Frame for each monitor
            frame = Gtk.Frame(label=f"Monitor {monitor['id']}: {monitor['model']}")
            self.monitors_box.pack_start(frame, False, False, 0)
            
            # Container for monitor controls
            control_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
            control_box.set_margin_start(10)
            control_box.set_margin_end(10)
            control_box.set_margin_top(10)
            control_box.set_margin_bottom(10)
            frame.add(control_box)
            
            # Brightness slider
            brightness_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            control_box.pack_start(brightness_box, False, False, 0)
            
            brightness_label = Gtk.Label(label="Brightness:")
            brightness_box.pack_start(brightness_label, False, False, 5)
            
            adjustment = Gtk.Adjustment(value=brightness, lower=0, upper=100, step_increment=1)
            scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adjustment)
            scale.set_digits(0)
            scale.set_hexpand(True)
            scale.set_size_request(200, -1)
            
            # Update value label during drag, but only set brightness on release
            scale.connect("value-changed", self.update_value_label, value_label := Gtk.Label(label=f"{brightness}%"))
            scale.connect("button-release-event", self.on_slider_release, monitor["id"])
            
            brightness_box.pack_start(scale, True, True, 0)
            brightness_box.pack_start(value_label, False, False, 5)
            
        except Exception as e:
            # If monitor not available, show error
            label = Gtk.Label(label=f"Error getting brightness: {str(e)}")
            self.monitors_box.pack_start(label, False, False, 0)
    
    def update_value_label(self, scale, label):
        value = int(scale.get_value())
        label.set_text(f"{value}%")
    
    def on_slider_release(self, scale, event, monitor_id):
        brightness = int(scale.get_value())
        threading.Thread(
            target=self.set_brightness,
            args=(monitor_id, brightness),
            daemon=True
        ).start()
    
    def set_brightness(self, monitor_id, brightness):
        try:
            subprocess.run(
                ["ddcutil", "setvcp", "10", str(brightness), "--display", str(monitor_id)],
                check=True
            )
            GLib.idle_add(
                self.status_label.set_text,
                f"Set monitor {monitor_id} brightness to {brightness}%"
            )
        except subprocess.CalledProcessError as e:
            GLib.idle_add(
                self.status_label.set_text,
                f"Error setting brightness: {e}"
            )

if __name__ == "__main__":
    app = MonitorBrightnessControl()
    app.run()
