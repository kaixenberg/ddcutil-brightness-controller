# Monitor Brightness Controller

A simple GTK application to control the brightness of external monitors using ddcutil.

## Features

- Automatically detects monitors with DDC/CI support
- Provides individual brightness sliders for each detected monitor
- Shows monitor information including model name
- Updates brightness only when the slider is released, preventing "stepping" effects
- Provides status feedback for all operations

## Requirements

- Python 3
- GTK 3.0
- ddcutil
- PyGObject (for GTK bindings)

## Installation

### Install Dependencies

```bash
# On Debian/Ubuntu
sudo apt install ddcutil python3-gi

# On Fedora
sudo dnf install ddcutil python3-gobject

# On Arch Linux
sudo pacman -S ddcutil python-gobject
```

### Configure permissions (optional)

By default, ddcutil requires root permissions to communicate with monitors. You can either:

1. Run the application with sudo
2. Configure permissions for your user:

```bash
# Add your user to the i2c group
sudo usermod -aG i2c $USER
```

You'll need to log out and log back in for this change to take effect.

### Run the application

1. Clone this repository:
```bash
git clone https://github.com/YOUR_USERNAME/monitor-brightness-controller.git
cd monitor-brightness-controller
```

2. Make the script executable:
```bash
chmod +x brightness_control.py
```

3. Run the application:
```bash
./brightness_control.py
```

## Future Plans

1. Add complete ddcutil functionality

2. Add command line interface

3. Add time-based brightness control

4. Improve the ui


## Usage

- Drag the slider to adjust the brightness level of each monitor
- The brightness will only change when you release the slider
- Click "Refresh Monitors" to re-detect connected monitors

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the GNU Public License v3 - see the LICENSE file for details.
