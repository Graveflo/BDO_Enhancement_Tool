# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QTableWidget, QMenu, QAction, QTableWidgetItem, QHeaderView, QTreeWidgetItem

from BDO_Enhancement_Tool.model import Enhance_model, SettingsException, Invalid_FS_Parameters, FailStackList
from BDO_Enhancement_Tool.WidgetTools import QBlockSig, MONNIES_FORMAT, MPThread, \
    GearWidget, set_cell_color_compare, set_cell_lvl_compare, monnies_twi_factory, NoScrollCombo, STR_PERCENT_FORMAT, \
    gt_str_to_q_color
from BDO_Enhancement_Tool.common import gear_types, \
    ItemStore, generate_gear_obj, Gear
from BDO_Enhancement_Tool.QtCommon.Qt_common import lbl_color_MainWindow, SpeedUpTable, clear_table

from PyQt5.QtCore import QThread, pyqtSignal, Qt
from .Abstract_Gear_Tree import AbstractGearTree, HEADER_NAME, HEADER_GEAR_TYPE, HEADER_BASE_ITEM_COST, HEADER_TARGET

from .Abstract_Table import AbstractTable


HEADER_RANGE = 'Range'
HEADER_STRAT = 'Strat'
HEADER_COST = 'Cost'


class TableFSSecondary(AbstractGearTree):
    sig_fsl_invalidated = pyqtSignal(name='sig_fsl_invalidated')
    HEADERS = [HEADER_NAME, HEADER_GEAR_TYPE, HEADER_BASE_ITEM_COST, HEADER_TARGET, HEADER_RANGE, HEADER_STRAT, HEADER_COST]

    def __init__(self, *args, **kwargs):
        super(TableFSSecondary, self).__init__(*args, **kwargs)

    def table_add_gear(self, this_gear: Gear, check_state=Qt.Checked):
        idx_NAME = self.get_header_index(HEADER_NAME)
        top_lvl = super(TableFSSecondary, self).table_add_gear(this_gear, check_state=check_state)
        gw:GearWidget = self.itemWidget(top_lvl, idx_NAME)
        gw.model_edit_func = self.enh_model.edit_fs_secondary_item
        with QBlockSig(self):
            self.add_children(top_lvl)

    def gw_check_state_changed(self, gw:GearWidget, state):
        this_gear = gw.gear
        if state == Qt.Checked:
            self.enh_model.include_fs_secondary_item(this_gear)
        else:
            self.enh_model.exclude_fs_secondary_item(this_gear)
        settings = self.enh_model.settings
        fsl:FailStackList = settings[settings.P_GENOME_FS]
        if fsl.secondary_gear is None:
            self.sig_fsl_invalidated.emit()

    def master_gw_sig_gear_changed(self, gw: GearWidget):
        super(TableFSSecondary, self).master_gw_sig_gear_changed(gw)
        self.set_item_data(gw.parent_widget)

    def add_children(self, top_lvl: QTreeWidgetItem):
        model = self.enh_model
        idx_NAME = self.get_header_index(HEADER_NAME)
        idx_GEAR_TYPE = self.get_header_index(HEADER_GEAR_TYPE)
        idx_BASE_ITEM_COST = self.get_header_index(HEADER_BASE_ITEM_COST)
        idx_TARGET = self.get_header_index(HEADER_TARGET)
        master_gw = self.itemWidget(top_lvl, idx_NAME)
        this_gear:Gear = master_gw.gear
        gear_type = this_gear.gear_type

        top_lvl.takeChildren()

        for i in range(gear_type.bt_start-1, len(gear_type.map)):
            twi = QTreeWidgetItem(top_lvl, [''] * self.columnCount())
            lvl = this_gear.gear_type.idx_lvl_map[i]
            _gear = this_gear.duplicate()
            _gear.set_enhance_lvl(lvl)
            this_gw = GearWidget(_gear, model, edit_able=False, display_full_name=False)
            self.setItemWidget(twi, idx_NAME, this_gw)
            top_lvl.addChild(twi)
            twi.setText(idx_GEAR_TYPE, gear_type.name)
            twi.setText(idx_BASE_ITEM_COST, top_lvl.text(2))
            twi.setText(idx_TARGET, _gear.enhance_lvl)
            twi.setForeground(idx_GEAR_TYPE, Qt.black)
            twi.setBackground(idx_GEAR_TYPE, gt_str_to_q_color(gear_type.name).lighter())

    def create_TreeWidgetItem(self, parent_wid, this_gear, check_state, icon_overlay=True) -> QTreeWidgetItem:
        top_lvl = super(TableFSSecondary, self).create_TreeWidgetItem(parent_wid, this_gear, check_state, icon_overlay=False)
        idx_TARGET = self.get_header_index(HEADER_TARGET)
        top_lvl.setText(idx_TARGET, '')
        return top_lvl

    def invalidate_item(self, top_lvl: QTreeWidgetItem):
        pass

    def refresh_strat(self):
        model = self.enh_model
        settings = model.settings
        fsl:FailStackList = settings[settings.P_GENOME_FS]
        idx_NAME = self.get_header_index(HEADER_NAME)
        if fsl.validate():
            for i in range(0, self.topLevelItemCount()):
                item = self.topLevelItem(i)
                this_gw = self.itemWidget(item, idx_NAME)
                this_gear = this_gw.gear
                if fsl.secondary_gear is this_gear:
                    idx_HEADER_RANGE = self.get_header_index(HEADER_RANGE)
                    idx_HEADER_STRAT = self.get_header_index(HEADER_STRAT)
                    idx_HEADER_COST = self.get_header_index(HEADER_COST)

                    bti_m_o = this_gear.gear_type.bt_start - 1
                    prv_num = fsl.starting_pos
                    for i, num in enumerate(fsl.secondary_map):
                        child = item.child(i)
                        amount_fs = this_gear.gear_type.get_fs_gain(bti_m_o+i) * num
                        child.setText(idx_HEADER_RANGE, '{} - {}'.format(prv_num, amount_fs))
                        try:
                            child.setText(idx_HEADER_STRAT, str(fsl.remake_strat[i]))
                            child.setText(idx_HEADER_COST, MONNIES_FORMAT.format(int(round(fsl.avg_cost[i]))))
                        except IndexError:
                            pass
                        prv_num += amount_fs
                    break

    def reload_list(self):
        super(TableFSSecondary, self).reload_list()
        self.refresh_strat()

    def set_common(self, model: Enhance_model, frmMain: lbl_color_MainWindow):
        super(TableFSSecondary, self).set_common(model, frmMain)
        settings = model.settings
        self.prop_in_list = settings.P_FAIL_STACKER_SECONDARY
        self.prop_out_list = settings.P_R_STACKER_SECONDARY
        self.model_add_item_func = model.add_fs_secondary_item
        self.main_invalidate_func = self.invalidate_item
        self.reload_list()
