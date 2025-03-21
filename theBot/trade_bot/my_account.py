import pandas as pd
import logging.config
import trade_bot.utils.enums as const
from pybitget.exceptions import BitgetAPIException
from pybitget import Client

class MyAccount:
    # the strategy applied
    _logger = None
    _client = None

    def __init__(self, logger: logging.Logger, client: Client):
        self._logger = logger
        self._client = client


#########################################


