from rp_tagger.conf._base import *

IMAGES_FROM_DIR = "/home/luis/Downloads/"
IMAGES_DIR = "/home/luis/Pictures/RP/"
UNCLS_IMAGES_DIR = BASE_DIR / "static" / "img"

# Config
DEBUG = False
DELETE_ORIGINAL = True

# Database
DATABASES = {
        "default": {
            "engine": f"sqlite:///{BASE_DIR}/db.sqlite",
            "config": {"autocommit": True,}
        }
}
