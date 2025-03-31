import os
import trade_bot.utils.enums as const
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
