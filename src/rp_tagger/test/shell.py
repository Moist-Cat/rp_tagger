from rp_tagger.conf import settings
from rp_tagger.db import *
from rp_tagger.api import *

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ENGINE = settings.DATABASES["default"]["engine"]

engine = create_engine(ENGINE)
Session = sessionmaker(bind=engine)
session = Session()
breakpoint()

