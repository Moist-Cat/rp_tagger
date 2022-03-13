from datetime import datetime
from sqlalchemy import desc, create_engine
from sqlalchemy.orm import sessionmaker
import json
from PIL import Image
import logging
from typing import Union, List, Set, Tuple, Dict
import os
from glob import glob
from pathlib import Path

from rp_tagger.settings import BASE_DIR, IMAGES_FROM_PATH, IMAGES_TO_PATH, ACCEPT
from rp_tagger.db import Tag, Image, tag_relationship
from rp_tagger.log import logged

log = logging.getLogger("global")

def load_images(path: Union[str, Path]=IMAGES_FROM_PATH) -> List[Tuple[str, Set[str]]]:
    """Loads images from the selected folder recursively and tries to guess
    the tags from the name"""
    images = []
    for ext in ACCEPT:
        new_images = glob(str(path) + f"/**/{ext}")

        # we try to guess the tags from the folders
        for image in new_images:
            tags = list(set((Path(image).parent.parts)).difference(set(path.parts)))
            log.debug("Recognized %d tags", len(tags))
            images.append((image, tags))
        log.info(f"Fetched %d %s files", len(new_images), ext)
    log.info(f"Fetched a total of %d files", len(images))
    return images

def dump_unclassified(images: List[str], file: BASE_DIR / "unclassified.json"):
    with open(file, "w") as file:
        file.write(json.dumps(images))

def load_unclassified(file: BASE_DIR / "unclassified.json"):
    with open(file) as file:
        data = json.loads(file.read())
    return data

class DBClient:

    def __init__(self):
        engine = create_engine(engine)
        Session = sessionmaker(bind=engine, **config)
        self.session = Session()

    def __delete__(self):
        self.session.close()

    def add_tag(self, name: str):
        self.session.begin()

        new_tag = Tag(name == name)
        self.session.add(new_tag)

        self.session.commit()

    def delete_tag(self, name: str):
        self.session.begin()

        tag = self.session.query(Tag).filter(Tag.name == name).one()
        self.session.delete(tag)

        self.session.commit()

    def query_tag(self, name: str):
        tag = self.session.query(Image).filter(Tag.name == name).join(tag_relationship).join(Image).all()
        return tag

    def most_used_tags(self):
        tags = self.session.query(Tag).order_by(desc(Tag.hits)).limit(10)
        return tags

    def add_image(self, path: str):
        self.session.begin()

        new_image = Image(path=path)
        self.session.add(new_image)
        
        self.session.commit()

    def delete_image(self, path: str):
        self.session.begin()

        image = self.session.query(Image).filter(Image.path == path).one()
        self.session.delete(image)
        # remove from the filesystem
        os.remove(path)

        self.session.commit()

    def query_image(self, tags: str):
        image = self.session.query(Image).join(tag_relationship).join(Tag).filter(Tag.name in tags)
        return image

    def most_used_images(self):
        images = self.session.query(Image).order_by(desc(Image.hits)).limit(10)
        return images

    def update_image(self, path: str):
        self.session.begin()

        self.session.execute(
                update(Image).
                where(Image.path == path).
                values(hits=Image.hits + 1, last_modified=datetime.now())
        )

        self.session.commit()
