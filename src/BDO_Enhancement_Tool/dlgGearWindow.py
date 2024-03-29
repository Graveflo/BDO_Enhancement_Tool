# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑  ❧
"""
import os

from PyQt6.QtCore import pyqtSignal, QModelIndex
from PyQt6.QtGui import QCloseEvent, QPixmap
from PyQt6.QtWidgets import QTableWidgetItem, QMainWindow, QHBoxLayout, QLabel, QWidget, QSizePolicy
from .Qt_common import SpeedUpTable, clear_table

from .qt_UI_Common import pix, ITEM_PIC_DIR

from .Core.Gear import Gear, ClassicGear
from .Core.ItemStore import ItemStore, STR_FMT_ITM_ID

from .WidgetTools import GearWidget, STR_PERCENT_FORMAT, MONNIES_FORMAT, make_material_list_widget

from .Forms.EnhGearWindow import Ui_dlgGearWindow
from .model import Enhance_model


class GearWindow(QMainWindow):
    sig_closed = pyqtSignal(object, name='sig_closed')

    def __init__(self, model:Enhance_model, gear:Gear, *args):
        super(GearWindow, self).__init__(*args)
        frmObj = Ui_dlgGearWindow()
        self.ui = frmObj
        frmObj.setupUi(self)
        self.model = model
        self.gear = gear

        gw = GearWidget(gear, model, self, edit_able=False, display_full_name=False, check_state=None, enhance_overlay=False)
        frmObj.verticalLayout.insertWidget(0, gw)

        frmObj.lblGearType.setText(gear.gear_type.name)
        frmObj.lblItemID.setText(STR_FMT_ITM_ID.format(gear.item_id))
        frmObj.lblDestroysOnFail.setText(STR_PERCENT_FORMAT.format(gear.cron_downg_chance))
        frmObj.lblCronDG.setText(str(gear.backtrack_accumulator))
        frmObj.tableLvlInfo.clicked.connect(self.tableLvlInfo_selectionChanged)
        self.populate_lvl_table()

    def tableLvlInfo_selectionChanged(self, clicked:QModelIndex):
        frmObj = self.ui
        tableLvlInfo = frmObj.tableLvlInfo
        twi = tableLvlInfo.itemFromIndex(clicked)
        self.reload_cost_table(twi.row())

    def reload_cost_table(self, idx):
        gear = self.gear
        gt = gear.gear_type
        mat_cost = gt.mat_cost
        frmObj = self.ui
        tableEnhanceCosts = frmObj.tableEnhanceCosts
        model = self.model
        settings = model.settings
        item_store: ItemStore = settings[settings.P_ITEM_STORE]

        num_fs = settings[settings.P_NUM_FS]

        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        min_cost = gear.cost_vec[idx]
        restore_cost = gear.restore_cost_vec[idx]
        with SpeedUpTable(tableEnhanceCosts):
            clear_table(tableEnhanceCosts)
            for fs in range(0, num_fs):
                rc = tableEnhanceCosts.rowCount()
                tableEnhanceCosts.insertRow(rc)

                twi_lvl = QTableWidgetItem(str(fs))
                tableEnhanceCosts.setItem(rc, 0, twi_lvl)

                twi_cost = QTableWidgetItem(MONNIES_FORMAT.format(int(round(min_cost[fs]))))
                tableEnhanceCosts.setItem(rc, 1, twi_cost)

                rest_cost = QTableWidgetItem(MONNIES_FORMAT.format(int(round(restore_cost[fs]))))
                tableEnhanceCosts.setItem(rc, 2, rest_cost)

    def populate_lvl_table(self):
        gear = self.gear
        gt = gear.gear_type
        mat_cost = gt.mat_cost
        frmObj = self.ui
        tableLvlInfo = frmObj.tableLvlInfo
        model = self.model
        settings = model.settings
        item_store:ItemStore = settings[settings.P_ITEM_STORE]

        cost_vec_min = gear.cost_vec_min
        restore_cost_vec_min = gear.restore_cost_vec_min


        prev_enh_cost = 0
        prev_mat_cost = 0
        for idx_lvl in range(0, len(gt.map)):
            lvl = gt.idx_lvl_map[idx_lvl]
            rc = tableLvlInfo.rowCount()

            tableLvlInfo.insertRow(rc)
            frmObj.tableLvlInfo.setRowHeight(rc, 50)

            twi_lvl = QTableWidgetItem(lvl)
            tableLvlInfo.setItem(rc, 0, twi_lvl)

            if gear in item_store:
                twi_cost = QTableWidgetItem(MONNIES_FORMAT.format(item_store.get_cost(gear, grade=idx_lvl+1)))
                tableLvlInfo.setItem(rc, 1, twi_cost)

            if idx_lvl in gear.cron_stone_dict:
                twi_cost = QTableWidgetItem(str(gear.cron_stone_dict[idx_lvl]))
                tableLvlInfo.setItem(rc, 2, twi_cost)

            prev_enh_cost += cost_vec_min[idx_lvl]
            prev_mat_cost += restore_cost_vec_min[idx_lvl]
            twi_cum_cost = QTableWidgetItem(MONNIES_FORMAT.format(prev_enh_cost))
            tableLvlInfo.setItem(rc, 3, twi_cum_cost)
            twi_mat_cost = QTableWidgetItem(MONNIES_FORMAT.format(prev_mat_cost))
            tableLvlInfo.setItem(rc, 4, twi_mat_cost)

            if isinstance(gear, ClassicGear):
                twi_fail_dura = QTableWidgetItem(str(gear.get_durability_cost(idx_lvl)))
                tableLvlInfo.setItem(rc, 5, twi_fail_dura)

                if mat_cost is not None:
                    mat_list = []
                    for mato in gt.mat_cost[idx_lvl]:
                        if isinstance(mato, list):  # List item may be a multiplier tuple
                            num, mat = mato
                        else:
                            mat = mato
                            num = 1
                        mat_list.append((int(mat), num))

                    widget = make_material_list_widget(mat_list)

                    tableLvlInfo.setCellWidget(rc, 6, widget)
                    widget.show()

    def closeEvent(self, a0: QCloseEvent) -> None:
        super(GearWindow, self).closeEvent(a0)
        self.sig_closed.emit(self)
