# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑  ❧
"""
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QTableWidget, QMenu, QTableWidgetItem
from PyQt6.QtCore import QThread, Qt, QModelIndex

from BDO_Enhancement_Tool.model import SettingsException
from BDO_Enhancement_Tool.WidgetTools import QBlockSig, MONNIES_FORMAT, MPThread, \
    GearWidget, set_cell_color_compare, set_cell_lvl_compare, monnies_twi_factory
from BDO_Enhancement_Tool.qt_UI_Common import STR_LENS_PATH, COLOR_CUSTOM_PRICE
from BDO_Enhancement_Tool.Core.Gear import Gear, generate_gear_obj, gear_types
from BDO_Enhancement_Tool.Core.ItemStore import ItemStore
from BDO_Enhancement_Tool.Qt_common import SpeedUpTable, clear_table
from BDO_Enhancement_Tool.qt_UI_Common import pix, STR_PLUS_PIC, STR_MINUS_PIC, STR_GOLD_PIC
from BDO_Enhancement_Tool.mp_login import CentralMarketPriceUpdator

from .Abstract_Table import AbstractTable

HEADER_NAME = 'Name'
HEADER_GEAR_TYPE = 'Gear Type'
HEADER_BASE_ITEM_COST = 'Base Item Cost'
HEADER_TARGET = 'Target'


class AbstractTableFS(QTableWidget, AbstractTable):
    HEADERS = [HEADER_NAME, HEADER_GEAR_TYPE, HEADER_BASE_ITEM_COST, HEADER_TARGET]

    def __init__(self, *args, **kwargs):
        super(AbstractTableFS, self).__init__(*args, **kwargs)
        self.prop_in_list = None
        self.prop_out_list = None
        self.main_invalidate_func = None
        self.model_invalidate_func = None
        self.model_add_item_func = None

        self.setSortingEnabled(True)
        self.cellChanged.connect(self.cellChanged_callback)

    def mouseReleaseEvent(self, a0) -> None:
        super(AbstractTableFS, self).mouseReleaseEvent(a0)
        AbstractTable.mouseReleaseEvent(self, a0)

    def cellChanged_callback(self, row, col):
        idx_NAME = self.HEADERS.index(HEADER_NAME)
        gw = self.cellWidget(row, idx_NAME)

        this_gear = gw.gear
        idx_BASE_ITEM_COST = self.get_header_index(HEADER_BASE_ITEM_COST)

        if col == idx_BASE_ITEM_COST:
            t_cost = self.item(row, col)
            str_this_item = t_cost.text()
            if str_this_item == '':
                str_this_item = '0'
            try:
                try:
                    this_cost_set = float(str_this_item)
                    item_store = self.enh_model.item_store()
                    item_store.override_gear_price(this_gear, -1, this_cost_set)
                    t_item = self.item(row, idx_BASE_ITEM_COST)
                    t_item.setForeground(COLOR_CUSTOM_PRICE)
                    this_gear.set_base_item_cost(this_cost_set)
                except ValueError:
                    self.frmMain.sig_show_message.emit(self.frmMain.REGULAR, 'Invalid number: {}'.format(str_this_item))
            except ValueError:
                self.frmMain.sig_show_message.emit(self.frmMain.WARNING, 'Cost must be a number.')

    def MPThread_sig_done(self, thread: QThread, ret):
        if isinstance(ret, Exception):
            return
        with QBlockSig(self):
            for i in range(self.rowCount()):
                self.set_item_data(i)
        self.model_invalidate_func()
        self.main_invalidate_func()

    def action_table_FS_remove_triggered(self):
        tmodel = self.enh_model
        tsettings = tmodel.settings
        idx_NAME = self.HEADERS.index(HEADER_NAME)

        effect_list = list(set([i.row() for i in self.selectedItems()]))
        effect_list.sort()
        effect_list.reverse()

        fail_stackers = tsettings[self.prop_in_list]
        r_fail_stackers = tsettings[self.prop_out_list]

        for i in effect_list:
            thic = self.cellWidget(i, idx_NAME).gear
            if thic in fail_stackers:
                fail_stackers.remove(thic)
                self.model_invalidate_func()

            if thic in r_fail_stackers:
                r_fail_stackers.remove(thic)

            self.removeRow(i)
        tsettings.changes_made = True

    def action_table_FS_add_triggered(self, bool_):
        model = self.enh_model

        gear_type = list(gear_types.items())[0][1]
        enhance_lvl = list(gear_type.lvl_map.keys())[0]
        this_gear = generate_gear_obj(model.settings, base_item_cost=0, enhance_lvl=enhance_lvl, gear_type=gear_type)
        self.table_FS_add_gear(this_gear)
        self.model_add_item_func(this_gear)
        self.main_invalidate_func()

    def fs_gear_sig_gear_changed(self, gw: GearWidget, old_gear:Gear):
        model = self.enh_model
        this_gear:Gear = gw.gear
        model.swap_gear(old_gear, this_gear)
        self.set_item_data(gw.row())

    def table_FS_add_gear(self, this_gear:Gear, check_state=Qt.CheckState.Checked):
        frmMain = self.frmMain
        model = self.enh_model
        rc = self.rowCount()

        idx_HEADER_NAME = self.get_header_index(HEADER_NAME)
        idx_HEADER_GEAR_TYPE = self.get_header_index(HEADER_GEAR_TYPE)
        idx_HEADER_TARGET = self.get_header_index(HEADER_TARGET)

        with SpeedUpTable(self, blk_sig=True):
            self.insertRow(rc)
            with QBlockSig(self):
                # If the rows are not initialized then the context menus will bug out
                for i in range(0, self.columnCount()):
                    twi = QTableWidgetItem('')
                    self.setItem(rc, i, twi)

            twi_gt = QTableWidgetItem()  # Hidden behind the combo box displays number (for sorting?)
            twi_lvl = QTableWidgetItem()  # Hidden behind the combo box displays number (for sorting?)

            f_two = GearWidget(this_gear, model, default_icon=pix.get_icon(STR_LENS_PATH), check_state=check_state, edit_able=True)
            f_two.sig_error.connect(self.frmMain.sig_show_message)
            f_two.context_menu = QMenu(f_two)  # Don't want upgrade / downgrade options on this type of gear
            self.make_menu(f_two.context_menu)
            f_two.create_Cmbs(self)
            cmb_gt = f_two.cmbType
            cmb_enh = f_two.cmbLevel

            cmb_gt.currentTextChanged.connect(lambda x: set_cell_color_compare(twi_gt, x))
            cmb_enh.currentTextChanged.connect(lambda x: set_cell_lvl_compare(twi_lvl, x, this_gear.gear_type))

            f_two.add_to_table(self, rc, col=idx_HEADER_NAME)
            self.setCellWidget(rc, idx_HEADER_GEAR_TYPE, cmb_gt)

            self.setCellWidget(rc, idx_HEADER_TARGET, cmb_enh)
            self.setItem(rc, idx_HEADER_GEAR_TYPE, twi_gt)
            self.setItem(rc, idx_HEADER_TARGET, twi_lvl)

            set_cell_lvl_compare(twi_lvl, cmb_enh.currentText(), this_gear.gear_type)
            set_cell_color_compare(twi_gt, cmb_gt.currentText())

            f_two.chkInclude.stateChanged.connect(lambda x: self.gw_check_state_changed(f_two, x))
            self.clearSelection()
            self.selectRow(rc)
            with QBlockSig(self):
                self.cellWidget(rc, idx_HEADER_GEAR_TYPE).currentTextChanged.connect(frmMain.invalidate_fs_list)
                self.cellWidget(rc, idx_HEADER_TARGET).currentTextChanged.connect(frmMain.invalidate_fs_list)
        self.set_item_data(rc)
        self.resizeColumnToContents(idx_HEADER_NAME)
        f_two.sig_gear_changed.connect(self.fs_gear_sig_gear_changed)

    def set_item_data(self, row):
        idx_BASE_ITEM_COST = self.get_header_index(HEADER_BASE_ITEM_COST)
        idx_HEADER_NAME = self.get_header_index(HEADER_NAME)

        item_store = self.enh_model.item_store()
        this_gear = self.cellWidget(row, idx_HEADER_NAME).gear
        twi = monnies_twi_factory(this_gear.base_item_cost)
        with QBlockSig(self):
            self.setItem(row, idx_BASE_ITEM_COST, twi)
            if item_store.price_is_overridden(this_gear, -1):
                twi.setForeground(COLOR_CUSTOM_PRICE)

    def gw_check_state_changed(self, gw:GearWidget, state):
        raise NotImplementedError()


    def make_menu(self, menu:QMenu):
        super(AbstractTableFS, self).make_menu(menu)
        menu.addSeparator()
        action_table_FS_add = QAction('Add Item', menu)
        action_table_FS_add.setIcon(pix.get_icon(STR_PLUS_PIC))
        menu.addAction(action_table_FS_add)
        action_table_FS_add.triggered.connect(self.action_table_FS_add_triggered)
        action_table_FS_remove = QAction('Remove Item', menu)
        action_table_FS_remove.setIcon(pix.get_icon(STR_MINUS_PIC))
        menu.addAction(action_table_FS_remove)
        action_table_FS_remove.triggered.connect(self.action_table_FS_remove_triggered)
        action_table_FS_mp_update = QAction('Central Market: Update All', menu)
        action_table_FS_mp_update.setIcon(pix.get_icon(STR_GOLD_PIC))
        settings = self.enh_model.settings
        itm_store: ItemStore = settings[settings.P_ITEM_STORE]
        action_table_FS_mp_update.setEnabled(isinstance(itm_store.price_updator, CentralMarketPriceUpdator))
        action_table_FS_mp_update.triggered.connect(self.action_mp_update_triggered)
        menu.addAction(action_table_FS_mp_update)

    def action_mp_update_triggered(self):
        model = self.enh_model
        settings = model.settings
        list = settings[self.prop_in_list] + settings[self.prop_out_list]
        thrd:MPThread = self.frmMain.get_mp_thread(list)
        thrd.sig_done.connect(self.MPThread_sig_done)
        thrd.start()

    def check_index_widget_menu(self, index:QModelIndex, menu:QMenu):
        pass

    def reload_list(self):
        model = self.enh_model
        settings = model.settings

        clear_table(self)

        try:
            fail_stackers = settings[self.prop_in_list]
            r_fail_stackers = settings[self.prop_out_list]
        except KeyError as e:
            raise SettingsException('Fail-stacking material is missing from the settings file', e)

        with SpeedUpTable(self):
            for gear in fail_stackers:
                with QBlockSig(self):
                    self.table_FS_add_gear(gear)
            for gear in r_fail_stackers:
                with QBlockSig(self):
                    self.table_FS_add_gear(gear, check_state=Qt.CheckState.Unchecked)
        self.setSortingEnabled(True)
