#- * -coding: utf - 8 - * -
"""
🛳 NSWCP 🚢 Code 324 🛳

@author: ☙ Ryan McConnell ♈♑ ryan.mcconnell@navy.mil ❧
"""
from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import QtWebEngineWidgets, QtWebEngineCore


class MPBrowser(QtWebEngineWidgets.QWebEngineView):
    pass

class DlgMPLogin(QtWidgets.QDialog):
    def __init__(self, parent):
        super(DlgMPLogin, self).__init__(parent)


        self.web = MPBrowser()
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.addWidget(self.web)

        self.profile = QtWebEngineWidgets.QWebEngineProfile('cookies', self.web)
        self.cookie_store = self.profile.cookieStore()

        self.cookie__RequestVerificationToken = None


        self.cookie_store.cookieAdded.connect(self.onCookieAdded)

        #self.web.loadFinished.connect(self.web_loadFinished)

        page = QtWebEngineWidgets.QWebEnginePage(self.profile, self.web)
        self.web.setPage(page)

        self.web.setUrl(QtCore.QUrl("https://market.blackdesertonline.com/"))

    def onCookieAdded(self, cooke):
        name = cooke.name().decode('utf-8')
        print('{}: {}'.format(cooke.name(), cooke.value()))
        if name == '__RequestVerificationToken':
            self.cookie__RequestVerificationToken = cooke.value()

    def web_loadFinished(self):
        print(self.web.page().toHtml(self.uh))

    def uh(self, txt):
        print(txt)
