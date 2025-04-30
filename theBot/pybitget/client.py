import requests
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from pybitget.enums import *
from pybitget import utils
from pybitget import exceptions
from trade_bot.utils.trade_logger import logger
from trade_bot.utils.s3_config_loader import S3ConfigLoader

class Client(object):

    def __init__(self, api_key, api_secret_key, passphrase, config, use_server_time=False, verbose=False):
        self.API_KEY = api_key
        self.API_SECRET_KEY = api_secret_key
        self.PASSPHRASE = passphrase
        self.use_server_time = use_server_time
        self.verbose = verbose
        self.__myconst = config
        # Create a retry-enabled session
        self.session = self._create_retry_session()

    def _create_retry_session(self, total_retries=5, backoff_factor=1, status_forcelist=(502, 503, 504, 429)):
        session = requests.Session()
        retry = Retry(
            total=total_retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "DELETE"],
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.headers.update({"Connection": "close"})
        return session

    def _request(self, method, request_path, params, cursor=False):
        if method == GET:
            request_path = request_path + utils.parse_params_to_str(params)

        # url
        url = API_URL + request_path

        # Get local time
        timestamp = utils.get_timestamp()

        # sign & header
        if self.use_server_time:
            # Get server time interface
            timestamp = self._get_timestamp()

        body = json.dumps(params) if method == POST else ""
        sign = utils.sign(utils.pre_hash(timestamp, method, request_path, str(body)), self.API_SECRET_KEY)
        header = utils.get_header(self.API_KEY, sign, timestamp, self.PASSPHRASE)

        try:
            if method == GET:
                response = self.session.get(url, headers=header, timeout=10)
            elif method == POST:
                response = self.session.post(url, data=body, headers=header, timeout=10)
            elif method == DELETE:
                response = self.session.delete(url, headers=header, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
        except requests.exceptions.RequestException as e:
            raise exceptions.BitgetRequestException(f"Network request failed: {e}")

        if not str(response.status_code).startswith('2'):
            raise exceptions.BitgetAPIException(response)

        try:
            res_header = response.headers
            if cursor:
                r = dict()
                try:
                    r['before'] = res_header['BEFORE']
                    r['after'] = res_header['AFTER']
                except KeyError:
                    pass
                return response.json(), r
            else:
                return response.json()
        except ValueError:
            raise exceptions.BitgetRequestException(f"Invalid JSON response: {response.text}")

    def _request_without_params(self, method, request_path):
        return self._request(method, request_path, {})

    def _request_with_params(self, method, request_path, params, cursor=False):
        return self._request(method, request_path, params, cursor)

    def _get_timestamp(self):
        url = API_URL + SERVER_TIMESTAMP_URL
        try:
            response = self.session.get(url, timeout=5)
            if response.status_code == 200:
                return response.json()['data']
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch server timestamp: {e}")
        return ""
    
    """ --- the used Api for the bot ---"""
    def mix_get_all_tickers(self):
        params = {}
        params["productType"] = self.__myconst.get("PRODUCT_TYPE_USED")
        return self._request_with_params(GET, MIX_MARKET_V2_URL + '/tickers', params)

    def mix_get_all_positions(self):
        params = {}
        params["productType"] = self.__myconst.get("PRODUCT_TYPE_USED")
        params["marginCoin"] = self.__myconst.get("MARGIN_COIN_USED")
        return self._request_with_params(GET, MIX_POSITION_V2_URL + '/all-position', params)
            
    def mix_get_candles(self, symbol, granularity, startTime, endTime):
        params = {}
        if symbol  and granularity and startTime and endTime :
            params["symbol"] = symbol
            params["productType"] = self.__myconst.get("PRODUCT_TYPE_USED")
            params["granularity"] = granularity
            params["startTime"] = startTime
            params["endTime"] = endTime
            params["kLineType"] = self.__myconst.get("KLINE_TYPE")
            params["limit"] = self.__myconst.get("MIN_CANDLES_FOR_INDICATORS")

            return self._request_with_params(GET, MIX_MARKET_V2_URL + '/candles', params)
        else:
            logger.error("pls check args")
            return False
    
    def mix_get_contract_config(self, symbol):
        params = {}
        if symbol:
            params["productType"] = self.__myconst.get("PRODUCT_TYPE_USED")
            params["symbol"] = symbol
            return self._request_with_params(GET, MIX_MARKET_V2_URL + '/contracts', params)
        else:
            logger.error("pls check args")
            return False
            
    def mix_get_merge_depth(self, symbol, precision='scale0', limit='max'):
        params = {}
        if symbol :
            params["symbol"] = symbol
            params["productType"] = self.__myconst.get("PRODUCT_TYPE_USED")
            params["precision"] = precision
            params["limit"] = limit
            return self._request_with_params(GET, MIX_MARKET_V2_URL + '/merge-depth', params)
        else:
            logger.error("pls check args")
            return False

    def mix_set_leverage(self, symbol):
        params = {}
        if symbol :
            params["symbol"] = symbol
            params["productType"] = self.__myconst.get("PRODUCT_TYPE_USED")
            params["marginCoin"] = self.__myconst.get("MARGIN_COIN_USED")
            params["leverage"] = self.__myconst.get("DEFAULT_LEVERAGE")
            return self._request_with_params(POST, MIX_ACCOUNT_V2_URL + '/set-leverage', params)
        else:
            logger.error("pls check args")
            return False
        
    def mix_set_position_mode(self):
        params = {}
        params["productType"] = self.__myconst.get("PRODUCT_TYPE_USED")
        params["posMode"] = self.__myconst.get("ONE_WAY_MODE_POSITION")
        
        return self._request_with_params(POST, MIX_ACCOUNT_V2_URL + '/set-position-mode', params)
                        
    def mix_root_place_order(self, symbol, size, price, side, clientOID):
        params = {}
        if symbol and size and price and side and clientOID:
            params["symbol"] = symbol
            params["productType"] = self.__myconst.get("PRODUCT_TYPE_USED")
            params["marginMode"] = self.__myconst.get("MARGIN_MODE")
            params["marginCoin"] = self.__myconst.get("MARGIN_COIN_USED")
            params["size"] = size
            params["price"] = price
            params["side"] = side
            params["orderType"] = self.__myconst.get("ORDER_TYPE_LIMIT")
            params["force"] = self.__myconst.get("TIME_IN_FORCE_TYPES[1]")
            params["clientOID"] = clientOID
            params["reduceOnly"] = self.__myconst.get("REDUCE_ONLY_NO")
            return self._request_with_params(POST, MIX_ORDER_V2_URL + '/place-order', params)
        else:
            logger.error("pls check args")
            return False

    def mix_take_profit_plan_order(self, symbol, planType,
                            triggerPrice, executePrice,
                            holdSide, size, clientOID):

        params = {}
        if symbol and planType and triggerPrice  and executePrice and holdSide and size and clientOID :
            params["marginCoin"] = self.__myconst.get("MARGIN_COIN_USED")
            params["productType"] = self.__myconst.get("PRODUCT_TYPE_USED")
            params["symbol"] = symbol
            params["planType"] = planType
            params["triggerPrice"] = triggerPrice
            params["triggerType"] = self.__myconst.get("TRIGGER_TYPES[1]")
            params["executePrice"] = executePrice            
            params["holdSide"] = holdSide
            params["size"] = size
            params["clientOID"] = clientOID
        
            return self._request_with_params(POST, MIX_ORDER_V2_URL + '/place-tpsl-order', params)
        else:
            logger.error("pls check args")
            return False
                         
    def mix_stop_loss_plan_order(self, symbol, planType, triggerPrice, holdSide, size, clientOID):

        params = {}
        if symbol and planType and triggerPrice and holdSide and size and clientOID :
            params["marginCoin"] = self.__myconst.get("MARGIN_COIN_USED")
            params["productType"] = self.__myconst.get("PRODUCT_TYPE_USED")
            params["symbol"] = symbol
            params["planType"] = planType
            params["triggerPrice"] = triggerPrice
            params["triggerType"] = self.__myconst.get("TRIGGER_TYPES[0]")
            params["executePrice"] = "0"            
            params["holdSide"] = holdSide
            params["size"] = size
            params["clientOID"] = clientOID
        
            return self._request_with_params(POST, MIX_ORDER_V2_URL + '/place-tpsl-order', params)
        else:
            logger.error("pls check args")
            return False
         
    def mix_trail_plan_order(self, symbol, size, triggerPrice, side):
        params = {}
        if symbol and size and triggerPrice and side :
            params["symbol"] = symbol
            params["planType"] = self.__myconst.get("TRAILING_PLAN_TYPE")
            params["productType"] = self.__myconst.get("PRODUCT_TYPE_USED")
            params["marginMode"] = self.__myconst.get("MARGIN_MODE")
            params["marginCoin"] = self.__myconst.get("MARGIN_COIN_USED")
            params["size"] = size
            params["callbackRatio"] = self.__myconst.get("CALL_BACK_RATIO")
            params["triggerPrice"] = triggerPrice
            params["triggerType"] = self.__myconst.get("TRIGGER_TYPES[1]")
            params["side"] = side
            params["orderType"] = self.__myconst.get("ORDER_TYPE_LIMIT")

            return self._request_with_params(POST, MIX_ORDER_V2_URL + '/place-plan-order', params)
        else:
            logger.error("pls check args")
            return False
        
    def mix_cancel_plan_order(self, symbol, planType): 
        params = {}
        if symbol and planType :
            params["symbol"] = symbol
            params["marginCoin"] = self.__myconst.get("MARGIN_COIN_USED")
            params["productType"] = self.__myconst.get("PRODUCT_TYPE_USED")
            params["planType"] = planType
            return self._request_with_params(POST, MIX_ORDER_V2_URL + '/cancel-plan-order', params)
        else:
            logger.error("pls check args")
            return False 


