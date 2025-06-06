import pandas as pd
from trade_bot.utils.trade_logger import logger
from trade_bot.utils.s3_config_loader import S3ConfigLoader

class MyStrategy:
    # the strategy applied
    __symbol = None
    __myconst = None

    def __init__(self, symbol: str, config : S3ConfigLoader):
        self.__symbol = symbol
        self.__myconst = config

    def validate_rules(self, df1: pd) -> bool:
        #########################################################################################################################
        #    Rule 1 : at least one crossing_kc(l,u) one touching bb(l,u) and one crossing hma both in that order
        #########################################################################################################################
        #    Rule 2 : Cannot have crossing_kc(l,u) or touching_bb(l,u) after the last_hma
        #           : Cannot have crossing_bbm at the last_hma or after it 
        #########################################################################################################################
        #    Rule 3 : not more than 4 candles between the last touchning_bb(u,l) and the crossing_hma
        #########################################################################################################################
        #    Rule 4 : short : the high price at crossing_hma cannot be higher (>) to the high price of the last bbu
        #           : long  : the low price at crossing_hma cannot be lower (<) to te the low price of the last bbl
        #########################################################################################################################
        #    Rule 5 : short : the highest price between last_bbu and last_hma cannot be higher than 5% of hma crossing price
        #           : long  : the lowest price between last_bbl and last_hma cannot be lower than 5% of hma crossing price
        #########################################################################################################################
        if self._rule1(df1):
            if self._rule2(df1):
                if self._rule3(df1):
                    if self._rule4(df1):
                        if self._rule5(df1):
                            logger.debug(f'{self.__symbol} : all rules : passed')
                            return True
        logger.debug(f'{self.__symbol} : one rule failed')
        return False

    #########################################################################################################################
    #    Rule 1 : at least one crossing_kc(l,u) one touching bb(l,u) and one crossing hma both in that order
    #########################################################################################################################        
    def _rule1(self, df1: pd) -> bool:
        # we have at leat one crossing_kcl, one touching bbl and one crossing hma 
        # in the right order
        if df1["crossing_kcl"].any():
            df2 = df1[df1.index >= df1["crossing_kcl"].idxmax()]
            if df2["touching_bbl"].any():
                df3 = df2[df2.index > df2["touching_bbl"].idxmax()]
                if df3["crossing_hma"].any():
                    logger.debug(f'{self.__symbol} : rule 1 : passed')
                    return True
                else:
                    logger.debug(f'{self.__symbol} : rule 1 : failed')
                    return False
            else:
                logger.debug(f'{self.__symbol} : rule 1 : failed')
                return False

        # or we have at leat one crossing_kcu, one touching bbu and one crossing hma 
        # in the right order
        elif df1["crossing_kcu"].any():
            df2 = df1[df1.index >= df1["crossing_kcu"].idxmax()]
            if df2["touching_bbu"].any():
                df3 = df2[df2.index >= df2["touching_bbu"].idxmax()]
                if df3["crossing_hma"].any():
                    logger.debug(f'{self.__symbol} : rule 1 : passed')
                    return True
                else:
                    logger.debug(f'{self.__symbol} : rule 1 : failed')
                    return False
            else:
                logger.debug(f'{self.__symbol} : rule 1 : failed')
                return False
        else:
            logger.debug(f'{self.__symbol} : rule 1 : failed')
            return False
        
    #########################################################################################################################
    #    Rule 2 : Cannot have crossing_kc(l,u) or touching_bb(l,u) after the last_hma
    #           : Cannot have crossing_bbm at the last_hma or after it 
    #########################################################################################################################
    def _rule2(self, df0: pd) -> bool:  
        # get all the row from the last_hma (included) till the end
        last_index = df0[df0['crossing_hma'] == True].index[-1]
        df_at_hma_and_after = df0[df0.index >= last_index]
        if df_at_hma_and_after["crossing_bbm"].any():
            logger.debug(f'{self.__symbol} : rule 2 : failed')
            return False
        # remove the last_hma row and keep all of them after
        df_after_hma = df_at_hma_and_after.iloc[1:] 
        if df_after_hma.empty:
            logger.debug(f'{self.__symbol} : rule 2 : passed')
            return True
        else:
            if df_after_hma["crossing_kcu"].any() or df_after_hma["crossing_kcl"].any():
                logger.debug(f'{self.__symbol} : rule 2 : failed')
                return False
            elif df_after_hma["touching_bbu"].any() or df_after_hma["touching_bbl"].any():
                logger.debug(f'{self.__symbol} : rule 2 : failed')
                return False
            
        logger.debug(f'{self.__symbol} : rule 2 : passed')
        return True
    
    #########################################################################################################################
    #    Rule 3 : not more than 4 candles between the last touchning_bb(u,l) and the crossing_hma
    #########################################################################################################################
    def _rule3(self, df1: pd) -> bool:
        hma_last_index = df1[df1['crossing_hma'] == True].index[-1]
        if df1["touching_bbl"].any():
            bb_last_index = df1[df1['touching_bbl'] == True].index[-1]
        elif df1["touching_bbu"].any():
            bb_last_index = df1[df1['touching_bbu'] == True].index[-1]
        else :
            logger.debug(f'{self.__symbol} : rule 3 : failed')
            return False

        delta = hma_last_index - bb_last_index
        # divide the delta by the scale of the index frequency (Daily, 1h, 15 min, 5 min, etc...)
        # to have the number of candles to compare with the nbr_of_candles_allowed_between_hma_&_bb(l,u)
        if delta.value / df1.index.freq.nanos <= self.__myconst.get("MAX_CANDLES_BETWEEN_HMA_AND_BB"):
            logger.debug(f'we have {delta.value/df1.index.freq.nanos} candles between hma_&_bb(l,u)')
            logger.debug(f'{self.__symbol} : rule 3 : passed')
            return True
        else :
            logger.debug(f'{self.__symbol} : rule 3 : failed')
            return False

    #########################################################################################################################
    #    Rule 4 : short : the high price at crossing_hma cannot be higher (>) to the high price of the last bbu
    #           : long  : the low price at crossing_hma cannot be lower (<) to te the low price of the last bbl
    #########################################################################################################################
    def _rule4(self, df1: pd) -> bool:
        hma_last_index = df1[df1['crossing_hma'] == True].index[-1]
        if df1["side"].eq(self.__myconst.get("OPEN_SHORT")).any():
            # we are in a trading long opportunity
            hma_high_price = df1.loc[hma_last_index, 'high']
            logger.debug(f'hma_high price is {hma_high_price} for {self.__symbol}')
            bbu_last_index = df1[df1['touching_bbu'] == True].index[-1]
            bbu_high_price = df1.loc[bbu_last_index, 'high']
            logger.debug(f'the high price at the bbu is {bbu_high_price} for {self.__symbol}')
            if hma_high_price < bbu_high_price:
                logger.debug(f'{self.__symbol} : rule 4 : passed')
                return True
            else:
                logger.debug(f'{self.__symbol} : rule 4 : failed')
                return False
        elif df1["side"].eq(self.__myconst.get("OPEN_LONG")).any():
            # we are in a trading short opportunity
            hma_low_price = df1.loc[hma_last_index, 'low']
            logger.debug(f'hma low price is {hma_low_price} for {self.__symbol}')
            bbl_last_index = df1[df1['touching_bbl'] == True].index[-1]
            bbl_low_price = df1.loc[bbl_last_index, 'low']
            logger.debug(f'the low price at the bbl is {bbl_low_price} for {self.__symbol}')
            if hma_low_price > bbl_low_price:
                logger.debug(f'{self.__symbol} : rule 4 : passed')
                return True
            else:
                logger.debug(f'{self.__symbol} : rule 4 :failed')
                return False
            
    #########################################################################################################################
    #    Rule 5 : short : the highest price between last_bbu and last_hma cannot be higher than 5% of hma crossing price
    #           : long  : the lowest price between last_bbl and last_hma cannot be lower than 5% of hma crossing price
    #########################################################################################################################
    def _rule5(self, df1: pd) -> bool:
        hma_last_index = df1[df1['crossing_hma'] == True].index[-1]
        hma_crossing_price = df1.loc[hma_last_index, 'hma']
        logger.debug(f'the crossing hma price is {hma_crossing_price} for {self.__symbol}') 
        boosted_hma_crossing_price = hma_crossing_price * self.__myconst.get("ACCEPTABLE_MARGE")
        logger.debug(f'105 % of crossing hma price is {boosted_hma_crossing_price} for {self.__symbol}') 

        if df1["side"].eq(self.__myconst.get("OPEN_LONG")).any():        
            # we are in a trading short opportunity
            bbl_last_index = df1[df1['touching_bbl'] == True].index[-1]
            df_interval = df1.loc[bbl_last_index:hma_last_index, 'low']
            logger.debug(f'interval is between {bbl_last_index} and {hma_last_index} for {self.__symbol}')
            lowest_price = df_interval.min()
            if lowest_price > boosted_hma_crossing_price :
                logger.debug(f'{self.__symbol} : rule 5 : failed')
                return False
            else:
                logger.debug(f'{self.__symbol} : rule 5 : passed')
                return True
        elif df1["side"].eq(self.__myconst.get("OPEN_SHORT")).any():
            bbu_last_index = df1[df1['touching_bbu'] == True].index[-1]
            df_interval = df1.loc[bbu_last_index:hma_last_index, 'high']
            logger.debug(f'interval is between {bbu_last_index} and {hma_last_index} for {self.__symbol}')
            highest_price = df_interval.max() 
            logger.debug(f'the highest price in the interval is {highest_price} for {self.__symbol}')       
            if highest_price < boosted_hma_crossing_price:
                logger.debug(f'{self.__symbol} : rule 5 : failed')
                return False
            else:
                logger.debug(f'{self.__symbol} : rule 5 : passed')
                return True
        else:
            logger.debug(f'something wrong in rule 5 for {self.__symbol}')  
            return False

