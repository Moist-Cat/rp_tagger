from rp_tagger.conf._base import *

TEST_DIR = Path(__file__).parent.parent.parent / "test"

IMAGES_FROM_DIR = TEST_DIR / "test_images"
IMAGES_DIR = TEST_DIR / "test_images_to"
UNCLS_IMAGES_DIR = BASE_DIR / "static" / "__debug__"

# Config
DEBUG = True
DELETE_ORIGINAL = False

# Database
DATABASES = {
        "default": {
            "engine": f"sqlite:///{TEST_DIR}/test_db.sqlite",
            "config": {"autocommit": True}
        },
}

