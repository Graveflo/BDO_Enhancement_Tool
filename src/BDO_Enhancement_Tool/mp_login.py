#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
from typing import Tuple, Union
from PyQt5.QtWidgets import QSplitter
from PyQt5 import QtWidgets
from PyQt5 import QtCore
import urllib3
from urllib.parse import urlencode
import json
import time

from .Core.ItemStore import BasePriceUpdator
from .utilities import string_between


#GetWorldMarketSubList = '/Home/GetWorldMarketSubList'
GetWorldMarketSubList_body = '__RequestVerificationToken={}&mainKey={}&usingCleint=0'
GetWorldMarketSubList = '/Trademarket/GetWorldMarketSubList'


class CentralMarketPriceUpdator(BasePriceUpdator):
    def __init__(self, connection):
        self.connection = connection

    def set_connection(self, connection):
        self.connection = connection

    def get_update(self, id: str) -> Tuple[float, Union[None, list]]:
        raise NotImplementedError()

    def __del__(self):
        self.connection.close()


class CentralMarketPOSTPriceUpdator(CentralMarketPriceUpdator):
    def get_update(self, id: str) -> Tuple[float, Union[None, list]]:
        r = self.connection.request('POST', GetWorldMarketSubList,
                         body='{"keyType": 0, "mainKey":'+id+'}',
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


class CentralMarketOldPriceUpdator(CentralMarketPriceUpdator):
    def __init__(self, profile, connection, cookies, token):
        super(CentralMarketOldPriceUpdator, self).__init__(connection)
        self.profile = profile
        self.cookies = cookies
        self.GetWorldMarketSubList_token = token

    def get_update(self, id: str) -> Tuple[float, Union[None, list]]:
        r = self.connection.request('POST', GetWorldMarketSubList,
                         body=GetWorldMarketSubList_body.format(self.GetWorldMarketSubList_token, int(id)).encode(
                             'utf-8'),
                         headers={
                             'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                             'Cookie': self.cookies,
                             'User-Agent': self.profile.httpUserAgent()
                         })
        r_obj = json.loads(r.data.decode('utf-8'))
        list = r_obj['detailList']
        expires = time.time() + 1800
        if len(list) > 0:
            return expires, [x['pricePerOne'] for x in r_obj['detailList']]
        else:
            return expires, None
