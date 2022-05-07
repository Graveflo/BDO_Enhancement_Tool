# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑  ❧
"""
from typing import Dict

from BDO_Enhancement_Tool.utilities import dict_box_list
from PyQt6.QtWidgets import QTableWidget, QMenu, QAction, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import pyqtSignal, QModelIndex

from BDO_Enhancement_Tool.model import Invalid_FS_Parameters, Enhance_model, FailStackItemExchange
from BDO_Enhancement_Tool.WidgetTools import QBlockSig, GearWidget, monnies_twi_factory, STR_PERCENT_FORMAT, \
    make_material_list_widget
from BDO_Enhancement_Tool.Qt_common import SpeedUpTable, clear_table
from BDO_Enhancement_Tool.qt_UI_Common import STR_PIC_DRAGON_SCALE, pix, STR_REFRESH_PIC
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

    def showEvent(self, a0) -> None:
        super(TableFSCost, self).showEvent(a0)
        index_GEAR = self.get_header_index(HEADER_GEAR)
        self.horizontalHeader().setSectionResizeMode(index_GEAR, QHeaderView.Stretch)

    def mouseReleaseEvent(self, a0) -> None:
        super(TableFSCost, self).mouseReleaseEvent(a0)
        AbstractTable.mouseReleaseEvent(self, a0)

    def make_menu(self, menu: QMenu):
        super(TableFSCost, self).make_menu(menu)
        menu.addSeparator()
        action_refresh = QAction('Refresh List', menu)
        action_refresh.setIcon(pix.get_icon(STR_REFRESH_PIC))
        menu.addAction(action_refresh)
        action_refresh.triggered.connect(self.cmdFSRefresh_clicked)

    def check_index_widget_menu(self, index:QModelIndex, menu:QMenu):
        pass

    def cmdFSRefresh_clicked(self):
        model:Enhance_model = self.enh_model

        try:
            model.calcFS()
        except Invalid_FS_Parameters as e:
            self.frmMain.show_warning_msg(str(e))
            return

        self.sig_fs_calculated.emit()
        self.reload_list()

    def reload_list(self):
        model = self.enh_model
        index_FS = self.get_header_index(HEADER_FS)
        index_GEAR = self.get_header_index(HEADER_GEAR)
        index_COST = self.get_header_index(HEADER_COST)
        index_CUMULATIVE_COST = self.get_header_index(HEADER_CUMULATIVE_COST)
        index_PROBABILITY = self.get_header_index(HEADER_PROBABILITY)
        index_CUMULATIVE_PROBABILITY = self.get_header_index(HEADER_CUMULATIVE_PROBABILITY)

        #exchange_dict = dict_box_list([x for x in model.fs_exchange if x.active], lambda x: x.effective_fs_level() - 1)
        exchange_dict: Dict[int, FailStackItemExchange] = {x.effective_fs_level()-1: x for x in model.fs_exchange if x.active}

        with SpeedUpTable(self):
            with QBlockSig(self):
                clear_table(self)
            fs_items = model.primary_fs_gear
            fs_cost = model.primary_fs_cost
            cum_fs_cost = model.primary_cum_fs_cost
            cum_fs_probs = model.cum_fs_probs
            fs_probs = model.fs_probs

            for i, this_gear in enumerate(fs_items):
                rc = self.rowCount()
                self.insertRow(rc)
                self.setRowHeight(rc, 32)
                twi = QTableWidgetItem(str(i+1))
                self.setItem(rc, index_FS, twi)
                if this_gear is None:
                    twi = QTableWidgetItem('Free!')
                    self.setItem(rc, index_GEAR, twi)
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

                if i in exchange_dict:
                    item = exchange_dict[i]
                    widget = make_material_list_widget([(x.item_id, x.amount) for x in item.exchange_items.values()], show_names=True, item_store=model.item_store())
                    self.removeCellWidget(rc, index_GEAR)
                    self.setCellWidget(rc, index_GEAR, widget)
            self.resizeColumnsToContents()
