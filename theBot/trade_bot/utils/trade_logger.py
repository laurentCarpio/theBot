import logging.config
from trade_bot.utils.enums import CONFIG_LOG_FILE
import pandas as pd
import json

logging.config.fileConfig(CONFIG_LOG_FILE)
logger = logging.getLogger()
order_logger = logging.getLogger("order_logger")
logger.info("Logging app is configured!")
order_logger.info("Orders log is configured!")

def log_order(order_id: str, df_row : pd):
    # convert row it to JSON
    row = df_row.to_dict()
    row_json = json.dumps(row, indent=4)  # Convert row to JSON format
    # Log the JSON string
    order_logger.info(f"{order_id}:{row_json}")
    
    