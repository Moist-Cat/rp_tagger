import uuid

from flask import Flask, render_template, request
from rp_tagger.api import load_unclassified, dump_unclassified, load_images

app = Flask(__name__)

CACHE = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data-uncls")
def data_uncls():
    page = 0
    if "page" in request.args:
        page = int(request.args["page"])
    new_images = dump_unclassified(load_images())
    if new_images > 0 or "images" not in CACHE:
        # meaning there are new images or is the
        # first time we run the server
        app.logger.info("Loaded %d new images", new_images)
        CACHE["images"] = load_unclassified()
    # paginate the result from the cache
    images = CACHE["images"][6*page:6*page + 6]
        
    app.logger.info("Loaded %d images. Page %d", len(images), page)
    return render_template("list.html", images=images)
 

def runserver():
    app.run(port=5050)
