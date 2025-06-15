# agent_ai/utils/platform_utils.py
"""
Platform utilities for cross-platform checks and helpers.
"""
import sys
import platform

def is_windows() -> bool:
    """Returns True if the current platform is Windows."""
    return sys.platform.startswith('win')

def is_mac() -> bool:
    """Returns True if the current platform is macOS."""
    return sys.platform.startswith('darwin')

def is_linux() -> bool:
    """Returns True if the current platform is Linux."""
    return sys.platform.startswith('linux')

def get_platform_name() -> str:
    """Returns a human-readable platform name."""
    if is_windows():
        return 'Windows'
    if is_mac():
        return 'macOS'
    if is_linux():
        return 'Linux'
    return platform.system()
