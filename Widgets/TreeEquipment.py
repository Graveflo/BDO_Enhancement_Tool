# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import numpy
from PyQt5.QtCore import Qt, QThread
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu, QAction
from BDO_Enhancement_Tool.WidgetTools import GearWidget, MONNIES_FORMAT, STR_TWO_DEC_FORMAT, STR_PERCENT_FORMAT, \
    MPThread, TreeWidgetGW, get_gt_color_compare, gt_str_to_q_color
from BDO_Enhancement_Tool.QtCommon.Qt_common import SpeedUpTable, QBlockSig, lbl_color_MainWindow
from BDO_Enhancement_Tool.common import Gear, generate_gear_obj, gear_types
from BDO_Enhancement_Tool.model import SettingsException, Enhance_model
from .Abstract_Gear_Tree import AbstractGearTree, HEADER_NAME, HEADER_GEAR_TYPE, HEADER_BASE_ITEM_COST, HEADER_TARGET


HEADER_CRONSTONE = 'Cronstone'
HEADER_FS = 'FS'
HEADER_COST = 'Cost'
HEADER_MAT_COST = 'Mat Cost'
HEADER_NUM_FAILS = 'Num Fails'
HEADER_PROBABILITY = 'Probability'
HEADER_USES_MEMFRAGS = 'Uses Memfrags'


