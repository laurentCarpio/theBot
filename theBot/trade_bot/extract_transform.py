import pandas as pd
from trade_bot.utils.trade_logger import logger
import pandas_ta as ta
from pybitget.enums import OPEN_LONG, OPEN_SHORT
from trade_bot.display.my_graph import MyGraph
from trade_bot.utils.frequency_utils import freq_to_resample
from trade_bot.utils.tools import adjust_price, adjust_quantity
from trade_bot.my_bitget import MyBitget
from trade_bot.my_strategy import MyStrategy
import trade_bot.utils.enums as const

class ExtractTransform:
    _symbol = None
    _df_data = pd.DataFrame()
    _mybit = None
    _myStrategy = None
    _myGraph = None
    _df_candidat = pd.DataFrame()
    _candidat_freq = None
    _df_row = pd.DataFrame()

    def __init__(self, symbol: str, mybit: MyBitget):
        self._symbol = symbol
        self._mybit = mybit
        self._myStrat = MyStrategy(symbol)
        self._myGraph = MyGraph(symbol)

    def _set_row(self, row: pd):
        self._df_row = row

    def get_row(self) -> pd:
        return self._df_row
    
    def set_data(self, df1: pd):
        self._df_data = df1

    def get_data(self) -> pd:
        return self._df_data

    def _set_candidat(self, df1: pd, freq: str):
        self._df_candidat = df1 
        self._candidat_freq = freq

    def _get_candidat(self) -> pd:
        return self._df_candidat
    
    def display_chart(self):
        self._myGraph.show_chart()

    def find_candidat(self) -> bool:
        for index, freq in enumerate(const.MY_FREQUENCY_LIST):
            logger.info('###########################################')
            logger.info(f'{self._symbol} : validation at frequency {freq}')
            self.set_data(self._mybit.get_candles(self._symbol, freq))
            if self._prepare_data_for(freq_to_resample(freq)):
                if self._myStrat.validate_rules(self._df_data.iloc[const.STRATEGY_WINDOW:].copy()):
                    # the next good candidat replace the last one found
                    logger.info(f'{self._symbol} : good candidat at this {freq}')
                    self._set_candidat(self.get_data(), freq)
                    self._myGraph.set_candidat(self.get_data(), freq)
                    # for debug only 
                    # self.display_chart()
                else:
                    logger.debug(f'{self._symbol} : bad candidat at this {freq}')
                    #self._myGraph.set_candidat(self.get_data(), freq)
                    # for debug only 
                    # self.display_chart()
            else:
                logger.debug(f'{self._symbol} : not enough data at this {freq}')
        
        return False if self._get_candidat().empty else True
                     
    def _prepare_data_for(self, resample: str) -> bool:
        df1 = self.get_data().copy()
        if len(df1.columns) < 7 or len(df1) < const.MIN_CANDLES_FOR_INDICATORS:
            logger.debug(f'{self._symbol} : empty dataframe or not enough candles to validate the strategy')
            return False
        else :
            df1 = df1.drop(['volume Currency'], axis= 1)
            df1['Date'] = pd.to_datetime(pd.to_numeric(df1['Date']), unit="ms")
            df1.set_index("Date", inplace=True)
            df1 = df1.resample(resample).ffill()
            logger.debug(f'{self._symbol} : ohclv processed at {df1.index.freq} index frequency')
            for col in df1.columns[:]:
                df1[col] = pd.to_numeric(df1[col])
            df1['symbol'] = self._symbol
            return self._calculate_indicators(df1)
            
    def _calculate_indicators(self, df1: pd) -> bool:
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

        logger.debug(f'{self._symbol} : all indicators has been calculated')
        return self._add_intersection_dot(df1)

    def _add_intersection_dot(self, df1: pd) -> bool:
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
            df1['side'] = OPEN_LONG
        elif df_last_rows["crossing_kcu"].any():
            df1['side'] = OPEN_SHORT
        else:
            df1['side'] = 'no_trade'

        logger.debug(f'{self._symbol} all the crossing and touching have been added')
        self.set_data(df1)
        return True

    def prep_row(self) -> bool:
        df1 = self._get_candidat().copy()        
        #df1 = df1.drop(['crossing_kcl','crossing_kcu','touching_bbu','crossing_hma'],axis=1)
        
        # get the last row 
        df_row = df1.iloc[-1].copy()
        df_row['highest'] = 0.0
        df_row['lowest'] = 0.0
        
        # the estimate profit is the difference between the bbm and the close price
        df_row['estim_profit'] = abs(df_row['bbm'] - df_row['close'])

        if df1["side"].eq(OPEN_LONG).any():
            df_row['side'] = OPEN_LONG
            df_row['lowest'] = df1.iloc[-(int(const.MAX_MIN_VALUE_WINDOW)):, df1.columns.get_loc('low')].min()
            df_row['presetStopLossPrice'] = df_row['lowest'] - (df_row['lowest'] * const.STOP_LOST)
        else:
            df_row['side'] = OPEN_SHORT
            df_row['highest'] = df1.iloc[-(int(const.MAX_MIN_VALUE_WINDOW)):, df1.columns.get_loc('high')].max()
            df_row['presetStopLossPrice'] = df_row['highest'] + (df_row['highest'] * const.STOP_LOST)

        # bbm is the first take profit at 50% usually 
        df_row['presetTakeProfitPrice'] = df_row['bbm']

        self._set_row(df_row)
        return self._set_price_and_validate_ratio()
        
    def _set_price_and_validate_ratio(self) -> bool:
        # a changer plus tard 
        df0 = self.get_row()

        contract = self._mybit.get_contract(self._symbol)
        if contract['limitOpenTime'].iloc[-1] != '-1': #if not = -1 no trade possible 
            return False 
        
        minTradeUSDT = float(contract['minTradeUSDT'].iloc[-1])
        priceEndStep = float(contract['priceEndStep'].iloc[-1])
        volumePlace = int(contract['volumePlace'].iloc[-1])
        pricePlace = int(contract['pricePlace'].iloc[-1])

        usdt_avail = self._mybit.get_usdt_per_trade()
        # for testing and debug trade = 8$ max  
        usdt_avail = float(8.0)
        
        # if not enough money to trade 
        if usdt_avail < 0.0 or usdt_avail < minTradeUSDT:   
            return False

        bids_asks = self._mybit.get_bids_and_asks(self._symbol)
        
        if df0['side'] == OPEN_LONG:
            df1 = pd.DataFrame(bids_asks.get('data')['asks'])
            #######################################################################################
            # we want to buy at the lowest price possible
            # the rule for now is to take the price at position 10
            ########################################################################################
            # df0['price']  = df1.iloc[10,0]
            df0['price']  = adjust_price(df1.iloc[10,0], priceEndStep, pricePlace)
            logger.info(f"{self._symbol} : price for trade is : {df0['price']}")

        elif df0['side'] == OPEN_SHORT:
            df1 = pd.DataFrame(bids_asks.get('data')['bids'])
            #######################################################################################
            # we want to sell at the highest price possible
            # the rule for now is to take the price at position 3
            ########################################################################################
            #df0['price']  = df1.iloc[3,0]
            df0['price']  = adjust_price(df1.iloc[10,0], priceEndStep, pricePlace)
        else :
            return False
        
        df0['size'] = adjust_quantity(usdt_avail / df0['price'], volumePlace)    

        if df0['side'] == OPEN_LONG:
            # the ratio is calculated with the price from the asks list
            df0['ratio'] = df0['estim_profit'] / (df0['price'] - df0['presetStopLossPrice'])
        else:
            # the ratio is calculated with the price from the bids list
            df0['ratio'] = df0['estim_profit']  / (df0['presetStopLossPrice'] - df0['price'])

        if df0['ratio'] > const.ACCEPTABLE_RATIO:
            logger.info(f"{self._symbol} :ratio {df0['ratio']} ok for trade")
            logger.info('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
            self._set_row(df0)
            return True
        else:
            logger.info(f"{self._symbol} :ratio {df0['ratio']} failed for trade")
            logger.info('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
            self._set_row(pd.DataFrame())
            return False
            



