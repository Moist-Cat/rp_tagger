import shutil
from datetime import datetime
import sqlalchemy.exc
from sqlalchemy import (
        desc,
        create_engine,
        update,
        func,
        select,
        column,
        text,
)
from sqlalchemy.orm import sessionmaker, aliased
from sqlalchemy.orm.query import Query
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

        db_file = Path(_ENGINE[10:])
        assert db_file.exists(), "DB file doesn't exist!"
        assert db_file.stat().st_size > 0, "DB file is just an empty file!"

        Session = sessionmaker(bind=engine, **config)
        self.session = Session()

        self.already_queried = []

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

            tag = tags.pop()
            query = stmt.filter(Tag.name.like(f"%{tag}%"))
            self.touch_tag(tag)

            # this might be slow
            for tag in tags:
                self.touch_tag(tag)
                query = query.intersect(stmt.filter(Tag.name.like(f"%{tag}%")))
        return query.order_by(desc(Image.hits)).offset(start).limit(size).all()

    def get_tag(self, id):
        return self.session.query(Tag.name).filter(Tag.id==id).scalar()

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
        return self.session.query(Tag).order_by(desc(Tag.hits)).limit(30).all()

    def get_most_popular_tags(self, limit=35):
        """SELECT tag.name FROM tag ORDER BY (SELECT count(assoc_tagged_image.tag_id) FROM assoc_tagged_image WHERE assoc_tagged_image.tag_id = tag.id) DESC;"""
        count_matches = select(func.count(tag_relationship._columns.tag_id)).where(tag_relationship._columns.tag_id == Tag.id).scalar_subquery()
        return self.session.query(Tag).order_by(desc(count_matches)).limit(limit).all()

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

    def touch_image(self, id):

        self.session.query(Image).filter(Image.id == id
                ).update({Image.hits: Image.hits + 1}, synchronize_session=False)
        self.logger.debug(f"Updated image {id} with hits {Image.hits + 1}")

    def touch_tag(self, name):
        self.session.query(Tag).filter(Tag.name.like(f"%{name}%")
                ).update({Tag.hits: Tag.hits + 1}, synchronize_session="fetch")
        self.logger.debug(f"Updated tag {name} with hits {Tag.hits + 1}")

    def get_popular_tags_ids(self, ids=None, t_ids=None, min_elements=5):
        query = self.session.query(tag_relationship).subquery()

        tag_id = query.columns.tag_id
        tag_count = func.count(tag_id)

        # temporary column to filter < 5
        _tagged = self.session.query(query, tag_count).group_by(tag_id)
        if ids:
            _tagged = _tagged.filter(query.columns.image_id.in_(ids))
        if t_ids:
            _tagged = _tagged.filter(query.columns.tag_id.not_in(t_ids))
        _tagged = _tagged.order_by(desc(tag_count)).subquery()
        tagged = self.session.query(
                _tagged.columns.tag_id
        ).filter(_tagged.columns[2] > min_elements)

        return tagged

    def _get_tagged_ids(self, tag_id, except_=None):
        except_ = except_ or []
        res = self.session.query(tag_relationship._columns.image_id)
        res = res.filter(tag_relationship._columns.tag_id == tag_id)
        if except_:
            res = res.filter(tag_relationship._columns.image_id.not_in(except_))
        return res

    def get_tagged_ids(self, tags, except_=None):
        except_ = except_ or []
        leet= tags.copy()
        stmt = self.session.query(tag_relationship._columns.image_id)
        query = stmt.filter(tag_relationship._columns.tag_id == tags.pop())
        # this might be slow
        for tag in tags:
            query = query.intersect(stmt.filter(tag_relationship._columns.tag_id == tag))
        if except_:
            query = query.filter(tag_relationship._columns.image_id.not_in(except_))
        return query


    def make_tree(self, all_ids=None, current_tags=None, already_queried=None):
        current_tags = current_tags or []
        # first time is just 1, 2... n
        all_ids = all_ids or set(map(lambda i: i[0], self.session.query(tag_relationship._columns.image_id).all()))

        res = self.get_popular_tags_ids(ids=all_ids, t_ids=current_tags)
        res_sq = res.subquery()
        i = self.session.query(
                tag_relationship._columns.image_id
                ).join(res_sq, tag_relationship.columns.tag_id == res_sq.columns.tag_id).all()
        new_ids = set(map(lambda e: e[0], i))
        pruned = all_ids.difference(new_ids)
        self.dump_images(pruned, current_tags)
        self.already_queried.extend(pruned)
        print(self.already_queried)

        tags = list(map(lambda i: i[0], res.all()))
        for tag in tags:
            res = self.get_tagged_ids(current_tags + [tag], self.already_queried)

            img_ids = set(map(lambda i: i[0], res.all()))
            if img_ids:
                self.make_tree(img_ids, current_tags + [tag], self.already_queried)

    def _make_tree(self, query=None, current_tags=None):
        raise NotImplementedError("Kept for historical reasons.")
        main_query = self.session.query(main_query).filter(main_query.columns.tag_id.in_(tagged)).subquery()
        for tag_id in tagged.all():
            tag_id = tag_id[0]
            # get images tagged with tag_id (all)
            tagged_images_ids = self.session.query(main_query.columns.image_id
                    ).filter(main_query.columns.tag_id == tag_id
                    ).group_by(main_query.columns.image_id).subquery()
            # tagged images (not exlcusive)
            tagged_images = self.session.query(main_query
                    ).filter(main_query.columns.image_id.in_(tagged_images_ids)
                    ).filter(main_query.columns.tag_id != tag_id)

            # fetch image_ids (exclusive)
            exclusive_images = self.session.query(tagged_images_ids)
            if any(tagged_images):
                self.make_tree(query=tagged_images.subquery(), current_tags=current_tags + [tag_id])

                tagged_images = tagged_images.subquery()
                not_excl_ids = select(tagged_images.columns.image_id).group_by(tagged_images.columns.image_id)

                exclusive_images = exclusive_images.filter(tagged_images_ids.columns.image_id.not_in(not_excl_ids))
            exclusive_images = exclusive_images.group_by(tagged_images_ids.columns.image_id)

            self.write_images(exclusive_images.all(), current_tags + [tag_id])

            # prune image_ids from main query (all)
            main_query = self.session.query(main_query
                    ).filter(main_query.columns.image_id.not_in(tagged_images_ids)
            ).subquery()


    def dump_images(self, images, current_tags=None):
        current_tags = current_tags or []
        # write the images on the filesystem
        for image_id in images:
            image = self.query_image(id=image_id)
            path = settings.IMAGES_DIR
            for tag in current_tags:
                tag_name = self.get_tag(tag)
                path = path / tag_name
            try:
                os.makedirs(path)
            except FileExistsError:
                pass
            shutil.copy(image.path, path / image.name)