class TableEquipment(AbstractGearTree):
    HEADERS = [HEADER_NAME, HEADER_GEAR_TYPE, HEADER_BASE_ITEM_COST, HEADER_TARGET, HEADER_CRONSTONE, HEADER_FS,
              HEADER_COST, HEADER_MAT_COST, HEADER_NUM_FAILS, HEADER_PROBABILITY, HEADER_USES_MEMFRAGS]

    def __init__(self, *args, **kwargs):
        super(TableEquipment, self).__init__(*args, **kwargs)
        self.invalidated_gear = set()

    def make_menu(self, menu:QMenu):
        action_update_costs = QAction('Calculate All Costs', menu)
        action_update_costs.triggered.connect(self.cmdEquipCost_clicked)
        menu.addAction(action_update_costs)
        menu.addSeparator()
        super(TableEquipment, self).make_menu(menu)

    def table_add_gear(self, this_gear: Gear, check_state=Qt.Checked):
        top_lvl = super(TableEquipment, self).table_add_gear(this_gear, check_state=check_state)
        idx_NAME = self.get_header_index(HEADER_NAME)
        gear_widget = self.itemWidget(top_lvl, idx_NAME)
        self.invalidated_gear.add(gear_widget.gear)
        gear_widget.chkInclude.stateChanged.connect(lambda: self.frmMain.invalidate_strategy())
        with QBlockSig(self):
            self.add_children(top_lvl)

    def cmdEquipCost_clicked(self):
        model = self.enh_model
        frmMain = self.frmMain

        try:
            model.calc_equip_costs(gear=self.invalidated_gear)
            self.invalidated_gear = set()
        except ValueError as f:
            frmMain.sig_show_message.emit(frmMain.WARNING, str(f))
            return

        idx_NAME = self.get_header_index(HEADER_NAME)
        idx_CRONSTONE = self.get_header_index(HEADER_CRONSTONE)
        idx_FS = self.get_header_index(HEADER_FS)
        idx_COST = self.get_header_index(HEADER_COST)
        idx_MAT_COST = self.get_header_index(HEADER_MAT_COST)
        idx_NUM_FAILS = self.get_header_index(HEADER_NUM_FAILS)
        idx_PROBABILITY = self.get_header_index(HEADER_PROBABILITY)
        idx_USES_MEMFRAGS = self.get_header_index(HEADER_USES_MEMFRAGS)


        def populate_row(this_head, this_gear:Gear, eh_idx):

            cost_vec_l = this_gear.cost_vec[eh_idx]
            restore_cost_vec_min = this_gear.restore_cost_vec_min[eh_idx]
            idx_ = numpy.argmin(this_gear.cost_vec[eh_idx])

            this_head.setText(idx_CRONSTONE, str(this_gear.get_enhance_lvl_idx() in this_gear.cron_use))
            this_head.setText(idx_FS, str(idx_))
            this_head.setText(idx_COST, MONNIES_FORMAT.format(round(cost_vec_l[idx_])))
            this_head.setText(idx_MAT_COST, MONNIES_FORMAT.format(round(restore_cost_vec_min)))

            this_fail_map = numpy.array(this_gear.gear_type.map)[eh_idx]
            #avg_num_fails = numpy.divide(numpy.ones(this_fail_map.shape), this_fail_map)[idx_] - 1
            avg_num_fails = this_gear.gear_type.p_num_atmpt_map[eh_idx][idx_] - 1

            this_head.setText(idx_NUM_FAILS, STR_TWO_DEC_FORMAT.format(avg_num_fails))
            this_head.setText(idx_PROBABILITY, STR_PERCENT_FORMAT.format(this_fail_map[idx_] * 100.0))
            if hasattr(this_gear, 'using_memfrags'):
                this_head.setText(idx_USES_MEMFRAGS, str(this_gear.using_memfrags))

        with SpeedUpTable(self):
            for i in range(0, self.topLevelItemCount()):
                this_head = self.topLevelItem(i)
                gear_widget = self.itemWidget(this_head, idx_NAME)
                this_gear = gear_widget.gear
                eh_idx = this_gear.get_enhance_lvl_idx()
                populate_row(this_head, this_gear, eh_idx)
                for j in range(0, this_head.childCount()):
                    this_child = this_head.child(j)
                    child_gear_widget = self.itemWidget(this_child, idx_NAME)
                    child_gear = child_gear_widget.gear
                    eh_idx = child_gear.get_enhance_lvl_idx()
                    populate_row(this_child, this_gear, eh_idx)

    def create_TreeWidgetItem(self, parent_wid, this_gear, check_state) -> QTreeWidgetItem:
        top_lvl = super(TableEquipment, self).create_TreeWidgetItem(parent_wid, this_gear, check_state)
        idx_NAME = self.get_header_index(HEADER_NAME)
        gear_widget = self.itemWidget(top_lvl, idx_NAME)
        self.create_lvl_cmb(gear_widget, top_lvl=top_lvl)
        self.create_gt_cmb(gear_widget, top_lvl=top_lvl)
        return top_lvl

    def add_children(self, top_lvl_wid: QTreeWidgetItem):
        frmMain = self.frmMain
        idx_NAME = self.get_header_index(HEADER_NAME)
        idx_GEAR_TYPE = self.get_header_index(HEADER_GEAR_TYPE)
        idx_BASE_ITEM_COST = self.get_header_index(HEADER_BASE_ITEM_COST)
        idx_TARGET = self.get_header_index(HEADER_TARGET)
        master_gw = self.itemWidget(top_lvl_wid, idx_NAME)
        this_gear = master_gw.gear
        these_lvls = this_gear.guess_target_lvls(intersect=None, excludes=None)

        prunes = []

        for i in range(0, top_lvl_wid.childCount()):
            child = top_lvl_wid.child(0)
            child_gw: GearWidget = self.itemWidget(child, idx_NAME)
            top_lvl_wid.takeChild(0)

            if not child_gw.chkInclude.isChecked():
                prunes.append(child_gw.gear.enhance_lvl)
            try:
                child_gw.chkInclude.disconnect()
            except TypeError:
                pass


        def chk_click(state):
            spinner = self.sender()
            lvl = spinner.__dict__['lvl']
            if state == Qt.Unchecked:
                try:
                    this_gear.target_lvls.remove(lvl)
                except ValueError:
                    pass
            else:
                if lvl not in this_gear.target_lvls:
                    this_gear.target_lvls.append(lvl)
            #self.model.invalidate_enahce_list()

        for lvl in these_lvls:
            twi = QTreeWidgetItem(top_lvl_wid, [''] * self.columnCount())
            _gear = this_gear.duplicate()
            _gear.set_enhance_lvl(lvl)
            this_check_state = Qt.Unchecked if lvl in prunes or lvl not in this_gear.target_lvls else Qt.Checked
            this_gw = GearWidget(_gear, frmMain, edit_able=False, display_full_name=False,
                                 check_state=this_check_state)
            self.make_menu(this_gw.context_menu)
            this_gw.chkInclude.__dict__['lvl'] = lvl
            this_gw.chkInclude.stateChanged.connect(chk_click)
            self.setItemWidget(twi, idx_NAME, this_gw)
            top_lvl_wid.addChild(twi)
            gt_txt = master_gw.cmbType.currentText()
            twi.setText(idx_GEAR_TYPE, gt_txt)
            twi.setText(idx_BASE_ITEM_COST, top_lvl_wid.text(2))
            twi.setText(idx_TARGET, _gear.enhance_lvl)
            twi.setForeground(idx_GEAR_TYPE, Qt.black)
            twi.setBackground(idx_GEAR_TYPE, gt_str_to_q_color(gt_txt).lighter())

    def reload_list(self):
        enhance_me, r_enhance_me = super(TableEquipment, self).reload_list()
        self.invalidated_gear = set(enhance_me + r_enhance_me)

    def set_common(self, model: Enhance_model, frmMain: lbl_color_MainWindow):
        settings = model.settings
        super(TableEquipment, self).set_common(model, frmMain)
        self.prop_in_list = settings.P_ENHANCE_ME
        self.prop_out_list = settings.P_R_ENHANCE_ME
        self.main_invalidate_func = frmMain.invalidate_equipment
        self.model_add_item_func = model.add_equipment_item
