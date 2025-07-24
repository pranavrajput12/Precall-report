"""
Centralized logging configuration for the CrewAI Workflow Orchestration Platform.
This module provides a standardized logging format and configuration across the application.
"""

import logging
import logging.config
import os
import sys
from datetime import datetime

# Note: We can't import config_system here to avoid circular imports
# since config_system imports logging_config
# Instead, we'll update the configuration in the configure_logging function
# when it's called after config_system is initialized

# Default log settings (will be overridden by config system when available)
LOG_LEVEL = os.environ.get("CREWAI_LOGGING_LEVEL", "INFO").upper()
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FILE = os.path.join('logs', f'app_{datetime.now().strftime("%Y%m%d")}.log')
MAX_BYTES = 10485760  # 10MB
BACKUP_COUNT = 10

# Configure logging
def configure_logging(config_system=None):
    """
    Configure the logging system with standardized format.
    This should be called at application startup before any logging occurs.
    
    Args:
        config_system: Optional configuration system instance.
                      If provided, will use config values instead of defaults.
    """
    global LOG_LEVEL, LOG_FORMAT, DATE_FORMAT, LOG_FILE, MAX_BYTES, BACKUP_COUNT
    
    # If config_system is provided, use it to override defaults
    if config_system:
        LOG_LEVEL = config_system.get("logging.level", LOG_LEVEL)
        LOG_FORMAT = config_system.get("logging.format", LOG_FORMAT)
        DATE_FORMAT = config_system.get("logging.date_format", DATE_FORMAT)
        LOG_FILE = config_system.get("logging.file", LOG_FILE)
        MAX_BYTES = config_system.get("logging.max_size", MAX_BYTES)
        BACKUP_COUNT = config_system.get("logging.backup_count", BACKUP_COUNT)
    
    # Ensure LOG_LEVEL is uppercase
    if isinstance(LOG_LEVEL, str):
        LOG_LEVEL = LOG_LEVEL.upper()
    
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': LOG_FORMAT,
                'datefmt': DATE_FORMAT,
            },
        },
        'handlers': {
            'console': {
                'level': LOG_LEVEL,
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                'stream': sys.stdout,
            },
            'file': {
                'level': LOG_LEVEL,
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': LOG_FILE,
                'maxBytes': MAX_BYTES,
                'backupCount': BACKUP_COUNT,
                'formatter': 'standard',
            },
        },
        'loggers': {
            '': {  # Root logger
                'handlers': ['console', 'file'],
                'level': LOG_LEVEL,
                'propagate': True,
            },
        },
    })

    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    # Log startup message
    logging.getLogger(__name__).info(f"Logging system initialized with level {LOG_LEVEL}")

# Helper functions for standardized log messages
def log_error(logger, message, error=None, exc_info=False):
    """
    Log an error with standardized format.
    
    Args:
        logger: The logger instance
        message: The error message
        error: The exception object (optional)
        exc_info: Whether to include exception traceback (default: False)
    """
    if error:
        logger.error(f"Error: {message}: {str(error)}", exc_info=exc_info)
    else:
        logger.error(f"Error: {message}", exc_info=exc_info)

def log_warning(logger, message):
    """
    Log a warning with standardized format.
    
    Args:
        logger: The logger instance
        message: The warning message
    """
    logger.warning(f"Warning: {message}")

def log_info(logger, message):
    """
    Log an info message with standardized format.
    
    Args:
        logger: The logger instance
        message: The info message
    """
    logger.info(message)

def log_debug(logger, message):
    """
    Log a debug message with standardized format.
    
    Args:
        logger: The logger instance
        message: The debug message
    """
    logger.debug(message)

# Configure logging when this module is imported
configure_logging()