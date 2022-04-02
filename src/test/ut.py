import os
#from typing import Union
from pathlib import Path
import unittest

from rp_tagger.db import Image, Tag, tag_relationship
from rp_tagger.api import load_images, DBClient
from rp_tagger.conf import settings
from rp_tagger.conf import _base
from test import build_test_db

assert settings.DEBUG is True, "You can't test with production settings"

TEST_FILES = settings.IMAGES_FROM_DIR
TEST_DIR = settings.TEST_DIR
UNCLS_DIR = settings.UNCLS_IMAGES_DIR

class Test_API(unittest.TestCase):
    
    def setUp(self):
        engine = build_test_db()
        self.client = DBClient(engine=engine)

    def test_load_images(self):
        images = load_images(TEST_FILES)
        self.assertEqual(len(images), 20)

        image = images[0]
        self.assertEqual(image["tags"], ["sci",])

        image = list(filter(lambda img: len(img["tags"]) > 1, images))[0]
        # we can't compare lists because the tags are not in order
        self.assertEqual(set(image["tags"]).difference({"g", "a"}), set())

    def test_dump_unclassified(self):
        images = load_images(TEST_FILES)

        for image in images:
            image["name"] = image["path"].split("/")[-1]

        self.client.dump_unclassified(images)

        uncls = self.client.load_images()

        x = uncls[0].as_dict()
        y = images[0]
        self.assertEqual(x["path"], y["path"])
        tag_names = list(map(lambda t: t["name"], x["tags"]))
        self.assertEqual(tag_names, y["tags"])

        x_2 = uncls[1].as_dict()
        y_2 = images[1]
        self.assertEqual(x_2["path"], y_2["path"])
        tag_names = list(map(lambda t: t["name"], x_2["tags"]))
        self.assertEqual(tag_names, y_2["tags"])

def main_suite() -> unittest.TestSuite:
    s = unittest.TestSuite()
    load_from = unittest.defaultTestLoader.loadTestsFromTestCase
    s.addTests(load_from(Test_API))

    return s

def run():
    t = unittest.TextTestRunner()
    t.run(main_suite())
