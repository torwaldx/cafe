import logging
import logging.config
import os

import __main__

LOG_DIR = "/logs"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
LOG_BACKUP_COUNT = 3
noisy_loggers = ["httpx", "databases", "telethon", "asyncio", "aiohttp"]

def get_caller_name(default="app"):
    file = getattr(__main__, "__file__", None)
    if file:
        return os.path.splitext(os.path.basename(file))[0]
    return default

def get_logging_config(name: str, log_file: str):
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": LOG_FORMAT,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "default",
                "filename": log_file,
                "maxBytes": LOG_MAX_BYTES,
                "backupCount": LOG_BACKUP_COUNT,
                "encoding": "utf8",
            },
        },
        "loggers": {
            name: {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            **{
                lib_name: {
                    "level": "WARNING",
                    "propagate": False,
                } for lib_name in noisy_loggers
            }
        },
        "root": {
            "handlers": ["console"],
            "level": "INFO",
        },
    }

def setup_logger(name=None):
    name = name or get_caller_name()
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, f"{name}.log")

    config = get_logging_config(name, log_file)
    logging.config.dictConfig(config)
    return logging.getLogger(name)