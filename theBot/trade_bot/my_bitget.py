import pandas as pd
import time
import json
import trade_bot.utils.enums as const
from trade_bot.my_account import MyAccount
from trade_bot.utils.trade_logger import logger, log_open_order
from trade_bot.utils.tools import get_client_oid, substract_one_unit, return_the_close_from
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
                                   "orders-algo": self.on_orders_algo_message,
                                   "orders": self.on_orders_message
                                   }
        channels = ([build_subscribe_req("USDT-FUTURES", "account", "coin", "default"),
                     #build_subscribe_req("USDT-FUTURES", "orders", "instId", "default"),
                     build_subscribe_req("USDT-FUTURES", "orders-algo", "instId", "default")])

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
        logger.debug(f"Account message: {data}")

    def on_orders_algo_message(self, data):
        logger.info(f"order trigger channel received : {data}")
        plan = data.get('data')[0]
        logger.info(f"order trigger channel data[0] received : {plan}")
        #if plan['planType'] == 'tp':
        #    logger.info(f" the tp_plan:  {plan['planType']}")
        #    if const.ORDER_STATUS_LIVE == plan['status']:
        #        # self.__update_profit_plan_size_from_trigger(plan)
        #else:
        #    logger.info("we pass over the __update_profit_plan_size_from_trigger")

    def on_orders_message(self, data):
        message_data = data.get('data')[0]
        logger.info(f" the data from the order publisher {message_data}")
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

    def getAllTickers(self, do_call=True, do_save=False, do_one=False) -> pd:
        try:
            if do_call:
                tickers = self.__client_api.mix_get_all_tickers(const.PRODUCT_TYPE_USED)
                df = pd.DataFrame(tickers.get('data'))
                shuffled_df = df.sample(frac=1).reset_index(drop=True)
                logger.debug('getting all tickers from bitget')
                if do_save:
                    df.to_csv(f'{const.DATA_DIR}/all_tickers.csv', index=True)
                return shuffled_df
            else:
                if do_one:
                    return pd.DataFrame(pd.Series(['COSUSDT'], name='symbol'))
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
                                                       startTime, endTime,
                                                       const.KLINE_TYPE, 
                                                       const.MIN_CANDLES_FOR_INDICATORS)
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
    
    def get_contract(self, symbol) -> pd:
        try:
            contract = self.__client_api.mix_get_contract_config(const.PRODUCT_TYPE_USED, symbol)
            return pd.DataFrame(contract.get('data'))
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
            df_row['clientOid'] = get_client_oid(const.CLIENT_0ID_ORDER)
            log_open_order("before the call",'ORDER', df_row)
            order = self.__client_api.mix_root_place_order(symbol= df_row['symbol'],
                                                     productType= df_row['productType'],
                                                     marginMode= df_row['marginMode'],
                                                     marginCoin= df_row['marginCoin'],
                                                     size= df_row['size'],
                                                     price=df_row['price'],
                                                     side= df_row['side'],
                                                     orderType= df_row['orderType'],
                                                     force = df_row['force'],
                                                     clientOid= df_row['clientOid'],
                                                     reduceOnly= df_row['reduceOnly'])   
            
            df_row['orderId_create'] = order.get('data').get('orderId')
            df_row['request_time'] = order.get('requestTime')
            log_open_order(order.get('msg'),'ORDER', df_row)
        except BitgetAPIException as e:
            logger.error(f'{e.code}: {e.message} to place order')
            return None
        
        # put a sleep to get a chance of the order to be executed before opening tp and sl 
        time.sleep(60)

        try:    
            if order.get('msg') == 'success':
                sl_clientOid = get_client_oid(const.CLIENT_0ID_STOP_LOSS)
                sl = self.__client_api.mix_tp_or_sl_plan_order(const.STOP_LOSS_PLAN_TYPE, 
                                                            df_row['symbol'], 
                                                            productType= df_row['productType'],
                                                            marginMode= df_row['marginMode'],
                                                            marginCoin= df_row['marginCoin'],
                                                            size= df_row['size'], 
                                                            triggerPrice = df_row['presetStopLossPrice'],
                                                            triggerType = const.TRIGGER_TYPES[1],
                                                            side = return_the_close_from(df_row['side']),
                                                            orderType= df_row['orderType'],
                                                            clientOID = sl_clientOid) 
                
                logger.info(f"stop loss order status :{sl.get('msg')} with clientOid = {sl_clientOid} and orderId = {sl.get('data').get('orderId')}")
                df_row['orderId_sl'] = sl.get('data').get('orderId')
                log_open_order(sl.get('msg'),'SL', df_row)

                tp_clientOid = get_client_oid(const.CLIENT_0ID_TAKE_PROFIT)
                tp = self.__client_api.mix_tp_or_sl_plan_order(const.TAKE_PROFIT_PLAN_TYPE, 
                                                            df_row['symbol'], 
                                                            productType= df_row['productType'],
                                                            marginMode= df_row['marginMode'],
                                                            marginCoin= df_row['marginCoin'],
                                                            size= str(float(df_row['size'])/2), 
                                                            triggerPrice = df_row['presetStopSurplusPrice'],
                                                            triggerType = const.TRIGGER_TYPES[1],
                                                            side = return_the_close_from(df_row['side']),
                                                            orderType= df_row['orderType'],
                                                            clientOID = tp_clientOid)                                                             

                logger.info(f"stop loss order status :{tp.get('msg')} with clientOid = {tp_clientOid} and orderId = {tp.get('data').get('orderId')}")
                df_row['orderId_tp'] = tp.get('data').get('orderId')
                log_open_order(tp.get('msg'),'TP', df_row)

        except BitgetAPIException as e:
            logger.error(f'{e.code}: {e.message} to place order tp and sl')
            return None

                