import os
import json
from pathlib import Path
import sys

# Paths
BASE_DIR = Path(__file__).parent.parent
CURR_DIR = Path().cwd()

# Config
DEBUG = False
ACCEPT = ["*.png", "*.jpg", "*.gif", "*.webm", "*.jpeg", "*.webp"]
DELETE_ORIGINAL = True

# Logging
LOGGERS = {
    "version": 1,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stderr,
            "formatter": "basic",
        },
    },
    "formatters": {
        "basic": {
            "style": "{",
            "format": "{asctime:s} [{levelname:s}] -- {name:s}: {message:s}",
        }
    },
    "loggers": {
        "user_info": {
            "handlers": ("console",),
            "level": "INFO" if DEBUG is False else "DEBUG",
        },
    },
}

