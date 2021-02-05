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

from PyQt5.QtCore import QThread, pyqtSignal, Qt
from .Abstract_FS_Table import HEADER_NAME, HEADER_GEAR_TYPE, HEADER_BASE_ITEM_COST, HEADER_TARGET, AbstractTableFS


class TableFS(AbstractTableFS):
    HEADERS = [HEADER_NAME, HEADER_GEAR_TYPE, HEADER_BASE_ITEM_COST, HEADER_TARGET]

    def __init__(self, *args, **kwargs):
        super(TableFS, self).__init__(*args, **kwargs)

    def set_common(self, model: Enhance_model, frmMain: lbl_color_MainWindow):
        super(TableFS, self).set_common(model, frmMain)
        settings = model.settings
        self.prop_in_list = settings.P_FAIL_STACKERS
        self.prop_out_list = settings.P_R_FAIL_STACKERS
        self.model_invalidate_func = model.invalidate_failstack_list
        self.model_add_item_func = model.add_fs_item
        self.main_invalidate_func = frmMain.invalidate_fs_list