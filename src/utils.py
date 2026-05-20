import os
import subprocess

def is_hyprland(verbose=False):
    if os.environ.get("XDG_CURRENT_DESKTOP") != "Hyprland":
        if verbose:
            print("XDG_CURRENT_DESKTOP is not Hyprland. Hiding display power off option.")
        return False
    return True

def turn_off_display(verbose=False):
    cmd = "sleep 3 && hyprctl dispatch 'hl.dsp.dpms({ action = \"off\" })' && loginctl lock-session"
    if verbose:
        print(f"Executing: {cmd}")
    subprocess.Popen(cmd, shell=True)

def get_version():
    version_str = "staging"
    try:
        git_commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL, text=True).strip()
        if git_commit:
            version_str += f"-{git_commit}"
    except Exception:
        pass
    return version_str
