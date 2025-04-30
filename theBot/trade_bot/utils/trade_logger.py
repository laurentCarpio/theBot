#import logging.config
import pandas as pd
import json
import boto3
from datetime import datetime
import io
import logging
import watchtower
import colorlog

timestamp_format = "%Y-%m-%d %H:%M:%S"

logger = logging.getLogger("tradebot")
logger.setLevel(logging.DEBUG)  # global level: handle all, handlers can filter

# CloudWatch handler (only warnings and above)
cw_handler = watchtower.CloudWatchLogHandler(
    log_group="TradebotLogs",
    stream_name="fargate-stream"
)
cw_handler.setLevel(logging.WARNING)

cw_formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s",
    datefmt=timestamp_format
)
cw_handler.setFormatter(cw_formatter)

logger.addHandler(cw_handler)

# Console handler (colored, show all)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
color_formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
    datefmt=timestamp_format,
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
    }
)
console_handler.setFormatter(color_formatter)
logger.addHandler(console_handler)

# Example
logger.info("✅ All systems go.")
logger.warning("⚠️ Warning: Something might go sideways.")
logger.error("🔥 Boom.")

def log_trade_order(log_dict, **kwargs):
    for key, value in kwargs.items():
        if key in log_dict:
            log_dict[key] = value
        else:
            raise KeyError(f"{key} is not a valid log field")
    __log_order(log_dict)

# to log order we do not use the logger library
def __log_order(trade_data : dict ):
    """
    Logs each order into a separate file in 'OPEN_TRADE_DIR'
    """
    try :
       json_data = json.dumps(trade_data, indent=4)
       
       timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
       s3_key = f"reports/trade/{trade_data['place_order_clientOID']}_{trade_data['symbol']}_{trade_data['frequence']}-{timestamp}.log"
    
       # Setup S3
       s3 = boto3.client("s3")
       bucket = "tradebot-thebot-bucket"

       # Upload directly from string
       s3.put_object(Bucket=bucket, Key=s3_key.strip(), Body=json_data.encode("utf-8"))
    except Exception as e:
        print(f"❌ Failed to upload {s3_key}: {e}")


    
    