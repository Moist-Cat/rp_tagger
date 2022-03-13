from rp_tagger.settings import DATABASES
from rp_tagger.db import *

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ENGINE = DATABASES["default"]["engine"]

engine = create_engine(ENGINE)
Session = sessionmaker(bind=engine)
session = Session()
breakpoint()

