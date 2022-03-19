import logging
import logging.config
from typing import Callable

from rp_tagger.conf import settings

logging.config.dictConfig(settings.LOGGERS)


def logged(cls) -> Callable:
    "Class decorator for logging purposes"

    cls.logger = logging.getLogger("user_info." + cls.__qualname__)
    cls.logger_err = logging.getLogger("audit." + cls.__qualname__)

    return cls

