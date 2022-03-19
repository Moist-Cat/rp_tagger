"""
ORM layer for the DB
"""
import functools
from datetime import datetime

from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Table
from sqlalchemy import create_engine
from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    Float,
    String,
    Text,
    ForeignKey
)

from rp_tagger.conf import settings

Base = declarative_base()



tag_relationship = Table(
    "assoc_tagged_image",
    Base.metadata,
    Column("image_id", Integer, ForeignKey("image.id"), nullable=False),
    Column("tag_id", Integer, ForeignKey("tag.id"), nullable=False),
)

class Tag(Base):
    """
    Tags that describe the image content
    """
    __tablename__ = "tag"

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    hits = Column(Integer, index=True, nullable=False, default=0)

    def __str__(self):
        return self.name

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "hits": self.hits
        }

class Image(Base):
    """
    Saves the image metadata
    """

    __tablename__ = "image"

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False, unique=True)
    path = Column(String, nullable=False)
    hits = Column(Integer, nullable=False, default=0)
    last_used = Column(DateTime, default=None, index=True)

    tags = relationship("Tag", secondary=tag_relationship, backref="images")

    date_created = Column(DateTime, default=datetime.now(), index=True, nullable=False)

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "hits": self.hits,
            "last_used": self.last_used,
            "tags": [tag.as_dict() for tag in self.tags],
            "date_created": self.date_created,
        }

def create_db(name="sqlite:///./db.sqlite"):
    engine = create_engine(name)

    Base.metadata.create_all(engine)

    return engine

def drop_db(name="sqlite:///./db.sqlite"):
    engine = create_engine(name)
    Base.metadata.drop_all(engine)
