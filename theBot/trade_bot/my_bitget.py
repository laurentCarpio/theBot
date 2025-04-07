import pandas as pd
import time
import json
import trade_bot.utils.enums as const
from trade_bot.my_account import MyAccount
from trade_bot.utils.trade_logger import logger, log_open_order
from trade_bot.utils.tools import get_client_oid, has_non_empty_column
from trade_bot.utils.frequency_utils import getFreq_in_ms
from pybitget.stream import BitgetWsClient, build_subscribe_req, handel_error
from pybitget.exceptions import BitgetAPIException
from pybitget import Client


class MyBitget:
    __all_symbols = None
    __client_api = None
    __channel_handlers = None
    __client_ws = None
    __my_account = None


    def __init__(self):
        self.__my_account = MyAccount()
        self.__client_api = Client(const.API_KEY,
                             const.SECRET_KEY,
                             const.API_PASSPHRASE,
                             verbose=True)
        
        self.__all_symbols = self.getAllTickers()
        self.__set_all_to_one_way_position_mode() 

        self.__client_ws = BitgetWsClient(const.API_KEY,
                                          const.SECRET_KEY,
                                          const.API_PASSPHRASE,
                                          const.CONTRACT_WS_PRIVATE_URL,
                                          #const.CONTRACT_WS_PUBLIC_URL, 
                                          verbose=True).error_listener(handel_error).build()
        
        self.__channel_handlers = {"account": self.on_account_message,
                                   "ticker": self.on_ticker_message,
                                   "orders": self.on_orders_message
                                   }
        channels = ([build_subscribe_req("USDT-FUTURES", "account", "coin", "default")])
        self.__client_ws.subscribe(channels, self._on_message)
        # should run once and for all for the bitget account
        #self.__set_leverage_for_all_pairs()
    
    def _on_message(self, message):
        try:
            data = json.loads(message)
            if "arg" in data:
                channel = data["arg"].get("channel")
                handler = self.__channel_handlers.get(channel)
                if handler:
                    handler(data)
                else:
                    logger.warning(f"No handler for channel: {channel}")
            else:
                logger.warning(f"No 'arg' in message: {message}")
        except Exception as e:
            logger.error(f"Error dispatching message: {e}")
            logger.debug(message)

    def on_account_message(self, data):
        self.__my_account.update(data)
        logger.info(f"Account message: {data}")

    def on_ticker_message(self, data):
        logger.info(f"Ticker message: {data}")

    def on_orders_message(self, data):
        logger.info(f"Orders message: {data}")
    
    def get_my_account(self):
        return self.__my_account
    
    def get_client_api(self) -> Client:
        return self.__client_api
    
    def get_all_symbol(self) -> pd:
        return self.__all_symbols['symbol']
    
    def __set_all_to_one_way_position_mode(self):
            pos_mode = self.__client_api.mix_set_position_mode(const.PRODUCT_TYPE_USED,const.ONE_WAY_MODE_POSITION)
            logger.debug(f" {pos_mode.get('msg')} to set all pairs at one way mode")
    
    def __set_leverage_for_all_pairs(self):        
        for symbol in self.get_all_symbol():
            try:
                response_leverage = self.__client_api.mix_set_leverage(symbol,
                                                              const.PRODUCT_TYPE_USED,
                                                               const.MARGIN_COIN_USED,
                                                                const.DEFAULT_LEVERAGE)
                logger.debug(f"{symbol} - set Leverage msg : {response_leverage.get('msg')}")
                time.sleep(1)  # Add delay to avoid API rate limits 
            except BitgetAPIException as e:
                time.sleep(1)  # Add delay to avoid API rate limits 

    def getAllTickers(self, do_call=False, do_save=False, do_one=True) -> pd:
        try:
            if do_call:
                tickers = self.__client_api.mix_get_all_tickers(const.PRODUCT_TYPE_USED)
                df = pd.DataFrame(tickers.get('data'))
                logger.debug('getting all tickers from bitget')
                if do_save:
                    df.to_csv(f'{const.DATA_DIR}/all_tickers.csv', index=True)
                return df
            else:
                if do_one:
                    return pd.DataFrame(pd.Series(['DOGSUSDT'], name='symbol'))
                else:
                    df = pd.read_csv(f'{const.DATA_DIR}/all_tickers.csv', index_col=0)
                    logger.debug('getting tickers from the debug directory')
                    return df
        except BitgetAPIException as e:
            logger.error(f'{e.code}: {e.message} for getAllTickers')
        except FileNotFoundError as e:
            logger.error(f'{e.args} to read or write files') 
            return None

    def get_candles(self, symbol: str, granularity: str, do_call=True, do_save=False) -> pd:
        try:
            if do_call:
                # Get the current timestamp in milliseconds
                endTime = int(time.time() * 1000)
                startTime = endTime - const.MIN_CANDLES_FOR_INDICATORS * getFreq_in_ms(granularity)
                _candles = self.__client_api.mix_get_candles(symbol, const.PRODUCT_TYPE_USED, granularity,
                                                       startTime, endTime)
                columns = ['Date', 'open', 'high', 'low', 'close',
                           'volume', 'volume Currency']
                df = pd.DataFrame(_candles.get('data'), columns=columns)
                logger.debug(f'{symbol} : getting ohclv data')
                if do_save:
                    # create a file for each ticker
                    df.to_csv(f'{const.DATA_DIR}/ticker_data_{granularity}/{symbol}.csv',
                              index=True)
                return df
            else:
                # read each ticker file
                df = pd.read_csv(f'{const.DATA_DIR}/ticker_data_{granularity}/{symbol}.csv',index_col=0)
                #df = pd.read_csv(f'trade_bot/data/ticker_data_for_backtest/BTC_1hour_2.csv')
                return df
        except BitgetAPIException as e:
            logger.error(f'{e.code}: {e.message} for get_trading_candles')
            return pd.DataFrame() # return empty df
        except FileNotFoundError as e:
            logger.error(f'{e.args} to read or write files for {symbol}')
            return pd.DataFrame() # return empty df
    
    def get_candles_for_trigger_order(self, symbol: str, granularity: str) -> pd:
        try:
            # Get the current timestamp in milliseconds
            endTime = int(time.time() * 1000)
            startTime = endTime - const.MIN_CANDLES_FOR_INDICATORS * getFreq_in_ms(granularity)
            candles = self._client__api.mix_get_candles(symbol, const.PRODUCT_TYPE_USED, granularity,
                                                    startTime, endTime)
            columns = ['Date', 'open', 'high', 'low', 'close',
                        'volume', 'volume Currency']
            df = pd.DataFrame(candles.get('data'), columns=columns)
            logger.debug(f'{symbol} : getting ohclv data for trigger order')
            return df
        except BitgetAPIException as e:
            logger.error(f'{e.code}: {e.message} for get candles for trigger order')

    def get_contract(self, symbol) -> pd:
        try:
            contract = self.__client_api.mix_get_contract_config(const.PRODUCT_TYPE_USED, symbol)
            df = pd.DataFrame(contract.get('data'))
            if has_non_empty_column(df, ['limitOpenTime','minTradeUSDT','priceEndStep','volumePlace','pricePlace']):
                logger.debug(f'get contract for {symbol} msg : {contract.get('msg')}')
                return df
            else :
                logger.debug(f'get contract for {symbol} msg : {contract.get('msg')} but has column(s) empty')
                return None
        except BitgetAPIException as e:
            logger.error(f'{e.code}: {e.message} to get contract')
            return None

    def get_bids_and_asks(self, symbol: str, precision='scale0', limit='max') -> pd:
        try:
            bids_asks = self.__client_api.mix_get_merge_depth(symbol,const.PRODUCT_TYPE_USED, precision, limit)
            logger.debug(f"get bids and asks msg: {bids_asks.get('msg')}")
            return bids_asks
        except BitgetAPIException as e: 
            logger.error(f'getting BitgetAPIException {e} to get_bids_asks')
      
    def place_order(self, df_row: pd):
        try: 
            df_row['clientOid'] = get_client_oid()
            
            order = self.__client_api.mix_place_order(symbol= df_row['symbol'],
                                                     productType= const.PRODUCT_TYPE_USED,
                                                     marginMode= const.MARGIN_MODE,
                                                     marginCoin= const.MARGIN_COIN_USED,
                                                     size= df_row['size'],
                                                     price=df_row['price'],
                                                     side= df_row['side'],
                                                     orderType= const.ORDER_TYPE_LIMIT,
                                                     force = const.TIME_IN_FORCE_TYPES[1],
                                                     clientOid= df_row['clientOid'],
                                                     reduceOnly= const.REDUCE_ONLY_NO,
                                                     presetStopSurplusPrice= df_row['presetStopSurplusPrice'],
                                                     presetStopLossPrice= df_row['presetStopLossPrice'])   
            df_row['orderId'] = order.get('data').get('orderId')
            df_row['request_time'] = order.get('requestTime')
            log_open_order(order.get('msg'),df_row)

        except BitgetAPIException as e:
            logger.error(f'{e.code}: {e.message} to get contract')
            return None
    
    def get_order_detail(self, symbol, clientOid):
        try:
            order_detail = self.__client_api.mix_get_order_detail(symbol, const.PRODUCT_TYPE_USED, clientOid)
            logger.debug(f"get order detail for clientOId : {clientOid} msg : {order_detail.get('msg')}")
            return order_detail.get('data')
        except BitgetAPIException as e:
            logger.error(f'{e.code}: {e.message} to get order detail')
            return None
    
    def cancel_order(self, symbol, clientOid):
        try:
            cancel = self.__client_api.mix_cancel_order(self, 
                                                  symbol= symbol, 
                                                  marginCoin= const.MARGIN_COIN_USED,  
                                                  clientOid=clientOid)
            msg = cancel.get('msg')
            logger.debug(f"cancel order for clientOId : {clientOid} msg :{msg}")
            return msg
        except BitgetAPIException as e:
            logger.error(f'{e.code}: {e.message} to get tp and sl orders')
            return None       

    def get_trigger_order(self, symbol: str, clientOid: str, stop_loss=False, take_profit=False) -> list:
        if stop_loss and take_profit:
            plan_types = const.SL_AND_TP_PLAN_TYPES
        elif stop_loss and not take_profit:
            plan_types = const.STOP_LOSS_PLAN_TYPES
        else:
            plan_types = const.TAKE_PROFIT_PLAN_TYPES

        try:
            trigger = self.__client_api.mix_get_pending_trigger_Order(plan_types, const.PRODUCT_TYPE_USED, 
                                                            clientOid, symbol)
            logger.debug(f"cancel order for clientOId : {clientOid} msg :{trigger.get('msg')}") 
            return trigger.get('data').get('entrustedList')
        except BitgetAPIException as e:
            logger.error(f'{e.code}: {e.message} to get stop loss orders')
            return None
    
    def modify_sl(self, clientOid, newSize, stopLossTriggerPrice, stopLossExecutePrice):
        try:
            new_sl = self.__client_api.mix_modify_trigger_order(clientOid,
                                                           const.PRODUCT_TYPE_USED,
                                                           newSize,
                                                           stopLossTriggerPrice,
                                                           stopLossExecutePrice,
                                                           const.TRIGGER_TYPES[0])
            #'stopLossTriggerPrice': '0.0932',
            #'stopLossExecutePrice': '0.0930',  // or whatever price you want to execute at
            #'stopLossTriggerType': 'fill_price'

            logger.debug(f"modify sl : {clientOid} msg :{new_sl.get('msg')}")
        except BitgetAPIException as e:
            logger.error(f'{e.code}: {e.message} to modify sl')
            return None
        