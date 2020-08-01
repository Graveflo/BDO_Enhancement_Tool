#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import os
from .common import relative_path_convert
from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import QtWebEngineWidgets, QtWebEngineCore
from .utilities import sanitizeFileName, string_between
import urllib3
from urllib.parse import urlencode
from urllib import request
import json

GetWorldMarketSubList = '/Home/GetWorldMarketSubList'
GetWorldMarketSubList_body = '__RequestVerificationToken={}&mainKey={}&usingCleint=0'


class CentralMarketPriceUpdator(object):
    def __init__(self, profile, connection, cookies, token):
        self.profile = profile
        self.connection = connection
        self.cookies = cookies
        self.GetWorldMarketSubList_token = token

    def get_update(self, id: str) -> list:
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
        if len(list) > 0:
            return [x['pricePerOne'] for x in r_obj['detailList']]
        else:
            return None

    def __del__(self):
        self.connection.close()


class MPBrowser(QtWebEngineWidgets.QWebEngineView):
    pass


class suppressPage(QtWebEngineWidgets.QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message: str, lineNumber: int, sourceID: str) -> None:
        return


class DlgMPLogin(QtWidgets.QDialog):
    sig_Market_Ready = QtCore.pyqtSignal(object, name='')

    def __init__(self, parent):
        super(DlgMPLogin, self).__init__(parent)

        self.resize(QtCore.QSize(365, 580))


        self.web = MPBrowser()
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.addWidget(self.web)

        self.profile = QtWebEngineWidgets.QWebEngineProfile('cookies', self.web)
        self.cookie_store = self.profile.cookieStore()

        self.cookie__RequestVerificationToken = None
        self.frmGetItemSellBuyInfo_token = None
        self.host_local = None
        self.cooks = {}


        self.cookie_store.cookieAdded.connect(self.onCookieAdded)
        self.web.loadFinished.connect(self.web_loadFinished)

        page = suppressPage(self.profile, self.web)
        self.web.setPage(page)
        self.update_page = True
        self.price_updator = None
        self.this_connection = None

    def showEvent(self, a0) -> None:
        super(DlgMPLogin, self).showEvent(a0)
        if self.update_page:
            self.web.setUrl(QtCore.QUrl("https://market.blackdesertonline.com/"))

    def onCookieAdded(self, cooke):
        name = cooke.name().data().decode('utf-8')
        value = cooke.value().data().decode('utf-8')
        self.cooks[name] = value
        #print('{}: {}'.format(name, cooke.value()))
        if name == '__RequestVerificationToken':
            self.set_cookie__RequestVerificationToken(value)

    def set_cookie__RequestVerificationToken(self, token):
        self.cookie__RequestVerificationToken = token

    def web_loadFinished(self):
        page = self.web.page()
        loc = page.url().path()
        if loc == '/Home/list/hot':
            self.host_local = 'https://' + page.url().host()
            page.toHtml(self.hot_load)

    def hot_load(self, txt):
        dat = string_between(txt, '<form id="frmGetItemSellBuyInfo">', '</form>').strip()
        sdat = string_between(dat, 'value="', '"')
        self.frmGetItemSellBuyInfo_token = ''.join(sdat.split())
        dat = string_between(txt, '<form id="frmGetWorldMarketSubList"', '</form>').strip()
        sdat = string_between(dat, 'value="', '"')
        self.GetWorldMarketSubList_token = ''.join(sdat.split())
        if self.this_connection is not None:
            self.this_connection.close()
        conn = urllib3.connection_from_url(self.host_local)
        self.this_connection = conn
        coks = urlencode(self.cooks).replace('&', '; ')

        self.price_updator = CentralMarketPriceUpdator(self.profile, conn, coks, self.GetWorldMarketSubList_token)
        self.sig_Market_Ready.emit(self.price_updator)
