import os
import hashlib

from flask import Flask, render_template, request, redirect, url_for

from rp_tagger.api import load_images, DBClient
from rp_tagger.conf import settings

try:
    # auto tagging
    import hydrus_dd as hydrus
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
    from hydrus_dd import evaluate
    from hydrus_dd.__main__ import load_model_and_tags

except ImportError:
    hydrus = None

app = Flask(__name__)

TAG_SEPARATOR = "_"
HASH_DELM = "__"
PAGE_SIZE = 7

CACHE = {"images": []}

UNCLS_IMAGES_DIR = settings.UNCLS_IMAGES_DIR
IMAGES_DIR = settings.IMAGES_DIR

client = DBClient()

def gen_img_obj(images):
    for image in images:
        path = image["path"]
        ext = path.split(".")[-1]
        app.logger.info("Loaded image %s", path.split("/")[-1])

        with open(image["path"], "r+b") as infile:
            data = infile.read()
        # to avoid duplicates
        name = HASH_DELM + hashlib.md5(data).hexdigest() + "." + ext
        image["name"] = name
        old_path = image["path"]
        new_path = UNCLS_IMAGES_DIR / name
            
        if new_path.exists():
            app.logger.info("Duplicate found: %s at %s", name, image["path"])
            continue
        image["path"] = str(new_path)
        yield image

        # after the image was successfully added to the DB
        if settings.DELETE_ORIGINAL:
            os.rename(old_path, new_path)
        else:
            with open(old_path, "r+b") as infile:
                with open(new_path, "w+b") as outfile:
                    outfile.write(infile.read())

def _sync_new():

    new_images = load_images()

    app.logger.info("Loaded %d new images", len(new_images))

    if new_images or not any(CACHE.values()):
        client.dump_unclassified(gen_img_obj(new_images))

        app.logger.info(
            "There is a total of images of %d images",
            client.count_images()
        )

@app.route("/")
def index():
    most_used_tags = list(map(lambda i: i.as_dict(), client.get_most_used_tags()))

    app.logger.info("Most used tags: %s", most_used_tags)

    return render_template("index.html", most_used_tags=most_used_tags)

@app.route("/data-images")
def data_images():
    """Yields rendered html code with the images"""
    page = 0
    tags = []

    if "page" in request.args:
        page = int(request.args["page"])
    if "tags" in request.args and request.args["tags"]:
        # expect space separated list of tags
        tags = request.args["tags"].split(" ")

    _sync_new()

    # paginate the result from the cache. 6 per page
    raw_images = client.get_paginated_result(PAGE_SIZE*page, PAGE_SIZE, tags=tags)
    images = list(map(lambda i: i.as_dict(), raw_images))


    app.logger.info("Loaded %d images. Page %d", len(images), page)
    return render_template("list.html", images=images) 

@app.route("/classify")
def classify():
    """Yield new images to tag them"""

    _sync_new()
    if len(CACHE["images"]) == 0:
        images = client.load_less_tagged()
        if not any(images):
            app.logger.info("Empty database. Can't classify anything.")
            return redirect(url_for("index"))
        CACHE["images"] = images

    if not "id" in request.args:
        image = CACHE["images"][-1].as_dict()
    else:
        id = int(request.args["id"])
        image = client.query_image(id=id).as_dict()

    raw_tags = client.get_most_popular_tags()
    popular_tags = list(map(lambda t: t.as_dict(), raw_tags))

    return render_template("detail.html", image=image, popular_tags=popular_tags)

@app.route("/auto-classify")
def auto_classify():
    if hydrus is None:
        return ("hydrus-dd is not installed.", 400)
    model, tags = load_model_and_tags(settings.MODEL_DIR / "model.h5", settings.MODEL_DIR / "tags.txt", compile_=None)

    images = [1]
    while any(images):
        images = client.load_less_tagged_images()
        for image in images:
            if image.name.endswith("webp") or image.name.endswith("webm") or image.name.endswith("gif"):
                continue
            path = image.path
            response = set(evaluate.eval(image_path=path, threshold=0.5, model=model, tags=tags))
            assert any(response), f"Error, response is nil {response}"
            app.logger.info("Guessed tags: %s for image %s", response, image.name)
            client.update_image(id=image.id, tags=response)
            app.logger.info("Successfully tagged %s images", image.path)
    return ("Everything should be tagged now.", 200)


@app.route("/add_tags", methods=["POST"])
def add_tags():
    if "id" not in request.form:
        return ("The id param is missing", 400,)
    id = int(request.form["id"])
    if "tags[]" in request.form:
        tags = request.form.getlist("tags[]")
    else:
        # clearing the tags
        tags = []

    app.logger.info("tags: %s; name: %s", tags, id)

    _sync_new()
    # check if we get the image from cache or not
    if len(CACHE["images"]) > 0:
        img = CACHE["images"][-1].as_dict()
        if img["id"] == id:
            # it will eventually empty and we will get more from the DB
            CACHE["images"].pop()
    # if is not the last image or the cache is empty, 
    # it means we fetched it directly
    # there is no need to take any action

    client.update_image(id=id, tags=tags)

    return ("", 200,)

@app.route("/touch-image/<int:id>")
def touch_image(id):
    client.touch_image(id)
    return ("", 200,)

@app.route("/image/delete/<int:id>", methods=["POST"])
def image_delete(id):
    client.delete_image(id)
    return redirect(url_for("classify"))

@app.route("/tree", methods=["GET","POST"])
def tree():
    if request.method == "GET":
        return render_template("tree.html")
    # it won't allow other than GET and POST
    client.make_tree()
    # XXX i know
    client.already_queried = []

    return redirect(url_for("index"))

def runserver():
    app.run(host="0.0.0.0",port=5050)

if __name__ == "__main__":
    runserver()
