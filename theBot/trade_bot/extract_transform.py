import pandas as pd
import pandas_ta as ta
import trade_bot.utils.enums as const
from trade_bot.utils.trade_logger import logger
from trade_bot.display.my_graph import MyGraph
from trade_bot.utils.frequency_utils import freq_to_resample
from trade_bot.my_bitget import MyBitget
from trade_bot.my_contract import MyContract
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

    def display_chart(self, client_oid, display=True):
        self.__myGraph.get_chart(client_oid, display)

    def find_candidat(self) -> bool:
        for index, freq in enumerate(const.MY_FREQUENCY_LIST):
            logger.debug(f'{self.__symbol} : validation at frequency {freq}')
            self.set_data(self.__mybit.get_candles(self.__symbol, freq))
            if self.__prepare_data_for(freq):
                if self.__my_strategy.validate_rules(self.__df_data.iloc[const.STRATEGY_WINDOW:].copy()):
                    # the next good candidat replace the last one found
                    logger.debug(f'{self.__symbol} : good candidat at this {freq}')
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
                     
    def __prepare_data_for(self, freq: str) -> bool:
        df1 = self.get_data().copy()
        if len(df1.columns) < 7 or len(df1) < const.MIN_CANDLES_FOR_INDICATORS:
            logger.debug(f'{self.__symbol} : empty dataframe or not enough candles to validate the strategy')
            return False
        else :
            resample = freq_to_resample(freq)
            df1 = df1.drop(['volume Currency'], axis= 1)
            df1['Date'] = pd.to_datetime(pd.to_numeric(df1['Date']), unit="ms")
            df1.set_index("Date", inplace=True)
            df1 = df1.resample(resample).ffill()
            logger.debug(f'{self.__symbol} : ohclv processed at {df1.index.freq} index frequency')
            for col in df1.columns[:]:
                df1[col] = pd.to_numeric(df1[col])
            df1['symbol'] = self.__symbol
            df1['freq'] = freq
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

        df_row['highest'] = 0.0
        df_row['lowest'] = 0.0
        
        my_contract = self.__mybit.get_contract(self.__symbol)
        my_contract = MyContract(self.__symbol, self.__mybit.get_contract(self.__symbol))
        if my_contract.is_not_valid_or_not_opened():
            return False

        # set the stop lost for OPEN_LONG
        if df_row["side"] == const.OPEN_LONG :
            df_row['lowest'] = df1.iloc[-(int(const.MAX_MIN_VALUE_WINDOW)):, df1.columns.get_loc('low')].min()
            presetStopLossPrice = my_contract.adjust_price(float(df_row['lowest']) - (float(df_row['lowest']) * float(const.STOP_LOST)))
        # set the stop lost for OPEN_SHORT
        elif df_row["side"] == const.OPEN_SHORT :
            df_row['highest'] = df1.iloc[-(int(const.MAX_MIN_VALUE_WINDOW)):, df1.columns.get_loc('high')].max()
            presetStopLossPrice = my_contract.adjust_price(float(df_row['highest']) + (float(df_row['highest']) * float(const.STOP_LOST)))

        df_row['presetStopLossPrice'] = presetStopLossPrice

        # set the take profit at the bbm value as a first take profit step 
        df_row['presetStopSurplusPrice'] = my_contract.adjust_price(df_row['bbm'])

        self.__set_row(df_row)
               
        return self.__set_price_and_validate_ratio(my_contract)
        
    def __set_price_and_validate_ratio(self, my_contract : MyContract) -> bool:

        df0 = self.get_row()
               
        # get the 2% usdt amount available for the trade
        usdt_avail = self.__mybit.get_my_account().get_usdt_per_trade(my_contract.get_minTradeUSDT())
        if usdt_avail is None:
            logger.debug(" no more usdt_avail for trading")
            return False
        
        # get the bids and asks list 
        bids_asks = self.__mybit.get_bids_and_asks(self.__symbol)
        
        if df0['side'] == const.OPEN_SHORT:
            df1 = pd.DataFrame(bids_asks.get('data')['asks'])
        elif df0['side'] == const.OPEN_LONG:
            df1 = pd.DataFrame(bids_asks.get('data')['bids'])
        else :
            logger.error(f"{self.__symbol} : not a valid side : {df0['side']}")
            return False
        
        #######################################################################################
        # we want to sell at the highest price possible or buy at the lowest price possible
        #  - we must place your limit sell order above or equal to the best ask price
        #  - we must place your limit buy order below or equal to the best bid price.
        # the rule is to choice the PRICE_RANK_IN_BIDS_ASKS position
        ########################################################################################
        df0['price']  = my_contract.adjust_price(df1.iloc[const.PRICE_RANK_IN_BIDS_ASKS,0])
        logger.debug(f"{self.__symbol} : price for trade is : {df0['price']}")
        
        df0['size'] = my_contract.adjust_quantity(usdt_avail / df0['price'])    
        
        if my_contract.is_not_under_min_trade_amount(df0['size'], df0['price']):
            logger.debug(f"{self.__symbol} : min 5 usdt for trade not reached {float(df0['size']) * float(df0['price'])}")
            return False

        # the estimate profit is the difference between the bbm and the close price
        df0['estim_profit'] = abs(df0['bbm'] - df0['price'])

        if df0['side'] == const.OPEN_LONG:
            # the ratio is calculated with the price from the asks list
            df0['ratio'] = df0['estim_profit'] / (df0['price'] - df0['presetStopLossPrice'])
        else:
            # the ratio is calculated with the price from the bids list
            df0['ratio'] = df0['estim_profit']  / (df0['presetStopLossPrice'] - df0['price'])

        if df0['ratio'] > const.ACCEPTABLE_RATIO:
            logger.debug(f"{self.__symbol} :ratio {df0['ratio']} ok for trade")
            logger.debug('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
            df0['price_end_step'] = my_contract.get_price_end_step()
            df0['minTradeUSDT'] = my_contract.get_minTradeUSDT()
            df0['price_place'] = my_contract.get_price_place()
            df0['volume_place'] = my_contract.get_volume_place()
            self.__set_row(df0)
            return True
        else:
            logger.debug(f"{self.__symbol} :ratio {df0['ratio']} failed for trade")
            logger.debug('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
            self.__set_row(pd.DataFrame())
            return False