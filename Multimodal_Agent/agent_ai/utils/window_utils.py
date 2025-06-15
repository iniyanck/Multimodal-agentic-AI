# agent_ai/utils/window_utils.py
"""
Utility functions for window management (focus, list, etc.) on Windows.
Requires: pygetwindow (pip install pygetwindow)
"""

import time
import pygetwindow as gw

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
