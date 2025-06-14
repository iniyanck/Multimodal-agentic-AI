# agent_ai/perception/file_io.py

import os
from ..utils.logger import Logger # Import Logger

class FileIO:
    def __init__(self, base_path="."):
        self.base_path = base_path
        self.logger = Logger() # Initialize Logger

    def read_file(self, filename: str) -> str | None:
        """Reads the content of a specified file. Designed for text files."""
        filepath = os.path.join(self.base_path, filename)
        
        # Add a simple check for common image file extensions
        # This is a heuristic and might not cover all binary files
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp']
        if any(filepath.lower().endswith(ext) for ext in image_extensions):
            self.logger.error(f"Attempted to read binary image file '{filename}' as text. Use appropriate image handling for this file type.")
            print(f"Error: Cannot read image file '{filename}' as text. This function is for text files.")
            return None

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f: # Specify encoding and error handling
                content = f.read()
            self.logger.info(f"Successfully read file: {filename}")
            return content
        except FileNotFoundError:
            self.logger.error(f"Error: File not found at {filepath}")
            print(f"Error: File not found at {filepath}")
            return None
        except Exception as e:
            self.logger.error(f"Error reading file {filename}: {e}", exc_info=True)
            print(f"Error reading file {filename}: {e}")
            return None

    def write_file(self, filename: str, content: str) -> bool:
        """Writes content to a specified file."""
        filepath = os.path.join(self.base_path, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f: # Specify encoding
                f.write(content)
            self.logger.info(f"Successfully wrote to file: {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Error writing to file {filename}: {e}", exc_info=True)
            print(f"Error writing to file {filename}: {e}")
            return False

    def list_directory(self, path: str = ".") -> list[str] | None:
        """Lists contents of a directory."""
        target_path = os.path.join(self.base_path, path)
        try:
            contents = os.listdir(target_path)
            self.logger.info(f"Listed contents of directory {target_path}")
            return contents
        except FileNotFoundError:
            self.logger.error(f"Error: Directory not found at {target_path}")
            print(f"Error: Directory not found at {target_path}")
            return None
        except Exception as e:
            self.logger.error(f"Error listing directory {target_path}: {e}", exc_info=True)
            print(f"Error listing directory {target_path}: {e}")
            return None