import time
import hashlib
import hmac
import requests

API_KEY = "your_demo_api_key"
SECRET_KEY = "your_demo_secret_key"
PASSPHRASE = "your_demo_passphrase"

BASE_URL = "https://api.bitget.com"
endpoint = "/api/mix/v1/market/contracts"
timestamp = str(int(time.time() * 1000))

def generate_signature(timestamp, method, request_path, body=""):
    message = f"{timestamp}{method}{request_path}{body}"
    signature = hmac.new(SECRET_KEY.encode(), message.encode(), hashlib.sha256).hexdigest()
    return signature

headers = {
    "ACCESS-KEY": API_KEY,
    "ACCESS-SIGN": generate_signature(timestamp, "GET", endpoint),
    "ACCESS-TIMESTAMP": timestamp,
    "ACCESS-PASSPHRASE": PASSPHRASE,
    "paptrading": "1"  # Enable demo trading
}

url = BASE_URL + endpoint
response = requests.get(url, headers=headers)
print(response.json())  # Check if this returns a list of available contracts
