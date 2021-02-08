# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QTableWidget, QMenu, QAction, QTableWidgetItem, QHeaderView

from BDO_Enhancement_Tool.model import Invalid_FS_Parameters, Enhance_model
from BDO_Enhancement_Tool.WidgetTools import QBlockSig, GearWidget, monnies_twi_factory, NoScrollCombo, STR_PERCENT_FORMAT
from BDO_Enhancement_Tool.QtCommon.Qt_common import SpeedUpTable, clear_table
from BDO_Enhancement_Tool.qt_UI_Common import STR_PIC_DRAGON_SCALE, pix, STR_MINUS_PIC, STR_REFRESH_PIC

from PyQt5.QtCore import Qt, pyqtSignal, QModelIndex
from .Abstract_Table import AbstractTable

HEADER_FS = 'FS'
HEADER_GEAR = 'Gear'
HEADER_COST = 'Cost'
HEADER_CUMULATIVE_COST = 'Cumulative Cost'
HEADER_PROBABILITY = 'Probability'
HEADER_CUMULATIVE_PROBABILITY = 'Cumulative Probability'


class TableFSCost(QTableWidget, AbstractTable):
    HEADERS = [HEADER_FS, HEADER_GEAR, HEADER_COST, HEADER_CUMULATIVE_COST, HEADER_PROBABILITY, HEADER_CUMULATIVE_PROBABILITY]
    sig_fs_calculated = pyqtSignal(name='sig_fs_calculated')

    def __init__(self, *args, **kwargs):
        super(TableFSCost, self).__init__(*args, **kwargs)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.fs_exception_boxes = {}

    def reset_exception_boxes(self):
        self.fs_exception_boxes = {}

    def make_menu(self, menu: QMenu):
        super(TableFSCost, self).make_menu(menu)
        menu.addSeparator()
        action_refresh = QAction('Refresh List', menu)
        action_refresh.setIcon(pix.get_icon(STR_REFRESH_PIC))
        menu.addAction(action_refresh)
        action_refresh.triggered.connect(self.cmdFSRefresh_clicked)

    def add_custom_fs_combobox(self, model, fs_exception_boxes, row_idx):
        settings = model.settings
        fs_exceptions = settings[settings.P_FS_EXCEPTIONS]
        fail_stackers = settings[settings.P_FAIL_STACKERS]
        this_cmb = NoScrollCombo(self)
        this_cmb.setFocusPolicy(Qt.ClickFocus)
        fs_exception_boxes[row_idx] = this_cmb
        this_item = fs_exceptions[row_idx]
        def this_cmb_currentIndexChanged(indx):
            model.edit_fs_exception(row_idx, fail_stackers[indx])

        for i, gear in enumerate(fail_stackers):
            this_cmb.addItem(gear.name)
            if gear is this_item:
                this_cmb.setCurrentIndex(i)
        this_cmb.currentIndexChanged.connect(this_cmb_currentIndexChanged)
        self.setCellWidget(row_idx, 1, this_cmb)

    def cmdFSEdit_clicked(self):
        frmObj = self.ui
        model = self.enh_model
        settings = model.settings
        fs_exception_boxes = self.fs_exception_boxes

        selected_rows = set([r.row() for r in self.selectedIndexes()])

        for indx in selected_rows:
            model.edit_fs_exception(indx, self.cellWidget(indx, 1).gear)
            self.add_custom_fs_combobox(model, fs_exception_boxes, indx)

    def check_index_widget_menu(self, index:QModelIndex, menu:QMenu):
        pass

    def cmdFSRefresh_clicked(self):
        model:Enhance_model = self.enh_model

        try:
            model.calcFS()
        except Invalid_FS_Parameters as e:
            self.show_warning_msg(str(e))
            return

        self.sig_fs_calculated.emit()
        self.reload_list()

    def reload_list(self):
        model = self.enh_model
        fs_exceptions = model.settings[model.settings.P_FS_EXCEPTIONS]
        index_FS = self.get_header_index(HEADER_FS)
        index_GEAR = self.get_header_index(HEADER_GEAR)
        index_COST = self.get_header_index(HEADER_COST)
        index_CUMULATIVE_COST = self.get_header_index(HEADER_CUMULATIVE_COST)
        index_PROBABILITY = self.get_header_index(HEADER_PROBABILITY)
        index_CUMULATIVE_PROBABILITY = self.get_header_index(HEADER_CUMULATIVE_PROBABILITY)

        with SpeedUpTable(self):
            with QBlockSig(self):
                clear_table(self)
            fs_items = model.primary_fs_gear
            fs_cost = model.primary_fs_cost
            cum_fs_cost = model.primary_cum_fs_cost
            cum_fs_probs = model.cum_fs_probs
            fs_probs = model.fs_probs
            fs_exception_boxes = self.fs_exception_boxes

            for i, this_gear in enumerate(fs_items):
                rc = self.rowCount()
                self.insertRow(rc)
                self.setRowHeight(rc, 32)
                twi = QTableWidgetItem(str(i+1))
                self.setItem(rc, index_FS, twi)
                if this_gear is None:
                    twi = QTableWidgetItem('Free!')
                    self.setItem(rc, index_GEAR, twi)
                elif i in fs_exceptions:
                    self.add_custom_fs_combobox(model, fs_exception_boxes, i)
                else:
                    two = GearWidget(this_gear, model, edit_able=False, display_full_name=True)
                    two.add_to_table(self, rc, col=index_GEAR)
                twi = monnies_twi_factory(fs_cost[i])
                self.setItem(rc, index_COST, twi)
                twi = monnies_twi_factory(cum_fs_cost[i])
                self.setItem(rc, index_CUMULATIVE_COST, twi)
                twi = QTableWidgetItem(STR_PERCENT_FORMAT.format(fs_probs[i]))
                self.setItem(rc, index_PROBABILITY, twi)
                twi = QTableWidgetItem(STR_PERCENT_FORMAT.format(cum_fs_probs[i]))
                self.setItem(rc, index_CUMULATIVE_PROBABILITY, twi)
            if model.dragon_scale_30:
                if not 19 in fs_exceptions:
                    self.removeCellWidget(19, index_GEAR)
                    itm = self.item(19, index_GEAR)
                    itm.setText('Dragon Scale x30')
                    itm.setIcon(QIcon(STR_PIC_DRAGON_SCALE))
            if model.dragon_scale_350:
                if not 39 in fs_exceptions:
                    self.removeCellWidget(39, index_GEAR)
                    self.item(39, index_GEAR).setText('Dragon Scale x350')

    def cmdFS_Cost_Clear_clicked(self):
        model = self.enh_model
        settings = model.settings

        def kill(x):
            try:
                del settings[settings.P_FS_EXCEPTIONS][x]
            except KeyError:
                pass
        settings.changes_made = True
        list(map(kill, set([r.row() for r in self.selectedIndexes()])))
        self.cmdFSRefresh_clicked()