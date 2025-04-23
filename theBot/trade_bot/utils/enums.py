########################################################################################
#main account:
API_KEY = 'bg_8fd9f7f4f1f2b9ae5b1661eef47d472f'
SECRET_KEY = '017ff9852826cf1a30c46af2fabe7d61da87ea5ff6158831eb832d8550d5e565'
API_PASSPHRASE = '522723041675'

# bot-account:
#API_KEY = 'bg_6452af8176ebd47051abb7c1439f661c'
#SECRET_KEY = 'a9175503be80b22d71a9ef309936c7bd0a6dc0b967ff537168835c46f73d369bM'
#API_PASSPHRASE = 'botau5227mtl'

# demo-not-account
# API_KEY = 'bg_2885944ddd8087f58b4cdeb6e04cb3c9'
# SECRET_KEY = '5d9cd94afdd157cf04254276da193616f163ae22a31c8efd70551a861ffbd812'
# API_PASSPHRASE = 'demobot5227mtl'

########################################################################################
# ws Url
#CONTRACT_WS_URL = 'wss://ws.bitget.com/mix/v1/stream'
CONTRACT_WS_PUBLIC_URL = 'wss://ws.bitget.com/v2/ws/public'
CONTRACT_WS_PRIVATE_URL  = 'wss://ws.bitget.com/v2/ws/private'


FREQUENCY_1M = '1m'   # (1minute)
FREQUENCY_3M = '3m'   # (3minute)
FREQUENCY_5M = '5m'   # (5minute)
FREQUENCY_15M = '15m'  # (15minute)
FREQUENCY_30M = '30m'  # (30minute)
FREQUENCY_1H = '1H'   # (1hour)
FREQUENCY_2H = '2H'   # (2hour)
FREQUENCY_4H = '4H'   # (4hour)
FREQUENCY_6H = '6H'   # (6hour)
FREQUENCY_12H = '12H'  # (12hour)
FREQUENCY_1D = '1D'   # (1day)
FREQUENCY_3D = '3D'   # (3day)
FREQUENCY_1W = '1W'   # (1week)
FREQUENCY_2W = '2W'   # (1week) 
FREQUENCY_1MT = '1M'   # (1month)

MY_FREQUENCY_LIST = [FREQUENCY_3M, FREQUENCY_5M, FREQUENCY_15M, FREQUENCY_30M, FREQUENCY_1H, 
                     FREQUENCY_2H, FREQUENCY_4H, FREQUENCY_6H, FREQUENCY_12H, FREQUENCY_1D]

THE_FULL_FREQUENCY_LIST = [FREQUENCY_1M, FREQUENCY_3M, FREQUENCY_5M, FREQUENCY_15M,
                           FREQUENCY_30M, FREQUENCY_1H, FREQUENCY_2H, FREQUENCY_4H, 
                           FREQUENCY_6H, FREQUENCY_12H, FREQUENCY_1D, FREQUENCY_3D, 
                           FREQUENCY_1W]

FREQUENCY_MAPPING = {FREQUENCY_5M : FREQUENCY_2H,
                     FREQUENCY_15M : FREQUENCY_2H,
                     FREQUENCY_30M : FREQUENCY_2H,
                     FREQUENCY_1H : FREQUENCY_4H,
                     FREQUENCY_2H : FREQUENCY_6H,
                     FREQUENCY_4H : FREQUENCY_12H}

###############################################################################
# the number of candles the algo check for a GO to trade
STRATEGY_WINDOW = -10

# the number of candles used to get the lowest or highest value in the period
MAX_MIN_VALUE_WINDOW = 6

# define the number of candle allowed between the last testing_bb(u,l) and 
# the last crossing_hma. not more than x candles. 
MAX_CANDLES_BETWEEN_HMA_AND_BB = 4

# use of k_line_type = mark instead of k_line_type = MARKET
KLINE_TYPE = 'mark'

# in fact min is 21 for HMA
MIN_CANDLES_FOR_INDICATORS = 50

# the stop lost is set to be x% lower or higher of the close
STOP_LOST = 0.002

# the highest (lowest) cannot be more than 105% of the hma crossing
ACCEPTABLE_MARGE = 1.05

