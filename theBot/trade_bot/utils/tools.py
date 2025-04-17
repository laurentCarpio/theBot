import os
import json
import time
import shutil
import pandas as pd
import trade_bot.utils.enums as const
from trade_bot.utils.trade_logger import logger
from trade_bot.utils.enums import ORDER_COUNTER, CLIENT_0ID_ORDER

def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
    
def has_not_empty_column(df, column_list) -> bool:
    for column_name in column_list:
        is_present = column_name in df and not df[column_name].empty
        if not is_present:
            return False
    return True

def move_one_unit(amount, side) -> str:
    """
    Adds one smallest decimal unit to the given float or string number.
    Examples:
        '0.0932' -> 0.0933
        14 -> 15
        0.49 -> 0.5
    """
    value_str = str(amount)
    
    if '.' in value_str:
        decimals = len(value_str.split('.')[-1])
        increment = 10 ** -decimals
    else:
        increment = 1
    
    if side == const.OPEN_SHORT:
        # for sell, execute_price must be > the trigger_price (minus 1)
        return str(round(float(value_str) + increment, decimals if '.' in value_str else 0))
    elif side == const.OPEN_LONG:
        # for buy, execute_price must be < the trigger_price (add 1)
        return str(round(float(value_str) - increment, decimals if '.' in value_str else 0))
    else :
        return 0.0

def is_place_order(client_oid : str) -> bool:
    if client_oid:
        return __get_suffix_from_client_oid(client_oid) == CLIENT_0ID_ORDER

def get_clientOID_for(clientOID : str, the_suffix):
    return __modify_client_oid(__get_prefix_from_client_oid(clientOID), the_suffix)

def get_new_client_oid(suffix: str):
    if os.path.exists(ORDER_COUNTER):
        with open(ORDER_COUNTER, "r") as f:
            order_counter = int(f.read().strip())
    else:
        order_counter = 0

    order_counter += 1

    with open(ORDER_COUNTER, "w") as f:
        f.write(str(order_counter))

    return f"{order_counter}_{suffix}"  # Example: 101_CR, 101_TP, 101_SL and 101_TR

def read_order_file(client_oid):
    loaded_data = {}
    file_path = __find_file_by_substring(const.TRADE_DIR, client_oid)
    logger.info(f'process the order file {file_path}')
    with open(file_path, 'r', encoding='utf-8') as f:
        loaded_data = json.load(f)
    logger.debug(f"get the dataFrame from the file {file_path}")
    return loaded_data

def __modify_client_oid(clientOid : str, suffix: str):
    return f"{clientOid}-{suffix}"

def __get_prefix_from_client_oid(client_oid):
    """
    Extracts and returns the prefix from the client_oid string.
    For example, '123345_CR' -> '123345'
    """
    if '_' in client_oid:
        return client_oid.split('_')[0]
    return None

def __get_suffix_from_client_oid(client_oid):
    """
    Extracts and returns the suffix from the client_oid string.
    For example, '123345_CR' -> 'CR'
    """
    if '_' in client_oid:
        return client_oid.split('_')[-1]
    return None

def __find_file_by_substring(directory, substring):
    for filename in os.listdir(directory):
        if substring in filename:
            return os.path.join(directory, filename)
    return None  # if no match is found

###################################################
# not use anymore 
###################################################

def round_one_digit_max(number):
    return round(number, 1) if isinstance(number, (float, int)) else number

def move_file(file_path, destination_dir):
    """Move a file to a new directory."""
    try:
        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)  # Create destination directory if it doesn't exist
        shutil.move(file_path, destination_dir)
        logger.debug(f"Moved {file_path} to {destination_dir}")
    except Exception as e:
        logger.debug(f"Error moving file {file_path}: {e}")

def get_files_fifo(directory):
    """Retrieve files from a directory in FIFO order based on creation time."""
    files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    files.sort(key=os.path.getctime)  # Sort files by creation time (oldest first)
    return files






            
    
