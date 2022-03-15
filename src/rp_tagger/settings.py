from pathlib import Path
import sys

# Paths
BASE_DIR = Path(__file__).parent
CURR_DIR = Path().cwd()
TEST_DIR = Path(__file__).parent.parent / "test"
TEST_IMAGES_DIR = TEST_DIR / "test_images"

IMAGES_FROM_PATH = "/home/luis/Downloads/"
IMAGES_TO_PATH = "/home/luis/Pictures/RP/"

UNCLS_IMAGES_DIR = BASE_DIR / "static" / "img"

# Config
DEBUG = True
ACCEPT = ["*.png", "*.jpg", "*.gif", "*.webm"]
DELETE_ORIGINAL = True

# Database
DATABASES = {
        "default": {
            "engine": f"sqlite:///{BASE_DIR}/db.sqlite",
        },
        "test": {
            "engine": f"sqlite:///{TEST_DIR}/test_db.sqlite",
        },
}

# Logging
LOGGERS = {
    "version": 1,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stderr,
            "formatter": "basic",
        },
        "audit_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "maxBytes": 5000000,
            "backupCount": 1,
            "filename": BASE_DIR / "logs" / "api.error",
            "encoding": "utf-8",
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
        "audit": {"handlers": ("audit_file",), "level": "ERROR"},
        "global": {
            "handlers": ("console",),
            "level": "INFO" if DEBUG is False else "DEBUG",
        },
    },
}

