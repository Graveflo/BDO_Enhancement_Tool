#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
from PyQt5 import QtWidgets, Qt, QtCore, QtGui
from PyQt5.QtCore import Qt
from .common import Classic_Gear, Smashable, relative_path_convert

from . import FrmMain
from .QtCommon.Qt_common import QBlockSort, QBlockSig
from .Forms.dlgCompact import Ui_dlgCompact
from .QtCommon.track_selection_proto import dlg_Track_Selection_Proto
import typing

QWidget = QtWidgets.QWidget
STR_TW_GEAR = 'lolwut'
BS_CHEER = relative_path_convert('Images/B.S.Happy.png')
BS_AW_MAN = relative_path_convert('Images/B.S. Awh Man.png')
BS_FACE_PALM = relative_path_convert('Images/B.S. Face Palm.png')
BS_HMM = relative_path_convert('Images/B.S. Hmmmm.png')


class DlgFS(dlg_Track_Selection_Proto):
    HEADERS = ['FS', 'Item']

    def __init__(self, app, parent=None):
        super(DlgFS, self).__init__(app, parent=parent)
        frmObj = self.ui
        frmObj.tableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        frmObj.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        frmObj.tableWidget.verticalHeader().setVisible(False)
        frmObj.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        frmObj.tableWidget.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)

    def select_row(self, int_row):
        tableWidget = self.ui.tableWidget
        tableWidget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        tableWidget.selectRow(int_row)
        tableWidget.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)

    def set_column_headers(self):
        frmObj = self.ui
        tv = frmObj.tableWidget
        tv.setColumnCount(len(self.HEADERS))
        tv.setHorizontalHeaderLabels(self.HEADERS)


class DlgChoices(dlg_Track_Selection_Proto):
    HEADERS = ['Item', 'Balance', 'Loss Prevention']

    def __init__(self, app, parent=None):
        super(DlgChoices, self).__init__(app, parent=parent)
        frmObj = self.ui
        frmObj.tableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        frmObj.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        frmObj.tableWidget.verticalHeader().setVisible(False)
        frmObj.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        frmObj.tableWidget.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        frmObj.tableWidget.setAlternatingRowColors(True)
        frmObj.tableWidget.setSortingEnabled(True)

    def select_gear(self, gear_obj):
        for i in range(0, self.ui.tableWidget.rowCount()):
            this_gear = self.ui.tableWidget.item(i, 0).__dict__[STR_TW_GEAR]
            if this_gear is gear_obj:
                self.select_row(i)

    def select_row(self, int_row):
        tableWidget = self.ui.tableWidget
        tableWidget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        tableWidget.selectRow(int_row)
        tableWidget.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)

    def show(self):
        super(DlgChoices, self).show()
        self.ui.tableWidget.horizontalHeader().setSortIndicator(1, QtCore.Qt.AscendingOrder)

    def set_column_headers(self):
        frmObj = self.ui
        tv = frmObj.tableWidget
        tv.setColumnCount(len(self.HEADERS))
        tv.setHorizontalHeaderLabels(self.HEADERS)


class BSWidget(QtWidgets.QWidget):
    def __init__(self, parent, pixmap=None):
        super(BSWidget, self).__init__(parent)
        self.pixmap:QtGui.QPixmap = pixmap
        if pixmap is not None:
            self.set_pixmap(pixmap)

    def set_pixmap(self, pixmap:QtGui.QPixmap):
        self.pixmap = pixmap
        self.setMinimumSize(self.pixmap.size())

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
        if self.pixmap is not None:
            p = QtGui.QPainter(self)
            p.drawPixmap(0,0, self.pixmap)
            self.setMinimumSize(self.pixmap.size())


class DecisionStep(QtWidgets.QTreeWidgetItem):
    def __init__(self, dlg_compact, *args):
        super(DecisionStep, self).__init__(*args)
        self.dlg_compact: Dlg_Compact = dlg_compact

    def get_buttons(self):
        pass



class Dlg_Compact(QtWidgets.QDialog):
    def __init__(self, frmMain):
        super(Dlg_Compact, self).__init__(parent=frmMain)
        frmObj = Ui_dlgCompact()
        self .ui = frmObj
        frmObj.setupUi(self)
        self.frmMain = frmMain
        model = frmMain.model
        self.selected_gear = None
        self.dlg_FS_shelf = DlgFS(frmMain.app, parent=self)
        self.dlg_Choices = DlgChoices(frmMain.app, parent=self)
        settings = model.settings
        num_fs = settings[settings.P_NUM_FS]
        frmObj.spinFS.setMaximum(num_fs)
        

        self.pix_hmm = QtGui.QPixmap(BS_HMM).scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.bs_wid = BSWidget(self, pixmap=self.pix_hmm)
        frmObj.ParentLayout.replaceWidget(frmObj.widget_6, self.bs_wid)

    def showEvent(self, a0: QtGui.QShowEvent) -> None:
        super(Dlg_Compact, self).showEvent(a0)
        self.frmMain.hide()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        super(Dlg_Compact, self).closeEvent(a0)
        self.frmMain.show()

    def decide(self):
        pass
