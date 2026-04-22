import logging
import logging.config
import os
from pythonjsonlogger import jsonlogger
from .config import settings

def setup_logging():
    """Configure structured JSON logging."""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, "trading_bot.json")
    
    # Custom format
    log_format = "%(asctime)s %(levelname)s %(name)s %(message)s"
    
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": jsonlogger.JsonFormatter,
                "fmt": log_format,
            },
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "level": settings.log_level,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "json",
                "filename": log_file,
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 3,
                "level": "DEBUG",
            }
        },
        "loggers": {
            "": {
                "handlers": ["console", "file"],
                "level": settings.log_level,
            },
            "uvicorn": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False
            }
        }
    }
    
    logging.config.dictConfig(logging_config)
    return logging.getLogger("TradingBot")
