# agent_ai/utils/window_utils.py
"""
Utility functions for window management (focus, list, etc.) on Windows.
Requires: pygetwindow (pip install pygetwindow)
"""

import time
import pygetwindow as gw
import psutil

def focus_window(title_substring: str, timeout: float = 5.0) -> bool:
    """
    Focuses the first window whose title contains the given substring.

    Args:
        title_substring (str): The substring to search for in the window title.
        timeout (float, optional): The time in seconds to wait for the window to appear. Defaults to 5.0.

    Returns:
        bool: True if the window was successfully focused, False otherwise.
    """
    end_time = time.time() + timeout
    while time.time() < end_time:
        windows = gw.getAllTitles()
        for win_title in windows:
            if title_substring.lower() in win_title.lower():
                win = gw.getWindowsWithTitle(win_title)[0]
                win.activate()
                return True
        time.sleep(0.2)
    return False

def list_open_windows() -> list:
    """Returns a list of all open window titles."""
    try:
        return gw.getAllTitles()
    except Exception:
        return []

def is_window_open(title_substring: str) -> bool:
    """Checks if any window with the given substring is open."""
    try:
        return any(title_substring.lower() in t.lower() for t in gw.getAllTitles())
    except Exception:
        return False

def list_processes() -> list:
    """Returns a list of all running process names."""
    try:
        return [p.name() for p in psutil.process_iter(['name'])]
    except Exception:
        return []

def is_process_running(process_name: str) -> bool:
    """Checks if a process with the given name is running."""
    try:
        return any(process_name.lower() in p.name().lower() for p in psutil.process_iter(['name']))
    except Exception:
        return False
