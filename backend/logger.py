"""
Logging configuration for TaskLedger.
Provides structured JSON logging for production readiness.
"""
import logging
import sys
from pythonjsonlogger import jsonlogger
from config import settings


def setup_logger() -> logging.Logger:
    """Configure and return application logger."""
    
    logger = logging.getLogger("taskledger")
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Clear existing handlers
    logger.handlers = []
    
    # Console handler with JSON formatting
    handler = logging.StreamHandler(sys.stdout)
    
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


# Global logger instance
logger = setup_logger()
