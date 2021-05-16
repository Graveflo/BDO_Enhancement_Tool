# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
from typing import List

import numpy
from PyQt5.QtCore import Qt, QThread, QModelIndex, pyqtSignal
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu, QAction
from BDO_Enhancement_Tool.WidgetTools import GearWidget, MONNIES_FORMAT, STR_TWO_DEC_FORMAT, STR_PERCENT_FORMAT, \
    MPThread, TreeWidgetGW, get_gt_color_compare, gt_str_to_q_color
from BDO_Enhancement_Tool.QtCommon.Qt_common import SpeedUpTable, QBlockSig, lbl_color_MainWindow
from BDO_Enhancement_Tool.common import Gear, generate_gear_obj, gear_types, ItemStore
from BDO_Enhancement_Tool.model import Enhance_model, Invalid_FS_Parameters
from BDO_Enhancement_Tool.qt_UI_Common import pix, STR_PIC_CRON, STR_CALC_PIC
from BDO_Enhancement_Tool.enh_for_profit import GearManager, GearNotProfitableException
from BDO_Enhancement_Tool.utilities import fmt_traceback
from QtCommon.Qt_common import NoScrollCombo, QColor
from .Abstract_Gear_Tree import AbstractGearTree, HEADER_NAME, HEADER_GEAR_TYPE, HEADER_BASE_ITEM_COST, HEADER_TARGET



class EnhForProfitLevelCmb(NoScrollCombo):
    def __init__(self, gear_obj:Gear, *args, **kwargs):
        super(EnhForProfitLevelCmb, self).__init__(*args, **kwargs)
        self.gear_obj = gear_obj
        self.set_levels()

    def set_levels(self):
        gear = self.gear_obj
        levels = list(gear.gear_type.lvl_map.keys())
        levels.sort(key=gear.gear_type.enumerate_gt_lvl)
        levels.insert(0, 'Auto')
        for x in levels[:-1]:
            self.addItem(x)

    def get_level(self):
        return self.gear_obj.gear_type.lvl_map[self.currentText()]


HEADER_SELL_OUT = 'Sell-out Level'
HEADER_FS = 'FS'
HEADER_MARGIN = 'Margin'
HEADER_COST = 'Cost'
HEADER_CRONSTONE = 'Cron?'



