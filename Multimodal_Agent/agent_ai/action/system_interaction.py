"""
SystemInteraction class for automating system-level actions (mouse, keyboard, shell, etc.).
"""

import pyautogui
import time
import subprocess
from ..utils.logger import Logger
from ..utils.window_utils import focus_window
from ..utils.platform_utils import is_windows, is_mac, is_linux

class SystemInteraction:
    """Automates system-level actions for the agent."""
    def __init__(self):
        pyautogui.FAILSAFE = True
        self.logger = Logger()

    def move_mouse(self, x: int, y: int, duration: float = 0.5):
        """Moves the mouse cursor to absolute coordinates."""
        print(f"Moving mouse to ({x}, {y})")
        pyautogui.moveTo(x, y, duration=duration)

    def click(self, x: int = None, y: int = None, button: str = 'left'):
        """Performs a mouse click at current position or specified coordinates."""
        if x is not None and y is not None:
            print(f"Clicking at ({x}, {y}) with {button} button")
            pyautogui.click(x=x, y=y, button=button)
        else:
            print(f"Clicking at current position with {button} button")
            pyautogui.click(button=button)

    def type_text(self, text: str, interval: float = 0.05):
        """Types out a string of text."""
        print(f"Typing text: '{text}'")
        pyautogui.write(text, interval=interval)

    def press_key(self, key: str):
        """Presses a single key."""
        print(f"Pressing key: '{key}'")
        pyautogui.press(key)

    def hotkey(self, *args):
        """Presses a combination of keys (e.g., 'ctrl', 'c')."""
        print(f"Pressing hotkey: {args}")
        pyautogui.hotkey(*args)

    def execute_shell_command(self, command: str, background: bool = False) -> tuple[int, str, str]:
        """Executes a shell command. If background=True, runs non-blocking and returns immediately. Platform-aware."""
        self.logger.info(f"Executing shell command: '{command}' (background={background})")
        shell = is_windows()
        try:
            if background:
                process = subprocess.Popen(command, shell=shell)
                self.logger.info(f"Started background process PID={process.pid}")
                return 0, f"Started background process PID={process.pid}", ""
            else:
                process = subprocess.run(command, shell=shell, capture_output=True, text=True, check=False)
                self.logger.info(f"Command '{command}' executed. Stdout: {process.stdout.strip()}")
                return process.returncode, process.stdout, process.stderr
        except Exception as e:
            self.logger.error(f"Error executing shell command '{command}': {e}", exc_info=True)
            return 1, "", str(e)

    def focus_window(self, title_substring: str, timeout: float = 5.0) -> bool:
        """Focuses a window whose title contains the given substring. Only works on Windows."""
        if not is_windows():
            self.logger.warning("Window focusing is only supported on Windows.")
            return False
        return focus_window(title_substring, timeout)

    # --- Selenium functions (Conceptual - requires more setup) ---
    # def initialize_browser(self, browser_type: str = 'chrome'):
    #     """Initializes a Selenium WebDriver."""
    #     if browser_type == 'chrome':
    #         self.driver = webdriver.Chrome() # Ensure chromedriver is in your PATH
    #     elif browser_type == 'firefox':
    #         self.driver = webdriver.Firefox() # Ensure geckodriver is in your PATH
    #     else:
    #         raise ValueError("Unsupported browser type")
    #     print(f"Initialized {browser_type} browser.")

    # def navigate_to_url(self, url: str):
    #     """Navigates the browser to a given URL."""
    #     if hasattr(self, 'driver'):
    #         self.driver.get(url)
    #         print(f"Navigated to: {url}")
    #     else:
    #         print("Browser not initialized. Call initialize_browser first.")

    # def find_element_and_click(self, by: By, value: str, timeout: int = 10):
    #     """Finds an element by locator and clicks it."""
    #     if hasattr(self, 'driver'):
    #         try:
    #             element = WebDriverWait(self.driver, timeout).until(
    #                 EC.element_to_be_clickable((by, value))
    #             )
    #             element.click()
    #             print(f"Clicked element found by {by} with value {value}")
    #         except Exception as e:
    #             print(f"Error clicking element: {e}")
    #     else:
    #         print("Browser not initialized.")

    # def close_browser(self):
    #     """Closes the Selenium browser."""
    #     if hasattr(self, 'driver'):
    #         self.driver.quit()
    #         print("Browser closed.")

system_interaction_logger = Logger()
SystemInteraction.logger = system_interaction_logger

# Example Usage (for testing)
if __name__ == "__main__":
    sys_interact = SystemInteraction()
    
    print("Moving mouse to 100, 100 in 2 seconds...")
    time.sleep(2) # Give yourself time to move mouse to top-left to activate failsafe if needed
    sys_interact.move_mouse(100, 100)
    
    print("Clicking at 100, 100 in 2 seconds...")
    time.sleep(2)
    sys_interact.click(100, 100) # This will click where your mouse currently is
    
    print("Typing 'Hello World!' in 2 seconds...")
    time.sleep(2)
    # Ensure you have a text editor or search bar active to see this
    sys_interact.type_text("Hello World!")
    
    print("Pressing Enter key in 2 seconds...")
    time.sleep(2)
    sys_interact.press_key('enter')
    
    # Selenium example (uncomment and install selenium if you want to test)
    # sys_interact.initialize_browser()
    # sys_interact.navigate_to_url("https://www.google.com")
    # time.sleep(3)
    # sys_interact.close_browser()