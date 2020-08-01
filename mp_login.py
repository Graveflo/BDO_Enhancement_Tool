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


class MPBrowser(QtWebEngineWidgets.QWebEngineView):
    pass

class DlgMPLogin(QtWidgets.QDialog):


    def __init__(self, parent):
        super(DlgMPLogin, self).__init__(parent)

        self.resize(QtCore.QSize(340, 550))


        self.web = MPBrowser()
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.addWidget(self.web)

        self.profile = QtWebEngineWidgets.QWebEngineProfile('cookies', self.web)
        self.cookie_store = self.profile.cookieStore()

        self.cookie__RequestVerificationToken = None
        self.frmGetItemSellBuyInfo_token = None


        self.cookie_store.cookieAdded.connect(self.onCookieAdded)

        self.web.loadFinished.connect(self.web_loadFinished)

        page = QtWebEngineWidgets.QWebEnginePage(self.profile, self.web)
        self.web.setPage(page)

        self.web.setUrl(QtCore.QUrl("https://market.blackdesertonline.com/"))
        #self.web.setUrl(QtCore.QUrl("https://google.com/"))

    def onCookieAdded(self, cooke):
        name = cooke.name().data().decode('utf-8')
        #print('{}: {}'.format(name, cooke.value()))
        if name == '__RequestVerificationToken':
            self.set_cookie__RequestVerificationToken(cooke.value().data().decode('utf-8'))

    def set_cookie__RequestVerificationToken(self, token):
        self.cookie__RequestVerificationToken = token
        conn = urllib3.connection_from_url('https://market.blackdesertonline.com/')
        r = conn.request('GET', '/Home/list/hot')
        print(r.data)


    def web_loadFinished(self):
        page = self.web.page()
        loc = self.web.page().url().path()

        if loc == '/Home/list/hot':
            page.toHtml(self.hot_load)
        #url_pat = sanitizeFileName(self.web.page().url().path().replace('/', ' '))
        #if url_pat.strip() == '':
        #    url_pat = 'index'
        #this_pat = os.path.join(relative_path_convert('webcache'), url_pat)

    def hot_load(self, txt):
        print(txt)
        dat = string_between(txt, '<form id="frmGetItemSellBuyInfo">', '</form>').strip()
        sdat = string_between(dat, 'value="', '"')
        self.frmGetItemSellBuyInfo_token = sdat

