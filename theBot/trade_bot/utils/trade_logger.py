import logging.config
from trade_bot.utils.enums import CONFIG_LOG_FILE,SUCCESS_OPEN_TRADE_DIR,FAILED_OPEN_TRADE_DIR
import pandas as pd
import json
import os
from datetime import datetime

logging.config.fileConfig(CONFIG_LOG_FILE)
logger = logging.getLogger()
logger.info("Logging app is configured!")

# Ensure directories exist
os.makedirs(SUCCESS_OPEN_TRADE_DIR, exist_ok=True)
os.makedirs(FAILED_OPEN_TRADE_DIR, exist_ok=True)

# to log order we do not use the logger library
def log_open_order(msg: str, df_row: pd):
    """
    Logs each order into a separate file in 'SUCCESS_OPEN_TRADE_DIR' or 'FAILED_OPEN_TRADE_DIR'.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = SUCCESS_OPEN_TRADE_DIR if msg == "success" else FAILED_OPEN_TRADE_DIR
    log_path = os.path.join(log_dir, f"order_{timestamp}.log")

    # convert row to dict
    row = df_row.to_dict()
    logger.debug(f"write the open order {print(row)}")

    # Write only the JSON data
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(row, f) # Convert row to JSON format


    
    