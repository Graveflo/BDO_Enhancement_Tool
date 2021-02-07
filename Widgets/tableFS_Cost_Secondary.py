# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QTableWidget, QMenu, QAction, QTableWidgetItem, QHeaderView

from BDO_Enhancement_Tool.model import Invalid_FS_Parameters, Enhance_model, FailStackList
from BDO_Enhancement_Tool.WidgetTools import QBlockSig, GearWidget, monnies_twi_factory, NoScrollCombo, STR_PERCENT_FORMAT
from BDO_Enhancement_Tool.QtCommon.Qt_common import SpeedUpTable, clear_table
from BDO_Enhancement_Tool.qt_UI_Common import STR_PIC_DRAGON_SCALE

from PyQt5.QtCore import Qt, pyqtSignal, QModelIndex
from .Abstract_Table import AbstractTable

HEADER_FS = 'FS'
HEADER_GEAR = 'Gear'
HEADER_COST = 'Cost'
HEADER_CUMULATIVE_COST = 'Cumulative Cost'
HEADER_PROBABILITY = 'Probability'
HEADER_CUMULATIVE_PROBABILITY = 'Cumulative Probability'


class TableFSCost_Secondary(QTableWidget, AbstractTable):
    HEADERS = [HEADER_FS, HEADER_GEAR, HEADER_COST, HEADER_CUMULATIVE_COST, HEADER_PROBABILITY, HEADER_CUMULATIVE_PROBABILITY]

    def __init__(self, *args, **kwargs):
        super(TableFSCost_Secondary, self).__init__(*args, **kwargs)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.fs_exception_boxes = {}

    def reset_exception_boxes(self):
        self.fs_exception_boxes = {}

    def make_menu(self, menu: QMenu):
        super(TableFSCost_Secondary, self).make_menu(menu)

    def check_index_widget_menu(self, index:QModelIndex, menu:QMenu):
        pass

    def cmdFSRefresh_clicked(self):
        model:Enhance_model = self.enh_model
        settings = model.settings
        fsl: FailStackList = settings[settings.P_GENOME_FS]
        if not fsl.validate():
            clear_table(self)
        try:
            if model.fs_needs_update:
                model.calcFS()
            else:
                model.calc_fs_secondary()
        except Invalid_FS_Parameters as e:
            self.frmMain.show_warning_msg(str(e))
            return

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

            for i, this_gear in enumerate(fs_items):
                rc = self.rowCount()
                self.insertRow(rc)
                twi = QTableWidgetItem(str(i+1))
                self.setItem(rc, index_FS, twi)
                if this_gear is None:
                    twi = QTableWidgetItem('Free!')
                    self.setItem(rc, index_GEAR, twi)
                two = GearWidget(this_gear, model, edit_able=False, display_full_name=True)
                two.add_to_table(self, rc, col=index_GEAR)
                twi = monnies_twi_factory(fs_cost[i])
                self.setItem(rc, index_COST, twi)
                twi = monnies_twi_factory(cum_fs_cost[i])
                self.setItem(rc, index_CUMULATIVE_COST, twi)



            if model.dragon_scale_30 and fsl.starting_pos > 19:
                self.removeCellWidget(19, index_GEAR)
                itm = self.item(19, index_GEAR)
                itm.setText('Dragon Scale x30')
                itm.setIcon(QIcon(STR_PIC_DRAGON_SCALE))
            if model.dragon_scale_350 and fsl.starting_pos > 39:
                self.removeCellWidget(39, index_GEAR)
                self.item(39, index_GEAR).setText('Dragon Scale x350')

    def set_common(self, *args):
        super(TableFSCost_Secondary, self).set_common(*args)
        self.cmdFSRefresh_clicked()