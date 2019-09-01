#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
from forms import dlg_Simple_TableWidget
from PyQt5 import QtWidgets
#from PyQt5.QtCore import pyqtSignal


class dlg_Track_Selection_Proto(QtWidgets.QDialog):
    def __init__(self, app, parent=None):
        super(dlg_Track_Selection_Proto, self).__init__(parent=parent)
        self.app = app
        frmObj = dlg_Simple_TableWidget.Ui_Dialog()
        self.ui = frmObj
        frmObj.setupUi(self)
        tv = frmObj.tableWidget

    def empty_list(self):
        """
        Used to reinitiaize the list. Remove all tracks currently listed.
        :return: None
        """
        # TODO: unhook the changed event
        tv = self.ui.tableWidget
        tv.clear()
        for i in range(0, tv.rowCount()):
            tv.removeRow(0)
        self.set_column_headers()

    def update_layout(self):
        frmObj = self.ui
        table_main = frmObj.tableWidget
        table_main.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        table_main.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        screen_geo = self.app.desktop().screenGeometry()
        screen_height = screen_geo.height()
        screen_width = screen_geo.width()
        MAX_HEIGHT = int(round(screen_height * 0.4))
        MAX_WIDTH = int(round(screen_width * 0.4))
        self.adjustSize()
        try_width = self.width()
        try_height = self.height()
        if try_width > MAX_WIDTH:
            try_width = MAX_WIDTH
        if try_height > MAX_HEIGHT:
            try_height = MAX_HEIGHT
        HALF_SCREEN_WIDTH = int(round(screen_width / 2.0))
        HALF_SCREEN_HEIGHT = int(round(screen_height / 2.0))
        try_x = HALF_SCREEN_WIDTH - int(round(try_width / 2.0))
        try_y = HALF_SCREEN_HEIGHT - int(round(try_height / 2.0))
        self.move(try_x, try_y)
        self.resize(try_width, try_height)

    def show(self):
        """
        Calling the show method not only raises the window but it also resized the window and list to fit the contents
        for a compact layout.
        :return: None
        """
        super(dlg_Track_Selection_Proto, self).show()
        self.update_layout()

    def set_column_headers(self):
        raise NotImplementedError()

    def table_main_changed(self):
        """
        This method is the callback for when the user makes and edit on one of the rows in the table.
        Use this method to update the field of the data structure represented in the list appropriately.
        :return:
        """
        raise NotImplementedError()
