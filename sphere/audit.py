# audit.py
# Author: Margaret Hamilton (Reliability, Safety & Failure-Aware Design)

import logging
import sys

# We configure a logger to write to a dedicated audit file within the user's .sphere directory.
# This ensures that even if the tool crashes, we have a record of what it was trying to do.
# This is mission-critical for debugging and ensuring we never fail silently.

LOG_FILE_PATH = ""

def initialize_logging(log_path: str):
    """Sets up the logging configuration. Must be called once at startup."""
    global LOG_FILE_PATH
    LOG_FILE_PATH = log_path
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE_PATH),
            logging.StreamHandler(sys.stdout) # Also print to console for immediate feedback
        ]
    )

def log_info(message: str):
    """Logs an informational message."""
    logging.info(message)

def log_warning(message: str):
    """Logs a warning. The system can continue, but something is not right."""
    logging.warning(message)

def log_error(message: str):
    """Logs a critical error. The system should likely terminate gracefully."""
    logging.error(message)

def handle_critical_failure(error_message: str):
    """
    This function is called when a catastrophic, unrecoverable error occurs.
    Its job is to log the failure state and exit cleanly, ensuring the user is not
    left with a corrupted state or a hanging process.
    """
    log_error(f"CRITICAL FAILURE: {error_message}")
    log_error(f"The application cannot continue. Please check the audit log at {LOG_FILE_PATH} for details.")
    log_error("Exiting with status code 1.")
    sys.exit(1)
