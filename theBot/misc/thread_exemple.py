import time
import requests
import threading

# Bitget API details
API_KEY = 'your_api_key'
API_SECRET = 'your_api_secret'
PASSPHRASE = 'your_passphrase'

# Trading parameters
symbol = 'BTCUSDT'
entry_price = 70000  # Example entry price
take_profit_1 = 70500  # TP for 50%
take_profit_2 = 71000  # TP for remaining 50%
stop_loss = 69500  # Initial stop loss

# Quantity (in BTC)
total_quantity = 0.02
first_tp_quantity = total_quantity / 2
remaining_quantity = total_quantity / 2

# Function to place an order
def place_order(side, quantity, price=None, tp=None, sl=None):
    order_data = {
        "side": side,
        "symbol": symbol,
        "quantity": quantity,
        "price": price,
        "takeProfit": tp,
        "stopLoss": sl
    }
    # Simulate API request
    response = requests.post('https://api.bitget.com/api/v2/order', json=order_data)
    return response.json()

# Function to monitor open trade
def monitor_trade():
    global stop_loss

    while True:
        # Check if first TP is hit
        current_price = float(requests.get('https://api.bitget.com/api/v2/ticker', params={'symbol': symbol}).json()['price'])

        if current_price >= take_profit_1:
            print("First Take Profit Hit. Closing 50%.")
            place_order('sell', first_tp_quantity)

            # Adjust SL to entry price for remaining 50%
            stop_loss = entry_price
            print("Adjusting SL to Entry Price.")

            # Set new TP for remaining 50%
            response = place_order('sell', remaining_quantity, tp=take_profit_2, sl=stop_loss)
            print("New TP/SL Set:", response)
            break

        time.sleep(5)

# Function to find trading opportunities
def find_opportunities():
    while True:
        # Placeholder logic for finding opportunities
        print("Scanning for trading opportunities...")
        time.sleep(10)

# Place initial order
response = place_order('buy', total_quantity, entry_price, tp=take_profit_1, sl=stop_loss)
print("Order placed:", response)

# Run both functions in parallel
trade_thread = threading.Thread(target=monitor_trade)
trade_thread.start()

opportunity_thread = threading.Thread(target=find_opportunities)
opportunity_thread.start()