import os
import trade_bot.utils.enums as const
from trade_bot.utils.enums import ORDER_COUNTER

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
