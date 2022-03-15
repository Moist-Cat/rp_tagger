import os
#from typing import Union
from pathlib import Path
import unittest

from rp_tagger.db import Image, Tag, tag_relationship
from rp_tagger.api import load_images, load_unclassified, dump_unclassified
from rp_tagger import settings

db = settings.DATABASES["test"]
ENGINE = db["engine"]

TEST_FILES = settings.TEST_IMAGES_DIR
TEST_DIR = settings.TEST_DIR
UNCLS_DIR = TEST_DIR / "test_unclassified.json"

def build_test_db(
        name=ENGINE,
    ):
    """
    Create test database and schema.
    """
    engine = create_engine(name)

    # Nuke everything and build it from scratch.
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    return engine

class Test_API(unittest.TestCase):
    
    def setUp(self):
        try:
            os.remove(UNCLS_DIR)
        except FileNotFoundError:
            pass

    def test_load_images(self):
        images = load_images(TEST_FILES)
        self.assertEqual(len(images), 9)

        image = images[0]
        self.assertEqual(image["tags"], ["sci",])

    def test_dump_unclassified(self):
        images = load_images(TEST_FILES)
        dump_unclassified(images, UNCLS_DIR)

        uncls = load_unclassified(UNCLS_DIR)

        x = uncls[0]
        y = images[0]
        self.assertEqual(x, y)

        x_2 = uncls[1]
        y_2 = images[1]
        self.assertEqual(x_2, y_2)
 
def main_suite() -> unittest.TestSuite:
    s = unittest.TestSuite()
    load_from = unittest.defaultTestLoader.loadTestsFromTestCase
    s.addTests(load_from(Test_API))
    
    return s

def run():
    t = unittest.TextTestRunner()
    t.run(main_suite())
