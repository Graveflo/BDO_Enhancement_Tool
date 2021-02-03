# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QTableWidget, QMenu

from BDO_Enhancement_Tool.model import Enhance_model
from BDO_Enhancement_Tool.QtCommon.Qt_common import lbl_color_MainWindow

from PyQt5.QtCore import Qt, QSize


class AbstractTable(object):
    HEADERS = []

    def __init__(self, *args, **kwargs):
        super(AbstractTable, self).__init__(*args, **kwargs)
        self.enh_model: Enhance_model = None
        self.frmMain: lbl_color_MainWindow = None

        self.menu = QMenu(self)
        self.make_menu(self.menu)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setIconSize(QSize(32, 32))

    def mouseReleaseEvent(self, a0: QMouseEvent) -> None:
        if a0.button() & Qt.RightButton == Qt.RightButton:
            a0.accept()
            a0.setAccepted(True)
            self.menu.close()
            self.menu.popup(a0.globalPos())

    def set_common(self, model: Enhance_model, frmMain: lbl_color_MainWindow):
        self.enh_model = model
        self.frmMain = frmMain

    def get_header_index(self, str_header):
        return self.HEADERS.index(str_header)

    def make_menu(self, menu:QMenu):
        raise NotImplementedError()

