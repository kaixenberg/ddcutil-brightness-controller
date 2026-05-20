#!/usr/bin/env python3
import argparse
import sys

import utils
from app import MonitorBrightnessControl

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-H", "--help", action="help", help="Show this help message and exit")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("-V", "--version", action="store_true", help="Show version info")
    parser.add_argument("--headless", action="store_true", help="Run in background with only the tray icon")
    
    args, unknown = parser.parse_known_args()
    
    if args.version:
        print(utils.get_version())
        sys.exit(0)
        
    app = MonitorBrightnessControl(verbose=args.verbose, headless=args.headless)
    app.run(sys.argv[:1] + unknown)

if __name__ == "__main__":
    main()
