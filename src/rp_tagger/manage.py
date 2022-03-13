from rp_tagger.db import create_db
from rp_tagger.settings import DATABASES
import sys

def get_command(command: list=sys.argv[1]):
    """Macros to maange the db"""
    if command == "shell":
        import test.shell

    elif command == "makemigrations":
        create_db(DATABASES["default"]["engine"])

    elif command == "test":
        from test import test_db
        test_db.run()

    elif command == "runserver":
        from rp_tagger.server import runserver
        runserver()


if __name__ == "__main__":
    get_command()
