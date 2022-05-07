# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑  ❧
"""
from typing import Set
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QTreeWidgetItem

from BDO_Enhancement_Tool.model import Enhance_model
from BDO_Enhancement_Tool.fsl import FailStackList
from BDO_Enhancement_Tool.WidgetTools import QBlockSig, MONNIES_FORMAT, GearWidget, gt_str_to_q_color
from BDO_Enhancement_Tool.Core.Gear import Gear
from BDO_Enhancement_Tool.Core.ItemStore import ItemStoreException, ItemStore
from BDO_Enhancement_Tool.Qt_common import lbl_color_MainWindow

from .Abstract_Gear_Tree import AbstractGearTree, HEADER_NAME, HEADER_GEAR_TYPE, HEADER_BASE_ITEM_COST, HEADER_TARGET

HEADER_RANGE = 'Range'
HEADER_ENHANCE_COST = 'Enhance Cost'
HEADER_AC_COST = 'Cost'
HEADER_ATTEMPTS = 'Attempts'
HEADER_ATTEMPTS_B4_SUC = 'Attempts b4 Success'


class TableFSSecondary(AbstractGearTree):
    sig_fsl_invalidated = pyqtSignal(name='sig_fsl_invalidated')
    HEADERS = [HEADER_NAME, HEADER_GEAR_TYPE, HEADER_BASE_ITEM_COST, HEADER_TARGET, HEADER_RANGE, HEADER_ENHANCE_COST,
               HEADER_AC_COST, HEADER_ATTEMPTS, HEADER_ATTEMPTS_B4_SUC]

    def __init__(self, *args, **kwargs):
        super(TableFSSecondary, self).__init__(*args, **kwargs)

    def table_add_gear(self, this_gear: Gear, check_state=Qt.CheckState.Checked):
        top_lvl = super(TableFSSecondary, self).table_add_gear(this_gear, check_state=check_state)
        with QBlockSig(self):
            self.add_children(top_lvl)

    def gw_check_state_changed(self, gw:GearWidget, state):
        this_gear = gw.gear
        settings = self.enh_model.settings
        invd = False
        fsl_l:Set[FailStackList] = settings[settings.P_GENOME_FS]
        for fsl in fsl_l:
            if fsl.secondary_gear is this_gear:
                invd = True
        if state == Qt.CheckState.Checked:
            self.enh_model.include_fs_secondary_item(this_gear)
        else:
            self.enh_model.exclude_fs_secondary_item(this_gear)
        if invd:
            self.sig_fsl_invalidated.emit()

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
            twi.setForeground(idx_GEAR_TYPE, Qt.GlobalColor.black)
            twi.setBackground(idx_GEAR_TYPE, gt_str_to_q_color(gear_type.name).lighter())

    def create_TreeWidgetItem(self, parent_wid, this_gear, check_state, icon_overlay=True) -> QTreeWidgetItem:
        top_lvl = super(TableFSSecondary, self).create_TreeWidgetItem(parent_wid, this_gear, check_state, icon_overlay=False)
        idx_TARGET = self.get_header_index(HEADER_TARGET)
        top_lvl.setText(idx_TARGET, '')
        return top_lvl

    def refresh_strat(self):
        model = self.enh_model
        settings = model.settings
        fsl_l:Set[FailStackList] = settings[settings.P_GENOME_FS]
        item_store: ItemStore = settings[settings.P_ITEM_STORE]
        idx_NAME = self.get_header_index(HEADER_NAME)

        gmap = {}
        for fsl in fsl_l:
            dis_gear = fsl.secondary_gear
            if dis_gear in gmap:
                if gmap[dis_gear].num_fs > fsl.num_fs:
                    continue
            gmap[dis_gear] = fsl

        for i in range(0, self.topLevelItemCount()):
            item = self.topLevelItem(i)
            this_gw = self.itemWidget(item, idx_NAME)
            this_gear:Gear = this_gw.gear
            if this_gear in gmap:
                fsl = gmap[this_gear]
                if fsl.validate():
                    if fsl.secondary_gear is this_gear:
                        idx_HEADER_RANGE = self.get_header_index(HEADER_RANGE)
                        idx_HEADER_COST = self.get_header_index(HEADER_ENHANCE_COST)
                        idx_HEADER_AC_COST = self.get_header_index(HEADER_AC_COST)
                        idx_HEADER_ATTEMPTS = self.get_header_index(HEADER_ATTEMPTS)
                        idx_HEADER_ATTEMPTS_B4_SUC = self.get_header_index(HEADER_ATTEMPTS_B4_SUC)

                        bti_m_o = this_gear.gear_type.bt_start - 1
                        prv_num = fsl.starting_pos
                        for i, num in enumerate(fsl.secondary_map):
                            child = item.child(i)
                            this_gw = self.itemWidget(child, idx_NAME)
                            if this_gw is None:
                                return
                            this_gear_enhlv = this_gw.gear

                            amount_fs = this_gear.gear_type.get_fs_gain(bti_m_o+i) * num
                            child.setText(idx_HEADER_RANGE, '{} - {}'.format(prv_num, prv_num+amount_fs))
                            try:
                                child.setText(idx_HEADER_COST, MONNIES_FORMAT.format(int(round(fsl.avg_cost[i]))))
                            except IndexError:
                                pass
                            try:
                                child.setText(idx_HEADER_ATTEMPTS, str(fsl.num_attempts[i]))
                                child.setText(idx_HEADER_ATTEMPTS_B4_SUC, str(fsl.num_attempts_b4_suc[i]))
                            except IndexError:
                                pass
                            if i==0:
                                enh_pri = True
                                try:
                                    this_cost = item_store.get_cost(this_gear_enhlv)
                                    if this_cost > this_gear.pri_cost:
                                        this_cost = this_gear.pri_cost
                                    else:
                                        enh_pri = False
                                except (KeyError, ItemStoreException):
                                    this_cost = this_gear.pri_cost
                                ptxt = MONNIES_FORMAT.format(this_cost)
                                if enh_pri:
                                    ptxt = 'Enhance: {}'.format(ptxt)
                                child.setText(idx_HEADER_AC_COST, ptxt)
                            elif i==len(fsl.secondary_map)-1:
                                try:
                                    prices = item_store.get_prices(this_gear)
                                    child.setText(idx_HEADER_AC_COST, MONNIES_FORMAT.format(-1*prices[-1]))
                                except (KeyError, ItemStoreException, TypeError):
                                    pass
                            prv_num += amount_fs

    def table_itemChanged(self, t_item: QTreeWidgetItem, col):
        super(TableFSSecondary, self).table_itemChanged(t_item, col)
        self.invalidate_item(t_item)

    def master_gw_sig_gear_changed(self, gw:GearWidget, old_gear:Gear):
        super(TableFSSecondary, self).master_gw_sig_gear_changed(gw, old_gear)
        twi = gw.parent_widget
        self.invalidate_item(twi)
        idx_GEAR_TYPE = self.get_header_index(HEADER_GEAR_TYPE)
        twi.setBackground(idx_GEAR_TYPE, gt_str_to_q_color(gw.gear.gear_type.name).lighter())
        self.add_children(twi)
        self.set_item_data(gw.parent_widget)

    def reload_list(self):
        super(TableFSSecondary, self).reload_list()
        self.refresh_strat()

    def set_common(self, model: Enhance_model, frmMain: lbl_color_MainWindow):
        super(TableFSSecondary, self).set_common(model, frmMain)
        settings = model.settings
        self.prop_in_list = settings.P_FAIL_STACKER_SECONDARY
        self.prop_out_list = settings.P_R_STACKER_SECONDARY
        self.model_add_item_func = model.add_fs_secondary_item
        self.reload_list()
