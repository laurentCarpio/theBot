import pandas as pd
import trade_bot.utils.enums as const
from trade_bot.utils.trade_logger import logger
from trade_bot.my_bitget import MyBitget
from trade_bot.utils.tools import get_files_fifo, process_order_file, move_file

def is_order_open(my_bitget : MyBitget, df_row : pd, file_path : str) -> bool :
    df_detail_order = my_bitget.get_order_detail(df_row['symbol'], df_row['clientOid'])
    status = df_detail_order.get('data').get('status')
    if "cancelled" == status:
        move_file(file_path,const.FAILED_OPEN_TRADE_DIR)
        return False
    if "live" == status:
        my_bitget.cancel_order(df_row['symbol'], df_row['clientOid'])
        return False
    return True

def process_trigger_order(my_bitget : MyBitget, df_row : pd, file_path : str) :
    stop_loss_List = my_bitget.get_trigger_order(df_row['symbol'],df_row['clientOid'],stop_loss=True)
    take_profit_List = my_bitget.get_trigger_order(df_row['symbol'],df_row['clientOid'],take_profit=True)

    if not stop_loss_List and not take_profit_List:
        # position has been closed, move the order to the folder CLOSE_POSITION_DIR
        move_file(file_path,const.CLOSE_POSITION_DIR)

    if stop_loss_List and not take_profit_List:      
        # case 2 : modify sl and create new tp 
        df_sl = pd.DataFrame(stop_loss_List[0])
        
        
        


        modify_sl(my_bitget, df_row, df_sl['clientOid'])
        create_tp(my_bitget, df_row)
 
 #       if len(entrustedList) > 1:
            # case 1 : trade open with original sl and tp still pending 
            # case 3 : trade open with new tp at bb(l,u) and new sl at bbm
  #          df2 = pd.DataFrame(entrustedList[1])
    


def modify_sl(my_bitget: MyBitget, df_row : pd, clientOid : str):
     sl = my_bitget.modify_sl(clientOid, df_row['size']/2,
                              df_row['price'], stopLossExecutePrice)

def create_tp(my_bitget: MyBitget, df_row : pd):
     # create new TP with :
     # size = df_row['size']/2 
     # price = new bbu or new bbl from get_candle(df_sl['symbol'])
     df_new = my_bitget.get_candles_for_trigger_order(df_row['symbol'], df_row['freq'])


     


    









#########################################


