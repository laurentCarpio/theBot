import pandas as pd
from trade_bot.utils.trade_logger import logger
import trade_bot.utils.enums as const
from pybitget.enums import NEW_BUY, NEW_SELL


class MyStrategy:
    # the strategy applied
    _symbol = None
    _github_test = None

    def __init__(self, symbol: str):
        self._symbol = symbol

    def validate_step2(self, df0: pd) -> bool:
        # for an eligible buy (sell) in the previous frequency we need to validade we do have the same
        # buy (sell signal in the above frequency
        #########################################################################################################################
        #    Rule step 2 : 
        #           : with sell signal 
        #               : no kcu and touching bbu - because it means the increase trend is present at this frequency, no reversal yet 
        #               : one crossing kcu or one touching bbu is ok if the touched one is lower than the highest of the second one 
        #
        #           : with buy signal 
        #               : no kcl and touching bbl - because it means the decrease trend is present at this frequency, no reversal yet 
        #               : one crossing kcl or one touching bbl is ok if the touched one is higher than the lowest of the second one        
        #########################################################################################################################
        if df0["crossing_hma"].any():
            logger.error(f'{self._symbol} Above frequency verification failed')
            return False
        
        if df0['side'].iloc[0] == NEW_SELL:
            if df0["crossing_kcu"].any() and df0["touching_bbu"].any():
                # double crossing - touching is a failure
                return False    
            else:
                if df0["crossing_kcu"].any():
                    if df0['kcu'].max() < df0['bbu'].max():
                        return True
                    else:
                        return False
                #df_kcu = df0.loc[df0[df0['crossing_kcu'] == True].index, 'kcu']
                #kcu_max = df_kcu.max()
                #bbu_max = df0['bbu'].max()
                if df0["touching_bbu"].any():
                    if df0['bbu'].max() < df0['kcu'].max():
                        return True
                    else:
                        return False  
        
        elif df0['side'].iloc[0] == NEW_BUY:
            if df0["crossing_kcl"].any() and df0["touching_bbl"].any():
                # double crossing - touching is a failure
                return False    
            else:
                if df0["crossing_kcl"].any():
                    if df0['kcl'].min() > df0['bbl'].min():
                        return True
                    else:
                        return False
                if df0["touching_bbl"].any():
                    if df0['bbl'].min() > df0['kcl'].min():
                        return True
                    else:
                        return False 
        else:
            return False

    def validate_step1(self, df1: pd) -> bool:
        #########################################################################################################################
        #    Rule 1 : at least one crossing_kc(l,u) one touching bb(l,u) and one crossing hma both in that order
        #########################################################################################################################
        #    Rule 2 : Cannot have crossing_kc(l,u) or touching_bb(l,u) after the last_hma
        #           : Cannot have crossing_bbm at the last_hma or after it 
        #########################################################################################################################
        #    Rule 3 : not more than 4 candles between the last testing_bb(u,l) and the crossing_hma
        #########################################################################################################################
        #    Rule 4 : short : the low price at crossing_hma cannot be lower (<) to te the low price of the last bbl
        #           : long  : the high price at crossing_hma cannot be higher (>) to the high price of the last bbu
        #########################################################################################################################
        #    Rule 5 : short : the lowest price between last_bbl and last_hma cannot be lower than 5% of hma crossing price
        #           : long  : the highest price between last_bbu and last_hma cannot be higher than 5% of hma crossing price
        #########################################################################################################################
        if self._rule1(df1):
            if self._rule2(df1):
                if self._rule3(df1):
                    if self._rule4(df1):
                        if self._rule5(df1):
                            logger.debug(f'{self._symbol} : all rules : passed')
                            return True

        logger.debug(f'{self._symbol} : one rule failed')
        return False

    def _rule1(self, df1: pd) -> bool:
        # we have at leat one crossing_kcl, one touching bbl and one crossing hma 
        # in the right order
        if df1["crossing_kcl"].any():
            df2 = df1[df1.index >= df1["crossing_kcl"].idxmax()]
            if df2["touching_bbl"].any():
                df3 = df2[df2.index > df2["touching_bbl"].idxmax()]
                if df3["crossing_hma"].any():
                    logger.info(f'{self._symbol} : rule 1 : passed')
                    return True
                else:
                    logger.info(f'{self._symbol} : rule 1 : failed')
                    return False
            else:
                logger.info(f'{self._symbol} : rule 1 : failed')
                return False

        # or we have at leat one crossing_kcu, one touching bbu and one crossing hma 
        # in the right order
        elif df1["crossing_kcu"].any():
            df2 = df1[df1.index >= df1["crossing_kcu"].idxmax()]
            if df2["touching_bbu"].any():
                df3 = df2[df2.index >= df2["touching_bbu"].idxmax()]
                if df3["crossing_hma"].any():
                    logger.info(f'{self._symbol} : rule 1 : passed')
                    return True
                else:
                    logger.info(f'{self._symbol} : rule 1 : failed')
                    return False
            else:
                logger.info(f'{self._symbol} : rule 1 : failed')
                return False
        else:
            logger.info(f'{self._symbol} : rule 1 : failed')
            return False

    def _rule2(self, df1: pd) -> bool:        
        # get all the row from the last_hma (included) till the end
        df_at_hma_and_after = df1[df1.index >= df1["crossing_hma"].idxmax()]
        if df_at_hma_and_after["crossing_bbm"].any():
            logger.info(f'{self._symbol} : rule 2 : failed')
            return False
        # remove the last_hma row and keep all of them after
        df_after_hma = df_at_hma_and_after.iloc[1:] 
        if df_after_hma.empty:
            logger.info(f'{self._symbol} : rule 2 : passed')
            return True
        else:
            if df_after_hma["crossing_kcu"].any() or df_after_hma["crossing_kcl"].any():
                logger.info(f'{self._symbol} : rule 2 : failed')
                return False
            elif df_after_hma["touching_bbu"].any() or df_after_hma["touching_bbl"].any():
                logger.info(f'{self._symbol} : rule 2 : failed')
                return False
            
        logger.info(f'{self._symbol} : rule 2 : passed')
        return True

    def _rule3(self, df1: pd) -> bool:
        hma_last_index = df1[df1['crossing_hma'] == True].index[-1]
        if df1["touching_bbl"].any():
            bb_last_index = df1[df1['touching_bbl'] == True].index[-1]
        else:
            bb_last_index = df1[df1['touching_bbu'] == True].index[-1]

        delta = hma_last_index - bb_last_index
        # divide the delta by the scale of the index frequency (Daily, 1h, 15 min, 5 min, etc...)
        # to have the number of candles to compare with the nbr_of_candles_allowed_between_hma_&_bb(l,u)
        if delta.value / df1.index.freq.nanos <= const.MAX_CANDLES_BETWEEN_HMA_AND_BB:
            logger.debug(f'we have {delta.value/df1.index.freq.nanos} candles between hma_&_bb(l,u)')
            logger.info(f'{self._symbol} : rule 3 : passed')
            return True
        else :
            logger.info(f'{self._symbol} : rule 3 : failed')
            return False

    def _rule4(self, df1: pd) -> bool:
        hma_last_index = df1[df1['crossing_hma'] == True].index[-1]
        if df1["crossing_kcl"].any():
            # we are in a trading short opportunity
            hma_low_price = df1.loc[hma_last_index, 'low']
            logger.debug(f'hma_low price is {hma_low_price} for {self._symbol}')
            bbl_last_index = df1[df1['touching_bbl'] == True].index[-1]
            bbl_low_price = df1.loc[bbl_last_index, 'low']
            logger.debug(f'the low price at the bbl is {bbl_low_price} for {self._symbol}')
            if hma_low_price > bbl_low_price:
                logger.info(f'{self._symbol} : rule 4 : passed')
                return True
            else:
                logger.info(f'{self._symbol} : rule 4 : failed')
                return False
        else:
            # we are in a trading long opportunity
            hma_high_price = df1.loc[hma_last_index, 'high']
            logger.debug(f'hma high price is {hma_high_price} for {self._symbol}')
            bbu_last_index = df1[df1['touching_bbu'] == True].index[-1]
            bbu_high_price = df1.loc[bbu_last_index, 'high']
            logger.debug(f'the high price at the bbu is {bbu_high_price} for {self._symbol}')
            if hma_high_price < bbu_high_price:
                logger.info(f'{self._symbol} : rule 4 : passed')
                return True
            else:
                logger.info(f'{self._symbol} : rule 4 :failed')
                return False

    def _rule5(self, df1: pd) -> bool:
        hma_last_index = df1[df1['crossing_hma'] == True].index[-1]
        hma_crossing_price = df1.loc[hma_last_index, 'hma']
        logger.debug(f'the crossing hma price is {hma_crossing_price} for {self._symbol}') 
        boosted_hma_crossing_price = hma_crossing_price * const.ACCEPTABLE_MARGE
        logger.debug(f'105 % of crossing hma price is {boosted_hma_crossing_price} for {self._symbol}') 

        if df1["crossing_kcl"].any():
            # we are in a trading short opportunity
            bbl_last_index = df1[df1['touching_bbl'] == True].index[-1]
            df_interval = df1.loc[bbl_last_index:hma_last_index, 'low']
            logger.debug(f'interval is between {bbl_last_index} and {hma_last_index} for {self._symbol}')
            lowest_price = df_interval.min()
            if lowest_price < boosted_hma_crossing_price :
                logger.info(f'{self._symbol} : rule 5 : failed')
                return False
            else:
                logger.info(f'{self._symbol} : rule 5 : passed')
                return True
        else:
            bbu_last_index = df1[df1['touching_bbu'] == True].index[-1]
            df_interval = df1.loc[bbu_last_index:hma_last_index, 'high']
            logger.debug(f'interval is between {bbu_last_index} and {hma_last_index} for {self._symbol}')
            highest_price = df_interval.max() 
            logger.debug(f'the highest price in the interval is {highest_price} for {self._symbol}')       
            if highest_price > boosted_hma_crossing_price:
                logger.info(f'{self._symbol} : rule 5 : failed')
                return False
            else:
                logger.info(f'{self._symbol} : rule 5 : passed')
                return True

