# agent_ai/utils/platform_utils.py
"""
Platform utilities for cross-platform checks and helpers.
"""
import sys
import platform

def is_windows() -> bool:
    return sys.platform.startswith('win')

def is_mac() -> bool:
    return sys.platform.startswith('darwin')

def is_linux() -> bool:
    return sys.platform.startswith('linux')

def get_platform_name() -> str:
    if is_windows():
        return 'Windows'
    if is_mac():
        return 'macOS'
    if is_linux():
        return 'Linux'
    return platform.system()
