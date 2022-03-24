from pathlib import Path
import os
import sys

from rp_tagger.db import create_db
from rp_tagger.conf import settings

def get_command(command: list=sys.argv[1]):
    """Macros to maange the db"""
    if command == "shell":
        import test.shell

    elif command == "migrate":
        create_db(settings.DATABASES["default"]["engine"])

    elif command == "test":
        from test import ut
        ut.run()

    elif command == "runserver":
        os.environ["TAGGER_SETTINGS_MODULE"] = "rp_tagger.conf.pro"
        from rp_tagger.server import runserver
        runserver()

    elif command == "livetest":
        from test.ft.test_server import run_test_server
        run_test_server()


if __name__ == "__main__":
    get_command()
