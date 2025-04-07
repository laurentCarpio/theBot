import os
import json
import shutil
import pandas as pd
# import trade_bot.utils.enums as const
from trade_bot.utils.trade_logger import logger
from trade_bot.utils.enums import ORDER_COUNTER
from decimal import Decimal, ROUND_DOWN

def adjust_quantity(quantity: float, volume_place: int) -> float:

    if volume_place == 0 and quantity < 1:
        return 1

    quantity = Decimal(str(quantity))
    return float(quantity.quantize(Decimal('1.' + '0' * volume_place), rounding=ROUND_DOWN))

def adjust_price(price: float, price_end_step: float, price_place: int) -> float:
    """
    Adjusts the price to comply with Bitget's priceEndStep and pricePlace.
    
    :param price: The calculated price
    :param price_end_step: The price step length
    :param price_place: The number of decimal places for the price
    :return: Adjusted price
    """
    price = Decimal(str(price))
    price_end_step = Decimal(str(price_end_step)) / (10 ** price_place)
    
    # Round down to the nearest step
    adjusted_price = (price // price_end_step) * price_end_step
    
    # Format to required decimal places
    return float(adjusted_price.quantize(Decimal('1.' + '0' * price_place), rounding=ROUND_DOWN))

def has_non_empty_column(df, column_list):
    for column_name in column_list:
        is_present = column_name in df and not df[column_name].empty
        if not is_present:
            return False
    return True

    return column_name in df and not df[column_name].empty

def get_client_oid():
    if os.path.exists(ORDER_COUNTER):
        with open(ORDER_COUNTER, "r") as f:
            order_counter = int(f.read().strip())
    else:
        order_counter = 0

    order_counter += 1

    with open(ORDER_COUNTER, "w") as f:
        f.write(str(order_counter))

    return f"order_{order_counter}_lc"  # Example: order_101, order_102, etc.

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






            
    
