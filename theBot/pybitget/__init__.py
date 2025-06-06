"""An unofficial Python wrapper for the bitget exchange API v1

... moduleauthor: Cuongitl

"""

__version__ = '1.0.8'

from trade_bot.utils.trade_logger import logger
from pybitget.client import Client
from pybitget import utils
from pybitget import exceptions
from pybitget.enums import *
