import logging
import logging.config
import os

import __main__

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

noisy_loggers = ["httpx", "databases", "telethon", "asyncio", "aiohttp"]

def get_caller_name(default="app"):
    file = getattr(__main__, "__file__", None)
    if file:
        return os.path.splitext(os.path.basename(file))[0]
    return default

def get_logging_config(name: str):
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
        },
        "loggers": {
            name: {
                "handlers": ["console"],
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

    config = get_logging_config(name)
    logging.config.dictConfig(config)
    return logging.getLogger(name)