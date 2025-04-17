import logging.config
import pandas as pd
import json
import os
from datetime import datetime
from trade_bot.utils.enums import CONFIG_LOG_FILE, LOG_DICT, TRADE_DIR

logging.config.fileConfig(CONFIG_LOG_FILE)
logger = logging.getLogger()
logger.info("Logging app is configured!")


# Ensure directories exist
os.makedirs(TRADE_DIR, exist_ok=True)

def log_trade_order(log_dict, **kwargs):
    for key, value in kwargs.items():
        if key in log_dict:
            log_dict[key] = value
        else:
            raise KeyError(f"{key} is not a valid log field")
    __log_order(log_dict)


# to log order we do not use the logger library
def __log_order(log_dict : dict ):
    """
    Logs each order into a separate file in 'OPEN_TRADE_DIR'
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(
        TRADE_DIR,
        f"{log_dict['place_order_clientOID']}_{log_dict['symbol']}_{log_dict['frequence']}-{timestamp}.log")

    # Write only the JSON data
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_dict, f, indent=4)


    
    