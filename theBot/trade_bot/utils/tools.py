import os
import json
import time
import shutil
import pandas as pd
import trade_bot.utils.enums as const
from trade_bot.utils.trade_logger import logger
from trade_bot.utils.enums import ORDER_COUNTER

def return_the_close_from(code) -> str:
    if code == const.OPEN_LONG:
        return const.CLOSE_LONG
    elif code == const.OPEN_SHORT:
        return const.CLOSE_SHORT
    else:
        return ''

def has_not_empty_column(df, column_list) -> bool:
    for column_name in column_list:
        is_present = column_name in df and not df[column_name].empty
        if not is_present:
            return False
    return True
    
def substract_one_unit(amount) -> str:
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

    return str(round(float(value_str) - increment, decimals if '.' in value_str else 0))

def get_suffix_from_client_oid(client_oid):
    """
    Extracts and returns the suffix from the client_oid string.
    For example, '123345_CR' -> 'CR'
    """
    if '_' in client_oid:
        return client_oid.split('_')[-1]
    return None

def get_client_oid(suffix: str):
    if os.path.exists(ORDER_COUNTER):
        with open(ORDER_COUNTER, "r") as f:
            order_counter = int(f.read().strip())
    else:
        order_counter = 0

    order_counter += 1

    with open(ORDER_COUNTER, "w") as f:
        f.write(str(order_counter))

    return f"order_{order_counter}_{suffix}"  # Example: 101_create, 101_mod_tk, 101_trailing etc.

def get_files_fifo(directory):
    """Retrieve files from a directory in FIFO order based on creation time."""
    files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    files.sort(key=os.path.getctime)  # Sort files by creation time (oldest first)
    return files

def read_order_file(file_path):
    data = []
    logger.info(f'process the order file {file_path}')
    with open(file_path, 'r', encoding='utf-8') as f:
        data.append(json.load(f))
    logger.debug(f"get the dataFrame from the file {file_path}")
    return pd.DataFrame(data)

def move_file(file_path, destination_dir):
    """Move a file to a new directory."""
    try:
        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)  # Create destination directory if it doesn't exist
        shutil.move(file_path, destination_dir)
        logger.debug(f"Moved {file_path} to {destination_dir}")
    except Exception as e:
        logger.debug(f"Error moving file {file_path}: {e}")






            
    
