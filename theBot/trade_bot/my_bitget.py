import pandas as pd
import logging.config
import time
import trade_bot.utils.enums as const
from trade_bot.utils.frequency_utils import getFreq_in_ms
# from my_account import MyAccount
from pybitget.exceptions import BitgetAPIException
from pybitget import Client


class MyBitget:
    _logger = None
    _all_symbols = None
    _client = None

    def __init__(self, logger: logging.Logger):
        self._client = Client(const.API_KEY,
                             const.SECRET_KEY,
                             const.API_PASSPHRASE,
                             verbose=True)
        
        self._logger = logger
        self._all_symbols = self.getAllTickers()    

    def get_all_symbol(self) -> pd:
        return self._all_symbols['symbol']
    
    def getAllTickers(self, do_call=False, do_save=False, do_one=False) -> pd:
        try:
            if do_call:
                tickers = self._client.mix_get_all_tickers(const.PRODUCT_TYPE_USED)
                df = pd.DataFrame(tickers.get('data'))
                self._logger.debug('getting all tickers from bitget')
                if do_save:
                    df.to_csv(f'{const.DATA_FOLDER}/all_tickers.csv', index=True)
                return df
            else:
                if do_one:
                    return pd.DataFrame(pd.Series(['CRVUSDT'], name='symbol'))
                else:
                    df = pd.read_csv(f'{const.DATA_FOLDER}/all_tickers.csv', index_col=0)
                    self._logger.debug('getting tickers from the debug directory')
                    return df
        except BitgetAPIException as e:
            self._logger.error(f'{e.code}: {e.message} for getAllTickers')
        except FileNotFoundError as e:
            self._logger.error(f'{e.args} to read or write files') 
            return None

    def get_candles(self, _symbol: str, granularity: str, do_call=False, do_save=False) -> pd:
        try:
            if do_call:
                # Get the current timestamp in milliseconds
                endTime = int(time.time() * 1000)
                startTime = endTime - const.MIN_CANDLES_FOR_INDICATORS * getFreq_in_ms(granularity)
                _candles = self._client.mix_get_candles(_symbol, const.PRODUCT_TYPE_USED, granularity,
                                                       startTime, endTime)
                columns = ['Date', 'open', 'high', 'low', 'close',
                           'volume', 'volume Currency']
                df = pd.DataFrame(_candles.get('data'), columns=columns)
                self._logger.debug(f'{_symbol} : getting ohclv data')
                if do_save:
                    # create a file for each ticker
                    df.to_csv(f'{const.DATA_FOLDER}/ticker_data_{granularity}/{_symbol}.csv',
                              index=True)
                return df
            else:
                # read each ticker file
                df = pd.read_csv(f'{const.DATA_FOLDER}/ticker_data_{granularity}/{_symbol}.csv',
                                 index_col=0)
                return df
        except BitgetAPIException as e:
            self._logger.error(f'{e.code}: {e.message} for get_trading_candles')
            return pd.DataFrame() # return empty df
        except FileNotFoundError as e:
            self._logger.error(f'{e.args} to read or write files for {_symbol}')
            return pd.DataFrame() # return empty df

    def get_contract(self, _symbol: str) -> pd:
        # contrat_config_demo for demo only without symbol
        #contract = myclient.mix_get_contract_config_demo('SUSDT-FUTURES')
        # contrat_config for production with symbol
        try:
            contract = self._client.mix_get_contract_config(_symbol, const.PRODUCT_TYPE_USED)
            df = pd.DataFrame(contract.get('data'))
            df = df.drop(['baseCoin','quoteCoin','feeRateUpRatio','makerFeeRate','takerFeeRate',
                      'openCostUpRatio','supportMarginCoins','symbolType','maxSymbolOrderNum',
                      'maxProductOrderNum','maxPositionNum','symbolStatus','offTime','limitOpenTime',
                      'deliveryTime','deliveryStartTime', 'deliveryPeriod','launchTime','fundInterval',
                      'minLever','maxLever','posLimit','maintainTime','openTime'],axis=1)
            return df
        except BitgetAPIException as e:
            self._logger.error(f'{e.code}: {e.message} to get contract')
            return None
        



