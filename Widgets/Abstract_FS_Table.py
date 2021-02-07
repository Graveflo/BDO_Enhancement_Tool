# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QTableWidget, QMenu, QAction, QTableWidgetItem

from BDO_Enhancement_Tool.model import Enhance_model, SettingsException
from BDO_Enhancement_Tool.WidgetTools import QBlockSig, MONNIES_FORMAT, MPThread, \
    GearWidget, set_cell_color_compare, set_cell_lvl_compare, monnies_twi_factory
from BDO_Enhancement_Tool.common import gear_types, \
    ItemStore, generate_gear_obj, Gear
from BDO_Enhancement_Tool.QtCommon.Qt_common import lbl_color_MainWindow, SpeedUpTable, clear_table

from PyQt5.QtCore import QThread, pyqtSignal, Qt, QModelIndex
from BDO_Enhancement_Tool.qt_UI_Common import pix, STR_PLUS_PIC, STR_MINUS_PIC, STR_GOLD_PIC

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

    def cellChanged_callback(self, row, col):
        idx_NAME = self.HEADERS.index(HEADER_NAME)
        t_item = self.cellWidget(row, idx_NAME)

        this_gear = t_item.gear

        if col == 2:
            t_cost = self.item(row, col)
            str_this_item = t_item.text()
            if str_this_item == '':
                str_this_item = '0'
            try:
                try:
                    this_gear.set_base_item_cost(float(str_this_item))
                except ValueError:
                    self.frmMain.sig_show_message.emit(self.frmMain.REGULAR, 'Invalid number: {}'.format(str_this_item))
            except ValueError:
                self.frmMain.sig_show_message.emit(self.frmMain.WARNING, 'Cost must be a number.')

    def cmdFSUpdateMP_callback(self, thread: QThread, ret):
        model = self.enh_model
        frmMain = self.frmMain

        idx_NAME = self.HEADERS.index(HEADER_NAME)

        if isinstance(ret, Exception):
            print(ret)
            frmMain.sig_show_message.emit(frmMain.CRITICAL, 'Error contacting central market')
        else:
            settings = model.settings
            item_store: ItemStore = settings[settings.P_ITEM_STORE]
            with QBlockSig(self):
                for i in range(self.rowCount()):
                    this_gear: Gear = self.cellWidget(i, idx_NAME).gear
                    self.fs_gear_set_costs(this_gear, item_store, i)
            frmMain.sig_show_message.emit(frmMain.REGULAR, 'Fail stacking prices updated')
        thread.wait(2000)
        if thread.isRunning():
            thread.terminate()
        self.mp_threads.remove(thread)

    def cmdFSRemove_clicked(self):
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

    def cmdFSUpdateMP_clicked(self):
        model = self.enh_model
        settings = model.settings

        thread = MPThread(model.update_costs, settings[self.prop_in_list] + settings[self.prop_out_list])
        self.mp_threads.append(thread)
        thread.sig_done.connect(self.cmdFSUpdateMP_callback)
        thread.start()

    def cmdFSAdd_clicked(self, bool_):
        model = self.enh_model

        gear_type = list(gear_types.items())[0][1]
        enhance_lvl = list(gear_type.lvl_map.keys())[0]
        this_gear = generate_gear_obj(model.settings, base_item_cost=0, enhance_lvl=enhance_lvl, gear_type=gear_type)
        self.table_FS_add_gear(this_gear)
        self.model_add_item_func(this_gear)
        self.main_invalidate_func()

    def fs_gear_sig_gear_changed(self, gw: GearWidget):
        model = self.enh_model
        settings = model.settings
        item_store: ItemStore = settings[settings.P_ITEM_STORE]
        this_gear:Gear = gw.gear
        model.update_costs([this_gear])
        with QBlockSig(self):
            self.fs_gear_set_costs(this_gear, item_store, gw.row())
        self.main_invalidate_func()

    def table_FS_add_gear(self, this_gear:Gear, check_state=Qt.Checked):
        frmMain = self.frmMain
        model = self.enh_model
        settings = model.settings
        rc = self.rowCount()

        with SpeedUpTable(self):

            self.insertRow(rc)
            with QBlockSig(self):
                # If the rows are not initialized then the context menus will bug out
                for i in range(0, self.columnCount()):
                    twi = QTableWidgetItem('')
                    self.setItem(rc, i, twi)

            twi_gt = QTableWidgetItem()  # Hidden behind the combo box displays number (for sorting?)
            twi_lvl = QTableWidgetItem()  # Hidden behind the combo box displays number (for sorting?)

            f_two = GearWidget(this_gear, model, default_icon=frmMain.search_icon, check_state=check_state, edit_able=True)
            f_two.sig_error.connect(self.frmMain.sig_show_message)
            f_two.context_menu = QMenu(f_two)  # Don't want upgrade / downgrade options on this type of gear
            self.make_menu(f_two.context_menu)
            f_two.create_Cmbs(self)
            cmb_gt = f_two.cmbType
            cmb_enh = f_two.cmbLevel

            cmb_gt.currentTextChanged.connect(lambda x: set_cell_color_compare(twi_gt, x))
            cmb_enh.currentTextChanged.connect(lambda x: set_cell_lvl_compare(twi_lvl, x, this_gear.gear_type))

            with QBlockSig(self):
                f_two.add_to_table(self, rc, col=0)
                self.setCellWidget(rc, 1, cmb_gt)
                twi = monnies_twi_factory(this_gear.base_item_cost)
                self.setItem(rc, 2, twi)
                self.setCellWidget(rc, 3, cmb_enh)
                self.setItem(rc, 1, twi_gt)
                self.setItem(rc, 3, twi_lvl)

            set_cell_lvl_compare(twi_lvl, cmb_enh.currentText(), this_gear.gear_type)
            set_cell_color_compare(twi_gt, cmb_gt.currentText())

            f_two.chkInclude.stateChanged.connect(lambda x: self.gw_check_state_changed(f_two, x))
            self.clearSelection()
            self.selectRow(rc)


            with QBlockSig(self):
                self.cellWidget(rc, 1).currentTextChanged.connect(frmMain.invalidate_fs_list)
                self.cellWidget(rc, 3).currentTextChanged.connect(frmMain.invalidate_fs_list)
        self.resizeColumnToContents(0)
        f_two.sig_gear_changed.connect(self.fs_gear_sig_gear_changed)

    def gw_check_state_changed(self, gw:GearWidget, state):
        raise NotImplementedError()

    def fs_gear_set_costs(self, this_gear:Gear, item_store:ItemStore, row):
        self.item(row, self.get_header_index(HEADER_BASE_ITEM_COST)).setText(MONNIES_FORMAT.format(this_gear.base_item_cost))

    def make_menu(self, menu:QMenu):
        super(AbstractTableFS, self).make_menu(menu)
        menu.addSeparator()
        action_table_FS_add = QAction('Add Item', menu)
        action_table_FS_add.setIcon(pix.get_icon(STR_PLUS_PIC))
        menu.addAction(action_table_FS_add)
        action_table_FS_add.triggered.connect(self.cmdFSAdd_clicked)
        action_table_FS_remove = QAction('Remove Item', menu)
        action_table_FS_remove.setIcon(pix.get_icon(STR_MINUS_PIC))
        menu.addAction(action_table_FS_remove)
        action_table_FS_remove.triggered.connect(self.cmdFSRemove_clicked)
        action_table_FS_mp_update = QAction('Central Market: Update All', menu)
        action_table_FS_mp_update.setIcon(pix.get_icon(STR_GOLD_PIC))
        action_table_FS_mp_update.setEnabled(False)
        menu.addAction(action_table_FS_mp_update)
        action_table_FS_mp_update.triggered.connect(self.cmdFSUpdateMP_clicked)

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
                    self.table_FS_add_gear(gear, check_state=Qt.Unchecked)
        self.setSortingEnabled(True)
