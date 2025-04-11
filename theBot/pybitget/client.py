import requests
import json
from pybitget.enums import *
from pybitget import utils
from pybitget import exceptions
from pybitget import logger

class Client(object):

    def __init__(self, api_key, api_secret_key, passphrase, use_server_time=False, verbose=False):

        self.API_KEY = api_key
        self.API_SECRET_KEY = api_secret_key
        self.PASSPHRASE = passphrase
        self.use_server_time = use_server_time
        self.verbose = verbose

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

        # send request
        response = None
        if method == GET:
            response = requests.get(url, headers=header)
        elif method == POST:
            response = requests.post(url, data=body, headers=header)
        elif method == DELETE:
            response = requests.delete(url, headers=header)
        # exception handle
        if not str(response.status_code).startswith('2'):
            raise exceptions.BitgetAPIException(response)
        try:
            res_header = response.headers
            if cursor:
                r = dict()
                try:
                    r['before'] = res_header['BEFORE']
                    r['after'] = res_header['AFTER']
                except:
                    pass
                return response.json(), r
            else:
                return response.json()

        except ValueError:
            raise exceptions.BitgetRequestException('Invalid Response: %s' % response.text)

    def _request_without_params(self, method, request_path):
        return self._request(method, request_path, {})

    def _request_with_params(self, method, request_path, params, cursor=False):
        return self._request(method, request_path, params, cursor)

    def _get_timestamp(self):
        url = API_URL + SERVER_TIMESTAMP_URL
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()['data']
        else:
            return ""

    """ --- the used Api for the bot ---"""
    def mix_get_all_tickers(self, productType):
        params = {}
        if productType:
            params["productType"] = productType
            return self._request_with_params(GET, MIX_MARKET_V2_URL + '/tickers', params)
        else:
            logger.error("pls check args")
            return False

    def mix_get_candles(self, symbol, 
                        productType, 
                        granularity, 
                        startTime, 
                        endTime, 
                        kLineType, 
                        limit):
        params = {}
        if symbol and productType and granularity and startTime and endTime :
            params["symbol"] = symbol
            ### j'ai ajouté le productType pour la V2 
            params["productType"] = productType
            params["granularity"] = granularity
            params["startTime"] = startTime
            params["endTime"] = endTime
            params["kLineType"] = kLineType
            params["limit"] = limit
            return self._request_with_params(GET, MIX_MARKET_V2_URL + '/candles', params)
        else:
            logger.error("pls check args")
            return False
    
    def mix_get_contract_config(self, productType, symbol):
        params = {}
        if productType and symbol:
            params["productType"] = productType
            params["symbol"] = symbol
            return self._request_with_params(GET, MIX_MARKET_V2_URL + '/contracts', params)
        else:
            logger.error("pls check args")
            return False
            
    def mix_get_merge_depth(self, symbol, productType, precision, limit):
        params = {}
        if symbol and productType and precision and limit:
            params["symbol"] = symbol
            params["productType"] = productType
            params["precision"] = precision
            params["limit"] = limit
            return self._request_with_params(GET, MIX_MARKET_V2_URL + '/merge-depth', params)
        else:
            logger.error("pls check args")
            return False

    def mix_set_position_mode(self, productType, posMode):
        params = {}
        if productType and posMode:
            params["productType"] = productType
            params["posMode"] = posMode
            return self._request_with_params(POST, MIX_ACCOUNT_V2_URL + '/set-position-mode', params)
        else:
            logger.error("pls check args")
            return False
                
    def mix_root_place_order(self, symbol, productType, marginMode, marginCoin, size, price, side, 
                        orderType, force, clientOid, reduceOnly):
        params = {}
        params["symbol"] = symbol
        params["productType"] = productType
        params["marginMode"] = marginMode
        params["marginCoin"] = marginCoin
        params["size"] = size
        params["price"] = price
        params["side"] = side
        # params["tradeSide"] = tradeSide   no trade side for one-way-mode position mode 
        params["orderType"] = orderType
        params["force"] = force
        params["clientOid"] = clientOid
        params["reduceOnly"] = reduceOnly
        return self._request_with_params(POST, MIX_ORDER_V2_URL + '/place-order', params)

    def mix_set_leverage(self, symbol, productType, marginCoin, leverage):
        params = {}
        if symbol and productType and marginCoin and leverage:
            params["symbol"] = symbol
            params["productType"] = productType
            params["marginCoin"] = marginCoin
            params["leverage"] = leverage
            return self._request_with_params(POST, MIX_ACCOUNT_V2_URL + '/set-leverage', params)
        else:
            logger.error("pls check args")
            return False
                     
    def mix_tp_or_sl_plan_order(self, planType, symbol, 
                             productType,
                             marginMode, marginCoin,
                             size, 
                             triggerPrice, triggerType, side,
                             orderType, clientOID):
        params = {}
        if planType and symbol and productType and marginMode and marginCoin and size and \
            triggerPrice and triggerType and side and orderType and clientOID :
            params["planType"] = planType
            params["symbol"] = symbol
            params["productType"] = productType
            params["marginMode"] = marginMode
            params["marginCoin"] = marginCoin
            params["size"] = size
            params["triggerPrice"] = triggerPrice
            params["triggerType"] = triggerType
            params["side"] = side
            params["orderType"] = orderType
            params["clientOID"] = clientOID
            
            logger.info(f"planType {planType}, symbol {symbol}, productType {productType},marginMode {marginMode}, \
                             marginCoin {marginCoin},size {size},triggerPrice {triggerPrice}, triggerType {triggerType}, \
                            side {side}, orderType {orderType}, clientOID {clientOID} ")

            return self._request_with_params(POST, MIX_ORDER_V2_URL + '/place-plan-order', params)
        else:
            logger.error("pls check args")
            return False
         
