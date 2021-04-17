#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import os
from typing import Tuple, Union

from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo
from PyQt5.QtWebEngineWidgets import QWebEngineSettings
from PyQt5.QtWidgets import QSplitter

from .common import relative_path_convert, BasePriceUpdator
from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import QtWebEngineWidgets, QtWebEngineCore
from .utilities import sanitizeFileName, string_between
import urllib3
from urllib.parse import urlencode
import json
import time

GetWorldMarketSubList = '/Home/GetWorldMarketSubList'
GetWorldMarketSubList_body = '__RequestVerificationToken={}&mainKey={}&usingCleint=0'


class CentralMarketPriceUpdator(BasePriceUpdator):
    def __init__(self, profile, connection, cookies, token):
        self.profile = profile
        self.connection = connection
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

    def __del__(self):
        self.connection.close()


class MPBrowser(QtWebEngineWidgets.QWebEngineView):
    def createWindow(self, type):
        return super(MPBrowser, self).createWindow(type)


class suppressPage(QtWebEngineWidgets.QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message: str, lineNumber: int, sourceID: str) -> None:
        return

    def load(self, url: QtCore.QUrl) -> None:
        super(suppressPage, self).load(url)


class DlgMPLogin(QtWidgets.QDialog):
    sig_Market_Ready = QtCore.pyqtSignal(object, name='')

    def __init__(self, parent):
        super(DlgMPLogin, self).__init__(parent)

        self.resize(QtCore.QSize(365, 580))


        self.web = QtWebEngineWidgets.QWebEngineView()
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        #self.splitter = QSplitter(QtCore.Qt.Horizontal, self)
        self.verticalLayout.addWidget(self.web)

        self.verticalLayout.setObjectName("verticalLayout")
        #self.splitter.addWidget(self.web)
        #self.verticalLayout.addWidget(self.web)
        #self.web3 = MPBrowser()
        #self.splitter.addWidget(self.web3)
        #self.verticalLayout.addWidget(self.web3)

        #page.loadFinished.connect(self.web_loadFinished)

        #self.profile = self.page.profile()
        self.host_local = 'na-trade.naeu.playblackdesert.com'

        self.profile = QtWebEngineWidgets.QWebEngineProfile('chrome-web-profile', self.web)
        #self.profile.clearAllVisitedLinks()
        #self.profile.clearHttpCache()
        #self.profile.cookieStore().deleteAllCookies()
        #self.profile.setHttpAcceptLanguage('en-US')
        #self.profile.setHttpCacheType(self.profile.NoCache)
        #self.interceptor = interceptor()
        #self.profile.setRequestInterceptor(self.interceptor)
        self.profile.setPersistentCookiesPolicy(QtWebEngineWidgets.QWebEngineProfile.NoPersistentCookies)
        self.profile.setHttpUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36')
        self.cookie_store = self.profile.cookieStore()

        self.cookie__RequestVerificationToken = None
        self.frmGetItemSellBuyInfo_token = None
        self.cooks = {}

        page = suppressPage(self.profile, self.web)
        self.page = page


        self.cookie_store.cookieAdded.connect(self.onCookieAdded)
        #self.web.loadFinished.connect(self.web_loadFinished)


        #self.page.settings().setAttribute(QWebEngineSettings.AllowRunningInsecureContent, True)
        #self.page.settings().setAttribute(QWebEngineSettings.PluginsEnabled, False)
        #self.page.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        #self.page.settings().setAttribute(QWebEngineSettings.HyperlinkAuditingEnabled, True)
        self.web.setPage(page)
        self.update_page = True
        self.price_updator = None
        self.connection_pool = None

        # naeu.Session=
        # TradeAuth_Session=
        # __RequestVerificationToken=

    def set_domain(self, domain):
        self.host_local = domain
        if self.update_page is False:
            self.web.load(QtCore.QUrl("https://{}/intro/".format(self.host_local)))

    def showEvent(self, a0) -> None:
        super(DlgMPLogin, self).showEvent(a0)
        # self.web3.load(QtCore.QUrl('http://localhost:4867'))
        if self.update_page:
            self.web.load(QtCore.QUrl("https://{}/intro/".format(self.host_local)))
            self.update_page = False

    def onCookieAdded(self, cooke):
        name = cooke.name().data().decode('utf-8')
        value = cooke.value().data().decode('utf-8')
        if cooke.domain().find('.playblackdesert') > -1:
            self.cooks[name] = value
            if name == '__RequestVerificationToken':
                self.web_loadFinished()
            #print('{} - {} - {}'.format(cooke.name(), cooke.value(), cooke.domain()))

    def web_loadFinished(self):
        page = self.web.page()
        if self.connection_pool is not None:  # TODO: What happens to price updator when this dies?
            self.connection_pool.close()
        self.connection_pool = urllib3.HTTPSConnectionPool(self.host_local, maxsize=1, block=True)
        agent = self.profile.httpUserAgent()
        r = self.connection_pool.request('GET', '/Home/list/hot',
                                    headers={
                                        'Cookie': urlencode(self.cooks).replace('&', '; '),
                                        'User-Agent': agent
                                    })
        self.hot_load(r.data.decode('utf-8'))

    def hot_load(self, txt):
        dat = string_between(txt, '<form id="frmGetItemSellBuyInfo">', '</form>').strip()
        sdat = string_between(dat, 'value="', '"')
        self.frmGetItemSellBuyInfo_token = ''.join(sdat.split())
        dat = string_between(txt, '<form id="frmGetWorldMarketSubList"', '</form>').strip()
        sdat = string_between(dat, 'value="', '"')
        self.GetWorldMarketSubList_token = ''.join(sdat.split())
        coks = urlencode(self.cooks).replace('&', '; ')

        self.price_updator = CentralMarketPriceUpdator(self.profile, self.connection_pool, coks, self.GetWorldMarketSubList_token)
        self.sig_Market_Ready.emit(self.price_updator)
