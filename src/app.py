import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk, Gio

GLib.set_prgname("app.nidhi.brctl")

from utils import is_hyprland, turn_off_display
from monitor import MonitorManager
from tray import TrayManager

class MonitorBrightnessControl(Gtk.Application):
    def __init__(self, verbose=False, headless=False):
        super().__init__(application_id="app.nidhi.brctl")
        self.verbose = verbose
        self.headless = headless
        self.dpms_available = is_hyprland(verbose)
        self.connect("activate", self.on_activate)
        self.monitors = []
        self.window = None
        self.monitor_manager = MonitorManager(verbose=verbose)
        self.tray_manager = None

    def on_activate(self, app):
        if self.window is not None:
            self.window.present()
            return

        self.window = Gtk.ApplicationWindow(application=app, title="Monitor Brightness Control")
        self.window.connect("delete-event", self.on_window_delete)
        self.window.connect("key-press-event", self.on_key_press)
        
        self.tray_manager = TrayManager(
            verbose=self.verbose,
            dpms_available=self.dpms_available,
            on_turn_off_display=self.on_turn_off_display_click,
            on_open=self.on_tray_open,
            on_quit=self.quit
        )

        self.window.set_default_size(400, 300)
        self.window.set_border_width(10)
        
        header_bar = Gtk.HeaderBar()
        header_bar.set_show_close_button(True)
        header_bar.set_title("Brightness Controller")
        self.window.set_titlebar(header_bar)
        
        menu_button = Gtk.MenuButton()
        icon = Gio.ThemedIcon(name="open-menu-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        menu_button.add(image)
        header_bar.pack_end(menu_button)
        
        menu = Gtk.Menu()
        
        refresh_item = Gtk.MenuItem(label="Refresh Monitors")
        refresh_item.connect("activate", self.detect_monitors)
        menu.append(refresh_item)
        
        about_item = Gtk.MenuItem(label="About")
        about_item.connect("activate", self.show_about_dialog)
        menu.append(about_item)
        
        menu.show_all()
        menu_button.set_popup(menu)
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.window.add(main_box)
        
        self.status_label = Gtk.Label(label="Detecting monitors...")
        main_box.pack_start(self.status_label, False, False, 0)
        
        self.monitors_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        main_box.pack_start(self.monitors_box, True, True, 0)
        
        if self.dpms_available:
            button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            main_box.pack_end(button_box, False, False, 0)
            
            turn_off_button = Gtk.Button(label="Turn off display")
            turn_off_button.connect("clicked", lambda w: self.on_turn_off_display_click())
            button_box.pack_start(turn_off_button, False, False, 0)
        
        if not self.headless:
            self.window.show_all()
        self.detect_monitors()

    def on_window_delete(self, widget, event):
        self.window.hide()
        return True

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.window.hide()
            return True
        return False

    def on_tray_open(self):
        self.headless = False
        if self.window:
            self.window.show_all()
            self.window.present()
            self.window.grab_focus()
            
            # Force focus on Hyprland
            if self.dpms_available:
                import subprocess
                subprocess.Popen(["hyprctl", "dispatch", "hl.dsp.focus({ window = \"class:app.nidhi.brctl\" })"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def on_turn_off_display_click(self):
        turn_off_display(verbose=self.verbose)

    def show_about_dialog(self, widget=None):
        from utils import get_version
        
        about = Gtk.AboutDialog(transient_for=self.window, modal=True)
        about.set_program_name("Brightness Controller")
        about.set_version(get_version())
        about.set_website("https://github.com/kaixenberg/ddcutil-brightness-controller")
        about.set_website_label("Source Code")
        about.set_authors(["https://github.com/kaixenberg/ddcutil-brightness-controller/graphs/contributors"])
        about.set_comments("Report an issue: https://github.com/kaixenberg/ddcutil-brightness-controller/issues")
        about.set_license("This application comes with absolutely no warranty. See the GNU General Public License, version 3 or later for details.")
        about.set_license_type(Gtk.License.CUSTOM)
        about.set_logo_icon_name("display-brightness-symbolic")
        
        about.run()
        about.destroy()

    def detect_monitors(self, widget=None):
        for child in self.monitors_box.get_children():
            self.monitors_box.remove(child)
        
        self.status_label.set_text("Detecting monitors...")
        self.monitor_manager.detect_monitors(
            on_success=self._on_monitors_detected,
            on_error=self._on_monitors_error
        )

    def _on_monitors_detected(self, monitors):
        if not monitors:
            self.status_label.set_text("No monitors detected with DDC support")
            return
            
        self.monitors = monitors
        for monitor in self.monitors:
            self._create_monitor_control(monitor)
        self.status_label.set_text(f"Found {len(self.monitors)} monitor(s)")
        
        if not self.headless:
            self.window.show_all()

    def _on_monitors_error(self, error_message):
        self.status_label.set_text(error_message)

    def _create_monitor_control(self, monitor):
        if monitor.get("error"):
            label = Gtk.Label(label=f"Monitor {monitor['id']} ({monitor['model']}): Error getting brightness: {monitor['error']}")
            self.monitors_box.pack_start(label, False, False, 0)
            return
            
        frame = Gtk.Frame(label=f"Monitor {monitor['id']}: {monitor['model']}")
        self.monitors_box.pack_start(frame, False, False, 0)
        
        control_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        control_box.set_margin_start(10)
        control_box.set_margin_end(10)
        control_box.set_margin_top(10)
        control_box.set_margin_bottom(10)
        frame.add(control_box)
        
        brightness_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        control_box.pack_start(brightness_box, False, False, 0)
        
        brightness_label = Gtk.Label(label="Brightness:")
        brightness_box.pack_start(brightness_label, False, False, 5)
        
        brightness = monitor["brightness"]
        adjustment = Gtk.Adjustment(value=brightness, lower=0, upper=100, step_increment=1)
        scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adjustment)
        scale.set_digits(0)
        scale.set_hexpand(True)
        scale.set_size_request(200, -1)
        
        value_label = Gtk.Label(label=f"{brightness}%")
        scale.connect("value-changed", self.update_value_label, value_label)
        scale.connect("button-release-event", self.on_slider_release, monitor["id"])
        
        brightness_box.pack_start(scale, True, True, 0)
        brightness_box.pack_start(value_label, False, False, 5)

    def update_value_label(self, scale, label):
        value = int(scale.get_value())
        label.set_text(f"{value}%")

    def on_slider_release(self, scale, event, monitor_id):
        brightness = int(scale.get_value())
        self.monitor_manager.set_brightness(
            monitor_id, 
            brightness,
            on_success=self._on_set_brightness_success,
            on_error=self._on_set_brightness_error
        )
        return False

    def _on_set_brightness_success(self, message):
        self.status_label.set_text(message)

    def _on_set_brightness_error(self, message):
        self.status_label.set_text(message)
