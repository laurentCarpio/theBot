import time
import pandas as pd
from decimal import Decimal, ROUND_DOWN
from trade_bot.my_bitget import MyBitget
from trade_bot.utils.tools import has_not_empty_column
from trade_bot.utils.trade_logger import logger

class MyContract:
    __symbol = None
    __df_contract = None
    __price_place = None
    __price_end_step = None
    __minTradeUSDT = None
    __volume_place = None

    def __init__(self, symbol: str, mybit: MyBitget):
        self.__symbol = symbol
        # get future contract details (minTradeUSDT, priceEndStep, volumePlace, pricePlace, limitOpenTime)
        df0 = mybit.get_contract(self.__symbol)
        if self.__is_contract_valide(df0):
            self.__df_contract = df0
            self.__price_end_step = float(df0['priceEndStep'].iloc[-1])
            self.__minTradeUSDT = float(df0['minTradeUSDT'].iloc[-1])
            self.__price_place = int(df0['pricePlace'].iloc[-1])
            self.__volume_place = int(df0['volumePlace'].iloc[-1])
        else :
            self.__df_contract = None

    def get_minTradeUSDT(self):
        return self.__minTradeUSDT

    def __is_contract_valide(self, df0: pd) -> bool:
        if df0 is not None and has_not_empty_column(df0, ['limitOpenTime','minTradeUSDT','priceEndStep','volumePlace','pricePlace','openTime']):
            # validate that the limit open time = '-1' 
            # -1 means normal; other values indicate that the symbol is under maintenance or 
            # to be maintained and trading is prohibited after the specified time.
            if df0['limitOpenTime'].iloc[-1] != '-1':
                logger.info(f"{self.__symbol} : failed because limitOpenTime is = -1")
                return False
            if self.__is_contract_not_open(df0['openTime'].iloc[-1]):
                logger.info(f"{self.__symbol} : failed because openTime is in future")
                return False
            # the contract is valid to do trading
            return True
        else:
            return False

    def __is_contract_not_open(self, open_time_ms: int) -> bool:
        """
        Returns True if the contract is not open yet (i.e., openTime is in the future).
        """
        open_time_ms = int(open_time_ms)  # Ensure it's an integer
        current_time_ms = int(time.time() * 1000)
        return open_time_ms != -1 and open_time_ms > current_time_ms
        
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



    