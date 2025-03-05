from logging.handlers import RotatingFileHandler
import inspect
import logging
import os

LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "logs"))
LOG_FILE = os.path.join(LOG_DIR, "backend.log")

def setup_logger(name) -> logging.Logger:
    """Initializes and configures the application logger."""
    
    os.makedirs(LOG_DIR, exist_ok=True) # Create the logs directory if it doesn't exist
    logger = logging.getLogger(name) 


    # Prevent duplicate handlers if setup_logger is called multiple times
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.DEBUG)
    log_format = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(caller_filename)s:%(caller_lineno)d - %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ"
    )


    # Console Handler (debugging)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

    # File Handler
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=3 * 1024 * 1024, backupCount=3
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    return logger

LOGGER = setup_logger(__name__)



def get_caller_info():
    """Returns filename and line number of the caller"""
    frame = inspect.stack()[2]  # [2] to get the caller of log function
    return os.path.basename(frame.filename), frame.lineno

def log_info(message):
    filename, lineno = get_caller_info()
    LOGGER.info(message, extra={"caller_filename": filename, "caller_lineno": lineno})

def log_error(message):
    filename, lineno = get_caller_info()
    LOGGER.error(message, extra={"caller_filename": filename, "caller_lineno": lineno})

def log_warning(message):
    filename, lineno = get_caller_info()
    LOGGER.warning(message, extra={"caller_filename": filename, "caller_lineno": lineno})

def log_debug(message):
    filename, lineno = get_caller_info()
    LOGGER.debug(message, extra={"caller_filename": filename, "caller_lineno": lineno})