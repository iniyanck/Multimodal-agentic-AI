"""
ScreenCapture class for capturing screenshots and screen regions with logging and error handling.
"""

from typing import Optional
import pyautogui
from PIL import Image
import io
from ..utils.logger import Logger
from ..utils.platform_utils import is_windows, is_mac, is_linux

class ScreenCapture:
    """Handles screen capture operations for the agent."""
    def __init__(self):
        pyautogui.FAILSAFE = True
        self.logger = Logger()
        try:
            from PIL import Image
            self.logger.info("Pillow (PIL) library is available for image processing.")
        except ImportError:
            self.logger.critical(
                "Pillow (PIL) library not found. Screen capture functionality will not work. "
                "Please install with: pip install Pillow"
            )
            raise ImportError("Pillow (PIL) library is required for ScreenCapture but not found.")

    def capture_screen(self, filename: str | None = None) -> Optional[Image.Image]:
        """Captures the entire screen. Optionally saves to a file. Platform-aware."""
        if not (is_windows() or is_mac() or is_linux()):
            self.logger.error("Screen capture is not supported on this platform.")
            return None
        try:
            screenshot = pyautogui.screenshot()
            if filename:
                screenshot.save(filename)
                self.logger.info(f"Screenshot saved to {filename}")
            self.logger.info("Screen captured successfully.")
            return screenshot
        except pyautogui.PyAutoGUIException as e:
            self.logger.error(f"PyAutoGUI error capturing screen: {e}.", exc_info=True)
            return None
        except Exception as e:
            self.logger.error(f"An unexpected error occurred capturing screen: {e}", exc_info=True)
            return None

    def capture_screen_bytes(self, filename: str | None = None) -> bytes | None:
        """Captures the entire screen and returns the image data as bytes. Optionally saves to a file."""
        try:
            screenshot_pil = pyautogui.screenshot()
            if filename:
                screenshot_pil.save(filename)
                self.logger.info(f"Screenshot saved to {filename}")
            img_byte_arr = io.BytesIO()
            screenshot_pil.save(img_byte_arr, format='PNG')
            self.logger.info("Screen captured as bytes.")
            return img_byte_arr.getvalue()
        except pyautogui.PyAutoGUIException as e:
            self.logger.error(f"PyAutoGUI error capturing screen to bytes: {e}.", exc_info=True)
            return None
        except Exception as e:
            self.logger.error(f"An unexpected error occurred capturing screen to bytes: {e}", exc_info=True)
            return None

    def capture_region(self, left: int, top: int, width: int, height: int, filename: str | None = None) -> Optional[Image.Image]:
        """Captures a specific region of the screen. Optionally saves to a file."""
        try:
            screenshot = pyautogui.screenshot(region=(left, top, width, height))
            if filename:
                screenshot.save(filename)
                self.logger.info(f"Region screenshot saved to {filename} (Region: {left},{top},{width},{height})")
            self.logger.info(f"Region captured: ({left}, {top}, {width}, {height}).")
            return screenshot
        except pyautogui.PyAutoGUIException as e:
            self.logger.error(f"PyAutoGUI error capturing region ({left},{top},{width},{height}): {e}.", exc_info=True)
            return None
        except Exception as e:
            self.logger.error(f"An unexpected error occurred capturing region ({left},{top},{width},{height}): {e}", exc_info=True)
            return None

    def capture_region_bytes(self, left: int, top: int, width: int, height: int, filename: str | None = None) -> bytes | None:
        """Captures a specific region of the screen and returns the image data as bytes. Optionally saves to a file."""
        try:
            screenshot_pil = pyautogui.screenshot(region=(left, top, width, height))
            if filename:
                screenshot_pil.save(filename)
                self.logger.info(f"Region screenshot saved to {filename} (Region: {left},{top},{width},{height})")
            img_byte_arr = io.BytesIO()
            screenshot_pil.save(img_byte_arr, format='PNG')
            self.logger.info(f"Region captured as bytes: ({left}, {top}, {width}, {height})")
            return img_byte_arr.getvalue()
        except pyautogui.PyAutoGUIException as e:
            self.logger.error(f"PyAutoGUI error capturing region to bytes ({left},{top},{width},{height}): {e}.", exc_info=True)
            return None
        except Exception as e:
            self.logger.error(f"An unexpected error occurred capturing region to bytes ({left},{top},{width},{height}): {e}", exc_info=True)
            return None

if __name__ == "__main__":
    import os
    # Clean up old test files if they exist
    test_files = ["full_screen.png", "full_screen_bytes.png", "region_screen.png", "region_screen_bytes.png"]
    for f in test_files:
        if os.path.exists(f):
            os.remove(f)
    print("--- Testing ScreenCapture ---")
    try:
        screen_capture = ScreenCapture()
    except ImportError as e:
        print(f"Skipping ScreenCapture tests due to missing dependency: {e}")
        print("Please install Pillow: pip install Pillow")
        exit()
    print("\nCapturing full screen and saving to 'full_screen.png'...")
    full_screen_pil_image = screen_capture.capture_screen("full_screen.png")
    if full_screen_pil_image:
        print(f"Full screen image captured (PIL Image object type: {type(full_screen_pil_image)}).")
    else:
        print("Full screen capture failed.")
    print("\nCapturing full screen as bytes and saving to 'full_screen_bytes.png'...")
    full_screen_bytes_data = screen_capture.capture_screen_bytes("full_screen_bytes.png")
    if full_screen_bytes_data:
        print(f"Full screen captured as bytes (Bytes object length: {len(full_screen_bytes_data)}).")
    else:
        print("Full screen capture to bytes failed.")
    region_left, region_top, region_width, region_height = 0, 0, 200, 100
    print(f"\nCapturing region ({region_left}, {region_top}, {region_width}, {region_height}) and saving to 'region_screen.png'...")
    region_pil_image = screen_capture.capture_region(region_left, region_top, region_width, region_height, "region_screen.png")
    if region_pil_image:
        print(f"Region image captured (PIL Image object type: {type(region_pil_image)}).")
    else:
        print("Region capture failed.")
    print(f"\nCapturing region ({region_left}, {region_top}, {region_width}, {region_height}) as bytes and saving to 'region_screen_bytes.png'...")
    region_bytes_data = screen_capture.capture_region_bytes(region_left, region_top, region_width, region_height, "region_screen_bytes.png")
    if region_bytes_data:
        print(f"Region captured as bytes (Bytes object length: {len(region_bytes_data)}).")
    else:
        print("Region capture to bytes failed.")
    print("\n--- ScreenCapture tests completed ---")