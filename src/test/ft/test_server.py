import unittest
from threading import Thread
import glob
import os
try:
    import requests
except ImportError:
    requests = None

from rp_tagger.conf import settings, ENVIRONMENT_VARIABLE
from rp_tagger.server import app
from test import build_test_db

PORT = 14548
HOST = "localhost"

def run_test_server():
    var = os.environ.get(ENVIRONMENT_VARIABLE)
    os.environ[ENVIRONMENT_VARIABLE] = "rp_tagger.conf.dev"
    app.run(port=PORT)

    os.environ[ENVIRONMENT_VARIABLE] = var

def delete_test_images():
    imgs = glob.glob(str(settings.BASE_DIR / "static" / "__debug__") + "/*")
    # we don't want anything funny to happen while removing files
    assert len(imgs) in (0,8), "Too many images in the test dir."
    for i in imgs:
        os.remove(i)

class TestServer(unittest.TestCase):
    
    def setUpClass():
        assert settings.DEBUG is True, "You can't test with production settings"

    def setUp(self):
        self.url = f"http://{HOST}:{PORT}/"
        self.imgs_url = f"{self.url}data-images"
        self.tagger_url = f"{self.url}classify"
        self.add_tag_url = f"{self.url}add_tags"
        delete_test_images()
        build_test_db()
        self.client = requests.Session()

    def tearDown(self):
        self.client.close()

    def test_index(self):
        res = self.client.get(self.url)

        self.assertTrue(res.status_code, 200)
        # the images are appended via AJAX
        self.assertNotIn("static/__debug__/__83b34cf54967dc5b4b86fcc6c2be7deb.png", res.text)

        res = self.client.get(self.imgs_url)

        img = "static/__debug__/__83b34cf54967dc5b4b86fcc6c2be7deb.png"
        self.assertEqual(res.status_code, 200)
        self.assertIn(img, res.text)

        res = self.client.head(self.url + "/" + img)
        self.assertEqual(res.status_code, 200) # better error message

        res = self.client.get(self.imgs_url + "?page=1")
        self.assertIn("<a href=\"/classify?id=7\"", res.text)

    def test_tagger(self):
        res = self.client.get(self.tagger_url)

        self.assertTrue(res.status_code, 200)
        self.assertIn("id=\"id_new_tag\"", res.text)

        tag = "<button name=\"tag\" id=\"id_tag_g\">g</button>"
        self.assertIn(tag, res.text)

        #img = """<video id="8" src="static/__debug__/__e52e29058facca1dd2d021757294b540.webm" class="image-detail"></video>"""
        img = """<img id="6" src="static/__debug__/__f20e54aa04d69b2892e58e724e6887bb.gif" class="image-detail"></img>"""
        self.assertIn(img, res.text)

    def test_add_tags(self):
        data = {"id": 1, "tags[]": "test"}
        res = self.client.post(self.add_tag_url, data=data)

        self.assertEqual(res.status_code, 200, res.text)

        res = self.client.get(self.tagger_url + "?id=1")
        self.assertIn("<button name=\"tag\" id=\"id_tag_test\">test</button>", res.text)

        data["[]tags"] = "test2"

        res = self.client.post(self.add_tag_url, data=data)

        self.assertEqual(res.status_code, 200, res.text)

        res = self.client.get(self.tagger_url + "?id=1")

        self.assertIn("<button name=\"tag\" id=\"id_tag_test\">test</button>", res.text)
        with open("a.html", "w+b") as f: f.write(res.content)
        self.assertIn("<button name=\"tag\" id=\"id_tag_test2\">test2</button>", res.text)
