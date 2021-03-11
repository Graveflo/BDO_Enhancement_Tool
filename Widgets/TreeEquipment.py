# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import numpy
from PyQt5.QtCore import Qt, QThread, QModelIndex, pyqtSignal
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu, QAction
from BDO_Enhancement_Tool.WidgetTools import GearWidget, MONNIES_FORMAT, STR_TWO_DEC_FORMAT, STR_PERCENT_FORMAT, \
    MPThread, TreeWidgetGW, get_gt_color_compare, gt_str_to_q_color
from BDO_Enhancement_Tool.QtCommon.Qt_common import SpeedUpTable, QBlockSig, lbl_color_MainWindow
from BDO_Enhancement_Tool.common import Gear, generate_gear_obj, gear_types
from BDO_Enhancement_Tool.model import SettingsException, Enhance_model, Invalid_FS_Parameters
from BDO_Enhancement_Tool.qt_UI_Common import pix, STR_PIC_CRON, STR_CALC_PIC
from BDO_Enhancement_Tool.dlgGearWindow import GearWindow
from BDO_Enhancement_Tool.utilities import fmt_traceback

from .Abstract_Gear_Tree import AbstractGearTree, HEADER_NAME, HEADER_GEAR_TYPE, HEADER_BASE_ITEM_COST, HEADER_TARGET


HEADER_CRONSTONE = 'Cronstone'
HEADER_FS = 'FS'
HEADER_COST = 'Cost'
HEADER_MAT_COST = 'Mat Cost'
HEADER_NUM_FAILS = 'Num Fails'
HEADER_PROBABILITY = 'Probability'
HEADER_USES_MEMFRAGS = 'Uses Memfrags'


class TableEquipment(AbstractGearTree):
    sig_fs_list_updated = pyqtSignal()
    HEADERS = [HEADER_NAME, HEADER_GEAR_TYPE, HEADER_BASE_ITEM_COST, HEADER_TARGET, HEADER_CRONSTONE, HEADER_FS,
              HEADER_COST, HEADER_MAT_COST, HEADER_NUM_FAILS, HEADER_PROBABILITY, HEADER_USES_MEMFRAGS]

    def __init__(self, *args, **kwargs):
        super(TableEquipment, self).__init__(*args, **kwargs)
        self.invalidated_gear = set()
        self.gear_windows = set()

    def make_menu(self, menu:QMenu):
        super(TableEquipment, self).make_menu(menu)
        menu.addSeparator()
        action_update_costs = QAction('Calculate All Costs', menu)
        action_update_costs.setIcon(pix.get_icon(STR_CALC_PIC))
        action_update_costs.triggered.connect(self.cmdEquipCost_clicked)
        menu.addAction(action_update_costs)
        menu.addSeparator()

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

        send_fs_signal = model.fs_needs_update

        #if len(self.invalidated_gear) == 0:
        #    return  This is handled in model.calc_equip_costs

        try:
            model.calc_equip_costs(gear=self.invalidated_gear)
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

            gw:GearWidget = self.itemWidget(this_head, idx_NAME)


            gw.update_data()
            uses_crons = eh_idx in this_gear.cron_use
            if uses_crons:
                if gw.trinket is None:
                    gw.set_trinket(pix[STR_PIC_CRON])
            else:
                if gw.trinket is not None:
                    gw.set_trinket(None)

            this_head.setText(idx_CRONSTONE, str(uses_crons))
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
                this_gear:Gear = gear_widget.gear
                eh_idx = this_gear.get_enhance_lvl_idx()
                populate_row(this_head, this_gear, eh_idx)
                for j in range(0, this_head.childCount()):
                    this_child = this_head.child(j)
                    child_gear_widget = self.itemWidget(this_child, idx_NAME)
                    child_gear = child_gear_widget.gear
                    eh_idx = child_gear.get_enhance_lvl_idx()
                    populate_row(this_child, this_gear, eh_idx)

    def create_TreeWidgetItem(self, parent_wid, this_gear, check_state, icon_overlay=True) -> QTreeWidgetItem:
        top_lvl = super(TableEquipment, self).create_TreeWidgetItem(parent_wid, this_gear, check_state, icon_overlay=icon_overlay)
        idx_NAME = self.get_header_index(HEADER_NAME)
        gear_widget:GearWidget = self.itemWidget(top_lvl, idx_NAME)
        if gear_widget.gear.item_id is not None:
            self.set_gear_not_editable(gear_widget)
        else:
            gear_widget.sig_gear_changed.connect(self.set_gear_not_editable)
        self.create_lvl_cmb(gear_widget, top_lvl=top_lvl)
        self.create_gt_cmb(gear_widget, top_lvl=top_lvl)
        return top_lvl

    def set_gear_not_editable(self, gw:GearWidget):
        if gw.edit_able:
            gw.set_editable(False)
            gw.labelIcon.sigMouseLeftClick.connect(lambda:self.gear_widget_mouse_click(gw))

    def gear_widget_mouse_click(self, gw:GearWidget):
        gw = GearWindow(self.enh_model, gw.gear)
        gw.sig_closed.connect(self.gear_window_closed)
        self.gear_windows.add(gw)
        gw.show()

    def gear_window_closed(self, gw:GearWindow):
        if gw in self.gear_windows:
            self.gear_windows.remove(gw)

    def gw_check_state_changed(self, gw:GearWidget, state):
        this_gear = gw.gear
        if state == Qt.Checked:
            self.enh_model.include_enhance_me(this_gear)
        else:
            self.enh_model.exclude_enhance_me(this_gear)

    def add_children(self, top_lvl_wid: QTreeWidgetItem):
        frmMain = self.frmMain
        model = self.enh_model
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
            this_gw = GearWidget(_gear, model, edit_able=False, display_full_name=False,
                                 check_state=this_check_state)
            this_gw.sig_error.connect(self.frmMain.sig_show_message)
            this_gw.sig_layout_changed.connect(lambda: self.resizeColumnToContents(0))
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
        self.reload_list()
        try:
            if len(self.invalidated_gear) > 0:
                self.cmdEquipCost_clicked()
        except Invalid_FS_Parameters:
            pass

    def check_index_widget_menu(self, index:QModelIndex, menu:QMenu):
        item = self.itemFromIndex(index)
        if item is not None:
            gw = self.itemWidget(item, self.get_header_index(HEADER_NAME))
            if isinstance(gw, GearWidget):
                if len(menu.actions()) > 0:
                    menu.addSeparator()
                action_downgrade = QAction('Downgrade', menu)
                action_downgrade.triggered.connect(lambda: self.frmMain.downgrade(gw))
                menu.addAction(action_downgrade)
                action_upgrade = QAction('Upgrade', menu)
                action_upgrade.triggered.connect(lambda: self.frmMain.simulate_success_gear(gw.gear, this_item=gw.parent_widget))
                menu.addAction(action_upgrade)
