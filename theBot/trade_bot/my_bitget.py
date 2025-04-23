import pandas as pd
import time
import json
import trade_bot.utils.enums as const
from trade_bot.my_account import MyAccount
from trade_bot.my_contract import MyContract
from trade_bot.utils.trade_logger import logger, log_trade_order
import trade_bot.utils.tools as my_tool 
from trade_bot.utils.frequency_utils import getFreq_in_ms
from pybitget.stream import BitgetWsClient, build_subscribe_req, handel_error
from pybitget.exceptions import BitgetAPIException
from pybitget import Client
import os

class MyBitget:
    __all_symbols = None
    __client_api = None
    __channel_handlers = None
    __client_ws = None
    __my_account = None


    def __init__(self):
        self.__my_account = MyAccount()
        API_KEY = os.getenv("API_KEY")
        SECRET_KEY = os.getenv("SECRET_KEY")
        API_PASSPHRASE = os.getenv("API_PASSPHRASE")
        if not all([API_KEY, SECRET_KEY, API_PASSPHRASE]):
            raise EnvironmentError("Missing one or more API environment variables.")

        self.__client_api = Client(API_KEY, SECRET_KEY, API_PASSPHRASE, verbose=True)
        self.__all_symbols = self.getAllTickers()
        self.__set_all_to_one_way_position_mode() 

        self.__client_ws = BitgetWsClient(API_KEY, SECRET_KEY, API_PASSPHRASE,
                                          const.CONTRACT_WS_PRIVATE_URL,
                                          #const.CONTRACT_WS_PUBLIC_URL, 
                                          verbose=True).error_listener(handel_error).build()
        
        self.__channel_handlers = {"account": self.on_account_message,
                                   "orders-algo": self.on_orders_algo_message,
                                   "orders": self.on_orders_message
                                   }
        channels = ([build_subscribe_req("USDT-FUTURES", "account", "coin", "default"),
                     build_subscribe_req("USDT-FUTURES", "orders", "instId", "default"),
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

    def on_orders_message(self, data):
        message_data = data.get('data')[0]
        logger.info(f"order channel received {message_data}")
        client_oid = message_data.get('clientOid')
        if my_tool.is_place_order(client_oid) :
            if message_data['status'] == const.PLACE_ORDER_PARTIALLY_FILLED or message_data['status'] == const.PLACE_ORDER_FILLED:
                trade_dict = my_tool.read_order_file(client_oid)
                my_contract = MyContract(message_data.get('instId'))
                my_contract.assign_contract_value(trade_dict['contract_price_end_step'],
                                                    trade_dict['contract_minTradeUSDT'],
                                                    trade_dict['contract_price_place'],
                                                    trade_dict['contract_volume_place'],
                                                    False)

                self.sl_place_order(message_data, trade_dict['place_order_preset_SL'], my_contract)
                self.tp_place_order(message_data, trade_dict['place_order_preset_TP'], my_contract)

    def on_orders_algo_message(self, data):
        logger.info(f"trigger channel received : {data}")
        message_data = data.get('data')[0]
        if message_data['planType'] == 'tp' and const.TRIGGER_ORDER_STATUS_EXECUTED == message_data['status']:
            self.cancel_trigger_sl_order(message_data)
            self.trail_place_order(message_data)

    def get_my_account(self):
        return self.__my_account
    
    def get_client_api(self) -> Client:
        return self.__client_api
    
    def get_all_symbol(self) -> pd:
        df = self.remove_symbol_with_opened_position(self.__all_symbols)
        shuffled_df = df.sample(frac=1).reset_index(drop=True)
        logger.debug('getting all tickers from bitget without already opened positions')
        return shuffled_df['symbol']
    
    def __set_all_to_one_way_position_mode(self):
            pos_mode = self.__client_api.mix_set_position_mode()
            logger.debug(f" {pos_mode.get('msg')} to set all pairs at one way mode")
    
    def __set_leverage_for_all_pairs(self):        
        for symbol in self.get_all_symbol():
            try:
                response_leverage = self.__client_api.mix_set_leverage(symbol)
                logger.debug(f"{symbol} - set Leverage msg : {response_leverage.get('msg')}")
                time.sleep(1)  # Add delay to avoid API rate limits 
            except BitgetAPIException as e:
                time.sleep(1)  # Add delay to avoid API rate limits 

    def getAllTickers(self, do_call=True, do_save=False, do_one=False) -> pd:
        try:
            if do_call:
                tickers = self.__client_api.mix_get_all_tickers()
                df = pd.DataFrame(tickers.get('data'))
                logger.debug('getting all tickers from bitget')
                if do_save:
                    df.to_csv(f'{const.DATA_DIR}/all_tickers.csv', index=True)
                return df
            else:
                if do_one:
                    return pd.DataFrame(pd.Series(['PUFFERUSDT'], name='symbol'))
                else:
                    df = pd.read_csv(f'{const.DATA_DIR}/all_tickers.csv', index_col=0)
                    logger.debug('getting tickers from the debug directory')
                    return df
        except BitgetAPIException as e:
            logger.error(f'{e.code}: {e.message} for getAllTickers')
        except FileNotFoundError as e:
            logger.error(f'{e.args} to read or write files') 
            return None

    def remove_symbol_with_opened_position(self, df1 : pd) -> pd:
        try:
            positions = self.__client_api.mix_get_all_positions()
            df2 = pd.DataFrame(positions.get('data'))
            
            # check first if we have open position then 
            if df2.empty:
                return df1
            else:
                # Remove rows from df1 where 'symbol' is in df2['symbol'] 
                return df1[~df1['symbol'].isin(df2['symbol'])]
                
        except BitgetAPIException as e:
            logger.error(f'{e.code}: {e.message} to get all positions')
            return None

    def get_candles(self, symbol: str, granularity: str, do_call=True, do_save=False) -> pd:
        try:
            if do_call:
                # Get the current timestamp in milliseconds
                endTime = int(time.time() * 1000)
                startTime = endTime - const.MIN_CANDLES_FOR_INDICATORS * getFreq_in_ms(granularity)
                _candles = self.__client_api.mix_get_candles(symbol, granularity, startTime, endTime)
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
            contract = self.__client_api.mix_get_contract_config(symbol)
            return pd.DataFrame(contract.get('data'))
        except BitgetAPIException as e:
            logger.error(f'{e.code}: {e.message} to get contract')
            return None
        
    def get_bids_and_asks(self, symbol: str) -> pd:
        try:
            bids_asks = self.__client_api.mix_get_merge_depth(symbol)
            logger.debug(f"get bids and asks msg: {bids_asks.get('msg')}")
            return bids_asks
        except BitgetAPIException as e: 
            logger.error(f'getting BitgetAPIException {e} to get_bids_asks')
      
    def place_order(self, df_row: pd) -> str:
        try: 
            clientOID = my_tool.get_new_client_oid(const.CLIENT_0ID_ORDER)
            order = self.__client_api.mix_root_place_order(symbol= df_row['symbol'],
                                                     size= df_row['size'],
                                                     price=df_row['price'],
                                                     side= df_row['side'],
                                                     clientOID= clientOID)   
            
            logger.info(f"place new order :{order.get('msg')} with clientOID = {clientOID}")
            new_log = const.LOG_DICT
            log_trade_order(new_log, symbol= df_row['symbol'],
                                 frequence= df_row['freq'],
                                 place_order_clientOID= clientOID,
                                 place_order_orderID= order.get('data').get('orderId'),
                                 place_order_msg= order.get('msg'),
                                 place_order_size= df_row['size'],
                                 place_order_price= df_row['price'],
                                 place_order_side= df_row['side'],
                                 place_order_preset_SL= df_row['presetStopLossPrice'],
                                 place_order_preset_TP= df_row['presetStopSurplusPrice'],
                                 contract_price_end_step= df_row['price_end_step'],
                                 contract_minTradeUSDT= df_row['minTradeUSDT'],
                                 contract_price_place= df_row['price_place'],
                                 contract_volume_place= df_row['volume_place']
                                 )
            return clientOID
        except BitgetAPIException as e:
            logger.error(f'{e.code}: {e.message} to place order')
            return None
            
    def sl_place_order(self, message_data: dict, sl_place_order_preset :str, my_contract : MyContract):
        try:
             sl_client_oid = my_tool.get_clientOID_for(clientOID=message_data.get('clientOid'), the_suffix=const.CLIENT_0ID_STOP_LOSS)
             symbol = message_data.get('instId')
             #baseVolume give the size of the last filled position, this is what we have to use to open tp and sl 
             baseVolume = my_contract.adjust_quantity(float(message_data.get('baseVolume')))
             side = message_data.get('side')
             executePrice = my_contract.adjust_price(float(my_tool.move_by_delta(sl_place_order_preset, side)))
                
             sl = self.__client_api.mix_tpsl_plan_order(symbol= symbol,
                                                        planType=const.STOP_LOSS_PLAN_TYPE,
                                                        triggerPrice=sl_place_order_preset,
                                                        executePrice=executePrice,
                                                        holdSide=side,
                                                        size=baseVolume,
                                                        clientOID= sl_client_oid) 
                
             logger.info(f"stop loss order status :{sl.get('msg')} with clientOID = {sl_client_oid}")

        except BitgetAPIException as e:
            logger.error(f'{e.code}: {e.message} to place order tp and sl')
            return None

    def tp_place_order(self, message_data: dict, tp_place_order_preset :str, my_contract : MyContract):
        try:
             tp_client_oid = my_tool.get_clientOID_for(clientOID=message_data.get('clientOid'), the_suffix=const.CLIENT_0ID_TAKE_PROFIT)
             symbol = message_data.get('instId')
             #baseVolume give the size of the last filled position, this is what we have to use to open tp and sl 
             baseVolume = my_contract.adjust_quantity(float(message_data.get('baseVolume'))/2.0)
             side = message_data.get('side')
             executePrice = my_contract.adjust_price(float(my_tool.move_by_delta(tp_place_order_preset, side)))
             
             tp = self.__client_api.mix_tpsl_plan_order(symbol=symbol,
                                                        planType=const.TAKE_PROFIT_PLAN_TYPE,
                                                        triggerPrice= tp_place_order_preset,                                                         
                                                        executePrice= executePrice,
                                                        holdSide= side,
                                                        size= baseVolume,
                                                        clientOID= tp_client_oid)                                                  

             logger.info(f"take profit order status :{tp.get('msg')} with clientOID = {tp_client_oid}")

        except BitgetAPIException as e:
            logger.error(f'{e.code}: {e.message} to place order tp and sl order')
            return None

    def trail_place_order(self, message_data: dict):
        try:
            symbol = message_data.get('instId')
            size = message_data.get('size')
            triggerPrice = my_tool.move_by_delta(message_data.get('executePrice'),
                                                 message_data.get('side'), 
                                                 const.TRAILING_DELTA_PRICE_MOVED)
            side = my_tool.define_the_trailing_side(message_data.get('side'))

            trail = self.__client_api.mix_trail_plan_order(symbol=symbol,
                                                           size=size,
                                                           triggerPrice=triggerPrice,
                                                           side=side)
            
            logger.info(f"trailing order status :{trail.get('msg')} for coin = {symbol}")

        except BitgetAPIException as e:
            logger.error(f'{e.code}: {e.message} to place order tp and sl order')
            return None

    def cancel_trigger_sl_order(self, message_data: dict):
        """
        Interface for cancelling trigger orders, can be used to cancel by 'productType', 'symbol' and/or trigger ID list.
        REMINDER : All orders that fall under that'productType' and 'symbol' will be cancelled.
        """   
        symbol = message_data.get('instId')
        try:
            cancel = self.__client_api.mix_cancel_plan_order(symbol=symbol, 
                                                             planType=const.STOP_LOSS_PLAN_TYPE)
            logger.info(f"cancel trigger order status :{cancel.get('msg')} for {symbol}")

        except BitgetAPIException as e:
            logger.error(f'{e.code}: {e.message} to place order tp and sl order')
            return None



            