# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑  ❧
"""
from PyQt6.QtGui import QMouseEvent, QAction
from PyQt6.QtWidgets import QMenu
from PyQt6.QtCore import Qt, QSize, QModelIndex

from BDO_Enhancement_Tool.model import Enhance_model
from BDO_Enhancement_Tool.Qt_common import lbl_color_MainWindow


class AbstractTable(object):
    HEADERS = []

    def __init__(self, *args, **kwargs):
        super(AbstractTable, self).__init__(*args, **kwargs)
        self.enh_model: Enhance_model = None
        self.frmMain: lbl_color_MainWindow = None

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setIconSize(QSize(32, 32))

    def mouseReleaseEvent(self, a0: QMouseEvent) -> None:  # MUST CALL QT SUPER IN CLIENT CLASS!!!!
        if a0.button() & Qt.MouseButton.RightButton == Qt.MouseButton.RightButton:
            a0.accept()
            a0.setAccepted(True)
            menu = QMenu(self)
            self.make_menu(menu)
            this_idx = self.indexAt(a0.position().toPoint())
            self.check_index_widget_menu(this_idx, menu)
            menu.popup(a0.globalPosition().toPoint())

    def check_index_widget_menu(self, index:QModelIndex, menu:QMenu):
        raise NotImplementedError()

    def set_common(self, model: Enhance_model, frmMain: lbl_color_MainWindow):
        self.enh_model = model
        self.frmMain = frmMain

    def get_header_index(self, str_header):
        return self.HEADERS.index(str_header)

    def make_menu(self, menu:QMenu):
        action_clear_selection = QAction('Clear Selection', menu)
        action_clear_selection.triggered.connect(self.clearSelection)
        menu.addAction(action_clear_selection)

        action_select_all = QAction('Select All', menu)
        action_select_all.triggered.connect(self.selectAll)
        menu.addAction(action_select_all)

