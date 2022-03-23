from datetime import datetime
import sqlalchemy.exc
from sqlalchemy import desc, create_engine, update, func, select, column
from sqlalchemy.orm import sessionmaker
import json
import logging
# the project is too unstable atm to make type hints
#from typing import Union, List, Set, Tuple, Dict
import os
from glob import glob
from pathlib import Path

from rp_tagger.conf import settings

from rp_tagger.db import Tag, Image, tag_relationship
from rp_tagger.log import logged

_ENGINE = settings.DATABASES["default"]["engine"]
ENGINE = create_engine(_ENGINE)
CONFIG = settings.DATABASES["default"]["config"]

log = logging.getLogger("global")

def load_images(path=settings.IMAGES_FROM_DIR):
    """Loads images from the selected folder recursively and tries to guess
    the tags from the name"""
    images = []
    for ext in settings.ACCEPT:
        new_images = glob(str(path) + f"/**/{ext}", recursive=True)

        # we try to guess the tags from the folders
        for image in new_images:
            tags = list(set((Path(image).parent.parts)).difference(set(Path(path).parts)))
            images.append({"path":image, "tags":tags})
        log.info(f"Fetched %d %s files", len(new_images), ext)
    log.info(f"Fetched a total of %d files", len(images))
    return images

@logged
class DBClient:

    def __init__(self, engine=ENGINE, config=CONFIG):
        config = config or {}
        self.logger.debug("Started %s. Engine: %s", self.__class__.__name__, ENGINE)

        db_file =Path(_ENGINE[10:])
        assert db_file.exists(), "DB file doesn't exist!"
        assert db_file.stat().st_size > 0, "DB file is just an empty file!"

        Session = sessionmaker(bind=engine, **config)
        self.session = Session()

    def __delete__(self):
        self.session.close()

    def dump_unclassified(
            self,
            images
        ):

        for image in images:
            path = image["path"]
            assert isinstance(path, str), "The path must be a string"

            tags = [self.add_tag(tag) for tag in image["tags"]]
            name = image["name"]

            img = Image(name=name, path=path, tags=tags)
            self.session.add(img)

    def load_images(self):
        return self.session.query(Image).limit(200).all()

    def load_less_tagged(self):
        """
        SELECT * from image ORDER BY (SELECT COUNT(image_id) from assoc_tagged_image WHERE image.id = image_id) LIMIT 200;
        """
        count_matches = select(func.count(
            tag_relationship._columns.image_id
        )).where(
              Image.id == tag_relationship._columns.image_id
          ).scalar_subquery()
        result = self.session.query(Image).order_by(count_matches).limit(200).all()#.where(count_matches < 5).all()
        return result

    def count_unclassified(self):
        return self.session.query(func.count(Image.id)).filter(Image.classified == False).one()[0]

    def count_images(self):
        return self.session.query(func.count(Image.id)).one()[0]

    def get_paginated_result(self, start, size, tags=None):
        """Gets a slice of the DB images. Images[start:end]"""
        query = self.session.query(Image)
            
        if tags:
            """SELECT image.name FROM tag JOIN assoc_tagged_image ON tag.id = tag_id JOIN image ON image_id = image.id WHERE tag.name == "a" INTERSECT SELECT image.name FROM tag JOIN assoc_tagged_image ON tag.id = tag_id JOIN image ON image_id = image.id WHERE tag.name == "g"; (...)"""
            stmt = query.select_from(Tag).join(tag_relationship, Tag.id == tag_relationship._columns.tag_id).join(Image, Image.id == tag_relationship._columns.image_id)
            query = stmt.filter(Tag.name == tags.pop())
            # this might be slow
            for tag in tags:
                query = query.intersect(stmt.filter(Tag.name == tag))
        return query.offset(start).limit(size).all()

    def add_tag(self, name):
        """Creates a new tag if it doesn't exist"""
        try:
            tag = self.session.query(Tag).filter(Tag.name==name).one()
        except sqlalchemy.exc.NoResultFound:
            tag = Tag(name=name)
            self.session.add(tag)

        return tag

    def delete_tag(self, name):
        tag = self.session.query(Tag).filter(Tag.name == name).one()
        self.session.delete(tag)

    def get_most_used_tags(self):
        return self.session.query(Tag).order_by(desc(Tag.hits)).limit(30)

    def get_most_popular_tags(self):
        """SELECT tag.name FROM tag ORDER BY (SELECT count(assoc_tagged_image.tag_id) FROM assoc_tagged_image WHERE assoc_tagged_image.tag_id = tag.id) DESC;"""
        count_matches = select(func.count(tag_relationship._columns.tag_id)).where(tag_relationship._columns.tag_id == Tag.id).scalar_subquery()
        return self.session.query(Tag).order_by(desc(count_matches)).limit(35).all()

    def query_image(self, id=None, path=None):
        query = self.session.query(Image)
        if id is not None:
            query = query.filter(Image.id == id)
        elif path is not None:
            query = query.filter(Image.path == path)
        return query.one()

    def add_image(self, name, path, tags, classified):
        tag_list = [self.add_tag(tag) for tag in tags]
        new_image = Image(name=name, path=path, classified=classified)
        new_image.tags.extend(tag_list)

        self.session.add(new_image)

    def delete_image(self, id, path):
        return

        #################### 
        image = self.session.query(Image).filter(Image.id == id).filter(Image.path == path).one()
        self.session.delete(image)
        # remove from the filesystem
        os.remove(path)

    def most_used_images(self):
        images = self.session.query(Image).order_by(desc(Image.hits)).limit(10)
        return images

    def update_image(self, id, name=None, path=None, tags=None):

        params = {}
        stmt = update(Image).where(Image.id == id)
        if name is not None:
            params["name"] = name
        if path is not None:
            params["path"] = path
            query = query.values(path=path)
        if tags is not None:
            _tags = [self.add_tag(tag) for tag in tags]
            img = self.session.query(Image).filter(Image.id == id).one()
            img.tags = _tags
            self.session.add(img)

        if params:
            self.session.execute(stmt.values(**params))

        self.logger.info("Updated image %d. Params %s. Tags %s", id, params, tags)

    def touch_image(self):

        self.session.execute(
                update(Image).
                where(Image.path == path).
                values(hits=Image.hits + 1, last_modified=datetime.now())
        )
