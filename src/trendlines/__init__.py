# -*- coding: utf-8 -*-
from trendlines._logging import setup_logging
logger = setup_logging(to_console=True, to_file=False)

from trendlines.app_factory import create_app
