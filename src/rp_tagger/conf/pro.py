from rp_tagger.conf._base import *

# Change this path to acquire images from a different folder
#IMAGES_FROM_DIR = "/home/[user]/Pictures/"
IMAGES_FROM_DIR = str(Path().home() / "Downloads")
IMAGES_DIR = Path().home() / "Pictures" / "RP"
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
