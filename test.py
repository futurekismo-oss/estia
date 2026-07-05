import subprocess


def get_active_window():
    window_id = subprocess.check_output(["xdotool", "getac"])
