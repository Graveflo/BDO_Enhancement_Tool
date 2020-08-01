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


class MPBrowser(QtWebEngineWidgets.QWebEngineView):
    pass

class DlgMPLogin(QtWidgets.QDialog):
    GetWorldMarketSubList = '/Home/GetWorldMarketSubList'
    GetWorldMarketSubList_body = '__RequestVerificationToken={}&mainKey={}&usingCleint=0'

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

        page = QtWebEngineWidgets.QWebEnginePage(self.profile, self.web)
        self.web.setPage(page)

        self.web.setUrl(QtCore.QUrl("https://market.blackdesertonline.com/"))
        #self.web.setUrl(QtCore.QUrl("https://google.com/"))

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
        #url_pat = sanitizeFileName(self.web.page().url().path().replace('/', ' '))
        #if url_pat.strip() == '':
        #    url_pat = 'index'
        #this_pat = os.path.join(relative_path_convert('webcache'), url_pat)

    def hot_load(self, txt):
        #print(txt)
        dat = string_between(txt, '<form id="frmGetItemSellBuyInfo">', '</form>').strip()
        sdat = string_between(dat, 'value="', '"')
        self.frmGetItemSellBuyInfo_token = sdat
        dat = string_between(txt, '<form id="frmGetWorldMarketSubList"', '</form>').strip()
        sdat = string_between(dat, 'value="', '"')
        self.GetWorldMarketSubList_token = sdat
        print(self.host_local)
        conn = urllib3.connection_from_url(self.host_local)
        coks = urlencode(self.cooks).replace('&', '; ')
        print(coks)
        r = conn.request('POST', self.GetWorldMarketSubList,
                         body=self.GetWorldMarketSubList_body.format(self.GetWorldMarketSubList_token, 4998).encode('utf-8'),
                         headers={
                             'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                             'Cookie': coks
                         })
        print(r.data)

