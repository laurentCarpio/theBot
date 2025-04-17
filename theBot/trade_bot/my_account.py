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
        
    def update(self, data):
        account_dir = data.get('data')[0]
        self.__marginCoin = account_dir.get('marginCoin')
        try:
            self.__frozen = float(account_dir.get('frozen') or 0)
            self.__available = float(account_dir.get('available') or 0)
            self.__maxOpenPosAvailable = float(account_dir.get('maxOpenPosAvailable') or 0)
            self.__maxTransferOut = float(account_dir.get('maxTransferOut') or 0)
            self.__equity = float(account_dir.get('equity') or 0)
            self.__usdtEquity = float(account_dir.get('usdtEquity') or 0)
            self.__crossedRiskRate = float(account_dir.get('crossedRiskRate') or 0)
            self.__unrealizedPL = float(account_dir.get('unrealizedPL') or 0)
            self.__ts = float(account_dir.get('ts') or 0)
        except (ValueError, TypeError):
            pass
        logger.info(f"account updated account balance = {self.__available}")
    
    def get_account_balance(self):
        return self.__available
    
    def get_usdt_per_trade(self, minTradeUSDT: float) -> float:
            usdt_avail = self.__available * float(PERCENTAGE_VALUE_PER_TRADE)
            # if not enough money to trade 
            if usdt_avail < minTradeUSDT:
                logger.debug(f'{usdt_avail} is under the usdt available is under the minTradeUSDT {minTradeUSDT}')
                return 0.0
            else :
                 # for testing and debug trade = 8$ max
                 logger.debug(f'the usdt available is {usdt_avail}')
                 return float(8.0)
                 # return usdt_avail


    




