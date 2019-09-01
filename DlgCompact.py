#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
from PyQt5 import QtWidgets, Qt, QtCore
from common import Classic_Gear, Smashable

import FrmMain
from QtCommon.Qt_common import QBlockSort, QBlockSig
from Forms.dlgCompact import Ui_dlgCompact
from QtCommon.track_selection_proto import dlg_Track_Selection_Proto


class DlgFS(dlg_Track_Selection_Proto):
    HEADERS = ['FS', 'Item']

    def __init__(self, app, parent=None):
        super(DlgFS, self).__init__(app, parent=parent)
        frmObj = self.ui
        frmObj.tableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        frmObj.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        frmObj.tableWidget.verticalHeader().setVisible(False)
        frmObj.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

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
        frmObj.tableWidget.setAlternatingRowColors(True)
        frmObj.tableWidget.setSortingEnabled(True)

    def show(self):
        super(DlgChoices, self).show()
        self.ui.tableWidget.horizontalHeader().setSortIndicator(1, QtCore.Qt.AscendingOrder)

    def set_column_headers(self):
        frmObj = self.ui
        tv = frmObj.tableWidget
        tv.setColumnCount(len(self.HEADERS))
        tv.setHorizontalHeaderLabels(self.HEADERS)


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
        frmObj.spinFS.valueChanged.connect(self.set_frame)
        frmObj.cmdUpgrade.clicked.connect(self.upgrade_gear)
        frmObj.cmdDownagrade.clicked.connect(self.downgrade_gear)
        frmObj.cmdSuccess.clicked.connect(self.cmdSuccess_clicked)
        frmObj.cmdFail.clicked.connect(self.cmdFail_clicked)
        frmObj.cmdFsShelf.clicked.connect(self.dlg_FS_shelf.show)
        frmObj.cmdChoices.clicked.connect(self.dlg_Choices.show)
        self.dlg_FS_shelf.ui.tableWidget.cellDoubleClicked.connect(self.dlg_FS_shelf_cellDoubleClicked)
        self.dlg_Choices.ui.tableWidget.cellDoubleClicked.connect(self.dlg_Choices_cellDoubleClicked)

    def dlg_FS_shelf_cellDoubleClicked(self, row, col):
        self.ui.spinFS.setValue(row)

    def dlg_Choices_cellDoubleClicked(self, row, col):
        dis_gear = self.dlg_Choices.ui.tableWidget.item(row, 0).__dict__[FrmMain.STR_TW_GEAR]
        self.set_gear(dis_gear)

    def update_dlg_Choices(self):
        dlg_Choices = self.dlg_Choices
        dlg_Choices.empty_list()
        table_Strat_FS = self.frmMain.ui.table_Strat_FS
        table_Strat_Equip = self.frmMain.ui.table_Strat_Equip
        def add_drc(table):
            for i in range(0, table.rowCount()):
                item_twi = table.item(i, 0)
                dis_gear = item_twi.__dict__[FrmMain.STR_TW_GEAR]
                item = item_twi.text()
                cost = table.item(i, 1).text()
                loss_prevention = table.item(i, 2).text()
                dlg_Choices.ui.tableWidget.insertRow(i)
                twi = QtWidgets.QTableWidgetItem(item)
                twi.__dict__[FrmMain.STR_TW_GEAR] = dis_gear
                dlg_Choices.ui.tableWidget.setItem(i,0, twi)
                dlg_Choices.ui.tableWidget.setItem(i, 1, FrmMain.comma_seperated_twi(cost))
                dlg_Choices.ui.tableWidget.setItem(i, 2, FrmMain.numeric_twi(loss_prevention))
        add_drc(table_Strat_FS)
        add_drc(table_Strat_Equip)

    def update_dlg_FS_shelf(self):
        dlg_FS_shelf = self.dlg_FS_shelf
        dlg_FS_shelf.empty_list()
        table_fs = self.frmMain.ui.table_Strat
        for i in range(0, table_fs.rowCount()):
            fs_num = table_fs.item(i, 0).text()
            name = table_fs.item(i, 1).text()
            dlg_FS_shelf.ui.tableWidget.insertRow(i)
            dlg_FS_shelf.ui.tableWidget.setItem(i,0, QtWidgets.QTableWidgetItem(fs_num))
            dlg_FS_shelf.ui.tableWidget.setItem(i, 1, QtWidgets.QTableWidgetItem(name))

    def cmdSuccess_clicked(self):
        self.upgrade_gear()
        self.ui.spinFS.setValue(0)

    def cmdFail_clicked(self):
        selected_gear = self.selected_gear
        if isinstance(selected_gear, Classic_Gear):
            this_lvl = selected_gear.get_enhance_lvl_idx()
            backtrack_start = selected_gear.gear_type.lvl_map['TRI']
            if this_lvl >= backtrack_start:
                self.downgrade_gear()
        elif isinstance(selected_gear, Smashable):
            tw_item = self.frmMain.get_enhance_table_item(selected_gear)
            with QBlockSig(self.frmMain.ui.table_Equip):
                tw_item.setCheckState(Qt.Unchecked)
            self.frmMain.table_Equip_cellChanged(tw_item.row(),0)
            self.frmMain.cmdStrat_go_clicked()

        fs_gain = selected_gear.fs_gain()
        self.ui.spinFS.setValue(self.ui.spinFS.value() + fs_gain)

    def upgrade_gear(self):
        frmObj = self.ui
        dis_gear = self.selected_gear
        enh_t = self.frmMain.get_enhance_table_item(dis_gear)
        if enh_t is None:
            return
        try:
            dis_gear.upgrade()
        except KeyError:
            self.show_warning_msg('Cannot upgrade gear past: ' + str(dis_gear.enhance_lvl))
            return
        self.frmMain.refresh_gear_obj(dis_gear, this_item=enh_t)
        self.set_frame()
        self.update_dlg_FS_shelf()

    def downgrade_gear(self):
        frmObj = self.ui
        dis_gear = self.selected_gear
        enh_t = self.frmMain.get_enhance_table_item(dis_gear)
        if enh_t is None:
            return
        try:
            dis_gear.downgrade()
        except KeyError:
            self.show_warning_msg('Cannot upgrade gear past: ' + str(dis_gear.enhance_lvl))
            return
        self.frmMain.refresh_gear_obj(dis_gear, this_item=enh_t)
        self.set_frame()
        self.update_dlg_FS_shelf()

    def show(self):
        frmMain = self.frmMain
        try:
            super(Dlg_Compact, self).show()
            frmMain.hide()
            self.update_dlg_FS_shelf()
        except AttributeError:
            frmMain.show_warning_msg('This window can not be opened until strategy is calculated')

    def closeEvent(self, QCloseEvent):
        super(Dlg_Compact, self).closeEvent(QCloseEvent)
        self.dlg_Choices.close()
        self.dlg_FS_shelf.close()
        self.frmMain.show()

    def set_frame(self):
        frmMain = self.frmMain
        frmObj = self.ui
        #frmMain = Frm_Main()
        model = frmMain.model
        MfrmObj = frmMain.ui
        table_Strat = MfrmObj.table_Strat

        fs_lvl = frmObj.spinFS.value()
        with QBlockSig(table_Strat):
            table_Strat.selectRow(fs_lvl)
        first_col = table_Strat.item(fs_lvl, 1)
        gear_obj = first_col.__dict__[FrmMain.STR_TW_GEAR]
        frmMain.table_Strat_selectionChanged(first_col)
        self.set_gear(gear_obj)
        self.update_dlg_Choices()
        with QBlockSig(self.dlg_FS_shelf.ui.tableWidget):
            self.dlg_FS_shelf.ui.tableWidget.selectRow(fs_lvl)

    def set_gear(self, gear_obj):
        frmObj =self.ui
        self.selected_gear = gear_obj
        frmObj.lblGear.setText(gear_obj.get_full_name())
        row_obj = self.get_strat_enhance_table_item(gear_obj)

        if row_obj is None:
            dlg_FS_shelf = self.frmMain.ui.table_Strat
            fail_times = 1
            fs_lvl = frmObj.spinFS.value()
            while gear_obj == dlg_FS_shelf.item(fs_lvl, 1).__dict__[FrmMain.STR_TW_GEAR]:
                fs_lvl += gear_obj.fs_gain()
                fail_times += 1
            frmObj.lblInfo.setText('Fail: {} times'.format(fail_times-1))
        else:
            table_Equip = self.frmMain.ui.table_Strat_Equip
            this_row = row_obj.row()
            effeciency = table_Equip.item(this_row, 2).text()
            num_fails = table_Equip.item(this_row, 3).text()
            confidence = table_Equip.item(this_row, 4).text()
            frmObj.lblInfo.setText('E: {} | N: {} | C: {}'.format(effeciency, num_fails, confidence))

    def get_strat_enhance_table_item(self, gear_obj):
        table_Equip = self.frmMain.ui.table_Strat_Equip

        for rew in range(0, table_Equip.rowCount()):
            if gear_obj is table_Equip.item(rew, 0).__dict__[FrmMain.STR_TW_GEAR]:
                return table_Equip.item(rew, 0)
