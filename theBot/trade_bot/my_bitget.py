import pandas as pd
from trade_bot.utils.trade_logger import logger, order_logger, log_order
import time
import trade_bot.utils.enums as const
from trade_bot.utils.tools import get_client_oid
from trade_bot.utils.frequency_utils import getFreq_in_ms
from pybitget.exceptions import BitgetAPIException
from pybitget import Client


class MyBitget:
    _all_symbols = None
    _client = None

    def __init__(self):
        self._client = Client(const.API_KEY,
                             const.SECRET_KEY,
                             const.API_PASSPHRASE,
                             verbose=True)
        
        self._all_symbols = self.getAllTickers()    

    def get_client(self) -> Client:
        return self._client
    
    def get_all_symbol(self) -> pd:
        return self._all_symbols['symbol']
    
    def getAllTickers(self, do_call=False, do_save=False, do_one=True) -> pd:
        try:
            if do_call:
                tickers = self._client.mix_get_all_tickers(const.PRODUCT_TYPE_USED)
                df = pd.DataFrame(tickers.get('data'))
                logger.debug('getting all tickers from bitget')
                if do_save:
                    df.to_csv(f'{const.DATA_FOLDER}/all_tickers.csv', index=True)
                return df
            else:
                if do_one:
                    return pd.DataFrame(pd.Series(['ENJUSDT'], name='symbol'))
                else:
                    df = pd.read_csv(f'{const.DATA_FOLDER}/all_tickers.csv', index_col=0)
                    logger.debug('getting tickers from the debug directory')
                    return df
        except BitgetAPIException as e:
            logger.error(f'{e.code}: {e.message} for getAllTickers')
        except FileNotFoundError as e:
            logger.error(f'{e.args} to read or write files') 
            return None

    def get_candles(self, _symbol: str, granularity: str, do_call=True, do_save=False) -> pd:
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
                logger.debug(f'{_symbol} : getting ohclv data')
                if do_save:
                    # create a file for each ticker
                    df.to_csv(f'{const.DATA_FOLDER}/ticker_data_{granularity}/{_symbol}.csv',
                              index=True)
                return df
            else:
                # read each ticker file
                df = pd.read_csv(f'{const.DATA_FOLDER}/ticker_data_{granularity}/{_symbol}.csv',index_col=0)
                #df = pd.read_csv(f'trade_bot/data/ticker_data_for_backtest/BTC_1hour_2.csv')
                return df
        except BitgetAPIException as e:
            logger.error(f'{e.code}: {e.message} for get_trading_candles')
            return pd.DataFrame() # return empty df
        except FileNotFoundError as e:
            logger.error(f'{e.args} to read or write files for {_symbol}')
            return pd.DataFrame() # return empty df

    def get_contract(self, _symbol=False) -> pd:
        try:
            if _symbol:
                contract = self._client.mix_get_contract_config(const.PRODUCT_TYPE_USED, symbol=_symbol)
            else: 
                contract = self._client.mix_get_contract_config(const.PRODUCT_TYPE_USED)

            df = pd.DataFrame(contract.get('data'))
            df = df.drop(['baseCoin','quoteCoin','feeRateUpRatio','makerFeeRate','takerFeeRate',
                      'openCostUpRatio','supportMarginCoins','symbolType','maxSymbolOrderNum',
                      'maxProductOrderNum','maxPositionNum','symbolStatus','offTime',
                      'deliveryTime','deliveryStartTime', 'deliveryPeriod','launchTime','fundInterval',
                      'minLever','maxLever','posLimit','maintainTime','openTime'],axis=1)
            return df
        except BitgetAPIException as e:
            logger.error(f'{e.code}: {e.message} to get contract')
            return None
    
    def get_usdt_per_trade(self) -> float:
        try:
            account = self._client.mix_get_accounts(const.PRODUCT_TYPE_USED)
            self._total_usdt = float(account.get('data')[0].get('available'))
            return self._total_usdt * float(const.PERCENTAGE_VALUE_PER_TRADE)
        except BitgetAPIException as e:
            logger.error(f'getting BitgetAPIException {e} to get_usdt_available')

    def get_bids_and_asks(self, symbol: str, precision='scale0', limit='max') -> pd:
        try:
            bids_asks = self._client.mix_get_merge_depth(symbol,const.PRODUCT_TYPE_USED, precision, limit)
            return bids_asks
        except BitgetAPIException as e: 
            logger.error(f'getting BitgetAPIException {e} to get_bids_asks')
    
    def place_order(self, df_row: pd):
        try:
            clientOid = get_client_oid()
            order = self._client.mix_place_order(symbol= df_row['symbol'],
                                                     productType= const.PRODUCT_TYPE_USED,
                                                     marginMode= const.MARGIN_MODE,
                                                     marginCoin= const.MARGIN_COIN_USED,
                                                     size= df_row['size'],
                                                     price=df_row['price'],
                                                     side= df_row['side'],
                                                     orderType= const.ORDER_TYPE_LIMIT,
                                                     force = const.TIME_IN_FORCE_TYPES[1],
                                                     clientOid= clientOid,  # order_1
                                                     reduceOnly= const.REDUCE_ONLY_NO,
                                                     presetStopSurplusPrice= df_row['presetStopSurplusPrice'],
                                                     presetStopLossPrice= df_row['presetStopLossPrice'])   
            orderId = order.get('data').get('orderId')
            msg = order.get('msg')
            df_row['msg'] = msg
            log_order(orderId,df_row)

        except BitgetAPIException as e:
            logger.error(f'{e.code}: {e.message} to get contract')
            return None