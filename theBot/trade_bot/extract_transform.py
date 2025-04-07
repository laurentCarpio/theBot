import pandas as pd
import pandas_ta as ta
import trade_bot.utils.enums as const
from trade_bot.utils.trade_logger import logger
from trade_bot.display.my_graph import MyGraph
from trade_bot.utils.frequency_utils import freq_to_resample
from trade_bot.utils.tools import adjust_price, adjust_quantity
from trade_bot.my_bitget import MyBitget
from trade_bot.my_strategy import MyStrategy

class ExtractTransform:
    __symbol = None
    __df_data = pd.DataFrame()
    __mybit = None
    __my_strategy = None
    __myGraph = None
    __df_candidat = pd.DataFrame()
    __candidat_freq = None
    __df_row = pd.DataFrame()

    def __init__(self, symbol: str, mybit: MyBitget):
        self.__symbol = symbol
        self.__mybit = mybit
        self.__my_strategy = MyStrategy(symbol)
        self.__myGraph = MyGraph(symbol)

    def __set_row(self, row: pd):
        self.__df_row = row

    def get_row(self) -> pd:
        return self.__df_row

    def __set_candidat(self, df1: pd, freq: str):
        self.__df_candidat = df1 
        self.__candidat_freq = freq

    def __get_candidat(self) -> pd:
        return self.__df_candidat
    
    def set_data(self, df1: pd):
        self.__df_data = df1

    def get_data(self) -> pd:
        return self.__df_data

    def display_chart(self):
        self.__myGraph.show_chart()

    def find_candidat(self) -> bool:
        for index, freq in enumerate(const.MY_FREQUENCY_LIST):
            logger.info('###########################################')
            logger.info(f'{self.__symbol} : validation at frequency {freq}')
            self.set_data(self.__mybit.get_candles(self.__symbol, freq))
            if self.__prepare_data_for(freq_to_resample(freq)):
                if self.__my_strategy.validate_rules(self.__df_data.iloc[const.STRATEGY_WINDOW:].copy()):
                    # the next good candidat replace the last one found
                    logger.info(f'{self.__symbol} : good candidat at this {freq}')
                    self.__set_candidat(self.get_data(), freq)
                    self.__myGraph.set_candidat(self.get_data(), freq)
                    # for debug only 
                    #self.display_chart()
                else:
                    logger.debug(f'{self.__symbol} : bad candidat at this {freq}')
                    #self.__myGraph.set_candidat(self.get_data(), freq)
                    # for debug only 
                    #self.display_chart()
            else:
                logger.debug(f'{self.__symbol} : not enough data at this {freq}')
        
        return False if self.__get_candidat().empty else True
                     
    def __prepare_data_for(self, resample: str) -> bool:
        df1 = self.get_data().copy()
        if len(df1.columns) < 7 or len(df1) < const.MIN_CANDLES_FOR_INDICATORS:
            logger.debug(f'{self.__symbol} : empty dataframe or not enough candles to validate the strategy')
            return False
        else :
            df1 = df1.drop(['volume Currency'], axis= 1)
            df1['Date'] = pd.to_datetime(pd.to_numeric(df1['Date']), unit="ms")
            df1.set_index("Date", inplace=True)
            df1 = df1.resample(resample).ffill()
            logger.debug(f'{self.__symbol} : ohclv processed at {df1.index.freq} index frequency')
            for col in df1.columns[:]:
                df1[col] = pd.to_numeric(df1[col])
            df1['symbol'] = self.__symbol
            return self.__calculate_indicators(df1)
            
    def __calculate_indicators(self, df1: pd) -> bool:
        # longueur = 21
        # source fermeture
        df1.ta.hma(close=df1['close'],
                       length=21, append=True)

        # ajout BBands:
        # longueur = 20
        # mode moyenne =  sma (default)
        # standard deviation = 3
        # décalage = 0
        # ATR
        # source fermeture
        df1.ta.bbands(close=df1['close'],
                          length=20, std=3, mamode='sma',
                          talib=True, append=True)
        # ajout keltner
        # longueur = 20
        # multi = 2
        # use_tr = True , only df1['close'] as source 
        # mode moyenne =  ema
        # Band style average
        # ATR length 10
        df1.ta.kc(high=df1['high'], low=df1['low'], close=df1['close'],
                              length=20, scalar=2, mamode='ema', use_tr=True, append=True)

        df1 = df1.drop(['BBB_20_3.0',
                                'BBP_20_3.0',
                                'KCBe_20_2.0'],
                               axis=1)

        df1.rename(columns={'HMA_21': 'hma',
                                'BBL_20_3.0': 'bbl',
                                'BBM_20_3.0': 'bbm',
                                'BBU_20_3.0': 'bbu',
                                'KCLe_20_2.0': 'kcl',
                                'KCUe_20_2.0': 'kcu'},
                       inplace=True)

        logger.debug(f'{self.__symbol} : all indicators has been calculated')
        return self.__add_intersection_dot(df1)

    def __add_intersection_dot(self, df1: pd) -> bool:
        df1['candles_color'] = 'red'
        mask = df1['close'] > df1['open']
        df1.loc[mask, 'candles_color'] = 'green'
        df1['crossing_kcu'] = False
        df1['crossing_kcl'] = False
        df1['touching_bbu'] = False
        df1['crossing_bbm'] = False
        df1['touching_bbl'] = False
        df1['crossing_hma'] = False

        # set crossing_kcu = True when kcu is betwwen the open and close of candles
        green_mask = (df1['close'] > df1['kcu']) & (df1['kcu'] > df1['open']) & (df1['candles_color'] == 'green')
        df1.loc[green_mask, 'crossing_kcu'] = True
        red_mask = (df1['open'] > df1['kcu']) & (df1['kcu'] > df1['close']) & (df1['candles_color'] == 'red')
        df1.loc[red_mask, 'crossing_kcu'] = True

        # set crossing_kcl = True when kcl is betwwen the open and close of candles
        green_mask = (df1['close'] > df1['kcl']) & (df1['kcl'] > df1['open']) & (df1['candles_color'] == 'green')
        df1.loc[green_mask, 'crossing_kcl'] = True
        red_mask = (df1['open'] > df1['kcl']) & (df1['kcl'] > df1['close']) & (df1['candles_color'] == 'red')
        df1.loc[red_mask, 'crossing_kcl'] = True

        # set crossing_hma = True when hma is betwwen the open and close of candles
        green_mask = (df1['close'] > df1['hma']) & (df1['hma'] > df1['open']) & (df1['candles_color'] == 'green')
        df1.loc[green_mask, 'crossing_hma'] = True
        red_mask = (df1['open'] > df1['hma']) & (df1['hma'] > df1['close']) & (df1['candles_color'] == 'red')
        df1.loc[red_mask, 'crossing_hma'] = True

        # set crossing_bbm = True when bbm is betwwen the open and close of candles
        green_mask = (df1['close'] > df1['bbm']) & (df1['bbm'] > df1['open']) & (df1['candles_color'] == 'green')
        df1.loc[green_mask, 'crossing_bbm'] = True
        red_mask = (df1['open'] > df1['bbm']) & (df1['bbm'] > df1['close']) & (df1['candles_color'] == 'red')
        df1.loc[red_mask, 'crossing_bbm'] = True

        # set touching_bbu = True when bbu is betwwen the low and high of candles
        mask = (df1['high'] >= df1['bbu']) & (df1['bbu'] >= df1['low'])
        df1.loc[mask, 'touching_bbu'] = True

        # set touching_bbl = True when bbl is betwwen the low and high of candles
        mask = (df1['high'] >= df1['bbl']) & (df1['bbl'] >= df1['low'])
        df1.loc[mask, 'touching_bbl'] = True

        df1 = df1.drop(['candles_color'], axis=1)

        # check only on the const.STRATEGY_WINDOW for the side of the trade
        # and set the side after 
        df_last_rows = df1.iloc[const.STRATEGY_WINDOW:].copy()
        if df_last_rows["crossing_kcl"].any():
            df1['side'] = const.OPEN_LONG
        elif df_last_rows["crossing_kcu"].any():
            df1['side'] = const.OPEN_SHORT
        else:
            df1['side'] = 'no_trade'

        logger.debug(f'{self.__symbol} all the crossing and touching have been added')
        self.set_data(df1)
        return True

    def prep_row(self) -> bool:
        df1 = self.__get_candidat().copy()        
        df1 = df1.drop(['crossing_kcl','crossing_kcu','touching_bbu','crossing_hma'],axis=1)
        
        # get the last row 
        df_row = df1.iloc[-1].copy()

        # add the frequency where the strategy was validated 
        df_row['freq'] = df1.index.freq.nanos

        df_row['highest'] = 0.0
        df_row['lowest'] = 0.0

        # get future contract details (minTradeUSDT, priceEndStep, volumePlace, pricePlace, limitOpenTime)
        contract = self.__mybit.get_contract(self.__symbol)
        if contract is None:
            return False

        # validate that the limit open time = '-1' 
        # -1 means normal; other values indicate that the symbol is under maintenance or 
        # to be maintained and trading is prohibited after the specified time.
        if contract['limitOpenTime'].iloc[-1] != '-1': #if not = -1 no trade possible 
            return False 

        minTradeUSDT = float(contract['minTradeUSDT'].iloc[-1])
        priceEndStep = float(contract['priceEndStep'].iloc[-1])
        volumePlace = int(contract['volumePlace'].iloc[-1])
        pricePlace = int(contract['pricePlace'].iloc[-1])

        # set the stop lost for OPEN_LONG
        if df1["side"].eq(const.OPEN_LONG).any():
            df_row['side'] = const.OPEN_LONG
            df_row['lowest'] = df1.iloc[-(int(const.MAX_MIN_VALUE_WINDOW)):, df1.columns.get_loc('low')].min()
            presetStopLossPrice = adjust_price(df_row['lowest'] - (df_row['lowest'] * const.STOP_LOST), priceEndStep, pricePlace)
            
        # set the stop lost for OPEN_SHORT
        elif df1["side"].eq(const.OPEN_SHORT).any():
            df_row['side'] = const.OPEN_SHORT
            df_row['highest'] = df1.iloc[-(int(const.MAX_MIN_VALUE_WINDOW)):, df1.columns.get_loc('high')].max()
            presetStopLossPrice = adjust_price(df_row['highest'] + (df_row['highest'] * const.STOP_LOST), priceEndStep, pricePlace)

        df_row['presetStopLossPrice'] = presetStopLossPrice

        # set the take profit at the bbm value as a first take profit step 
        df_row['presetStopSurplusPrice'] = adjust_price(df_row['bbm'], priceEndStep, pricePlace)

        self.__set_row(df_row)

        # get the 2% usdt amount available for the trade
        usdt_avail = self.__mybit.get_my_account().get_usdt_per_trade(minTradeUSDT)
        if usdt_avail is None:
            return False
        return self.__set_price_and_validate_ratio(usdt_avail, priceEndStep, pricePlace, volumePlace)
        
    def __set_price_and_validate_ratio(self, 
                                      usdt_avail: float, 
                                      priceEndStep: float, 
                                      pricePlace : int, 
                                      volumePlace: int) -> bool:

        df0 = self.get_row()
        
        # get the bids and asks list 
        bids_asks = self.__mybit.get_bids_and_asks(self.__symbol)
        
        if df0['side'] == const.OPEN_SHORT:
            df1 = pd.DataFrame(bids_asks.get('data')['asks'])
            #######################################################################################
            # we want to sell at the highest price possible
            # You must place your limit sell order above or equal to the best ask price.
            # the rule is to choice the SELL_POSITION_IN_ASKS (4th position or else) 
            ########################################################################################
            df0['price']  = adjust_price(df1.iloc[const.PRICE_RANK_IN_BIDS_ASKS,0], priceEndStep, pricePlace)
            logger.info(f"{self.__symbol} : price for trade is : {df0['price']}")

        elif df0['side'] == const.OPEN_LONG:
            df1 = pd.DataFrame(bids_asks.get('data')['bids'])
            #######################################################################################
            # we want to buy at the lowest price possible
            # You must place your limit buy order below or equal to the best bid price.
            # the rule is to choice the BUY_POSITION_IN_BIDS (4th position or else) 
            ########################################################################################
            df0['price']  = adjust_price(df1.iloc[const.PRICE_RANK_IN_BIDS_ASKS,0], priceEndStep, pricePlace)
            logger.info(f"{self.__symbol} : price for trade is : {df0['price']}")
        else :
            return False
        
        df0['size'] = adjust_quantity(usdt_avail / df0['price'], volumePlace)    

        # the estimate profit is the difference between the bbm and the close price
        df0['estim_profit'] = abs(df0['bbm'] - df0['price'])

        if df0['side'] == const.OPEN_LONG:
            # the ratio is calculated with the price from the asks list
            df0['ratio'] = df0['estim_profit'] / (df0['price'] - df0['presetStopLossPrice'])
        else:
            # the ratio is calculated with the price from the bids list
            df0['ratio'] = df0['estim_profit']  / (df0['presetStopLossPrice'] - df0['price'])

        if df0['ratio'] > const.ACCEPTABLE_RATIO:
            logger.info(f"{self.__symbol} :ratio {df0['ratio']} ok for trade")
            df0['productType'] = const.PRODUCT_TYPE_USED
            df0['marginMode'] = const.MARGIN_MODE
            df0['marginCoin'] = const.MARGIN_COIN_USED
            df0['orderType'] = const.ORDER_TYPE_LIMIT
            df0['force'] = const.TIME_IN_FORCE_TYPES[1]
            df0['reduceOnly'] = const.REDUCE_ONLY_NO
            logger.info('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
            self.__set_row(df0)
            return True
        else:
            logger.info(f"{self.__symbol} :ratio {df0['ratio']} failed for trade")
            logger.info('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
            self.__set_row(pd.DataFrame())
            return False