import os
import sys
import gi
from pathlib import Path
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gio

try:
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3 as appindicator
except ValueError:
    appindicator = None

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # If running in development, use the absolute path of main.py's parent
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    return os.path.join(base_path, relative_path)

class TrayManager:
    def __init__(self, verbose=False, dpms_available=False, on_turn_off_display=None, on_open=None, on_quit=None):
        self.verbose = verbose
        self.dpms_available = dpms_available
        self.on_turn_off_display = on_turn_off_display
        self.on_open = on_open
        self.on_quit = on_quit
        
        if appindicator is None:
            print("AppIndicator3 not available. Tray icon will not be shown.")
            return

        self.icons_dir = get_resource_path(os.path.join("res", "icons"))

        self.indicator = appindicator.Indicator.new(
            "brightness-control-indicator",
            "display-brightness-symbolic",
            appindicator.IndicatorCategory.APPLICATION_STATUS)
        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)

        self.update_tray_icon()

        settings = Gtk.Settings.get_default()
        if settings:
            settings.connect("notify::gtk-theme-name", self.on_theme_changed)
            settings.connect("notify::gtk-application-prefer-dark-theme", self.on_theme_changed)
        
        menu = Gtk.Menu()
        
        open_item = Gtk.MenuItem(label="Open App")
        if self.on_open:
            open_item.connect("activate", lambda w: self.on_open())
        menu.append(open_item)
        
        if self.dpms_available:
            turn_off_item = Gtk.MenuItem(label="Turn off display")
            if self.on_turn_off_display:
                turn_off_item.connect("activate", lambda w: self.on_turn_off_display())
            menu.append(turn_off_item)
        
        about_item = Gtk.MenuItem(label="About")
        about_item.connect("activate", self.show_about)
        menu.append(about_item)
        
        exit_item = Gtk.MenuItem(label="Exit")
        if self.on_quit:
            exit_item.connect("activate", lambda w: self.on_quit())
        menu.append(exit_item)
        
        menu.show_all()
        self.indicator.set_menu(menu)

        try:
            bus = Gio.bus_get_sync(Gio.BusType.SESSION)
            bus.add_filter(self._dbus_message_filter)
            if self.verbose:
                print("DBus filter registered for tray left/middle click")
        except Exception as e:
            if self.verbose:
                print(f"Failed to set up DBus tray click handler: {e}")

    def show_about(self, widget=None):
        from utils import get_version
        
        about = Gtk.AboutDialog()
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

    def _dbus_message_filter(self, connection, message, incoming):
        if incoming and message.get_message_type() == Gio.DBusMessageType.METHOD_CALL:
            member = message.get_member()
            if member in ("Activate", "SecondaryActivate"):
                if self.verbose:
                    print(f"Tray icon {member} received (left/middle click)")
                if self.on_open:
                    GLib.idle_add(self.on_open)
        return message

    def on_theme_changed(self, settings, param):
        self.update_tray_icon()

    def update_tray_icon(self):
        if not hasattr(self, 'indicator') or appindicator is None:
            return

        settings = Gtk.Settings.get_default()
        
        is_dark = False
        if settings:
            theme_name = settings.get_property("gtk-theme-name") or ""
            prefer_dark = settings.get_property("gtk-application-prefer-dark-theme")
            is_dark = "dark" in theme_name.lower() or prefer_dark
        
        if self.verbose:
            print(f"Detected {'dark mode' if is_dark else 'light mode'} UI")
            
        icon_name = "tray_icon_light" if is_dark else "tray_icon_dark"
        icon_path = os.path.join(self.icons_dir, f"{icon_name}.svg")

        if os.path.exists(icon_path):
            self.indicator.set_icon_theme_path(self.icons_dir)
            self.indicator.set_icon_full(icon_name, "Brightness Control")
        else:
            self.indicator.set_icon_full("display-brightness-symbolic", "Brightness Control")
