import os
import json
import time
import shutil
import boto3
import pandas as pd
from trade_bot.utils.trade_logger import logger
from botocore.exceptions import ClientError

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

def move_by_delta(amount, side, myconst, delta=1) -> str:
    """
    Moves the given amount by `delta` units based on its smallest decimal unit.
    
    Parameters:
        amount (float or str): The value to modify.
        side (str): Direction of the move, OPEN_SHORT adds, OPEN_LONG subtracts.
        delta (int or float): Number of smallest units to move. Default is 1.

    Returns:
        str: The adjusted amount as a string.
        
    Examples:
        move_by_delta('0.0932', const.OPEN_SHORT, 5) -> '0.0937'
        move_by_delta(14, const.OPEN_SHORT, 2) -> '16'
        move_by_delta(0.49, const.OPEN_LONG, 3) -> '0.47'
    """
    value_str = str(amount)

    if '.' in value_str:
        decimals = len(value_str.split('.')[-1])
        increment = 10 ** -decimals
    else:
        decimals = 0
        increment = 1

    movement = delta * increment

    if side == myconst.get("OPEN_SHORT"):
        # for sell, execute_price must be > the trigger_price (add delta)
        return str(round(float(value_str) + movement, decimals))
    elif side == myconst.get("OPEN_LONG"):
        # for buy, execute_price must be < the trigger_price (subtract delta)
        return str(round(float(value_str) - movement, decimals))
    else:
        return '0.0'

def is_place_order(client_oid : str, suffix: str ) -> bool:
    if client_oid:
        return __get_suffix_from_client_oid(client_oid) == suffix

def get_clientOID_for(clientOID : str, the_suffix):
    return __modify_client_oid(__get_prefix_from_client_oid(clientOID), the_suffix)

def get_new_client_oid(suffix: str) -> str :
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("TradebotOrderCounter")
    counter_name = "order_id"

    try:
        response = table.update_item(
            Key={"CounterName": counter_name},
            UpdateExpression="SET CounterValue = if_not_exists(CounterValue, :start) + :inc",
            ExpressionAttributeValues={
                ":start": 1000,
                ":inc": 1
            },
            ReturnValues="UPDATED_NEW"
        )
        next = response["Attributes"]["CounterValue"]
        return f"{next}_{suffix}"  # Example: 101_CR, 101_TP, 101_SL and 101_TR
    except ClientError as e:
        logger.error("Error updating counter:", e)
        raise

def read_order_S3_file(client_oid, myconst) -> dict:
    # Setup S3 client
    s3 = boto3.client("s3")
    bucket_name = myconst.get("S3_BUCKET")
    prefix = myconst.get("S3_TRADE_DIR")
    substring = client_oid  # your substring to search for

    # List and filter files
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    if "Contents" in response:
        for obj in response["Contents"]:
            key = obj["Key"]
            if substring in key and not key.endswith(".html"):  # ✅ Exclude HTML files
                # Found a matching file; read its contents
                s3_object = s3.get_object(Bucket=bucket_name, Key=key)
                file_content = s3_object["Body"].read().decode("utf-8")
                return json.loads(file_content)
        else:
            logger.debug(f"No matching files found for {substring}")
            return None
    else:
        logger.debug(f"No files found under the prefix {prefix}")
        return None

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

def define_the_trailing_side(order_side, myconst) -> str:
    if order_side == myconst.get("OPEN_SHORT"):
        return myconst.get("CLOSE_SHORT")
    elif order_side == myconst.get("OPEN_LONG"):
        return myconst.get("CLOSE_LONG")





            
    