#######################################################################
########     not used api for now 
#######################################################################

    def mix_get_pending_orders(self, clientOid, productType, limit=100):
        params = {}
        if clientOid and productType :
            params["clientOid"] = clientOid
            params["productType"] = productType
            params["limit"] = limit
            return self._request_with_params(GET, MIX_ORDER_V2_URL + '/orders-pending', params)
        else:
            logger.error("pls check args")
            return False
        
    def mix_get_pending_trigger_Order(self, orderId, planType, productType, limit=100):
        params = {}
        if productType and orderId and planType and productType:
            params["orderId"] = orderId
            params["planType"] = planType
            params["productType"] = productType
            params["limit"] = limit
            return self._request_with_params(GET, MIX_ORDER_V2_URL + '/orders-plan-pending', params)
        else:
            logger.error("pls check args")
            return False
        
    def mix_modify_size_tp_order(self, orderId, productType, newSize):
        params = {}
        if productType and orderId and newSize:
            params["orderId"] = orderId
            params["productType"] = productType
            params["newSize"] = newSize
            return self._request_with_params(POST, MIX_ORDER_V2_URL + '/modify-plan-order', params)
        else:
            logger.error("pls check args")
            return False

    def mix_get_single_position(self, productType, symbol, marginCoin):
        params = {}
        if productType and symbol and marginCoin:
            params["productType"] = productType
            params["symbol"] = symbol
            params["marginCoin"] = marginCoin
            return self._request_with_params(GET, MIX_POSITION_V2_URL + '/single-position', params)
        else:
            logger.error("pls check args")
            return False
        
    def mix_cancel_plan_order(self, symbol, marginCoin, orderId, productType, planType): 
        params = {}
        if symbol and marginCoin and orderId and productType and planType:
            params["symbol"] = symbol
            params["marginCoin"] = marginCoin
            params["productType"] = productType
            params["orderId"] = orderId
            params["planType"] = planType
            return self._request_with_params(POST, MIX_ORDER_V2_URL + '/cancel-plan-order', params)
        else:
            logger.error("pls check args")
            return False 
                
    def mix_get_all_positions(self, productType, marginCoin=None):
        params = {}
        if productType:
            params["productType"] = productType
            if marginCoin is not None:
                params["marginCoin"] = marginCoin
            return self._request_with_params(GET, MIX_POSITION_V2_URL + '/all-position', params)
        else:
            logger.error("pls check args")
            return False

    def mix_get_order_detail(self, symbol, productType, clientOid):
        params = {}
        if symbol and productType and clientOid :
            params["symbol"] = symbol
            params["productType"] = productType
            params["clientOid"] = clientOid
            return self._request_with_params(GET, MIX_ORDER_V2_URL + '/detail', params)
        else:
            logger.error("pls check args")
            return False
            
    def mix_cancel_order(self, symbol, marginCoin, clientOid):
        params = {}
        if symbol and marginCoin and clientOid :
            params["symbol"] = symbol
            params["marginCoin"] = marginCoin
            params["clientOid"] = clientOid
            return self._request_with_params(POST, MIX_ORDER_V2_URL + '/cancel-order', params)
        else:
            logger.error("pls check args")
            return False            
        
    def mix_get_accounts(self, productType):
        params = {}
        if productType:
            params['productType'] = productType
            return self._request_with_params(GET, MIX_ACCOUNT_V2_URL + '/accounts', params)
        else:
            logger.error("pls check args")
            return False
        
    def mix_get_vip_fee_rate(self):
        """
        VIP fee rate: https://bitgetlimited.github.io/apidoc/en/mix/#vip-fee-rate
        Limit rule: 10 times/1s (IP)
        Required: None
        :return:
        """
        return self._request_without_params(GET, MIX_MARKET_V1_URL + '/contract-vip-level')
    
    def mix_get_single_symbol_ticker(self, symbol, productType):
        """
        Get Single Symbol Ticker: https://bitgetlimited.github.io/apidoc/en/mix/#get-single-symbol-ticker

        Limit rule: 20 times/1s (IP)

        Required: symbol

        :param symbol: Symbol Id (Must be capitalized)
        :type symbol: str
        :return:
        """
        params = {}
        if symbol and productType:
            params["symbol"] = symbol
            params["productType"] = productType
            return self._request_with_params(GET, MIX_MARKET_V2_URL + '/ticker', params)
        else:
            logger.error("pls check args")
            return False

    def mix_get_fills(self, symbol, limit=100):
        """
        Get recent trades: https://bitgetlimited.github.io/apidoc/en/mix/#get-fills

        Limit rule: 20 times/1s (IP)

        Required: symbol, limit

        :param symbol: Symbol Id (Must be capitalized)
        :type symbol: str
        :param limit: Default limit is 100
        :type limit: str
        :return:
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
            params["limit"] = limit
            return self._request_with_params(GET, MIX_MARKET_V1_URL + '/fills', params)
        else:
            logger.error("pls check args")
            return False

    def mix_get_history_candles(self, symbol, granularity, startTime, endTime, limit=100):
        """
        Get History Candle Data: https://bitgetlimited.github.io/apidoc/en/mix/#get-history-candle-data
        Limit rule: 20 times/1s (IP)
        Required: symbol, granularity, startTime, endTime
        :return:
        """
        params = {}
        if symbol and granularity and startTime and endTime:
            params["symbol"] = symbol
            params["granularity"] = granularity
            params["startTime"] = startTime
            params["endTime"] = endTime
            params["limit"] = limit
            return self._request_with_params(GET, MIX_MARKET_V1_URL + '/history-candles', params)
        else:
            logger.error("pls check args")
            return False

    def mix_get_symbol_index_price(self, symbol):
        """
        Get Symbol Index Price: https://bitgetlimited.github.io/apidoc/en/mix/#get-symbol-index-price
        Limit rule: 20 times/1s (IP)
        Required: symbol
        :return:
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
            return self._request_with_params(GET, MIX_MARKET_V1_URL + '/index', params)
        else:
            logger.error("pls check args")
            return False

    def mix_get_symbol_next_funding(self, symbol):
        """
        Get Symbol Next Funding Time: https://bitgetlimited.github.io/apidoc/en/mix/#get-symbol-next-funding-time
        Limit rule: 20 times/1s (IP)
        Required: symbol
        :return:
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
            return self._request_with_params(GET, MIX_MARKET_V1_URL + '/funding-time', params)
        else:
            logger.error("pls check args")
            return False

    def mix_get_history_fund_rate(self, symbol, pageSize=20, pageNo=1, nextPage=False):
        """
        Get History Funding Rate: https://bitgetlimited.github.io/apidoc/en/mix/#get-history-funding-rate
        Limit rule: 20 times/1s (IP)
        Required: symbol
        :return:
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
            params["pageSize"] = pageSize
            params["pageNo"] = pageNo
            params["nextPage"] = nextPage
            return self._request_with_params(GET, MIX_MARKET_V1_URL + '/history-fundRate', params)
        else:
            logger.error("pls check args")
            return False

    def mix_get_current_fund_rate(self, symbol):
        """
        Get Current Funding Rate: https://bitgetlimited.github.io/apidoc/en/mix/#get-current-funding-rate
        Limit rule: 20 times/1s (IP)
        Required: symbol
        :return:
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
            return self._request_with_params(GET, MIX_MARKET_V1_URL + '/current-fundRate', params)
        else:
            logger.error("pls check args")
            return False

    def mix_get_open_interest(self, symbol):
        """
        Get Open Interest: https://bitgetlimited.github.io/apidoc/en/mix/#get-open-interest
        Limit rule: 20 times/1s (IP)
        Required: symbol
        :return:
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
            return self._request_with_params(GET, MIX_MARKET_V1_URL + '/open-interest', params)
        else:
            logger.error("pls check args")
            return False

    def mix_get_market_price(self, symbol):
        """
        Get Symbol Mark Price: https://bitgetlimited.github.io/apidoc/en/mix/#get-symbol-mark-price
        Limit rule: 20 times/1s (IP)
        Required: symbol
        :return:
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
            return self._request_with_params(GET, MIX_MARKET_V1_URL + '/mark-price', params)
        else:
            logger.error("pls check args")
            return False

    def mix_get_leverage(self, symbol):
        """
        Get Symbol Leverage: https://bitgetlimited.github.io/apidoc/en/mix/#get-symbol-leverage
        Limit rule: 20/sec (IP)
        Required: symbol.

        """
        params = {}
        if symbol:
            params["symbol"] = symbol
            return self._request_with_params(GET, MIX_MARKET_V1_URL + '/symbol-leverage', params)
        else:
            logger.error("pls check args")
            return False
        

    """ --- the place_order used until now with sl and tp ----- """

    def mix_place_order(self, symbol, productType, marginMode, marginCoin, size, price, side, 
                        orderType, force, clientOid, reduceOnly, presetStopSurplusPrice, presetStopLossPrice):
        params = {}
        params["symbol"] = symbol
        params["productType"] = productType
        params["marginMode"] = marginMode
        params["marginCoin"] = marginCoin
        params["size"] = size
        params["price"] = price
        params["side"] = side
        # params["tradeSide"] = tradeSide   no trade side for one-way-mode position mode 
        params["orderType"] = orderType
        params["force"] = force
        params["clientOid"] = clientOid
        params["reduceOnly"] = reduceOnly
        params["presetStopSurplusPrice"] = presetStopSurplusPrice
        params["presetStopLossPrice"] = presetStopLossPrice
        return self._request_with_params(POST, MIX_ORDER_V2_URL + '/place-order', params)
    
    """ --- MIX-AccountApi """

    def mix_get_account(self, symbol, productType, marginCoin):
        """
        Get Single Account: https://bitgetlimited.github.io/apidoc/en/mix/#get-single-account
        Required: symbol, marginCoin
        :return:
        """
        params = {}
        if symbol and productType and marginCoin:
            params['symbol'] = symbol
            params['productType'] = productType
            params['marginCoin'] = marginCoin
            return self._request_with_params(GET, MIX_ACCOUNT_V2_URL + '/account', params)
        else:
            logger.error("pls check args")
            return False

    def mix_get_sub_account_contract_assets(self, productType):
        """
        Get sub Account Contract Assets: https://bitgetlimited.github.io/apidoc/en/mix/#get-sub-account-contract-assets
        Limit rule: 1 times/10s (uid)
        Required: productType
        :return:
        """
        params = {}
        if productType:
            params['productType'] = productType
            return self._request_with_params(GET, MIX_ACCOUNT_V1_URL + '/sub-account-contract-assets', params)
        else:
            logger.error("pls check args")
            return False

    def mix_get_open_count(self, symbol, marginCoin, openPrice, openAmount, leverage=20):
        """
        Get Open Count: https://bitgetlimited.github.io/apidoc/en/mix/#get-open-count
        Limit rule: 20 times/1s (IP)
        Required: symbol, marginCoin, openPrice, openAmount

        """
        params = {}
        if symbol and marginCoin and openPrice and openAmount:
            params["symbol"] = symbol
            params["marginCoin"] = marginCoin
            params["openPrice"] = openPrice
            params["openAmount"] = openAmount
            params["leverage"] = leverage
            return self._request_with_params(GET, MIX_ACCOUNT_V1_URL + '/open-count', params)
        else:
            logger.error("pls check args")
            return False

    def mix_adjust_margin(self, symbol, marginCoin, amount, holdSide=None):
        """
        Change Margin: https://bitgetlimited.github.io/apidoc/en/mix/#change-margin
        Limit rule: 5 times/1s (uid)
        Required: symbol, marginCoin, marginMode
        """
        params = {}
        if symbol and marginCoin and amount:
            params["symbol"] = symbol
            params["marginCoin"] = marginCoin
            params["marginMode"] = amount
            if holdSide is not None:
                params["holdSide"] = holdSide
            return self._request_with_params(POST, MIX_ACCOUNT_V1_URL + '/setMargin', params)
        else:
            logger.error("pls check args")
            return False

    def mix_adjust_margintype(self, symbol, marginCoin, marginMode):
        """
        Change Margin Mode: https://bitgetlimited.github.io/apidoc/en/mix/#change-margin-mode
        Limit rule: 5 times/1s (uid)
        Required: symbol, marginCoin, marginMode
        """
        params = {}
        if symbol and marginCoin and marginMode:
            params["symbol"] = symbol
            params["marginCoin"] = marginCoin
            params["marginMode"] = marginMode

            return self._request_with_params(POST, MIX_ACCOUNT_V1_URL + '/setMarginMode', params)
        else:
            logger.error("pls check args")
            return False

    def mix_get_accountBill(self, symbol, marginCoin, startTime, endTime, lastEndId='', pageSize=20, next=False):
        """
        Get Account Bill: https://bitgetlimited.github.io/apidoc/en/mix/#get-account-bill
        Limit rule: 10/sec (uid)
        Required: symbol, marginCoin, startTime, endTime
        :return:
        """
        params = {}
        if symbol and marginCoin and startTime and endTime:
            params['symbol'] = symbol
            params['marginCoin'] = marginCoin
            params['startTime'] = startTime
            params['endTime'] = endTime
            params['lastEndId'] = lastEndId
            params['pageSize'] = pageSize
            params['next'] = next
            return self._request_with_params(GET, MIX_ACCOUNT_V1_URL + '/accountBill', params)
        else:
            logger.error("pls check args")
            return False

    def mix_get_accountBusinessBill(self, productType, startTime, endTime, lastEndId='', pageSize=20, next=False):
        """
        Get Business Account Bill: https://bitgetlimited.github.io/apidoc/en/mix/#get-business-account-bill
        Limit rule: 5/sec (uid)
        Required: productType, startTime, endTime
        :return:
        """
        params = {}
        if productType and startTime and endTime:
            params['productType'] = productType
            params['startTime'] = startTime
            params['endTime'] = endTime
            params['lastEndId'] = lastEndId
            params['pageSize'] = pageSize
            params['next'] = next
            return self._request_with_params(GET, MIX_ACCOUNT_V1_URL + '/accountBusinessBill', params)
        else:
            logger.error("pls check args")
            return False

    """ --- MIX-tradeApi """

    def mix_reversal(self, symbol, marginCoin, side, orderType,
                     size=None, clientOrderId=None, timeInForceValue='normal', reverse=False):
        """
        Reversal: https://bitgetlimited.github.io/apidoc/en/mix/#reversal
        Limit rule: 10 times/1s (uid), counted together with placeOrder
        Reversal share the same interface with Place order.

        Required: symbol, marginCoin, side, orderType

        :return:
        """
        params = {}
        if symbol and marginCoin and side and orderType:
            params["symbol"] = symbol
            params["marginCoin"] = marginCoin
            params["side"] = side
            params["orderType"] = orderType
            if size is not None:
                params["size"] = size
            if clientOrderId is not None:
                params["clientOid"] = clientOrderId
            params["timeInForceValue"] = timeInForceValue
            params["reverse"] = reverse
            return self._request_with_params(POST, MIX_ORDER_V1_URL + '/placeOrder', params)
        else:
            logger.error("pls check args")
            return False

    def mix_batch_orders(self, symbol, marginCoin, orderDataList):
        """
        Batch Order: https://bitgetlimited.github.io/apidoc/en/mix/#batch-order
        Limit rule: 10 times/1s (uid)
        Trader Limit rule: 1 times/1s (uid)
        Required: symbol, marginCoin, orderDataList
        """
        params = {}
        if symbol and marginCoin and orderDataList:
            params["symbol"] = symbol
            params["marginCoin"] = marginCoin
            params["orderDataList"] = orderDataList
            return self._request_with_params(POST, MIX_ORDER_V1_URL + '/batch-orders', params)
        else:
            logger.error("pls check args")
            return False

    def mix_batch_cancel_orders(self, symbol, marginCoin, orderId: list = None, clientOid: list = None):
        """ Batch Cancel Order
        https://bitgetlimited.github.io/apidoc/en/mix/#batch-cancel-order
        Limit rule: 10 times/1s (uid)
        Required: symbol, marginCoin, orderIds or clientOids
        - Order Id list, int64 in string format, 'orderIds' or 'clientOids' must have one
        - Client Order Id list, 'orderIds' or 'clientOids' must have one
        """
        params = {}
        if symbol and marginCoin and orderIds:
            params["symbol"] = symbol
            params["marginCoin"] = marginCoin
            if orderId is not None:
                params["orderId"] = orderId
            elif clientOid is not None:
                params["clientOid"] = clientOid
            return self._request_with_params(POST, MIX_ORDER_V1_URL + '/cancel-batch-orders', params)
        else:
            logger.error("pls check args")
            return False

    def mix_cancel_all_orders(self, productType, marginCoin):
        """ Cancel All Order
        https://bitgetlimited.github.io/apidoc/en/mix/#cancel-all-order
        Limit rule: 10 times/1s (uid)

        Required: productType, marginCoin
        """
        params = {}
        if productType and marginCoin:
            params["productType"] = productType
            params["marginCoin"] = marginCoin
            return self._request_with_params(POST, MIX_ORDER_V1_URL + '/cancel-all-orders', params)
        else:
            logger.error("pls check args")
            return False

    def mix_get_open_order(self, symbol):
        """
        Get the current order: https://bitgetlimited.github.io/apidoc/en/mix/#get-open-order
        Required: symbol
        :return:
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
            return self._request_with_params(GET, MIX_ORDER_V2_URL + '/current', params)
        else:
            logger.error("pls check args")
            return False

    def mix_get_all_open_orders(self, productType, marginCoin=None):
        """
        Get All Open Order:::https://bitgetlimited.github.io/apidoc/en/mix/#get-all-open-order
        Required: productType
        :return:
        """
        params = {}
        if productType:
            params["productType"] = productType
            if marginCoin is not None:
                params["marginCoin"] = marginCoin
            return self._request_with_params(GET, MIX_ORDER_V1_URL + '/marginCoinCurrent', params)
        else:
            logger.error("pls check args")
            return False

    def mix_get_history_orders(self, symbol, startTime, endTime, pageSize, lastEndId='', isPre=False):
        """
        Get History Orders: https://bitgetlimited.github.io/apidoc/en/mix/#get-history-orders

        Limit rule: 20 times/2s (uid)

        Required: symbol, startTime, endTime, pageSize

        :param symbol: Symbol Id (Must be capitalized)
        :type symbol: str
        :param startTime: Start time, milliseconds
        :type startTime: str
        :param endTime: End time, milliseconds
        :type endTime: str
        :param pageSize: page Size
        :type pageSize: str
        :param lastEndId: last end Id of last query
        :type lastEndId: str
        :param isPre: true: order by order Id asc; default false
        :type isPre: Boolean
        :return:
        """
        params = {}
        if symbol and startTime and endTime and pageSize:
            params["symbol"] = symbol
            params["startTime"] = startTime
            params["endTime"] = endTime
            params["pageSize"] = pageSize
            params["lastEndId"] = lastEndId
            params["isPre"] = isPre
            return self._request_with_params(GET, MIX_ORDER_V1_URL + '/history', params)
        else:
            logger.error("pls check args")
            return False

    def mix_get_productType_history_orders(self, productType, startTime, endTime, pageSize, lastEndId='', isPre=False):
        """
        Get ProductType History Orders: https://bitgetlimited.github.io/apidoc/en/mix/#get-producttype-history-orders

        Limit rule: 5/1s (uid)

        Required: productType, startTime, endTime, pageSize

        :param productType
        :type productType: str
        :param startTime: Start time, milliseconds
        :type startTime: str
        :param endTime: End time, milliseconds
        :type endTime: str
        :param pageSize: page Size
        :type pageSize: str
        :param lastEndId: last end Id of last query
        :type lastEndId: str
        :param isPre: true: order by order Id asc; default false
        :type isPre: Boolean
        :return:
        """
        params = {}
        if productType and startTime and endTime and pageSize:
            params["productType"] = productType
            params["startTime"] = startTime
            params["endTime"] = endTime
            params["pageSize"] = pageSize
            params["lastEndId"] = lastEndId
            params["isPre"] = isPre
            return self._request_with_params(GET, MIX_ORDER_V1_URL + '/historyProductType', params)
        else:
            logger.error("pls check args")
            return False

    def mix_get_order_fill_detail(self, symbol, orderId=None, startTime=None, endTime=None, lastEndId=None):
        """
        Get Order fill detail: https://bitgetlimited.github.io/apidoc/en/mix/#get-order-fill-detail
        Limit rule: 20 times/2s (uid)
        Required: symbol
        :return:
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
            if orderId is not None:
                params["orderId"] = orderId
            if startTime is not None:
                params["startTime"] = startTime
            if endTime is not None:
                params["endTime"] = endTime
            if lastEndId is not None:
                params["lastEndId"] = lastEndId
            return self._request_with_params(GET, MIX_ORDER_V1_URL + '/fills', params)
        else:
            logger.error("pls check args")
            return False

    def mix_get_productType_order_fill_detail(self, productType, startTime=None, endTime=None, lastEndId=None):
        """
        Get ProductType Order fill detail: https://bitgetlimited.github.io/apidoc/en/mix/#get-producttype-order-fill-detail
        Limit rule: 10 times/1s (uid)
        Required: productType
        :return:
        """
        params = {}
        if productType:
            params["productType"] = productType
            if startTime is not None:
                params["startTime"] = startTime
            if endTime is not None:
                params["endTime"] = endTime
            if lastEndId is not None:
                params["lastEndId"] = lastEndId
            return self._request_with_params(GET, MIX_ORDER_V1_URL + '/allFills', params)
        else:
            logger.error("pls check args")
            return False

    def mix_modify_plan_order_tpsl(self, symbol, marginCoin, orderId
                                   , presetTakeProfitPrice=None, presetStopLossPrice=None):
        """
        Modify Plan Order TPSL: https://bitgetlimited.github.io/apidoc/en/mix/#modify-plan-order-tpsl
        Limit rule: 10 times/1s (uid)

        Required: symbol, marginCoin, orderId
        :return:
        """
        params = {}
        if symbol and marginCoin and orderId:
            params["symbol"] = symbol
            params["marginCoin"] = marginCoin
            params["orderId"] = orderId
            if presetTakeProfitPrice is not None:
                params["presetTakeProfitPrice"] = presetTakeProfitPrice
            if presetStopLossPrice is not None:
                params["presetStopLossPrice"] = presetStopLossPrice
            return self._request_with_params(POST, MIX_PLAN_V1_URL + '/modifyPlanPreset', params)
        else:
            logger.error("pls check args")
            return False

    def mix_place_stop_order(self, symbol, marginCoin, triggerPrice, planType, holdSide,
                             triggerType='fill_price', size=None, rangeRate=None):
        """
        Place Stop Order: https://bitgetlimited.github.io/apidoc/en/mix/#place-stop-order
        Limit rule: 10 times/1s (uid)

        Required: symbol, marginCoin, triggerPrice, planType, holdSide
        :return:
        """
        params = {}
        if symbol and marginCoin and planType and holdSide and triggerPrice:
            params["symbol"] = symbol
            params["marginCoin"] = marginCoin
            params["planType"] = planType
            params["holdSide"] = holdSide
            params["triggerPrice"] = triggerPrice
            params["triggerType"] = triggerType
            if size is not None:
                params["size"] = size
            if rangeRate is not None:
                params["rangeRate"] = rangeRate
            return self._request_with_params(POST, MIX_PLAN_V1_URL + '/placeTPSL', params)
        else:
            logger.error("pls check args")
            return False

    def mix_place_trailing_stop_order(self, symbol, marginCoin, triggerPrice, side,
                                      triggerType=None, size=None, rangeRate=None):
        """
        Place Trailing Stop Order: https://bitgetlimited.github.io/apidoc/en/mix/#place-trailing-stop-order
        Limit rule: 10 times/1s (uid)

        Required: symbol, marginCoin, triggerPrice, side
        :return:
        """
        params = {}
        if symbol and marginCoin and side and triggerPrice:
            params["symbol"] = symbol
            params["marginCoin"] = marginCoin
            params["side"] = side
            params["triggerPrice"] = triggerPrice
            if triggerType is not None:
                params["triggerType"] = triggerType
            if size is not None:
                params["size"] = size
            if rangeRate is not None:
                params["rangeRate"] = rangeRate
            return self._request_with_params(POST, MIX_PLAN_V1_URL + '/placeTrailStop', params)
        else:
            logger.error("pls check args")
            return False

    def mix_place_PositionsTPSL(self, symbol, marginCoin, planType, triggerPrice, triggerType, holdSide=None):
        """
        Place Position TPSL: https://bitgetlimited.github.io/apidoc/en/mix/#place-position-tpsl
        Limit rule: 10 times/1s (uid)
        When the position take profit and stop loss are triggered, the full amount of the position will be entrusted at the market price by default.
        Required: marginCoin, symbol, planType, triggerPrice, triggerType
        triggertype: fill_price, market_price
        """
        params = {}
        if marginCoin and symbol and planType and triggerPrice and triggerType:
            params["symbol"] = symbol
            params["marginCoin"] = marginCoin
            params["planType"] = planType
            params["triggerPrice"] = triggerPrice
            params["triggerType"] = triggerType
            if holdSide is not None:
                params["holdSide"] = holdSide
            return self._request_with_params(POST, MIX_PLAN_V1_URL + '/placePositionsTPSL', params)
        else:
            logger.error("pls check args")
            return False

    def mix_cancel_all_trigger_orders(self, productType, planType):
        """
        Cancel All trigger Order (TPSL): https://bitgetlimited.github.io/apidoc/en/mix/#cancel-all-trigger-order-tpsl
        Required: productType, planType
        Limit rule: 10 times/1s (uid)
        """
        params = {}
        if productType and planType:
            params["productType"] = productType
            params["planType"] = planType
            return self._request_with_params(POST, MIX_PLAN_V1_URL + '/cancelAllPlan', params)
        else:
            logger.error("pls check args")
            return False

    def mix_get_plan_order_tpsl(self, symbol=None, productType=None, isPlan=None):
        """
        Get Plan Order (TPSL) List:https://bitgetlimited.github.io/apidoc/en/mix/#get-plan-order-tpsl-list
        can get orders without symbol parameter.
        But either or both of symbol and productType have to be set as request parameters.
        Required: symbol or productType
        isPlan: plan/profit_loss
        Limit rule: 10 times/1s (uid)
        :return:
        """
        params = {}
        if symbol is not None or productType is not None:
            if symbol is not None:
                params["symbol"] = symbol
            if productType is not None:
                params["productType"] = productType
            if isPlan is not None:
                params["isPlan"] = isPlan
            return self._request_with_params(GET, MIX_PLAN_V1_URL + '/currentPlan', params)
        else:
            logger.error("pls check args")
            return False

    def mix_get_history_plan_orders(self, symbol, startTime, endTime, pageSize=100, lastEndId=None, isPre=False, isPlan=None):
        """
        Get History Plan Orders (TPSL): https://bitgetlimited.github.io/apidoc/en/mix/#get-history-plan-orders-tpsl
        Limit rule: 10 times/1s (uid)
        Required: symbol, startTime, endTime
        :return:
        """
        params = {}
        if symbol and startTime and endTime:
            params["symbol"] = symbol
            params["startTime"] = startTime
            params["endTime"] = endTime
            params["pageSize"] = pageSize
            params["isPre"] = isPre
            if lastEndId is not None:
                params["lastEndId"] = lastEndId
            if isPlan is not None:
                params["isPlan"] = isPlan
            return self._request_with_params(GET, MIX_PLAN_V1_URL + '/historyPlan', params)
        else:
            logger.error("pls check args")
            return False