# we want to buy at the lowest price possible
# the limit buy order must be below or equal to the best bid price 
# for now the rule is to choice the PRICE_RANK_IN_BIDS_ASKS position

# we want to sell at the highest price possible
# You must place your limit sell order above or equal to the best ask price.
# the rule is to choice the PRICE_RANK_IN_BIDS_ASKS position 
PRICE_RANK_IN_BIDS_ASKS = 1

# the acceptable ratio to open a trade, below this number the possible profit 
# is not enough (fee, spread, risk ,etc..)
ACCEPTABLE_RATIO = 1.2

# % of the trailing stop to follow for execution 
CALL_BACK_RATIO = 1.5

# the amount we add or soustract (depending the side) to the executive price 
# to get the launch price of the trailing stop order 
TRAILING_DELTA_PRICE_MOVED = 5 

# the risk management 
# the % of value per trade 
PERCENTAGE_VALUE_PER_TRADE = 0.2   # 2% du total disponible 
###############################################################################
# SIDE - Order direction
OPEN_LONG = "buy"
CLOSE_LONG = "sell"
OPEN_SHORT = "sell"
CLOSE_SHORT = "buy"

ORDER_TYPE_LIMIT = 'limit'

# timeInForceValue
TIME_IN_FORCE_TYPES = ['normal', 'post_only', 'fok', 'ioc']
REDUCE_ONLY_YES = 'YES'
REDUCE_ONLY_NO = 'NO'
CONTRACT_OPEN_TIME_INDEF = -1

ONE_WAY_MODE_POSITION = "one_way_mode"   # opposite to hedge_mode
DEFAULT_LEVERAGE = '1'

# triggerType
TRIGGER_TYPES = ['fill_price', 'mark_price']

# Trigger Order status
TRIGGER_ORDER_STATUS_LIVE = 'live'                   # plan order created
TRIGGER_ORDER_STATUS_EXECUTED = 'executed'           # executed
TRIGGER_ORDER_STATUS_FAIL_EXECUTED = 'fail_execute'  # execute failed
TRIGGER_ORDER_STATUS_CANCELLED = 'cancelled'         # cancelled
TRIGGER_ORDER_STATUS_EXECUTING = 'executing'         # executing

# Place Order status
PLACE_ORDER_LIVE = 'live'                            # New order, waiting for a match in orderbook
PLACE_ORDER_PARTIALLY_FILLED = 'partially_filled'    # Partially filled
PLACE_ORDER_FILLED = 'filled'                        # All filled
PLACE_ORDER_CANCELLED = 'canceled'                   # the order is cancelled

# planType
TRAILING_PLAN_TYPE = 'track_plan'
STOP_LOSS_PLAN_TYPE = 'loss_plan'
TAKE_PROFIT_PLAN_TYPE = 'profit_plan'

PRODUCT_TYPE_USED = 'usdt-futures'  # = 'susdt-futures' for DEMO
MARGIN_COIN_USED = 'USDT'  # 'SUSDT' for demo 
MARGIN_MODE = 'isolated'

#REPORTS_FOLDER = 'trade_bot/reports'
TRADE_DIR = '../theBot/trade_bot/reports/trade'
DATA_DIR = 'trade_bot/data'
CONFIG_LOG_FILE = 'trade_bot/utils/logging.conf'
ORDER_COUNTER = 'trade_bot/utils/order_counter.txt'

# clientOID suffix
CLIENT_0ID_ORDER = 'CR'
CLIENT_0ID_TAKE_PROFIT = 'TP'
CLIENT_0ID_STOP_LOSS = 'SL'
CLIENT_0ID_TRAILING_LOSS = 'TR'

LOG_DICT = {'symbol':'',
            'frequence':'', 
            'place_order_clientOID':'',
            'place_order_orderID':'',
            'place_order_msg':'',
            'place_order_size':'',
            'place_order_price':'',
            'place_order_side':'', 
            'place_order_preset_SL':'',
            'place_order_preset_TP':'',
            'contract_price_end_step':'',
            'contract_minTradeUSDT':'',
            'contract_price_place':'',
            'contract_volume_place':''
            }

# 'commission fee': 0.02,
# 'back_test_start': Timestamp("2022-01-1"),
# 'back_test_end': Timestamp("2022-03-31"),
