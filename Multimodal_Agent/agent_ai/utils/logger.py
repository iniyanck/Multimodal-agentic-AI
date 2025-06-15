# agent_ai/utils/logger.py

import logging
import os

class Logger:
    """Logger class for logging messages to file and console."""
    _initialized = False # Class-level flag

    def __init__(self, log_file: str = "agent.log", level=logging.INFO):
        """Initializes the logger, sets up file and console handlers."""
        if not Logger._initialized: # Only run basicConfig once
            log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
            os.makedirs(log_dir, exist_ok=True)
            self.log_filepath = os.path.join(log_dir, log_file)

            # Clear existing handlers to prevent duplicate messages if run multiple times
            # in quick succession or by external frameworks.
            for handler in logging.root.handlers[:]:
                logging.root.removeHandler(handler)

            logging.basicConfig(
                level=level,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(self.log_filepath),
                    logging.StreamHandler() # Also print to console
                ]
            )
            Logger._initialized = True
            self.logger = logging.getLogger(__name__) # Use specific logger for this class
            self.logger.info("Agent Logger initialized.")
        else:
            self.logger = logging.getLogger(__name__) # Just get the existing logger instance
            # You could log a debug message here if you want to know it's being "re-got"
            # self.logger.debug("Logger already initialized, reusing existing instance.")

    def info(self, message: str, *args, **kwargs):
        """Logs an informational message."""
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        """Logs a warning message."""
        self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        """Logs an error message."""
        self.logger.error(message, *args, **kwargs)

    def debug(self, message: str, *args, **kwargs):
        """Logs a debug message."""
        self.logger.debug(message, *args, **kwargs)

# Example Usage (for testing)
if __name__ == "__main__":
    logger = Logger()
    logger.info("This is an informational message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message with traceback.", exc_info=True) # Now works
    logger.debug("This is a debug message.")