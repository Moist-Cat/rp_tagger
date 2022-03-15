import os
import hashlib

from flask import Flask, render_template, request

from rp_tagger.api import load_unclassified, dump_unclassified, load_images
from rp_tagger import settings

app = Flask(__name__)

CACHE = {"images":[], "saved_images":[]}

UNCLS_IMAGES_DIR = settings.UNCLS_IMAGES_DIR

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data-uncls")
def data_uncls():
    page = 0

    if "page" in request.args:
        page = int(request.args["page"])

    new_images = load_images()

    if new_images or not any(CACHE.values()):
        images = []
        for image in new_images:
            path = image["path"]
            ext = path.split(".")[-1]
            app.logger.info("Loaded image %s", path.split("/")[-1])

            with open(image["path"], "r+b") as infile:
                data = infile.read()
                # to avoid duplicates
                name = hashlib.md5(data).hexdigest() + "." + ext
                image["id"] = name
                with open(UNCLS_IMAGES_DIR / name, "w+b") as file:
                    file.write(data)
                images.append(image)            
            if settings.DELETE_ORIGINAL:
                os.remove(path)

        CACHE["images"] = dump_unclassified(images)

    app.logger.info("Loaded %d new images", len(new_images))
    # paginate the result from the cache
    images = CACHE["images"][6*page:6*page + 6]
        
    app.logger.info("Loaded %d images. Page %d", len(images), page)
    return render_template("list.html", images=images)

@app.route("/add_tags", methods=["POST"])
def add_tags():
    tags = request.POST["tags"]
 

def runserver():
    app.run(port=5050)
