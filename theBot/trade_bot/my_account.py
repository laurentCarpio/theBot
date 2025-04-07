from trade_bot.utils.trade_logger import logger
from trade_bot.utils.enums import MARGIN_COIN_USED, PERCENTAGE_VALUE_PER_TRADE

class MyAccount:
    __marginCoin = None
    __frozen = 0.0
    __available = 0.0
    __maxOpenPosAvailable = 0.0
    __maxTransferOut = 0.0
    __equity = 0.0
    __usdtEquity = 0.0
    __crossedRiskRate = 0.0
    __unrealizedPL = 0.0
    __ts = 0.0

    def __init__(self):
        self.__marginCoin = MARGIN_COIN_USED
        
    def update(self, account_dir : dir):
        self.__marginCoin = account_dir.get('marginCoin')
        try:
            self.__frozen = float(account_balance.get('frozen') or 0)
            self.__available = float(dir.get('available') or 0)
            self.__maxOpenPosAvailable = float(dir.get('maxOpenPosAvailable') or 0)
            self.__maxTransferOut = float(dir.get('maxTransferOut') or 0)
            self.__equity = float(dir.get('equity') or 0)
            self.__usdtEquity = float(dir.get('usdtEquity') or 0)
            self.__crossedRiskRate = float(dir.get('crossedRiskRate') or 0)
            self.__unrealizedPL = float(dir.get('unrealizedPL') or 0)
            self.__ts = float(dir.get('ts') or 0)
        except (ValueError, TypeError):
            pass
        logger.info(f"account updated account balance = {self.__available}")
    
    def get_account_balance(self):
        return self.__available
    
    def get_usdt_per_trade(self, minTradeUSDT: float) -> float:
            usdt_avail = self.__available * float(PERCENTAGE_VALUE_PER_TRADE)
            # if not enough money to trade 
            if usdt_avail < minTradeUSDT:
                logger.info(f'the usdt available is under the minTradeUSDT {minTradeUSDT}')
                return 0.0
            else :
                 # for testing and debug trade = 8$ max
                 logger.debug(f'the usdt available is {usdt_avail}')
                 return float(8.0)
                 # return usdt_avail


    




