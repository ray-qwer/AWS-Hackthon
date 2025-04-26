import logging
import os

def setup_logging():
    """Set up logging configuration"""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def get_logger(name: str):
    """Get a logger with the specified name"""
    return logging.getLogger(name)

def log_error(logger: logging.Logger, error: Exception, message: str = None):
    """Log an error with optional message"""
    if message:
        logger.error(f"{message}: {str(error)}")
    else:
        logger.error(str(error))

def log_info(logger: logging.Logger, message: str):
    """Log an info message"""
    logger.info(message)

def log_debug(logger: logging.Logger, message: str):
    """Log a debug message"""
    logger.debug(message)

def log_warning(logger: logging.Logger, message: str):
    """Log a warning message"""
    logger.warning(message) 