"""
Logging configuration with structlog for structured JSON logging
"""

import structlog
from pathlib import Path
from datetime import datetime
import json
import logging
from logging.handlers import RotatingFileHandler
import sys

from app.config import settings


def setup_logging():
    """Configure structured logging for the application"""
    
    # Ensure logs directory exists
    log_dir = Path(settings.LOGS_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Log file paths
    app_log = log_dir / "app.log"
    access_log = log_dir / "access.log"
    processing_log = log_dir / "processing.log"
    
    # Configure root logger
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Create file handlers with rotation
    def create_rotating_handler(filename):
        handler = RotatingFileHandler(
            filename,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        handler.setFormatter(logging.Formatter('%(message)s'))
        return handler
    
    # Application logger
    app_logger = logging.getLogger("app")
    app_logger.addHandler(create_rotating_handler(app_log))
    app_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Access logger
    access_logger = logging.getLogger("access")
    access_logger.addHandler(create_rotating_handler(access_log))
    access_logger.setLevel(logging.INFO)
    
    # Processing logger
    processing_logger = logging.getLogger("processing")
    processing_logger.addHandler(create_rotating_handler(processing_log))
    processing_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.LOG_LEVEL.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    return {
        "app": app_logger,
        "access": access_logger,
        "processing": processing_logger
    }


# Initialize loggers
loggers = setup_logging()
app_logger = loggers["app"]
access_logger = loggers["access"]
processing_logger = loggers["processing"]

# Create structlog-wrapped versions
log = structlog.get_logger("app")
access_log = structlog.get_logger("access")
processing_log = structlog.get_logger("processing")
