# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
from PyQt5.QtCore import Qt

from BDO_Enhancement_Tool.model import Enhance_model
from BDO_Enhancement_Tool.Qt_common import lbl_color_MainWindow
from BDO_Enhancement_Tool.WidgetTools import GearWidget
from .Abstract_FS_Table import HEADER_NAME, HEADER_GEAR_TYPE, HEADER_BASE_ITEM_COST, HEADER_TARGET, AbstractTableFS


class TableFS(AbstractTableFS):
    HEADERS = [HEADER_NAME, HEADER_GEAR_TYPE, HEADER_BASE_ITEM_COST, HEADER_TARGET]

    def __init__(self, *args, **kwargs):
        super(TableFS, self).__init__(*args, **kwargs)

    def gw_check_state_changed(self, gw: GearWidget, state):
        this_gear = gw.gear
        if state == Qt.Checked:
            self.enh_model.include_fs_item(this_gear)
        else:
            self.enh_model.exclude_fs_item(this_gear)
        if self.enh_model.fs_needs_update:
            self.frmMain.invalidate_fs_list()

    def set_common(self, model: Enhance_model, frmMain: lbl_color_MainWindow):
        super(TableFS, self).set_common(model, frmMain)
        settings = model.settings
        self.prop_in_list = settings.P_FAIL_STACKERS
        self.prop_out_list = settings.P_R_FAIL_STACKERS
        self.model_invalidate_func = model.invalidate_failstack_list
        self.model_add_item_func = model.add_fs_item
        self.main_invalidate_func = frmMain.invalidate_fs_list
        self.reload_list()