class TableForProfit(AbstractGearTree):
    sig_fs_list_updated = pyqtSignal()
    HEADERS = [HEADER_NAME, HEADER_GEAR_TYPE, HEADER_BASE_ITEM_COST, HEADER_TARGET, HEADER_SELL_OUT, HEADER_FS,
               HEADER_MARGIN, HEADER_COST, HEADER_CRONSTONE]

    def __init__(self, *args, **kwargs):
        super(TableForProfit, self).__init__(*args, **kwargs)
        self.invalidated_gear = set()

    def table_add_gear(self, this_gear: Gear, check_state=Qt.Checked):
        idx_NAME = self.get_header_index(HEADER_NAME)
        top_lvl = super(TableForProfit, self).table_add_gear(this_gear, check_state=check_state)
        gw:GearWidget = self.itemWidget(top_lvl, idx_NAME)
        self.invalidated_gear.add(gw.gear)

    def gw_check_state_changed(self, gw:GearWidget, state):
        this_gear = gw.gear
        #if state == Qt.Checked:
        #    self.enh_model.include_fs_secondary_item(this_gear)
        #else:
        #    self.enh_model.exclude_fs_secondary_item(this_gear)

    def master_gw_sig_gear_changed(self, gw: GearWidget, old_gear:Gear):
        if old_gear in self.invalidated_gear:
            self.invalidated_gear.remove(old_gear)
        super(TableForProfit, self).master_gw_sig_gear_changed(gw, old_gear)
        self.set_item_data(gw.parent_widget)
        twi = gw.parent_widget
        idx_GEAR_TYPE = self.get_header_index(HEADER_GEAR_TYPE)
        twi.setBackground(idx_GEAR_TYPE, gt_str_to_q_color(gw.gear.gear_type.name).lighter())

    def cmdCalc_clicked(self):
        model = self.enh_model
        frmMain = self.frmMain

        send_fs_signal = model.fs_needs_update or model.fs_secondary_needs_update
        if send_fs_signal:
            model.calcFS()

        #if len(self.invalidated_gear) == 0:
        #    return  This is handled in model.calc_equip_costs

        try:
            model.calc_equip_cost_u(self.invalidated_gear, model.cum_fs_cost)
            self.invalidated_gear = set()
        except ValueError as f:
            print(fmt_traceback(f.__traceback__))
            frmMain.sig_show_message.emit(frmMain.WARNING, str(f))
            return
        except Invalid_FS_Parameters as e:
            frmMain.sig_show_message.emit(frmMain.WARNING, str(e))
            return

        if send_fs_signal:
            # This updates the UI to the fail stack list being updated from model.calc_equip_costs
            self.sig_fs_list_updated.emit()

        idx_NAME = self.get_header_index(HEADER_NAME)
        idx_TARGET = self.get_header_index(HEADER_TARGET)
        idx_CRONSTONE = self.get_header_index(HEADER_CRONSTONE)
        idx_FS = self.get_header_index(HEADER_FS)
        idx_COST = self.get_header_index(HEADER_COST)
        idx_SELL_OUT = self.get_header_index(HEADER_SELL_OUT)
        idx_MARGIN = self.get_header_index(HEADER_MARGIN)

        model = self.enh_model
        settings = model.settings
        tax = settings[settings.P_MARKET_TAX]
        item_store = settings[settings.P_ITEM_STORE]
        with SpeedUpTable(self):
            for i in range(0, self.topLevelItemCount()):
                this_head = self.topLevelItem(i)
                this_head.takeChildren()
                gear_widget:GearWidget = self.itemWidget(this_head, idx_NAME)
                this_gear:Gear = gear_widget.gear
                manager = GearManager(this_gear)
                manager.calculate_margins()
                if gear_widget.cmbLevel.currentIndex() == 0:
                    try:
                        start, stop = manager.find_best_margin()
                        lvl_txt = this_gear.gear_type.idx_lvl_map[start]
                        margin = manager.get_margin(start, stop)
                    except GearNotProfitableException:
                        margin = 0
                    pure_margin_stop = manager.find_margin_idx_for_pure()
                    pure_margin = manager.get_margin(-1, pure_margin_stop)
                    if pure_margin < margin:
                        start = -1
                        stop = pure_margin_stop
                        margin = pure_margin
                        lvl_txt = 'From Scratch'
                    if margin >= 0:
                        this_head.setText(idx_SELL_OUT, 'Not profitable')
                        continue
                    gear_widget.cmbLevel.setItemText(0, 'Auto({})'.format(lvl_txt))
                else:
                    start = gear_widget.cmbLevel.get_level()
                    stop = manager.find_best_margin_for_start(start)
                    margin = manager.get_margin(start, stop)
                fs = numpy.argmin(this_gear.cost_vec[stop])
                this_gear.set_enhance_lvl(this_gear.gear_type.idx_lvl_map[start + 1])
                self.add_children(this_head, start, stop, manager)
                this_head.setText(idx_SELL_OUT, str(this_gear.gear_type.idx_lvl_map[stop]))
                this_head.setText(idx_MARGIN, MONNIES_FORMAT.format(margin))
                this_head.setText(idx_FS, str(fs))

    def add_children(self, top_lvl: QTreeWidgetItem, start, stop, manager):
        model = self.enh_model
        idx_NAME = self.get_header_index(HEADER_NAME)
        idx_GEAR_TYPE = self.get_header_index(HEADER_GEAR_TYPE)
        master_gw = self.itemWidget(top_lvl, idx_NAME)
        this_gear:Gear = master_gw.gear
        gear_type = this_gear.gear_type

        idx_NAME = self.get_header_index(HEADER_NAME)
        idx_TARGET = self.get_header_index(HEADER_TARGET)
        idx_CRONSTONE = self.get_header_index(HEADER_CRONSTONE)
        idx_FS = self.get_header_index(HEADER_FS)
        idx_COST = self.get_header_index(HEADER_COST)
        idx_SELL_OUT = self.get_header_index(HEADER_SELL_OUT)
        idx_MARGIN = self.get_header_index(HEADER_MARGIN)

        if start > -1:
            actual_start_idx = this_gear.gear_type.idx_lvl_map[start]
        else:
            actual_start_idx = 'From Scratch'
        act_start = start+1

        top_lvl.takeChildren()

        for i in range(act_start, len(gear_type.map)):
            if i == stop:  # This is the top level widget
                continue
            margin = manager.get_margin(start, i)
            twi = QTreeWidgetItem(top_lvl, [''] * self.columnCount())
            lvl = this_gear.gear_type.idx_lvl_map[i]
            _gear = this_gear.duplicate()
            _gear.set_enhance_lvl(lvl)
            this_gw = GearWidget(_gear, model, edit_able=False, display_full_name=True)
            self.setItemWidget(twi, idx_NAME, this_gw)
            top_lvl.addChild(twi)
            twi.setText(idx_GEAR_TYPE, gear_type.name)
            twi.setForeground(idx_GEAR_TYPE, Qt.black)
            twi.setBackground(idx_GEAR_TYPE, gt_str_to_q_color(gear_type.name).lighter())
            twi.setText(idx_TARGET, str(actual_start_idx))
            twi.setText(idx_SELL_OUT, str(lvl))
            fs = numpy.argmin(this_gear.cost_vec[i])
            twi.setText(idx_FS, str(fs))
            twi.setText(idx_MARGIN, MONNIES_FORMAT.format(margin))

    def create_TreeWidgetItem(self, parent_wid, this_gear, check_state, icon_overlay=True) -> QTreeWidgetItem:
        top_lvl = super(TableForProfit, self).create_TreeWidgetItem(parent_wid, this_gear, check_state, icon_overlay=False)
        idx_HEADER_TARGET = self.get_header_index(HEADER_TARGET)
        #top_lvl.setText(idx_HEADER_TARGET, 'Auto')
        idx_NAME = self.get_header_index(HEADER_NAME)
        gear_widget: GearWidget = self.itemWidget(top_lvl, idx_NAME)
        cmdLevel = EnhForProfitLevelCmb(this_gear, self)
        gear_widget.cmbLevel = cmdLevel
        self.setItemWidget(top_lvl, idx_HEADER_TARGET, cmdLevel)
        def changed(x):
            self.invalidated_gear.add(this_gear)
        cmdLevel.currentTextChanged.connect(changed)
        return top_lvl

    def invalidate_items(self, item_list:List[QTreeWidgetItem]):
        gear_set = super(TableForProfit, self).invalidate_items(item_list)
        self.invalidated_gear.update(gear_set)
        for itm in item_list:
            gw = self.itemWidget(itm, 0)
            gear = gw.gear
            parent_cost = int(round(gear.base_item_cost))
            str_monies = MONNIES_FORMAT.format(parent_cost)
            with QBlockSig(self):
                itm.setText(2, str_monies)
                if hasattr(gear, 'excl'):
                    itm.setForeground(2, QColor(Qt.red).lighter())
                for i in range(4, len(self.HEADERS)):
                    itm.setText(i, '')
                for i in range(0, itm.childCount()):
                    child = itm.child(i)
                    child_gw = self.itemWidget(child, 0)
                    child_gw.gear.set_base_item_cost(parent_cost)
                    #child.setText(2, str_monies)
                    for i in range(4, len(self.HEADERS)):
                        child.setText(i, '')
        self.enh_model.invalidate_enahce_list()
        return gear_set

    def reload_list(self):
        super(TableForProfit, self).reload_list()

    def action_fs_with_triggered(self):
        pass

    def make_menu(self, menu:QMenu):
        super(TableForProfit, self).make_menu(menu)
        menu.addSeparator()
        action_update_costs = QAction('Calculate All Costs', menu)
        action_update_costs.setIcon(pix.get_icon(STR_CALC_PIC))
        action_update_costs.triggered.connect(self.cmdCalc_clicked)
        menu.addAction(action_update_costs)

        action_fs_with = QAction('Fail stack with this list', menu)
        action_fs_with.setCheckable(True)
        action_fs_with.setChecked(False)
        action_fs_with.triggered.connect(self.action_fs_with_triggered)
        menu.addAction(action_fs_with)
        menu.addSeparator()

    def set_common(self, model: Enhance_model, frmMain: lbl_color_MainWindow):
        super(TableForProfit, self).set_common(model, frmMain)
        settings = model.settings
        self.prop_in_list = settings.P_ENH_FOR_PROFIT
        self.prop_out_list = settings.P_R_FOR_PROFIT
        self.model_add_item_func = model.add_for_profit_item
        self.reload_list()
