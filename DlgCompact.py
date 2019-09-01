#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
from PyQt5 import QtWidgets, Qt
from common import Classic_Gear, Smashable

import FrmMain
from QtCommon.Qt_common import QBlockSort, QBlockSig
from Forms.dlgCompact import Ui_dlgCompact

class Dlg_Compact(QtWidgets.QDialog):
    def __init__(self, frmMain):
        super(Dlg_Compact, self).__init__(parent=frmMain)
        frmObj = Ui_dlgCompact()
        self .ui = frmObj
        frmObj.setupUi(self)
        self.frmMain = frmMain
        model = frmMain.model
        self.selected_gear = None
        settings = model.settings
        num_fs = settings[settings.P_NUM_FS]
        frmObj.spinFS.setMaximum(num_fs)
        frmObj.spinFS.valueChanged.connect(self.set_frame)
        frmObj.cmdUpgrade.clicked.connect(self.upgrade_gear)
        frmObj.cmdDownagrade.clicked.connect(self.downgrade_gear)
        frmObj.cmdSuccess.clicked.connect(self.cmdSuccess_clicked)
        frmObj.cmdFail.clicked.connect(self.cmdFail_clicked)

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

    def show(self):
        frmMain = self.frmMain
        try:
            super(Dlg_Compact, self).show()
            frmMain.hide()
        except AttributeError:
            frmMain.show_warning_msg('This window can not be opened until strategy is calculated')

    def closeEvent(self, QCloseEvent):
        super(Dlg_Compact, self).closeEvent(QCloseEvent)
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
        self.selected_gear = gear_obj
        frmMain.table_Strat_selectionChanged(first_col)
        frmObj.lblGear.setText(gear_obj.get_full_name())
        MfrmObj.cmdStrat_go.click()

