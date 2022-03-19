from rp_tagger.db import Base, create_engine
from rp_tagger.conf import settings

db = settings.DATABASES["default"]
ENGINE = db["engine"]

def build_test_db(
        name=ENGINE,
    ):
    """
    Create test database and schema.
    """
    engine = create_engine(name)

    # Nuke everything and build it from scratch.
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    return engine
