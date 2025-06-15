import os
import re
from typing import List

def find_files_by_keyword(directory: str, keyword: str, extensions: List[str] = None) -> List[str]:
    """Search for files in a directory whose names contain the keyword (case-insensitive) and match given extensions."""
    matches = []
    if not os.path.isdir(directory):
        return matches
    for fname in os.listdir(directory):
        if keyword.lower() in fname.lower():
            if extensions:
                if any(fname.lower().endswith(ext) for ext in extensions):
                    matches.append(fname)
            else:
                matches.append(fname)
    return matches

def find_files_by_keyword_recursive(directory: str, keyword: str, extensions: List[str] = None) -> List[str]:
    """Recursively search for files in a directory and all subdirectories whose names contain the keyword (case-insensitive) and match given extensions."""
    matches = []
    for root, _, files in os.walk(directory):
        for fname in files:
            if keyword.lower() in fname.lower():
                if extensions:
                    if any(fname.lower().endswith(ext) for ext in extensions):
                        matches.append(os.path.join(root, fname))
                else:
                    matches.append(os.path.join(root, fname))
    return matches

VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']

def find_video_files_by_keyword(directory: str, keyword: str) -> List[str]:
    return find_files_by_keyword(directory, keyword, VIDEO_EXTENSIONS)

def find_video_files_by_keyword_recursive(directory: str, keyword: str) -> List[str]:
    return find_files_by_keyword_recursive(directory, keyword, VIDEO_EXTENSIONS)
