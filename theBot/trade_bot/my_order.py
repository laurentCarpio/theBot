from trade_bot.utils.trade_logger import logger
from theBot.trade_bot.extract_transform import ExtractTransform
import trade_bot.utils.enums as const
from pybitget.exceptions import BitgetAPIException
from pybitget import Client
import pandas as pd


class MyOrder:
    
    def __init__(self, row: pd, client: Client):
        self._my_row = row
        self._client = client

    def place_order(self):
        try:
            order = self._client.mix_place_order(_symbol, const.PRODUCT_TYPE_USED)





            return None
        except BitgetAPIException as e:
            logger.error(f'{e.code}: {e.message} to get contract')
            return None