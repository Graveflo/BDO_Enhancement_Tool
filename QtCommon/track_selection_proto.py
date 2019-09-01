#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import abc
from forms import dlg_Simple_TableWidget
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QTableWidgetItem
from PyQt5.QtCore import pyqtSignal

from Qt_common import QBlockSig, QBlockSort

# TODO: select/activate modes activated/not remove the ui elements if not

class dlg_Track_Selection_Proto(QDialog):
    """
    This class is the veiw model for the track selection dialog. It has functionality to allow other forms to hook its
    selection even (on double click). It also allows for sorting and editing of the information while in edit mode.
    """
    trackSelected = pyqtSignal(int, int, name='trackSelected')

    def __init__(self, app):
        super(dlg_Track_Selection_Proto, self).__init__()
        self.app = app
        frmObj = dlg_Simple_TableWidget.Ui_Dialog()
        self.ui = frmObj
        frmObj.setupUi(self)
        tv = frmObj.tableWidget
        self.old_tv_clickers = tv.contextMenuEvent

    def double_click_callback(self, evt):
        this_item_head = self.ui.table_main.item(evt.row(), 0)
        self.trackSelected.emit(this_item_head.origonal_index, evt.row())

    def add_tracks(self, struct_):
        tv = self.ui.tableWidget
        return_me = []
        with QBlockSort(tv):
            with QBlockSig(tv):
                for i, this_line in enumerate(struct_):
                    self.add_track(this_line)
        return return_me

    def add_track(self, trek):
        tv = self.ui.tableWidget
        return_me = []
        with QBlockSort(tv):
            with QBlockSig(tv):
                i = tv.rowCount()
                tv.insertRow(i)
                for num, val_ in enumerate(trek):
                    this_item = QTableWidgetItem(val_)
                    return_me.append(this_item)
                    tv.setItem(i, num, this_item)
                return_me[0].__dict__['origonal_index'] = i
        return return_me

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
        left,top,right,bottom = frmObj.verticalLayout.layout().getContentsMargins()
        vertical_spacing = frmObj.verticalLayout.spacing()
        table_main = frmObj.tableWidget
        table_main.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        screen_geo = self.app.desktop().screenGeometry()
        screen_height = screen_geo.height()
        screen_width = screen_geo.width()
        MAX_HEIGHT = int(round(screen_height * 0.8))
        MAX_WIDTH = int(round(screen_width * 0.8))
        #print table_main.verticalHeader().width()
        try_width = table_main.horizontalHeader().length()
        try_width += left+right+vertical_spacing+vertical_spacing+1
        try_height = table_main.verticalHeader().length()
        try_height += bottom + top + (vertical_spacing*2)+1
        if try_width > MAX_WIDTH:
            try_width = MAX_WIDTH
        if try_height > MAX_HEIGHT:
            try_height = MAX_HEIGHT
        HALF_SCREEN_WIDTH = int(round(screen_width/2.0))
        HALF_SCREEN_HEIGHT = int(round(screen_height/2.0))
        try_x = HALF_SCREEN_WIDTH-int(round(try_width/2.0))
        try_y = HALF_SCREEN_HEIGHT-int(round(try_height/2.0))
        self.setGeometry(try_x, try_y, try_width, try_height)
        #self.setMinimumSize(self.sizeHint())

    def show(self):
        """
        Calling the show method not only raises the window but it also resized the window and list to fit the contents
        for a compact layout.
        :return: None
        """
        self.update_layout()
        super(dlg_Track_Selection_Proto, self).show()

    @abc.abstractmethod
    def set_column_headers(self):
        return

    @abc.abstractmethod
    def table_main_changed(self):
        """
        This method is the callback for when the user makes and edit on one of the rows in the table.
        Use this method to update the field of the data structure represented in the list appropriately.
        :return:
        """
        return
