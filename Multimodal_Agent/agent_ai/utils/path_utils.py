import os
from typing import Optional

def resolve_special_folder(folder_name: str) -> Optional[str]:
    """
    Attempts to resolve the absolute path of a special folder (e.g., 'videos', 'documents', 'desktop')
    in a platform-agnostic way. Returns None if not found.
    The folder_name should be case-insensitive and not hardcoded in the agent logic.
    """
    folder_name = folder_name.lower()
    user_profile = os.environ.get('USERPROFILE') or os.environ.get('HOME')
    if not user_profile:
        return None
    # Common Windows folders
    candidates = [
        os.path.join(user_profile, folder_name.capitalize()),
        os.path.join(user_profile, folder_name),
    ]
    for path in candidates:
        if os.path.isdir(path):
            return path
    # Try XDG user dirs (Linux)
    xdg_dir = os.environ.get(f'XDG_{folder_name.upper()}_DIR')
    if xdg_dir and os.path.isdir(xdg_dir):
        return xdg_dir
    return None
