import pandas as pd
import logging.config
import pandas_ta as ta
from pybitget.enums import NEW_BUY, NEW_SELL, ORDER_TYPE_LIMIT, TIME_IN_FORCE_TYPES
from trade_bot.display.my_graph import MyGraph
from trade_bot.utils.frequency_utils import freq_to_resample, get_frequency_for_next_step
from trade_bot.utils.tools import get_client_oid
from trade_bot.my_bitget import MyBitget
from trade_bot.the_strategy import TheStrategy
import trade_bot.utils.enums as const

class ExtractTransform:
    _logger = None
    _symbol = None
    _df_data = pd.DataFrame()
    _mybit = None
    _myStrategy = None
    _myGraph = None
    _df_candidat = pd.DataFrame()
    _candidat_freq = None

    def __init__(self, logger: logging.Logger, symbol: str, mybit: MyBitget):
        self._logger = logger
        self._symbol = symbol
        self._mybit = mybit
        self._myStrat = TheStrategy(logger, symbol)
        self._myGraph = MyGraph(symbol)

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
            self._logger.info('###########################################')
            self._logger.info(f'{self._symbol} : validation at frequency {freq}')
            self.set_data(self._mybit.get_candles(self._symbol, freq))
            if self._prepare_data_for(freq_to_resample(freq)):
                if self._myStrat.validate_step1(self._df_data.iloc[const.STRATEGY_WINDOW:].copy()):
                    # the next good candidat replace the last one found
                    self._logger.debug(f'{self._symbol} : good candidat at this {freq}')
                    self._set_candidat(self.get_data(), freq)
                    self._myGraph.set_candidat(self.get_data(), freq)
                else:
                    self._logger.debug(f'{self._symbol} : bad candidat at this {freq}')
            else:
                self._logger.debug(f'{self._symbol} : not enough data at this {freq}')
        
        return False if self._get_candidat().empty else True
                     
    def _prepare_data_for(self, resample: str) -> bool:
        df1 = self.get_data().copy()
        if len(df1.columns) < 7 or len(df1) < const.MIN_CANDLES_FOR_INDICATORS:
            self._logger.debug(f'{self._symbol} : empty dataframe or not enough candles to validate the strategy')
            return False
        else :
            df1 = df1.drop(['volume Currency'], axis= 1)
            df1['Date'] = pd.to_datetime(pd.to_numeric(df1['Date']), unit="ms")
            df1.set_index("Date", inplace=True)
            df1 = df1.resample(resample).ffill()
            self._logger.debug(f'{self._symbol} : ohclv processed at {df1.index.freq} index frequency')
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
        # source fermeture
        # mode moyenne =  ema
        # Band style average
        # ATR length 10
        df1.ta.kc(close=df1['close'],
                      length=20, scalar=2,
                      mamode='ema', use_tr=True, append=True)

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

        self._logger.debug(f'{self._symbol} : all indicators has been calculated')
        return self._add_intersection_dot(df1)

    def _add_intersection_dot(self, df1: pd) -> bool:
        df1['candles_color'] = 'red'
        mask = df1['close'] > df1['open']
        df1.loc[mask, 'candles_color'] = 'green'
        df1['crossing_kcu'] = False
        df1['crossing_kcl'] = False
        df1['touching_bbu'] = False
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

        # set touching_bbu = True when bbu is betwwen the low and high of candles
        mask = (df1['high'] >= df1['bbu']) & (df1['bbu'] >= df1['low'])
        df1.loc[mask, 'touching_bbu'] = True

        # set touching_bbl = True when bbl is betwwen the low and high of candles
        mask = (df1['high'] >= df1['bbl']) & (df1['bbl'] >= df1['low'])
        df1.loc[mask, 'touching_bbl'] = True

        df1 = df1.drop(['candles_color'], axis=1)
        
        if df1["crossing_kcl"].any():
            df1['side'] = NEW_BUY
        else:
            df1['side'] = NEW_SELL

        self._logger.debug(f'{self._symbol} all the crossing kc(l,u) , bb(l,u) and hma have been added')
        self.set_data(df1)
        return True

    def prep_row(self) -> pd:
        df1 = self._get_candidat().copy()        
        df1 = df1.drop(['crossing_kcl','crossing_kcu','touching_bbu','crossing_hma'],axis=1)
        
        # get the last row 
        df_row = df1.iloc[-1].copy()
        df_row['highest'] = 0.0
        df_row['lowest'] = 0.0
        
        # the estimate profit is the difference between the bbm and the close price
        estimate_profit = abs(df_row['bbm'] - df_row['close'])

        if df1["side"].eq(NEW_BUY).any():
            df_row['side'] = NEW_BUY
            df_row['lowest'] = df1.iloc[-(int(const.MAX_MIN_VALUE_WINDOW)):, df1.columns.get_loc('low')].min()
            df_row['presetStopLossPrice'] = df_row['lowest'] - (df_row['lowest'] * const.STOP_LOST)
            
            # the ratio is calculated with the premise the buying price = the close price 
            df_row['ratio'] = estimate_profit / (df_row['close'] - df_row['presetStopLossPrice'])
        else:
            df_row['side'] = NEW_SELL
            df_row['highest'] = df1.iloc[-(int(const.MAX_MIN_VALUE_WINDOW)):, df1.columns.get_loc('high')].max()
            df_row['presetStopLossPrice'] = df_row['highest'] + (df_row['highest'] * const.STOP_LOST)
            df_row['ratio'] = estimate_profit / (df_row['presetStopLossPrice'] - df_row['close'])
        df_row['marginCoin'] = const.MARGIN_COIN_USED
        df_row['size'] = 0.0
        df_row['price'] = 0.0
        df_row['orderType'] = ORDER_TYPE_LIMIT
        df_row['timeInForceValue'] = TIME_IN_FORCE_TYPES[1]
        df_row['custom_id'] = get_client_oid()  # order_1
        df_row['reduceOnly'] = 'false'

        # bbm is the first take profit at 50% usually 
        df_row['presetTakeProfitPrice'] = df_row['bbm']
        
        if df_row['ratio'] > const.ACCEPTABLE_RATIO:
            self._logger.info(f"{self._symbol} :ratio {df_row['ratio']} ok for trade")
            self._logger.info('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
            return df_row
        else:
            self._logger.info(f"{self._symbol} :ratio {df_row['ratio']} failed for trade")
            self._logger.info('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
            return pd.DataFrame()




