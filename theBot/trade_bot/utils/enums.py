########################################################################################
# demo-not-account
API_KEY = 'xxxxx'
SECRET_KEY = 'xxxxxx'
API_PASSPHRASE = 'xxxx'

########################################################################################
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
FREQUENCY_1MT = '1M'   # (1month)

MY_FREQUENCY_LIST = [FREQUENCY_5M, FREQUENCY_15M, FREQUENCY_30M, FREQUENCY_1H, 
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

PRODUCT_TYPE_USED = 'usdt-futures'  # = 'susdt-futures' for prod
MARGIN_COIN_USED = 'USDT'  # 'SUSDT' for demo 

###############################################################################
# the number of candles the algo check for a GO to trade
STRATEGY_WINDOW = -10

# the number of candles used to get the lowest or highest value in the period
MAX_MIN_VALUE_WINDOW = 6

# define the number of candle allowed between the last testing_bb(u,l) and 
# the last crossing_hma. not more than x candles. 
MAX_CANDLES_BETWEEN_HMA_AND_BB = 4

# -------------------  TO BE VALIDATED ----------------------- #
# use of k_line_type = MARK instead of k_line_type = MARKET    #
################################################################
# 'k_line_type':'MARK'

# in fact min is 21 for HMA
MIN_CANDLES_FOR_INDICATORS = 50

# the stop lost is set to be x% lower or higher of the close
STOP_LOST = 0.002

# the highest (lowest) cannot be more than 105% of the hma crossing
ACCEPTABLE_MARGE = 1.05

# the acceptable ratio to open a trade, below this number the possible profit 
# is not enough (fee, spread, risk ,etc..)
ACCEPTABLE_RATIO = 1.2

# the risk management 
# the % of value per trade 
PERCENTAGE_VALUE_PER_TRADE = 0.2   # 2% du total disponible 
###############################################################################
REPORTS_FOLDER = 'trade_bot/reports'
DATA_FOLDER = 'trade_bot/data'
CONFIG_LOG_FILE = 'trade_bot/utils/logging.conf'
ORDER_COUNTER = 'trade_bot/utils/order_counter.txt'

# 'commission fee': 0.02,
# 'back_test_start': Timestamp("2022-01-1"),
# 'back_test_end': Timestamp("2022-03-31"),
