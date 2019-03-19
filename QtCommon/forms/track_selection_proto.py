#- * -coding: utf - 8 - * -
"""
🛳 NSWCP 🚢 Code 324 🛳

@author: ☙ Ryan McConnell ♈♑ ryan.mcconnell@navy.mil ❧
"""
import os, sys, abc
relative_path_add = lambda str_path: sys.path.append(
    os.path.abspath(os.path.join(os.path.split(__file__)[0], str_path)))
def relative_path_covnert(x):
    """
    Takes a valid path: either relative to CWD or an absolute path and convert it to a relative path for this file.
    The relative path assumes that simply joining the returned path with the path of this file shall result in a valid
    path pointing to the origonal valid file object (x).
    :param x: str: path to a valid file object
    :return: str: a path to the file object relative to this file
    """
    return os.path.abspath(os.path.join(os.path.split(__file__)[0], x))

import dlg_Track_Selection
from QtCommon import Qt_common
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QTableWidgetItem, QAbstractItemView, QAction, QMenu
from PyQt5.QtCore import Signal

setIcon = Qt_common.setIcon

# TODO: select/activate modes activated/not remove the ui elements if not

class dlg_Track_Selection_Proto(QDialog):
    """
    This class is the veiw model for the track selection dialog. It has functionality to allow other forms to hook its
    selection even (on double click). It also allows for sorting and editing of the information while in edit mode.
    """
    trackSelected = Signal(int, int)

    def __init__(self, app):
        super(dlg_Track_Selection_Proto, self).__init__()
        self.app = app
        frmObj = dlg_Track_Selection.Ui_Dialog_TrackSelection()
        self.ui = frmObj
        frmObj.setupUi(self)
        tv = frmObj.table_main
        self.old_tv_clickers = tv.contextMenuEvent
        chbox_edit = frmObj.chkSelectEdit
        chbox_edit.toggled.connect(self.chkSelectEdit_toggled)
        setIcon(frmObj.chkSelectEdit, relative_path_covnert("Resources/lock.png"))
        self.set_locked_mode()

    def double_click_callback(self, evt):
        this_item_head = self.ui.table_main.item(evt.row(), 0)
        self.trackSelected.emit(this_item_head.origonal_index, evt.row())

    def chkSelectEdit_toggled(self):
        """
        Changed the appearance of the checkbox and choses a method to set the window for select vs edit mode.
        :return: None
        """
        chkSelectEdit = self.ui.chkSelectEdit
        new_val = chkSelectEdit.isChecked()
        if new_val:
            self.set_locked_mode()
            chkSelectEdit.setText('(Select) /  Edit ')
        else:
            self.set_edit_mode()
            chkSelectEdit.setText(' Select  / (Edit)')

    def set_edit_mode(self):
        """
        Sepcific logic for when edit mode is enabled via chkSelectEdit
        :return: None
        """
        frmObj = self.ui
        tv = frmObj.table_main
        tv.setEditTriggers(QAbstractItemView.AllEditTriggers)
        tv.cellChanged.connect(self.table_main_changed)
        tv.doubleClicked.disconnect(self.double_click_callback)

    def set_locked_mode(self):
        """
        This method handles the signals and behavior of the UI as the mode is changed from select mode to edit more and
        vise versa
        :return: None
        """
        tv = self.ui.table_main
        tv.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tv.setSelectionBehavior(QAbstractItemView.SelectRows)
        tv.selectionModel()
        tv.doubleClicked.connect(self.double_click_callback)
        try:
            tv.cellChanged.disconnect(self.table_main_changed)
        except TypeError:
            pass # never connected (this is fine)
        tree_right_click = self.old_tv_clickers
        def this_context_menu(event_star):
            root_menu = QMenu(self.ui.table_main)
            open_action = QAction(root_menu)
            open_action.setText('Display in Analyzer')
            # self.ui.table_main.indexAt(event_star.pos())
            def open_action_triggered():
                this_row = tv.indexAt(event_star.pos()).row()
                this_head = tv.item(this_row, 0)
                self.trackSelected.emit(this_head.origonal_index, this_row)
            open_action.triggered.connect(open_action_triggered)
            root_menu.addAction(open_action)
            root_menu.exec_(event_star.globalPos())
            tree_right_click(event_star)
        tv.contextMenuEvent = this_context_menu
        # tv.selectionModel().selectionChanged.connect(self.track_selection_callback)

    def add_tracks(self, struct_):
        """
        This method takes a list of lists (as described in add_track) and adds them into the track list sequentially
        :param struct_: list(list(str, str, str, str, str, str, str, str, str): number, name, magnitude, Unit, Coef_A, Coef_B, Type, Range_Peak, Coupling)):
        :return: None
        """
        tv = self.ui.table_main
        sorting_enabled = tv.isSortingEnabled()
        if sorting_enabled:
            tv.setSortingEnabled(False)
        tv.blockSignals(True)
        return_me = []
        try:
            for i, this_line in enumerate(struct_):
                self.add_track(this_line)
                #tv.insertRow(i)
                #this_line = []
                #for num, val_ in enumerate(this_line):
                #    this_item = QTableWidgetItem(val_)
                #    this_line.append(this_item)
                #    tv.setItem(i, num, this_item)
                #return_me.append(this_line)
        finally:
            tv.blockSignals(False)
            if sorting_enabled:
                tv.setSortingEnabled(True)
        return return_me

    def add_track(self, trek):
        """
        This method takes a list structure and adds it to the list with each column in place
        :param trek: list(str, str, str, str, str, str, str, str, str): number, name, magnitude, Unit, Coef_A, Coef_B, Type, Range_Peak, Coupling):
        :return: None
        """
        tv = self.ui.table_main
        sorting_enabled = tv.isSortingEnabled()
        if sorting_enabled:
            tv.setSortingEnabled(False)
        tv.blockSignals(True)
        return_me = []
        try:
            i = tv.rowCount()
            tv.insertRow(i)
            for num, val_ in enumerate(trek):
                this_item = QTableWidgetItem(val_)
                return_me.append(this_item)
                tv.setItem(i, num, this_item)
            return_me[0].__dict__['origonal_index'] = i
        finally:
            tv.blockSignals(False)
            if sorting_enabled:
                tv.setSortingEnabled(True)
        return return_me

    def empty_list(self):
        """
        Used to reinitiaize the list. Remove all tracks currently listed.
        :return: None
        """
        # TODO: unhook the changed event
        tv = self.ui.table_main
        tv.clear()
        for i in range(0, tv.rowCount()):
            tv.removeRow(0)
        self.set_column_headers()
        #tv.setHorizontalHeaderLabels(HEADERS)

    def update_layout(self):
        frmObj = self.ui
        left,top,right,bottom = frmObj.verticalLayout.layout().getContentsMargins()
        vertical_spacing = frmObj.verticalLayout.spacing()
        table_main = frmObj.table_main
        table_main.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        screen_geo = self.app.desktop().screenGeometry()
        screen_height = screen_geo.height()
        screen_width = screen_geo.width()
        MAX_HEIGHT = int(round(screen_height * 0.8))
        MAX_WIDTH = int(round(screen_width * 0.8))
        print table_main.verticalHeader().width()
        try_width = table_main.horizontalHeader().length()
        try_width += left+right+vertical_spacing+vertical_spacing+1
        try_height = table_main.verticalHeader().length() + frmObj.widget.height()
        try_height += bottom + top + (vertical_spacing*2)+1
        if try_width > MAX_WIDTH:
            try_width = MAX_WIDTH
        if try_height > MAX_HEIGHT:
            try_height = MAX_HEIGHT
        HALF_SCREEN_WIDTH = int(round(screen_width/2.0))
        HALF_SCREEN_HEIGHT = int(round(screen_height/2.0))
        try_x = HALF_SCREEN_WIDTH-int(round(try_width/2.0))
        try_y = HALF_SCREEN_HEIGHT-int(round(try_height/2.0))
        self.setGeometry(try_x, try_y,
                         try_width,try_height)
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
        Use this method to update the feild of the datastructure represented in the list approprietly.
        :return:
        """
        return
