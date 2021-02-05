# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
from PyQt5.QtWidgets import QTableWidget, QMenu, QAction, QTableWidgetItem, QHeaderView

from BDO_Enhancement_Tool.model import Invalid_FS_Parameters
from BDO_Enhancement_Tool.WidgetTools import QBlockSig, GearWidget, monnies_twi_factory, NoScrollCombo, STR_PERCENT_FORMAT
from BDO_Enhancement_Tool.QtCommon.Qt_common import SpeedUpTable, clear_table

from PyQt5.QtCore import Qt, pyqtSignal
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
        action_refresh = QAction('Refresh List', menu)
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

    def cmdFSRefresh_clicked(self):
        model = self.enh_model
        fs_exceptions = model.settings[model.settings.P_FS_EXCEPTIONS]
        try:
            model.calcFS()
        except Invalid_FS_Parameters as e:
            self.show_warning_msg(str(e))
            return

        self.sig_fs_calculated.emit()

        index_FS = self.get_header_index(HEADER_FS)
        index_GEAR = self.get_header_index(HEADER_GEAR)
        index_COST = self.get_header_index(HEADER_COST)
        index_CUMULATIVE_COST = self.get_header_index(HEADER_CUMULATIVE_COST)
        index_PROBABILITY = self.get_header_index(HEADER_PROBABILITY)
        index_CUMULATIVE_PROBABILITY = self.get_header_index(HEADER_CUMULATIVE_PROBABILITY)

        with SpeedUpTable(self):
            with QBlockSig(self):
                clear_table(self)
            fs_items = model.optimal_fs_items
            fs_cost = model.fs_cost
            cum_fs_cost = model.cum_fs_cost
            cum_fs_probs = model.cum_fs_probs
            fs_probs = model.fs_probs
            fs_exception_boxes = self.fs_exception_boxes

            for i, this_gear in enumerate(fs_items):
                rc = self.rowCount()
                self.insertRow(rc)
                twi = QTableWidgetItem(str(i+1))
                self.setItem(rc, index_FS, twi)
                if this_gear is None:
                    twi = QTableWidgetItem('Free!')
                    self.setItem(rc, index_GEAR, twi)
                elif i in fs_exceptions:
                    self.add_custom_fs_combobox(model, fs_exception_boxes, i)
                else:
                    two = GearWidget(this_gear, self.frmMain, edit_able=False, display_full_name=True)
                    self.make_menu(two.context_menu)
                    two.add_to_table(self, rc, col=1)
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
                    self.item(19, index_GEAR).setText('Dragon Scale x30')
            if model.dragon_scale_350:
                if not 39 in fs_exceptions:
                    self.item(39, index_GEAR).setText('Dragon Scale x350')
        #tw.setVisible(True)  # Sometimes this is not visible when loading
        self.frmMain.ui.cmdEquipCost.setEnabled(True)

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