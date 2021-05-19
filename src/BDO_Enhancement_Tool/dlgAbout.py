#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
from .Forms.dlg_About import Ui_Dialog
import PyQt5.QtWidgets as QtWidgets
from PyQt5.QtGui import QPixmap

from .common import relative_path_convert
from .__main__ import RELEASE_VER


class dlg_About(QtWidgets.QDialog):
    def __init__(self, parent):
        super(dlg_About, self).__init__(parent)
        frmObj = Ui_Dialog()
        self.ui = frmObj
        frmObj.setupUi(self)

        pix = QPixmap(relative_path_convert('Graveflo.png'))
        frmObj.lblPicture.setPixmap(pix)
        html = frmObj.textEdit.toHtml()
        html = html.replace('|VERS|', str(RELEASE_VER))
        frmObj.textEdit.setHtml(html)
