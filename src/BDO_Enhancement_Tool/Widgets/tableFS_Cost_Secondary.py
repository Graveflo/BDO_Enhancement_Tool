# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑  ❧
"""
import numpy
from PyQt6.QtWidgets import QTableWidget, QMenu, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import QModelIndex

from BDO_Enhancement_Tool.model import Invalid_FS_Parameters, Enhance_model
from BDO_Enhancement_Tool.fsl import FailStackList
from BDO_Enhancement_Tool.WidgetTools import QBlockSig, GearWidget, monnies_twi_factory
from BDO_Enhancement_Tool.Qt_common import SpeedUpTable, clear_table
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
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.fs_exception_boxes = {}

    def mouseReleaseEvent(self, a0) -> None:
        super(TableFSCost_Secondary, self).mouseReleaseEvent(a0)
        AbstractTable.mouseReleaseEvent(self, a0)

    def reset_exception_boxes(self):
        self.fs_exception_boxes = {}

    def make_menu(self, menu: QMenu):
        super(TableFSCost_Secondary, self).make_menu(menu)

    def check_index_widget_menu(self, index:QModelIndex, menu:QMenu):
        pass

    def cmdFSRefresh_clicked(self, fsl:FailStackList):
        model:Enhance_model = self.enh_model
        settings = model.settings

        with SpeedUpTable(self):
            with QBlockSig(self):
                clear_table(self)

        if not fsl.validate():
            return

        clear_table(self)
        try:
            if model.fs_needs_update:
                model.calcFS()
            else:
                model.calc_fs_secondary()
        except Invalid_FS_Parameters as e:
            self.frmMain.show_warning_msg(str(e))
            return

        if not fsl.has_ran():
            fsl.set_primary_data(model.primary_fs_gear, model.primary_fs_cost, model.primary_cum_fs_cost)
            fsl.evaluate_map()

        index_FS = self.get_header_index(HEADER_FS)
        index_GEAR = self.get_header_index(HEADER_GEAR)
        index_COST = self.get_header_index(HEADER_COST)
        index_CUMULATIVE_COST = self.get_header_index(HEADER_CUMULATIVE_COST)
        index_PROBABILITY = self.get_header_index(HEADER_PROBABILITY)
        index_CUMULATIVE_PROBABILITY = self.get_header_index(HEADER_CUMULATIVE_PROBABILITY)

        with SpeedUpTable(self):
            fs_items = fsl.gear_list
            fs_cost = fsl.fs_cost
            cum_fs_cost = fsl.fs_cum_cost

            this_gear = fsl.secondary_gear
            bti_m_o = this_gear.gear_type.bt_start - 1
            prv_num = fsl.starting_pos
            for i, num in enumerate(fsl.secondary_map):
                fsg = this_gear.gear_type.get_fs_gain(bti_m_o + i)
                for j in range(0, num):
                    rc = self.rowCount()
                    self.insertRow(rc)
                    self.setItem(rc, index_FS, QTableWidgetItem(str(prv_num)))
                    two = GearWidget(fs_items[prv_num], model, edit_able=False, display_full_name=True)
                    two.add_to_table(self, rc, col=index_GEAR)
                    this_cost = numpy.sum(fs_cost[prv_num:prv_num+fsg])
                    twi = monnies_twi_factory(this_cost)
                    self.setItem(rc, index_COST, twi)
                    this_cum_cost = cum_fs_cost[min(len(cum_fs_cost)-1, prv_num+fsg)]
                    twi = monnies_twi_factory(this_cum_cost)
                    self.setItem(rc, index_CUMULATIVE_COST, twi)
                    prv_num += fsg

                    if prv_num > settings[settings.P_NUM_FS]:
                        return

    def set_common(self, *args):
        super(TableFSCost_Secondary, self).set_common(*args)