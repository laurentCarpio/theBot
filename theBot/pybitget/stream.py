#!/usr/bin/python
import json
import math
import threading
import time
import traceback
from threading import Timer
from zlib import crc32
import hmac
import base64
import websocket
from typing import Optional
from pybitget.enums import GET, REQUEST_PATH, CONTRACT_WS_PUBLIC_URL
from pybitget import logger

WS_OP_LOGIN = 'login'
WS_OP_SUBSCRIBE = "subscribe"
WS_OP_UNSUBSCRIBE = "unsubscribe"


def handle(message):
    logger.info(message)

def handel_error(message):
    logger.error(message)

def create_sign(message, secret_key):
    mac = hmac.new(bytes(secret_key, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
    d = mac.digest()
    return str(base64.b64encode(d), 'utf8')

def pre_hash(timestamp, method, request_path):
    return str(timestamp) + str.upper(method) + str(request_path)

def build_subscribe_req(instType, channel, third_key, third_value):
    if third_key == 'coin':
        return SubscribeReq(instType, channel, coin=third_value)
    elif third_key == 'instId':
        return SubscribeReq(instType, channel, third_value)
    else:
        raise ValueError("Unsupported third_key")

class BitgetWsClient:
    def __init__(self, api_key=None, api_secret=None, passphrase=None, ws_url=None, verbose=False):
        self.__api_key = api_key
        self.__api_secret_key = api_secret
        self.__passphrase = passphrase
        self.__connection = False
        self.__login_status = False
        self.__reconnect_status = False
        self.__all_suribe = set()
        self.__listener = handle
        self.__error_listener = handel_error
        self.__scribe_map = {}
        self.__allbooks_map = {}
        self.__ws_client = None
        self.last_pong_time = time.time()

        self.STREAM_URL = ws_url or CONTRACT_WS_PUBLIC_URL
        self.verbose = verbose

    def build(self):
        self.__ws_client = self.__init_client()
        threading.Thread(target=self.connect).start()

        while not self.has_connect():
            logger.info("start connecting...%s" % self.STREAM_URL)
            time.sleep(1)

        if self.__api_key and self.__api_secret_key and self.__passphrase:
            self.__login()

        self.__keep_connected(25)
        self.schedule_daily_reconnect()
        return self

    def listener(self, listener):
        self.__listener = listener
        return self

    def error_listener(self, error_listener):
        self.__error_listener = error_listener
        return self

    def has_connect(self):
        return self.__connection

    def __init_client(self):
        return websocket.WebSocketApp(
            self.STREAM_URL,
            on_open=self.__on_open,
            on_message=self.__on_message,
            on_error=self.__on_error,
            on_close=self.__on_close
        )

    def __login(self, retries=3):
        for attempt in range(retries):
            timestamp = int(round(time.time()))
            sign = create_sign(pre_hash(timestamp, GET, REQUEST_PATH), self.__api_secret_key)
            ws_login_req = WsLoginReq(self.__api_key, self.__passphrase, str(timestamp), sign)
            self.send_message(WS_OP_LOGIN, [ws_login_req])
            logger.info("logging in... attempt %d", attempt + 1)
            time.sleep(3)
            if self.__login_status:
                return
        logger.error("Login failed after %d attempts", retries)

    def connect(self):
        try:
            self.__ws_client.run_forever(ping_timeout=10)
        except Exception as ex:
            logger.error(ex)

    def __keep_connected(self, interval):
        try:
            if time.time() - self.last_pong_time > 35:
                logger.warning("No pong received in 35 seconds. Reconnecting...")
                self.__close()
                self.__re_connect()
                return
            Timer(interval, self.__keep_connected, (interval,)).start()
            self.__ws_client.send("ping")
        except Exception as ex:
            logger.error(ex)

    def schedule_daily_reconnect(self):
        Timer(60 * 60 * 23.5, self.__daily_reconnect).start()

    def __daily_reconnect(self):
        logger.info("Performing scheduled daily reconnect.")
        self.__close()
        self.__re_connect()

    def send_message(self, op, args):
        message = json.dumps(BaseWsReq(op, args), default=lambda o: o.__dict__)
        if self.verbose:
            logger.debug(message)
        time.sleep(0.1)
        self.__ws_client.send(message)

    def subscribe(self, channels, listener=None):
        if listener:
            for ch in channels:
                ch.instType = str(ch.instType)
                self.__scribe_map[ch] = listener

        for ch in channels:
            self.__all_suribe.add(ch)

        self.send_message(WS_OP_SUBSCRIBE, channels)

    def unsubscribe(self, channels):
        for ch in channels:
            self.__scribe_map.pop(ch, None)
            self.__all_suribe.discard(ch)
        self.send_message(WS_OP_UNSUBSCRIBE, channels)

    def __on_open(self, ws):
        logger.info('connection is success....')
        self.__connection = True
        self.__reconnect_status = False

    def __on_message(self, ws, message):
        if message == 'pong':
            self.last_pong_time = time.time()
            if self.verbose:
                logger.info("Received pong.")
            return

        json_obj = json.loads(message)
        if "code" in json_obj and json_obj.get("code") != 0:
            self.__error_listener(message)
            return

        if json_obj.get("event") == "login":
            self.__login_status = True
            return

        if "data" in json_obj and not self.__check_sum(json_obj):
            return

        listener = self.get_listener(json_obj)
        if listener:
            listener(message)
        else:
            self.__listener(message)

    def get_listener(self, json_obj):
        try:
            if 'arg' in json_obj:
                subscribe_req = json.loads(str(json_obj['arg']).replace("'", '"'), object_hook=self.__dict_to_subscribe_req)
                return self.__scribe_map.get(subscribe_req)
        except Exception as e:
            logger.error("%s %s " % (json_obj.get('arg'), e))
        return None

    def __on_error(self, ws, msg):
        logger.error(msg)
        self.__close()
        if not self.__reconnect_status:
            self.__re_connect()

    def __on_close(self, ws, code, msg):
        logger.info(f"WebSocket closed. Code: {code}, Message: {msg}")
        self.__close()
        if not self.__reconnect_status:
            self.__re_connect()

    def __re_connect(self):
        self.__reconnect_status = True
        logger.info("start reconnection ...")
        self.build()
        for ch in self.__all_suribe:
            self.subscribe([ch])

    def __close(self):
        self.__login_status = False
        self.__connection = False
        self.__ws_client.close()

    def __check_sum(self, json_obj):
        try:
            if json_obj.get("arg", {}).get("channel") != "books":
                return True
            arg = json_obj["arg"]
            data = json_obj["data"]
            action = json_obj.get("action")
            subscribe_req = self.__dict_to_subscribe_req(arg)
            books_info = [BooksInfo(d['asks'], d['bids'], d['checksum']) for d in data][0]

            if action == "snapshot":
                self.__allbooks_map[subscribe_req] = books_info
                return True
            elif action == "update":
                all_books = self.__allbooks_map.get(subscribe_req)
                if not all_books:
                    return False
                all_books.merge(books_info)
                if not all_books.check_sum(books_info.checksum):
                    self.unsubscribe([subscribe_req])
                    self.subscribe([subscribe_req])
                    return False
                self.__allbooks_map[subscribe_req] = all_books
        except Exception as e:
            logger.error(traceback.format_exc())
        return True

    def __dict_to_subscribe_req(self, a_dict):
        if 'coin' in a_dict:
            return SubscribeReq(a_dict['instType'], a_dict['channel'], coin=a_dict['coin'])
        elif 'instId' in a_dict:
            return SubscribeReq(a_dict['instType'], a_dict['channel'], a_dict['instId'])
        else:
            raise ValueError("a_dict must contain either 'coin' or 'instId'")

class BooksInfo:
    def __init__(self, asks, bids, checksum):
        self.asks = asks
        self.bids = bids
        self.checksum = checksum

    def merge(self, book_info):
        self.asks = self.innerMerge(self.asks, book_info.asks, False)
        self.bids = self.innerMerge(self.bids, book_info.bids, True)
        return self

    def innerMerge(self, all_list, update_list, is_reverse):
        price_and_value = {v[0]: v for v in all_list}
        for v in update_list:
            if v[1] == "0":
                price_and_value.pop(v[0], None)
            else:
                price_and_value[v[0]] = v
        return sorted(price_and_value.values(), key=lambda x: x[0], reverse=is_reverse)

    def check_sum(self, new_check_sum):
        try:
            crc32str = ''
            for x in range(25):
                if x < len(self.bids):
                    crc32str += f"{self.bids[x][0]}:{self.bids[x][1]}:"
                if x < len(self.asks):
                    crc32str += f"{self.asks[x][0]}:{self.asks[x][1]}:"
            crc32str = crc32str[:-1]
            merge_num = crc32(bytes(crc32str, encoding="utf8"))
            return self.__signed_int(merge_num) == new_check_sum
        except Exception:
            return False

    def __signed_int(self, checknum):
        int_max = 2**31 - 1
        return checknum - int_max * 2 - 2 if checknum > int_max else checknum

class SubscribeReq:
    def __init__(self, instType, channel, *args, **kwargs):
        self.instType = instType
        self.channel = channel
        if args:
            self.instId = args[0]
            self.coin = None
        elif 'coin' in kwargs:
            self.coin = kwargs['coin']
            self.instId = None
        else:
            raise ValueError("Either instId or coin must be provided")

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __hash__(self):
        identifier = ('instId', self.instId) if self.instId is not None else ('coin', self.coin)
        return hash((self.instType, self.channel, identifier))

class BaseWsReq:
    def __init__(self, op, args):
        self.op = op
        self.args = args

class WsLoginReq:
    def __init__(self, api_key, passphrase, timestamp, sign):
        self.api_key = api_key
        self.passphrase = passphrase
        self.timestamp = timestamp
        self.sign = sign
