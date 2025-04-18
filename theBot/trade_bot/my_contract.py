import time
import pandas as pd
from trade_bot.utils.enums import CONTRACT_OPEN_TIME_INDEF
from decimal import Decimal, ROUND_DOWN
from trade_bot.utils.tools import has_not_empty_column, safe_int
from trade_bot.utils.trade_logger import logger

class MyContract:
    __symbol = None
    __price_place = None
    __price_end_step = None
    __minTradeUSDT = None
    __volume_place = None
    __is_not_valid_or_not_opened = True


    def __init__(self, symbol: str, df0: pd=None):
        self.__symbol = symbol
        if self.__is_contract_exist(df0):
            limitOpenTime = int(df0['limitOpenTime'].iloc[-1])
            openTime = safe_int(df0['openTime'].iloc[-1], CONTRACT_OPEN_TIME_INDEF)
            if self.__is_contract_open(limitOpenTime, openTime):
                self.__price_end_step = float(df0['priceEndStep'].iloc[-1])
                self.__minTradeUSDT = float(df0['minTradeUSDT'].iloc[-1])
                self.__price_place = int(df0['pricePlace'].iloc[-1])
                self.__volume_place = int(df0['volumePlace'].iloc[-1])
                self.__is_not_valid_or_not_opened = False
        else :
            pass

    def assign_contract_value(self, price_end_step, minTradeUSDT, price_place, volume_place, is_not_valid_or_not_opened):
        self.__price_end_step = price_end_step
        self.__minTradeUSDT = minTradeUSDT
        self.__price_place = price_place
        self.__volume_place = volume_place      
        self.__is_not_valid_or_not_opened = is_not_valid_or_not_opened

    def get_price_end_step(self):
        return self.__price_end_step

    def get_minTradeUSDT(self):
        return self.__minTradeUSDT

    def get_price_place(self):
        return self.__price_place

    def get_volume_place(self):
        return self.__volume_place
    
    def is_not_valid_or_not_opened(self):
        return self.__is_not_valid_or_not_opened
    
    def get_minTradeUSDT(self):
        return self.__minTradeUSDT

    def __is_contract_exist(self, df0: pd) -> bool:
        if df0 is not None and has_not_empty_column(df0, ['limitOpenTime','minTradeUSDT','priceEndStep','volumePlace','pricePlace','openTime']):
            return True
        else:
            logger.debug(f"{self.__symbol} : failed because contract have missing column(s)")
            return False

    def __is_contract_open(self, limitOpenTime, openTime) -> bool:
        if limitOpenTime != -1:
            logger.debug(f"{self.__symbol} : failed because limitOpenTime != -1")
            return False
        elif openTime == CONTRACT_OPEN_TIME_INDEF:
            return True
        else :        
            current_time_ms = int(time.time() * 1000)
            return openTime <= current_time_ms
        
    def adjust_price(self, price: float) -> float:
        """
        Adjusts the price to comply with Bitget's priceEndStep and pricePlace.
        
        :param price: The calculated price
        :param price_end_step: The price step length
        :param price_place: The number of decimal places for the price
        :return: Adjusted price
        """
        price = Decimal(str(price))
        price_end_step = Decimal(str(self.__price_end_step)) / (10 ** self.__price_place)
        
        # Round down to the nearest step
        adjusted_price = (price // price_end_step) * price_end_step
        
        # Format to required decimal places
        return float(adjusted_price.quantize(Decimal('1.' + '0' * self.__price_place), rounding=ROUND_DOWN))

    def is_not_under_min_trade_amount(self, size, price) -> bool:
        # size x price must be > 5 usdt to open a trade
        return (float(size) * float(price)) <= self.__minTradeUSDT
    
    def adjust_quantity(self, quantity: float) -> float:
        if self.__volume_place == 0 and quantity < 1:
            return 1

        quantity = Decimal(str(quantity))
        return float(quantity.quantize(Decimal('1.' + '0' * self.__volume_place), rounding=ROUND_DOWN))



    