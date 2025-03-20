import pandas as pd
import logging.config
import utils.enums as const
from pybitget.exceptions import BitgetAPIException
from pybitget import Client
from pybitget.enums import NEW_BUY, NEW_SELL, MARGIN_COIN_SUSDT


class MyAccount:
    # the strategy applied
    _logger = None
    _client = None
    _total_usdt = float(0) 
    _usdt_per_trade = float(0)

    def __init__(self, logger: logging.Logger, client: Client):
        self._logger = logger
        self._client = client
        self._get_usdt_available_from_account()


    def _get_usdt_available_from_account(self):
        try:
            account = self._client.mix_get_accounts(const.PRODUCT_TYPE_USED)
            self._total_usdt = float(account.get('data')[0].get('available'))
            self._usdt_per_trade = self._total_usdt * float(const.PERCENTAGE_VALUE_PER_TRADE)
        except BitgetAPIException as e:
            self._logger.error(f'getting BitgetAPIException {e} to get_usdt_available')

    def get_usdt_per_trade(self):
        return self._usdt_per_trade

#########################################


