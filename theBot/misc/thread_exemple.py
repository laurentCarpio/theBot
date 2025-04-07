import threading
import time
from bitget_api import Client  # Assuming this is the correct import
import const  # Your constants file

# Global instance of my_bitget (initialized once)
class MyBitget:
    def __init__(self):
        self.client = Client(const.API_KEY, const.SECRET_KEY, const.API_PASSPHRASE, verbose=True)

    def get_account_info(self):
        return self.client.get_account_info()

    def place_order(self, symbol, side, price, size):
        return self.client.place_order(symbol=symbol, side=side, price=price, size=size)

# Create a single global instance
my_bitget = MyBitget()

def monitor_trade():
    while True:
        try:
            account_info = my_bitget.get_account_info()
            print("Monitoring Trade:", account_info)
        except Exception as e:
            print("Error in monitor_trade:", e)
        time.sleep(5)  # Avoid spamming API requests

def find_opportunities():
    while True:
        try:
            # Example trade opportunity check
            print("Checking for trade opportunities...")
            my_bitget.place_order("BTCUSDT", "buy", 68000, 0.01)
        except Exception as e:
            print("Error in find_opportunities:", e)
        time.sleep(10)  # Simulate some delay

# Run both functions in parallel
trade_thread = threading.Thread(target=monitor_trade, daemon=True)
opportunity_thread = threading.Thread(target=find_opportunities, daemon=True)

trade_thread.start()
opportunity_thread.start()

# Keep the main thread alive
while True:
    time.sleep(1)