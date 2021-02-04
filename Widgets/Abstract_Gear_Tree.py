# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import numpy
from PyQt5.QtCore import Qt, QThread
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu, QAction
from BDO_Enhancement_Tool.WidgetTools import GearWidget, MONNIES_FORMAT, STR_TWO_DEC_FORMAT, STR_PERCENT_FORMAT, \
    MPThread, TreeWidgetGW, get_gt_color_compare, gt_str_to_q_color
from BDO_Enhancement_Tool.QtCommon.Qt_common import SpeedUpTable, QBlockSig
from BDO_Enhancement_Tool.common import Gear, generate_gear_obj, gear_types
from BDO_Enhancement_Tool.model import SettingsException

from .Abstract_Table import AbstractTable

HEADER_NAME = 'Name'
HEADER_GEAR_TYPE = 'Gear Type'
HEADER_BASE_ITEM_COST = 'Base Cost'
HEADER_TARGET = 'Target'


class AbstractGearTree(QTreeWidget, AbstractTable):
    HEADERS = [HEADER_NAME, HEADER_GEAR_TYPE, HEADER_BASE_ITEM_COST, HEADER_TARGET]

    def __init__(self, *args, **kwargs):
        super(AbstractGearTree, self).__init__(*args, **kwargs)
        self.itemChanged.connect(self.table_Equip_itemChanged)
        self.itemDoubleClicked.connect(self.itemDoubleClicked_callback)
        self.prop_in_list = None
        self.prop_out_list = None
        self.main_invalidate_func = None
        self.model_add_item_func = None

    def make_menu(self, menu:QMenu):
        action_add_gear = QAction('Add Gear', menu)
        action_add_gear.triggered.connect(self.add_item_basic)
        menu.addAction(action_add_gear)
        action_remove_gear = QAction('Remove Gear(s)', menu)
        action_remove_gear.triggered.connect(self.remove_selected_equipment)
        menu.addAction(action_remove_gear)
        menu.addSeparator()
        action_mp_update = QAction('MP: Update All', menu)
        action_mp_update.setEnabled(False)
        menu.addAction(action_mp_update)

    def remove_selected_equipment(self):
        tmodel = self.enh_model
        tsettings = tmodel.settings

        effect_list = [i for i in self.selectedItems()]

        idx_NAME = self.get_header_index(HEADER_NAME)

        enhance_me = tsettings[self.prop_in_list]
        r_enhance_me = tsettings[self.prop_out_list]

        for i in effect_list:
            thic = self.itemWidget(i, idx_NAME).gear
            try:
                enhance_me.remove(thic)
            except ValueError:
                pass
            try:
                r_enhance_me.remove(thic)
            except ValueError:
                pass
            p = i.parent()
            if p is None:
                self.takeTopLevelItem(self.indexOfTopLevelItem(i))
        tsettings.changes_made = True

    def add_item_basic(self):
        model = self.enh_model

        gear_type = list(gear_types.items())[0][1]
        enhance_lvl = list(gear_type.lvl_map.keys())[0]

        this_gear = generate_gear_obj(model.settings, base_item_cost=0, enhance_lvl=enhance_lvl, gear_type=gear_type)

        self.table_add_gear(this_gear)
        self.model_add_item_func(this_gear)

    def MP_callback(self, thread:QThread, ret):
        frmMain = self.frmMain
        if isinstance(ret, Exception):
            print(ret)
            frmMain.sig_show_message.emit(frmMain.CRITICAL, 'Error contacting central market')
        else:
            with QBlockSig(self):
                self.invalidate_equipment()
            frmMain.sig_show_message.emit(frmMain.REGULAR, 'Enhancement gear prices updated')
        thread.wait(2000)
        if thread.isRunning():
            thread.terminate()
        frmMain.mp_threads.remove(thread)

    def cmdEnhanceMeMP_clicked(self):
        model = self.enh_model
        settings = model.settings
        thread = MPThread(model.update_costs, settings[self.prop_in_list] + settings[self.prop_out_list])
        self.mp_threads.append(thread)
        thread.sig_done.connect(self.MP_callback)
        thread.start()

    def table_Equip_itemChanged(self, t_item: QTreeWidgetItem, col):
        frmMain = self.frmMain
        idx_NAME = self.get_header_index(HEADER_NAME)
        gear_widget = self.itemWidget(t_item, idx_NAME)
        this_gear = gear_widget.gear
        idx_BASE_ITEM_COST = self.get_header_index(HEADER_BASE_ITEM_COST)
        if col == idx_BASE_ITEM_COST:
            # columns that are not 0 are non-cosmetic and may change the cost values
            try:
                try:
                    str_val = t_item.text(idx_BASE_ITEM_COST).replace(',', '')
                    if str_val == '':
                        str_val='0'
                    this_cost_set = float(str_val)
                    this_gear.set_base_item_cost(this_cost_set)
                    self.main_invalidate_func(t_item)
                except ValueError:
                    frmMain.sig_show_message.emit(frmMain.REGULAR, 'Invalid number: {}'.format(t_item.text(idx_BASE_ITEM_COST)))
            except ValueError:
                frmMain.sig_show_message.emit(frmMain.WARNING, 'Cost must be a number.')

    def create_TreeWidgetItem(self, parent_wid, this_gear, check_state, icon_overlay=True) -> QTreeWidgetItem:
        frmMain = self.frmMain
        top_lvl = TreeWidgetGW(parent_wid, [''] * self.columnCount())
        top_lvl.setFlags(top_lvl.flags() | Qt.ItemIsEditable)

        f_two = GearWidget(this_gear, frmMain, default_icon=frmMain.search_icon, check_state=check_state,
                           edit_able=True, enhance_overlay=icon_overlay)
        frmMain.give_gear_widget_upgrade_downgrade(f_two)
        f_two.context_menu.addSeparator()
        self.make_menu(f_two.context_menu)

        idx_NAME = self.get_header_index(HEADER_NAME)
        idx_BASE_ITEM_COST = self.get_header_index(HEADER_BASE_ITEM_COST)
        idx_GEAR_TYPE = self.get_header_index(HEADER_GEAR_TYPE)
        idx_TARGET = self.get_header_index(HEADER_TARGET)

        gt_name = this_gear.gear_type.name

        f_two.add_to_tree(self, top_lvl, col=idx_NAME)
        top_lvl.setText(idx_BASE_ITEM_COST, MONNIES_FORMAT.format(int(round(this_gear.base_item_cost))))
        top_lvl.setText(idx_GEAR_TYPE, gt_name)
        top_lvl.setText(idx_TARGET, this_gear.enhance_lvl)
        top_lvl.setForeground(idx_GEAR_TYPE, Qt.black)
        top_lvl.setBackground(idx_GEAR_TYPE, gt_str_to_q_color(gt_name).lighter())

        return top_lvl

    def create_gt_cmb(self, gear_widget:GearWidget, top_lvl=None):
        this_gear = gear_widget.gear
        if top_lvl is None:
            top_lvl = self.find_top_lvl_item_from_gear(this_gear)

        gear_widget.create_gt_cmb(self)

        cmb_gt = gear_widget.cmbType

        idx_GEAR_TYPE = self.get_header_index(HEADER_GEAR_TYPE)

        cmb_gt.currentTextChanged.connect(lambda x: top_lvl.setText(idx_GEAR_TYPE, get_gt_color_compare(x)))
        self.setItemWidget(top_lvl, idx_GEAR_TYPE, cmb_gt)

    def create_lvl_cmb(self, gear_widget:GearWidget, top_lvl=None):
        this_gear = gear_widget.gear
        if top_lvl is None:
            top_lvl = self.find_top_lvl_item_from_gear(this_gear)

        gear_widget.create_lvl_cmb(self)
        cmb_enh = gear_widget.cmbLevel

        idx_TARGET = self.get_header_index(HEADER_TARGET)

        cmb_enh.currentTextChanged.connect(lambda x: top_lvl.setText(idx_TARGET, get_gt_color_compare(x)))

        self.setItemWidget(top_lvl, idx_TARGET, cmb_enh)


    def table_add_gear(self, this_gear: Gear, check_state=Qt.Checked) -> QTreeWidgetItem:
        idx_NAME = self.get_header_index(HEADER_NAME)
        with QBlockSig(self):
            top_lvl = self.create_TreeWidgetItem(self, this_gear, check_state)

            master_gw: GearWidget = self.itemWidget(top_lvl, idx_NAME)

            master_gw.sig_gear_changed.connect(self.master_gw_sig_gear_changed)
            self.addTopLevelItem(top_lvl)
            self.clearSelection()
        settings = self.enh_model.settings

        def chkInclude_stateChanged(state):
            r_enhance_me = settings[self.prop_out_list]
            enhance_me = settings[self.prop_in_list]

            this_gear = master_gw.gear
            if state == Qt.Checked:
                try:
                    r_enhance_me.remove(this_gear)
                except ValueError:
                    # Item already removed. This is likely not a check change on col 0
                    pass

                enhance_me.append(this_gear)
                settings[self.prop_in_list] = list(set(enhance_me))
            else:
                try:
                    enhance_me.remove(this_gear)
                except ValueError:
                    # Item already removed. This is likely not a check change on col 0
                    pass

                r_enhance_me.append(this_gear)
                settings[self.prop_out_list] = list(set(r_enhance_me))

        master_gw.chkInclude.stateChanged.connect(chkInclude_stateChanged)

        self.resizeColumnToContents(idx_NAME)
        cmbType = master_gw.cmbType
        cmbLevel = master_gw.cmbLevel
        if cmbType is not None:
            master_gw.cmbType.currentIndexChanged.connect(lambda: self.main_invalidate_func(top_lvl))
        if cmbLevel is not None:
            master_gw.cmbLevel.currentIndexChanged.connect(lambda: self.main_invalidate_func(top_lvl))
        return top_lvl

    def master_gw_sig_gear_changed(self, gw: GearWidget):
        self.add_children(gw.parent_widget)
        self.main_invalidate_func(gw.parent_widget)

    def itemDoubleClicked_callback(self, item, col):
        idx_BASE_ITEM_COST = self.get_header_index(HEADER_BASE_ITEM_COST)
        if col == idx_BASE_ITEM_COST:
            self.editItem(item, col)

    def find_top_lvl_item_from_gear(self, gear:Gear) -> QTreeWidgetItem:
        idx_NAME = self.get_header_index(HEADER_NAME)
        for i in range(self.topLevelItemCount()):
            this_i = self.topLevelItem(i)
            gw = self.itemWidget(this_i, idx_NAME)
            if gear == gw.gear:
                return this_i
        raise Exception('Gear not found on list {}'.format(gear.get_full_name()))

    def reload_list(self):
        settings = self.enh_model.settings

        try:
            enhance_me = settings[self.prop_in_list]
            r_enhance_me = settings[self.prop_out_list]
        except KeyError as e:
            raise SettingsException('Key missing for enhancement gear', e)

        with SpeedUpTable(self):
            for gear in enhance_me:
                with QBlockSig(self):
                    self.table_add_gear(gear)
            for gear in r_enhance_me:
                with QBlockSig(self):
                    self.table_add_gear(gear, check_state=Qt.Unchecked)
        self.setSortingEnabled(True)
        return enhance_me, r_enhance_me
