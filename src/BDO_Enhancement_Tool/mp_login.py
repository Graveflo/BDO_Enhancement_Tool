#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑  ❧
"""
from typing import Tuple, Union
from PyQt6.QtWidgets import QSplitter
from PyQt6 import QtWidgets
from PyQt6 import QtCore
import urllib3
from urllib.parse import urlencode, ParseResult
import json
import time

from .Core.ItemStore import BasePriceUpdator
from .utilities import string_between
from urllib3 import HTTPSConnectionPool

#GetWorldMarketSubList = '/Home/GetWorldMarketSubList'
GetWorldMarketSubList_body = '__RequestVerificationToken={}&mainKey={}&usingCleint=0'
GetWorldMarketSubList = '/Trademarket/GetWorldMarketSubList'
ARSHA_GetWorldMarketSubList = '/GetWorldMarketSubList?id={}&lang=en'

class CentralMarketPriceUpdator(BasePriceUpdator):
    def __init__(self, connection, url:ParseResult):
        self.connection:HTTPSConnectionPool = connection
        self.url = url

    def set_connection(self, connection):
        self.connection = connection

    def get_update(self, id: str) -> Tuple[float, Union[None, list]]:
        raise NotImplementedError()

    def __del__(self):
        self.connection.close()


class CentralMarketPOSTPriceUpdator(CentralMarketPriceUpdator):
    def get_update(self, id: str) -> Tuple[float, Union[None, list]]:
        r = self.connection.request('POST', GetWorldMarketSubList,
                         body='{"keyType": 0, "mainKey":'+str(id)+'}', retries=False, timeout=5,
                         headers={
                             'Content-Type': 'application/json',
                             'User-Agent': 'BlackDesert'
                         })
        print('Updating price of {}'.format(id))
        r_obj = json.loads(r.data.decode('utf-8'))
        expires = time.time() + 1800
        if r_obj['resultCode'] == 0:
            result_msg = r_obj['resultMsg']
            if result_msg == '0':
                return float('inf'), None
            if result_msg.endswith('|'):
                result_msg = result_msg[:-1]
            parts = result_msg.split('|')
            base_prices = [float(x.split('-')[3]) for x in parts]
            return expires, base_prices
        else:
            return expires, None


class CentralMarketARSHATPriceUpdator(CentralMarketPriceUpdator):
    def get_update(self, id: str) -> Tuple[float, Union[None, list]]:
        r = self.connection.request('GET', self.url.path+ARSHA_GetWorldMarketSubList.format(id),  retries=False, timeout=5)
        print('Updating price of {}'.format(id))
        r_obj = json.loads(r.data.decode('utf-8'))
        if r_obj[0]['basePrice'] is None:
            return float('inf'), None
        expires = time.time() + 1800
        return expires, [sub_l['basePrice'] for sub_l in r_obj]


