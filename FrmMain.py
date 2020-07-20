#- * -coding: utf - 8 - * -
"""
http://forum.ragezone.com/f1000/release-bdo-item-database-rest-1153913/

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
# TODO: Make graphs and menu items work
# TODO: Ability to input custom failstack lists

# TODO: Make the separator in the menu a visible color on the dark theme


from .Forms.Main_Window import Ui_MainWindow
from .Forms.dlg_Sale_Balance import Ui_DlgSaleBalance
from .DlgAddGear import Dlg_AddGear, gears
from .dlgAbout import dlg_About
from .dlgExport import dlg_Export
from .QtCommon import Qt_common
from .common import relative_path_convert, gear_types, enumerate_gt_lvl, Classic_Gear, Smashable, enumerate_gt, binVf,\
    ItemStore, generate_gear_obj, Gear, IMG_TMP, GEAR_ID_FMT, ENH_IMG_PATH
from .model import Enhance_model, Invalid_FS_Parameters

import numpy, types, os
from PyQt5.QtGui import QPixmap, QPalette, QIcon, QPainter
from PyQt5.QtWidgets import QWidget, QTableWidgetItem, QHeaderView, QSpinBox, QFileDialog, QMenu, QAction, QDialog, QTreeWidgetItem
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QThread
from PyQt5 import QtWidgets
from PyQt5 import QtGui
import urllib3
#from PyQt5 import QtWidgets
from .DlgCompact import Dlg_Compact
import utilities

QBlockSig = Qt_common.QBlockSig
NoScrollCombo = Qt_common.NoScrollCombo
clear_table = Qt_common.clear_table
dlg_format_list = Qt_common.dlg_format_list
get_dark_palette = Qt_common.get_dark_palette

QTableWidgetItem_NoEdit = Qt_common.QTableWidgetItem_NoEdit
#STR_TW_GEAR = 'gear_item'
STR_COST_ERROR = 'Cost must be a number.'
MONNIES_FORMAT = "{:,}"
STR_TWO_DEC_FORMAT = "{:.2f}"
STR_PERCENT_FORMAT = '{:.2f}%'
STR_INFINITE = 'INF'

ITEM_PIC_DIR = relative_path_convert('Images/items/')
STR_PIC_VALKS = os.path.join(ITEM_PIC_DIR, '00017800.png')
STR_PIC_BSA = os.path.join(ITEM_PIC_DIR, '00000007.png')
STR_PIC_BSW = os.path.join(ITEM_PIC_DIR, '00000008.png')
STR_PIC_CBSA = os.path.join(ITEM_PIC_DIR, '00000019.png')
STR_PIC_CBSW = os.path.join(ITEM_PIC_DIR, '00000018.png')
STR_PIC_CRON = os.path.join(ITEM_PIC_DIR, '00016080.png')
STR_PIC_MEME = os.path.join(ITEM_PIC_DIR, '00044195.png')
STR_PIC_PRIEST = os.path.join(ITEM_PIC_DIR, 'ic_00017.png')
STR_PIC_DRAGON_SCALE = os.path.join(ITEM_PIC_DIR, '00044364.png')

STR_PIC_VALUE_PACK = os.path.join(ITEM_PIC_DIR, '00017583.png')
STR_PIC_RICH_MERCH_RING = os.path.join(ITEM_PIC_DIR, '00012034.png')
STR_PIC_MARKET_TAX = os.path.join(ITEM_PIC_DIR, '00000005_special.png')


COL_GEAR_TYPE = 2
COL_FS_SALE_SUCCESS = 4
COL_FS_SALE_FAIL = 5
COL_FS_PROC_COST = 6


remove_numeric_modifiers = lambda x: x.replace(',', '').replace('%','')

def numeric_less_than(self, y):
    return float(remove_numeric_modifiers(self.text())) <= float(remove_numeric_modifiers(y.text()))

#def color_compare(self, other):
#    print self.cellWidget(self.row(), self.column())


class ImageLoadThread(QThread):
    DEATH = -42069
    sig_icon_ready = pyqtSignal(str, str, name='sig_icon_ready')

    def __init__(self, connection_pool, url_location, file_dest):
        super(ImageLoadThread, self).__init__()
        self.url = url_location
        self.file_dest = file_dest
        self.connection_pool:urllib3.HTTPSConnectionPool = connection_pool

    def run(self) -> None:
        url, str_pth = self.url, self.file_dest

        dat = self.connection_pool.request('GET', url, preload_content=False)

        with open(str_pth, 'wb') as f:
            for chunk in dat.stream(512):
                f.write(chunk)
        self.sig_icon_ready.emit(url, str_pth)


class custom_twi(QTableWidgetItem, QSpinBox):
    pass


class numeric_twi(QTableWidgetItem):
    def __lt__(self, other):
        return numeric_less_than(self, other)


class comma_seperated_twi(numeric_twi):
    def __init__(self, text):
        super(comma_seperated_twi, self).__init__(text)
        self.setText(text)

    def setData(self, role, p_str):
        p_str = remove_numeric_modifiers(p_str)
        if p_str is None or p_str == '':
            super(comma_seperated_twi, self).setData(role, p_str)
        else:
            super(comma_seperated_twi, self).setData(role, MONNIES_FORMAT.format(int(p_str)))

#    def setText(self, p_str):

    
    def text(self):
        return super(comma_seperated_twi, self).text().replace(',','')


class Dlg_Sale_Balance(QDialog):
    sig_accepted = pyqtSignal(int ,name='sig_accepted')

    def __init__(self, parent, lbl_txt):
        super(Dlg_Sale_Balance, self).__init__(parent)
        self.main_window = parent
        frmObj = Ui_DlgSaleBalance()
        self.ui = frmObj
        frmObj.setupUi(self)

        self.lbl_txt = lbl_txt
        self.balance = 0
        #frmObj.spinValue.setMaximum(10000000000)

        frmObj.buttonBox.accepted.connect(self.buttonBox_accepted)
        frmObj.spinValue.valueChanged.connect(self.spinValue_valueChanged)
        frmObj.spinPercent.valueChanged.connect(self.spinPercent_valueChanged)
        frmObj.chkValuePack.clicked.connect(self.chkValuePack_checkStateSe)

    def spinPercent_valueChanged(self, val):
        self.update_balance()

    def chkValuePack_checkStateSe(self, state):
        self.update_balance()

    def spinValue_valueChanged(self, val):
        self.update_balance()

    def update_balance(self):
        frmObj = self.ui
        percent = frmObj.spinPercent.value() / 100.0
        if frmObj.chkValuePack.isChecked():
            percent += percent * 0.3
        self.balance = int(round(percent * frmObj.spinValue.value()))
        frmObj.lblSale.setText("{}".format(self.lbl_txt))
        frmObj.txtProfit.setText('{:,}'.format(self.balance))

    def buttonBox_accepted(self):
        self.sig_accepted.emit(self.balance)


class TableWidgetGW(QTableWidgetItem):
    def __lt__(self, other):
        return str(self) < str(other)

    def __str__(self):
        row = self.row()
        col = self.column()
        gw = self.tableWidget().cellWidget(row, col)
        return str(gw.gear.name)


class TreeWidgetGW(QTreeWidgetItem):
    def __lt__(self, other):
        return str(self) < str(other)
    def __str__(self):
        w = self.treeWidget().itemWidget(self, 0)
        if w is None:
            return ''
        else:
            return str(self.treeWidget().itemWidget(self, 0).gear.name)


class GearWidget(QWidget):
    sig_gear_changed = pyqtSignal(object, name='sig_gear_changed')

    def __init__(self, gear: Gear, frmMain, parent=None, edit_able=False, default_icon=None, display_full_name=False,
                 check_state=None, give_upgrade_downgrade=True):
        super(GearWidget, self).__init__(parent=parent)
        self.gear = None
        self.frmMain = frmMain
        self.model: Enhance_model = frmMain.model
        self.table_widget = None
        self.icon = None
        self.row = None
        self.col = None
        self.cmbLevel = None
        self.cmbType = None
        self.pixmap = None
        self.horizontalLayout = QtWidgets.QHBoxLayout(self)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.display_full_name = display_full_name
        self.edit_able = edit_able

        self.chkInclude: QtWidgets.QCheckBox = None
        self.labelIcon = None
        self.txtEditName = None
        self.load_thread = None
        self.dlg_chose_gear = None
        self.parent_widget = None
        self.upgrade_downgrade = give_upgrade_downgrade
        self.cmbType: QtWidgets.QComboBox  = None
        self.cmbLevel: QtWidgets.QComboBox = None
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)


        self.lblName = Qt_common.CLabel(self)
        self.horizontalLayout.addWidget(self.lblName)

        self.lblName.sigMouseDoubleClick.connect(self.lblName_sigMouseDoubleClick)

        if check_state is not None:
            self.setCheckState(check_state)

        if default_icon is not None:
            self.set_icon(default_icon)

        self.set_gear(gear)

    def mouseReleaseEvent(self, a0: QtGui.QMouseEvent) -> None:
        if self.upgrade_downgrade:
            if a0.button() & Qt.RightButton == Qt.RightButton:
                context_menu = QMenu(self)
                action_downgrade = QAction('Downgrade', context_menu)
                action_downgrade.triggered.connect(self.downgrade)
                context_menu.addAction(action_downgrade)
                action_upgrade = QAction('Upgrade', context_menu)
                action_upgrade.triggered.connect(self.upgrade)
                context_menu.addAction(action_upgrade)
                context_menu.exec_(a0.globalPos())

    def downgrade(self):
        if self.upgrade_downgrade:
            self.gear.downgrade()
            self.fix_cmb_lvl()
            self.sig_gear_changed.emit(self)

    def upgrade(self):
        if self.upgrade_downgrade:
            self.gear.upgrade()
            self.fix_cmb_lvl()
            self.sig_gear_changed.emit(self)

    def fix_cmb_lvl(self):
        if self.cmbLevel is not None:
            idx = self.cmbLevel.findText(self.gear.enhance_lvl)
            self.cmbLevel.setCurrentIndex(idx)

    def lblName_sigMouseDoubleClick(self, ev):
        if self.edit_able:
            self.txtEditName = Qt_common.FocusLineEdit(self)
            self.txtEditName.setText(self.lblName.text())
            self.txtEditName.selectAll()
            self.horizontalLayout.replaceWidget(self.lblName, self.txtEditName)
            self.txtEditName.returnPressed.connect(self.return_lblName)
            self.txtEditName.sig_lost_focus.connect(self.return_lblName)
            self.lblName.deleteLater()
            self.lblName = None
            self.txtEditName.setFocus()

    def return_lblName(self):
        if self.txtEditName is not None:
            self.lblName = Qt_common.CLabel(self)
            new_name = self.txtEditName.text()
            self.lblName.setText(new_name)
            self.gear.name = new_name
            self.frmMain.ui.table_Equip.resizeColumnToContents(0)
            self.horizontalLayout.replaceWidget(self.txtEditName, self.lblName)
            self.lblName.sigMouseDoubleClick.connect(self.lblName_sigMouseDoubleClick)
            self.txtEditName.deleteLater()
            self.txtEditName = None

    def load_gear_icon(self):
        if self.gear.item_id is not None:
            item_id = self.gear.item_id
            pad_item_id = GEAR_ID_FMT.format(item_id)
            try:
                name, grade,url,itype = gears[item_id]
            except KeyError:
                return
            icon_path = os.path.join(IMG_TMP, pad_item_id + '.png')
            if os.path.isfile(icon_path):
                self.set_icon(QIcon(icon_path))
            else:
                self.load_thread = ImageLoadThread(self.frmMain.connection, url , icon_path)
                self.load_thread.sig_icon_ready.connect(lambda _url,_str_path: self.set_icon(QIcon(_str_path)))
                self.load_thread.start()

    def set_icon(self, icon: QIcon, enhance_overlay=True):
        self.icon = icon
        self.set_pixmap(icon.pixmap(QSize(32, 32)), enhance_overlay=enhance_overlay)

    def set_pixmap(self, pixmap:QPixmap, enhance_overlay=True):
        if self.pixmap is None:
            self.labelIcon = Qt_common.CLabel(self)
            self.labelIcon.setMinimumSize(QSize(32, 32))
            self.labelIcon.setMaximumSize(QSize(32, 32))
            self.labelIcon.setText("")
            if self.chkInclude is None:
                self.horizontalLayout.insertWidget(0, self.labelIcon)
            else:
                self.horizontalLayout.insertWidget(1, self.labelIcon)
            self.labelIcon.sigMouseLeftClick.connect(self.labelIcon_sigMouseClick)

        if self.gear is not None and enhance_overlay:
            enh_lvl_n = self.gear.enhance_lvl_to_number()
            if enh_lvl_n > 0:
                enhance_lvl = self.gear.enhance_lvl_from_number(enh_lvl_n-1)
                enh_p = os.path.join(ENH_IMG_PATH, enhance_lvl+".png")
                if os.path.isfile(enh_p):
                    this_pix = QPixmap(QSize(32, 32))
                    this_pix.fill(Qt.transparent)
                    painter = QPainter(this_pix)

                    painter.drawPixmap(0, 0, pixmap)
                    painter.drawPixmap(0, 0, QPixmap(enh_p))
                    pixmap = this_pix
        self.pixmap = pixmap
        self.labelIcon.setPixmap(pixmap)

    def setCmbLevel(self, cmbLevel:QtWidgets.QComboBox):
        self.cmbLevel = cmbLevel

    def setCmbType(self, cmbType:QtWidgets.QComboBox):
        self.cmbType = cmbType

    def set_gear(self, gear:Gear):
        self.gear = gear
        self.update_data()

    def update_data(self):
        gear = self.gear
        if self.display_full_name:
            self.lblName.setText(gear.get_full_name())
        else:
            self.lblName.setText(gear.name)
        self.frmMain.ui.table_Equip.resizeColumnToContents(0)
        self.fix_cmb_lvl()
        self.load_gear_icon()

    def labelIcon_sigMouseClick(self, ev):
        if self.edit_able:
            if self.dlg_chose_gear is not None:
                self.dlg_chose_gear.close()
                self.dlg_chose_gear.deleteLater()
            self.dlg_chose_gear = Dlg_AddGear(self.frmMain)
            self.dlg_chose_gear.sig_gear_chosen.connect(self.dlg_chose_gear_sig_gear_chosen)
            self.dlg_chose_gear.show()

    def dlg_chose_gear_sig_gear_chosen(self, name, item_class, item_grade, item_id):
        self.gear.item_id = int(item_id)
        if self.gear.name is None or self.gear.name == '':
            self.gear.name = name
        if item_grade == 'Yellow':
            item_grade = 'Boss'
        type_str = item_grade + " " + item_class
        idx = self.cmbType.findText(type_str)
        if idx > -1:
            self.cmbType.setCurrentIndex(idx)
        self.update_data()
        self.sig_gear_changed.emit(self)

    def setCheckState(self, state):
        if self.chkInclude is None:
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            self.chkInclude = QtWidgets.QCheckBox(self)
            sizePolicy.setHeightForWidth(self.chkInclude.sizePolicy().hasHeightForWidth())
            self.chkInclude.setSizePolicy(sizePolicy)
            self.chkInclude.setText("")
            self.horizontalLayout.insertWidget(0, self.chkInclude)
        self.chkInclude.setCheckState(state)

    def add_to_table(self, table_widget: QtWidgets.QTableWidget, row, col=0):
        table_widget.setCellWidget(row, col, self)
        table_widget.setItem(row, col, TableWidgetGW(''))
        if self.icon is not None:
            table_widget.setRowHeight(row, 45)
        self.table_widget = table_widget
        self.row = row
        self.col = col

    def create_Cmbs(self, tw, model_edit_func=None):
        if model_edit_func is None:
            model_edit_func = self.model.swap_gear
        gear = self.gear
        cmb_gt = NoScrollCombo(tw)
        cmb_enh = NoScrollCombo(tw)
        self.cmbType = cmb_gt
        self.cmbLevel = cmb_enh
        self.frmMain.set_sort_gear_cmbBox(list(gear_types.keys()), enumerate_gt, gear.gear_type.name, cmb_gt)
        gtype_s = cmb_gt.currentText()


        self.frmMain.set_sort_gear_cmbBox(list(gear_types[gtype_s].lvl_map.keys()), enumerate_gt_lvl, gear.enhance_lvl, cmb_enh)

        def cmb_gt_currentTextChanged(str_picked):
            current_enhance_string = cmb_enh.currentText()
            new_gt = gear_types[str_picked]
            with QBlockSig(cmb_enh):
                cmb_enh.clear()
                self.frmMain.set_sort_gear_cmbBox(list(new_gt.lvl_map.keys()), enumerate_gt_lvl, current_enhance_string, cmb_enh)
            this_gear = self.gear
            if str_picked.lower().find('accessor') > -1 or str_picked.lower().find('life') > -1:
                if not isinstance(this_gear, Smashable):
                    old_g = this_gear
                    this_gear = generate_gear_obj(self.model.settings, base_item_cost=this_gear.base_item_cost, enhance_lvl=cmb_enh.currentText(),
                                                        gear_type=gear_types[str_picked], name=this_gear.name,
                                                        sale_balance=this_gear.sale_balance, id=this_gear.item_id)
                    #self.model.edit_fs_item(old_g, this_gear)
                    model_edit_func(old_g, this_gear)
                else:
                    this_gear.set_gear_params(gear_types[str_picked], cmb_enh.currentText())
            else:
                if not isinstance(this_gear, Classic_Gear):
                    old_g = this_gear
                    this_gear = generate_gear_obj(self.model.settings, base_item_cost=this_gear.base_item_cost, enhance_lvl=cmb_enh.currentText(),
                                                        gear_type=gear_types[str_picked], name=this_gear.name, id=this_gear.item_id)
                    #self.model.edit_fs_item(old_g, this_gear)
                    model_edit_func(old_g, this_gear)
                else:
                    this_gear.set_gear_params(gear_types[str_picked], cmb_enh.currentText())
            self.set_gear(this_gear)
            #self.model.invalidate_failstack_list()
            self.sig_gear_changed.emit(self)
            # Sets the hidden value of the table widget so that colors are sorted in the right order

        def cmb_enh_currentTextChanged(str_picked):
            this_gear = self.gear
            try:
                this_gear.set_enhance_lvl(str_picked)

                self.load_gear_icon()
            except KeyError:
                self.frmMain.show_critical_error('Enhance level does not appear to be valid.')
            self.sig_gear_changed.emit(self)

        cmb_gt.currentTextChanged.connect(cmb_gt_currentTextChanged)
        cmb_enh.currentTextChanged.connect(cmb_enh_currentTextChanged)

    def add_to_tree(self, tree, item, col=0):
        tree.setItemWidget(item, col, self)
        self.table_widget = tree
        self.parent_widget = item
        self.col = col


class Frm_Main(Qt_common.lbl_color_MainWindow):
    def __init__(self, app):
        super(Frm_Main, self).__init__()
        frmObj = Ui_MainWindow()
        frmObj.setupUi(self)
        self.ui = frmObj
        self.app = app

        model = Enhance_model()
        self.model = model

        pix = QPixmap(relative_path_convert('title.png'))
        frmObj.label.setPixmap(pix)
        self.search_icon = QIcon(relative_path_convert('images/lens2.png'))

        self.pool_size = 5
        self.connection = urllib3.HTTPSConnectionPool('bddatabase.net', maxsize=self.pool_size, block=True)

        self.clear_data()
        self.fs_c = None
        self.eh_c = None
        self.mod_enhance_me = None
        self.mod_fail_stackers = None
        self.mod_enhance_split_idx = None

        self.strat_go_mode = False  # The strategy has been calculated and needs to be updated

        self.about_win = dlg_About(self)

        def actionGitHub_README_triggered():
            import webbrowser
            webbrowser.open('https://github.com/ILikesCaviar/BDO_Enhancement_Tool')

        def actionWindow_Always_on_Top_triggered(bowl):
            aot_mask = Qt.WindowStaysOnTopHint
            this_flags = self.windowFlags()
            if bowl:
                self.setWindowFlags(this_flags | aot_mask)
                self.show()
            else:
                self.setWindowFlags(this_flags & (~aot_mask))
                self.show()

        def actionExport_Excel_triggered():
            wind = dlg_Export(self)
            wind.show()

        def actionExport_CSV_triggered():
            wind = dlg_Export(self)
            wind.show()

        def actionMarket_Tax_Calc_triggered():
            slg = Dlg_Sale_Balance(self, 'Profit')
            slg.ui.buttonBox.setEnabled(False)
            slg.ui.buttonBox.setVisible(False)
            slg.show()

        frmObj.lblBlackStoneArmorPic.setPixmap(QPixmap(STR_PIC_BSA).scaled(32, 32, transformMode=Qt.SmoothTransformation))
        frmObj.lblBlackStoneWeaponPic.setPixmap(QPixmap(STR_PIC_BSW).scaled(32, 32, transformMode=Qt.SmoothTransformation))
        frmObj.lblConcBlackStoneArmorPic.setPixmap(QPixmap(STR_PIC_CBSA).scaled(32, 32, transformMode=Qt.SmoothTransformation))
        frmObj.lblConcBlackStoneWeaponPic.setPixmap(QPixmap(STR_PIC_CBSW).scaled(32, 32, transformMode=Qt.SmoothTransformation))
        frmObj.lblCronStonePic.setPixmap(QPixmap(STR_PIC_CRON).scaled(32, 32, transformMode=Qt.SmoothTransformation))
        frmObj.lblMemoryFragmentPic.setPixmap(QPixmap(STR_PIC_MEME).scaled(32, 32, transformMode=Qt.SmoothTransformation))
        frmObj.lblGearCleansePic.setPixmap(
            QPixmap(STR_PIC_PRIEST).scaled(32, 32, transformMode=Qt.SmoothTransformation))
        frmObj.lblDragonScalePic.setPixmap(
            QPixmap(STR_PIC_DRAGON_SCALE).scaled(32, 32, transformMode=Qt.SmoothTransformation))

        frmObj.lblMarketTaxPic.setPixmap(
            QPixmap(STR_PIC_MARKET_TAX).scaled(32, 32, transformMode=Qt.SmoothTransformation))
        frmObj.chkValuePackPic.setPixmap(
            QPixmap(STR_PIC_VALUE_PACK).scaled(32, 32, transformMode=Qt.SmoothTransformation))
        frmObj.chkMerchantsRingPic.setPixmap(
            QPixmap(STR_PIC_RICH_MERCH_RING).scaled(32, 32, transformMode=Qt.SmoothTransformation))


        frmObj.actionAbout.triggered.connect(self.about_win.show)
        frmObj.actionExit.triggered.connect(app.exit)
        frmObj.actionLoad_Info.triggered.connect(self.open_file_dlg)
        frmObj.actionSave_Info.triggered.connect(self.save_file_dlg)
        frmObj.actionWindow_Always_on_Top.triggered.connect(actionWindow_Always_on_Top_triggered)
        frmObj.actionGitHub_README.triggered.connect(actionGitHub_README_triggered)
        frmObj.actionExport_CSV.triggered.connect(actionExport_CSV_triggered)
        frmObj.actionExport_Excel.triggered.connect(actionExport_Excel_triggered)
        frmObj.actionMarket_Tax_Calc.triggered.connect(actionMarket_Tax_Calc_triggered)

        table_Equip = frmObj.table_Equip
        table_FS = frmObj.table_FS
        table_Strat = frmObj.table_Strat
        table_Strat_Equip = frmObj.table_Strat_Equip

        for i in range(table_Equip.columnCount()):
            table_Equip.header().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        table_Equip.header().setSectionResizeMode(0, QHeaderView.Interactive)
        table_Equip.header().setSectionResizeMode(2, QHeaderView.Interactive)


        def cmdEquipRemove_clicked():
            tmodel = self.model
            tsettings = tmodel.settings
            tw = frmObj.table_Equip

            effect_list = [i for i in tw.selectedItems()]


            enhance_me = tsettings[tsettings.P_ENHANCE_ME]
            r_enhance_me = tsettings[tsettings.P_R_ENHANCE_ME]

            for i in effect_list:
                thic = tw.itemWidget(i, 0).gear
                try:
                    enhance_me.remove(thic)
                    tmodel.invalidate_enahce_list()
                except ValueError:
                    pass
                try:
                    r_enhance_me.remove(thic)
                except ValueError:
                    pass
                p = i.parent()
                if p is None:
                    tw.takeTopLevelItem(tw.indexOfTopLevelItem(i))
                #else:
                #    p.removeChild(i)
                #tw.takeTopLevelItem()
            tsettings.changes_made = True

        def cmdFSRemove_clicked():
            tmodel = self.model
            tsettings = tmodel.settings
            tw = frmObj.table_FS

            effect_list = [i.row() for i in tw.selectedItems()]
            effect_list.sort()
            effect_list.reverse()

            fail_stackers_counts = tsettings[tsettings.P_FAIL_STACKERS_COUNT]
            fail_stackers = tsettings[tsettings.P_FAIL_STACKERS]
            r_fail_stackers = tsettings[tsettings.P_R_FAIL_STACKERS]

            for i in effect_list:
                thic = tw.cellWidget(i, 0).gear
                try:
                    fail_stackers.remove(thic)
                    tmodel.invalidate_failstack_list()
                except ValueError:
                    pass
                try:
                    r_fail_stackers.remove(thic)
                except ValueError:
                    pass
                try:
                    del fail_stackers_counts[thic]
                except KeyError:
                    pass
                tw.removeRow(i)
            tsettings.changes_made = True

        frmObj.cmdEquipRemove.clicked.connect(cmdEquipRemove_clicked)
        frmObj.cmdFSRemove.clicked.connect(cmdFSRemove_clicked)

        frmObj.cmdFSAdd.clicked.connect(self.cmdFSAdd_clicked)
        frmObj.cmdEquipAdd.clicked.connect(self.cmdEquipAdd_clicked)
        frmObj.table_FS.cellChanged.connect(self.table_FS_cellChanged)
        frmObj.table_Equip.itemChanged.connect(self.table_Equip_itemChanged)
        frmObj.cmdFSRefresh.clicked.connect(self.cmdFSRefresh_clicked)
        frmObj.cmdFSEdit.clicked.connect(self.cmdFSEdit_clicked)
        frmObj.cmdFS_Cost_Clear.clicked.connect(self.cmdFS_Cost_Clear_clicked)
        frmObj.cmdEquipCost.clicked.connect(self.cmdEquipCost_clicked)
        frmObj.cmdStrat_go.clicked.connect(self.cmdStrat_go_clicked)
        self.compact_window = Dlg_Compact(self)

        def cmdCompact_clicked():
            try:
                fs_order = frmObj.table_Strat.selectedItems()[0].row()
                self.compact_window.ui.spinFS.setValue(fs_order)
            except IndexError:
                pass
            self.compact_window.show()

        frmObj.cmdCompact.clicked.connect(self.cmdStrat_go_clicked)
        frmObj.cmdCompact.clicked.connect(cmdCompact_clicked)
        frmObj.cmdCompact.clicked.connect(self.compact_window.set_frame)

        frmObj.table_FS_Cost.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        #frmObj.table_Equip.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        #frmObj.table_FS.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        frmObj.table_Strat_FS.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        frmObj.table_Strat.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        frmObj.table_Strat_Equip.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        frmObj.cmd_Strat_Graph.clicked.connect(self.cmd_Strat_Graph_clicked)
        frmObj.table_Equip.setSortingEnabled(True)
        frmObj.table_FS.setSortingEnabled(True)
        frmObj.table_Strat_FS.setSortingEnabled(True)
        frmObj.table_Strat_Equip.setSortingEnabled(True)
        frmObj.table_Equip.setIconSize(QSize(32, 32))
        frmObj.table_FS.setIconSize(QSize(32, 32))

        self.load_ui_common()

        frmObj.table_Equip.itemDoubleClicked.connect(self.table_Equip_itemDoubleClicked)

    def table_Equip_itemDoubleClicked(self, item, col):
        if col == 2:
            self.ui.table_Equip.editItem(item, col)

    def closeEvent(self, *args, **kwargs):
        model = self.model
        model.save_to_file()
        super(Frm_Main, self).closeEvent(*args, **kwargs)
        self.app.exit()

    def dragEnterEvent(self, e):
        """
        When the user drags anything over the window this event triggers. It accepts 'text/uri-list' for a list of files.
        :param e: EventParams
        :return: None
        """
        if e.mimeData().hasFormat('text/uri-list'):
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, *event):
        """
        This event fires when an accepted drop is actuated.
        :param event:
        :return: None
        """
        super(Frm_Main, self).dropEvent(*event)
        files = [x.toLocalFile() for x in list(event[0].mimeData().urls())]
        this_file = files[0]
        if os.path.isfile(this_file):
            try:
                self.load_file(this_file)
            except IOError:
                self.show_warning_msg('Cannot load file. A settings JSON file is expected.')

    def upgrade_gear(self, dis_gear, this_item):
        try:
            dis_gear.upgrade()
            self.model.save()
        except KeyError:
            self.show_warning_msg('Cannot upgrade gear past: ' + str(dis_gear.enhance_lvl))
            return
        self.refresh_gear_obj(dis_gear, this_item=this_item)

    def downgrade_gear(self, dis_gear, this_item):
        try:
            dis_gear.downgrade()
            self.model.save()
        except KeyError:
            self.show_warning_msg('Cannot downgrade gear below: ' + str(dis_gear.enhance_lvl))
            return
        self.refresh_gear_obj(dis_gear, this_item=this_item)

    def get_enhance_table_item(self, gear_obj):
        table_Equip = self.ui.table_Equip

        for rew in range(0, table_Equip.topLevelItemCount()):
            item = table_Equip.topLevelItem(rew)
            if gear_obj is table_Equip.cellWidget(item, 0).gear:
                return table_Equip.item(item, 0)

    def refresh_gear_obj(self, dis_gear, this_item=None):
        """
        This change can be in the strat window or in the minimal window. The gear widget object may need to be
        syncronized

        :param dis_gear:
        :param this_item:
        :return:
        """
        table_Equip = self.ui.table_Equip
        if this_item is None:
            this_item = self.get_enhance_table_item(dis_gear)

        if this_item is None:
            self.show_critical_error('Gear was not found on the gear list. ' + str(dis_gear.get_full_name()))
        else:
            self.invalidate_equiptment(this_item)
            gw = table_Equip.itemWidget(this_item, 0)
            gw.update_data()
            if self.strat_go_mode:
                self.cmdStrat_go_clicked()

    def clear_data(self):
        self.eh_c = None
        self.fs_exception_boxes = {}

    def monnies_twi_factory(self, i_f_val):
        twi = comma_seperated_twi(str(int(round(i_f_val))))
        return twi

    def adjust_equip_splitter(self):
        frmObj = self.ui
        tw = self.ui.table_Strat

        tot = numpy.sum(frmObj.splitter.sizes())
        h_ = tw.horizontalHeader().length() + 2
        if tw.verticalScrollBar().isVisible():
            h_ += tw.verticalScrollBar().width()
        frmObj.splitter.setSizes([h_, tot - h_])

    def cmd_Strat_Graph_clicked(self):
        model = self.model
        eh_c = self.eh_c

        if eh_c is None:
            self.show_warning_msg('Need to calculate the strategy first.')
            return


        #for i, plowt in enumerate(eh_c):
        #    item = model.enhance_me[i]
        #    ploot = plt.plot(range(0, 121), plowt, label=item.name)
        #    plt.axvline(x=numpy.argmin(item.enhance_cost(model.cum_fs_cost)[item.gear_type.lvl_map[item.enhance_lvl]]),
        #                color=ploot[0].get_color())
        #plt.legend(loc='upper left')
        #plt.show()

    def cmdStrat_go_clicked(self):
        model = self.model
        settings = model.settings
        enhance_me = settings[settings.P_ENHANCE_ME]
        fail_stackers = settings[settings.P_FAIL_STACKERS]
        frmObj = self.ui
        tw = frmObj.table_Strat

        self.strat_go_mode = True

        #for row in range(0, tw.rowCount()):
        #    tw.removeRow(0)
        self.invalidate_strategy()

        if not len(model.cum_fs_cost) > 0:
            self.cmdFSRefresh_clicked()
        if not len(model.equipment_costs) > 0:
            self.cmdEquipCost_clicked()

        mod_idx_gear_map = {}

        mod_enhance_me = enhance_me[:]
        mod_fail_stackers = fail_stackers[:]
        current_gear_idx = len(enhance_me)
        self.mod_enhance_split_idx = current_gear_idx
        for i in range(0, frmObj.table_Equip.topLevelItemCount()):
            twi = frmObj.table_Equip.topLevelItem(i)
            master_gw = frmObj.table_Equip.itemWidget(twi, 0)
            master_gear = master_gw.gear
            if master_gear not in enhance_me:
                continue
            for j in range(0, twi.childCount()):
                child = twi.child(j)
                child_gw: GearWidget = frmObj.table_Equip.itemWidget(child, 0)
                if child_gw.chkInclude.checkState() == Qt.Checked:
                    child_gear = child_gw.gear

                    child_gear.cost_vec = numpy.array(master_gear.cost_vec, copy=True)
                    child_gear.restore_cost_vec = numpy.array(master_gear.restore_cost_vec, copy=True)
                    child_gear.cost_vec_min = numpy.array(master_gear.cost_vec_min, copy=True)
                    child_gear.restore_cost_vec_min = numpy.array(master_gear.restore_cost_vec_min, copy=True)
                    mod_idx_gear_map[len(mod_enhance_me)] = child_gear
                    mod_enhance_me.append(child_gear)

        self.mod_enhance_me = mod_enhance_me
        self.mod_fail_stackers = mod_fail_stackers

        try:
            fs_c, eh_c = model.calcEnhances(enhance_me=mod_enhance_me)
            self.fs_c = fs_c
            self.eh_c = eh_c
        except Invalid_FS_Parameters as f:
            self.show_warning_msg(str(f))
            return
        fs_c_T = fs_c.T
        eh_c_T = eh_c.T

        this_enhance_me = mod_enhance_me[:]
        this_fail_stackers = fail_stackers[:]

        try:
            tw.currentItemChanged.disconnect()
        except TypeError:
            # This happens the first time because nothing is connected.
            pass
        tw.itemSelectionChanged.connect(self.table_Strat_selectionChanged)

        with Qt_common.SpeedUpTable(tw):

            for i, ev in enumerate(eh_c_T):
                fv = fs_c_T[i]
                tw.insertRow(i)
                twi = QTableWidgetItem(str(i))
                tw.setItem(i, 0, twi)
                ev_min = numpy.argmin(ev)
                fv_min = numpy.argmin(fv)
                if fv[fv_min] > ev[ev_min]:
                    is_fake_enh_gear = ev_min >= self.mod_enhance_split_idx
                    dis_gear = this_enhance_me[ev_min]
                    two = GearWidget(dis_gear, self, edit_able=False, display_full_name=True, give_upgrade_downgrade=not is_fake_enh_gear)
                    if is_fake_enh_gear:
                        two.set_icon(QIcon(relative_path_convert('images/items/00017800.png')), enhance_overlay=False)
                        two.lblName.setText('Save Stack: {}'.format(two.lblName.text()))
                        twi2 = QTableWidgetItem("YES")
                    else:
                        twi2 = QTableWidgetItem("NO")
                else:
                    dis_gear = this_fail_stackers[fv_min]
                    two = GearWidget(dis_gear, self, edit_able=False, display_full_name=True)
                    twi2 = QTableWidgetItem("NO")
                two.add_to_table(tw, i, col=1)
                tw.setItem(i, 2, twi2)

            self.eh_c = eh_c

        self.adjust_equip_splitter()

    def table_Strat_selectionChanged(self):
        row_obj = self.ui.table_Strat.selectedItems()[0]
        if self.eh_c is None or self.fs_c is None:
            self.show_critical_error('No details when strategy is not calculated.')
            return
        frmObj = self.ui
        model = self.model
        settings = model.settings
        enhance_me = self.mod_enhance_me
        fail_stackers = self.mod_fail_stackers
        this_enhance_me = enhance_me[:]
        this_fail_stackers = fail_stackers[:]
        fs_c_T = self.fs_c.T
        eh_c_T = self.eh_c.T
        tw_eh = frmObj.table_Strat_Equip
        tw_fs = frmObj.table_Strat_FS
        if row_obj is None:
            # null selection is possible
            return
        p_int = row_obj.row()
        this_vec = eh_c_T[p_int]
        this_sort = numpy.argsort(this_vec)

        with QBlockSig(tw_eh):
            clear_table(tw_eh)
        with QBlockSig(tw_fs):
            clear_table(tw_fs)
        tw_eh.setSortingEnabled(False)
        tw_fs.setSortingEnabled(False)
        for i in range(0, len(this_vec)):
            this_sorted_idx = this_sort[i]
            is_real_gear = this_sorted_idx < self.mod_enhance_split_idx
            this_sorted_item = this_enhance_me[this_sorted_idx]
            tw_eh.insertRow(i)
            two = GearWidget(this_sorted_item, self, display_full_name=True, edit_able=False, give_upgrade_downgrade=is_real_gear)
            two.add_to_table(tw_eh, i, col=0)
            twi = self.monnies_twi_factory(this_vec[this_sorted_idx])
            #twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
            tw_eh.setItem(i, 1, twi)

            eh_idx = this_sorted_item.get_enhance_lvl_idx()
            cost_vec_l = this_sorted_item.cost_vec[eh_idx]
            idx_ = numpy.argmin(cost_vec_l)
            opti_val = cost_vec_l[idx_]
            optimality = (1.0 + ((opti_val - cost_vec_l[p_int]) / opti_val)) * 100
            twi = numeric_twi(STR_PERCENT_FORMAT.format(optimality))
            #twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
            tw_eh.setItem(i, 2, twi)

            this_fail_map = numpy.array(this_sorted_item.gear_type.map)[eh_idx][p_int]
            avg_num_attempt = numpy.divide(1.0, this_fail_map)
            avg_num_fails = avg_num_attempt - 1
            twi = numeric_twi(STR_TWO_DEC_FORMAT.format(avg_num_fails))
            #twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
            tw_eh.setItem(i, 3, twi)

            # attempts = int(numpy.ceil(avg_num_attempt))
            # if attempts == 0:
            #    attempts = 1
            # print 'cdf(1,{},{}) = {} | {} {}'.format(attempts, this_fail_map, binVf(attempts, this_fail_map), avg_num_attempt, this_sorted_item.name)
            confidence = binVf(avg_num_attempt, this_fail_map) * 100
            twi = numeric_twi(STR_PERCENT_FORMAT.format(confidence))
            #twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
            tw_eh.setItem(i, 4, twi)

        this_vec = fs_c_T[p_int]
        this_sort = numpy.argsort(this_vec)

        for i in range(0, len(this_vec)):
            this_sorted_idx = this_sort[i]
            this_sorted_item = this_fail_stackers[this_sorted_idx]
            tw_fs.insertRow(i)
            two = GearWidget(this_sorted_item, self, display_full_name=True, edit_able=False, give_upgrade_downgrade=False)
            two.add_to_table(tw_fs, i, col=0)
            twi = self.monnies_twi_factory(this_vec[this_sorted_idx])
            #twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
            tw_fs.setItem(i, 1, twi)

            opti_val = this_vec[this_sort[0]]
            optimality = (1.0 - ((opti_val - this_vec[this_sorted_idx]) / opti_val)) * 100
            twi = numeric_twi(STR_PERCENT_FORMAT.format(optimality))
            #twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
            tw_fs.setItem(i, 2, twi)
        tw_eh.setSortingEnabled(True)
        tw_fs.setSortingEnabled(True)

    def cmdEquipCost_clicked(self):
        model = self.model
        frmObj = self.ui
        tw = frmObj.table_Equip

        try:
            model.calc_equip_costs()
        except Invalid_FS_Parameters as f:
            self.show_warning_msg(str(f))
            return

        tw.setSortingEnabled(False)

        def populate_row(this_head, this_gear, eh_idx):

            cost_vec_l = this_gear.cost_vec[eh_idx]
            mat_cost_vec_l = this_gear.restore_cost_vec[eh_idx]
            idx_ = numpy.argmin(this_gear.cost_vec[eh_idx])
            #twi = numeric_twi(str(idx_))
            #twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
            #tw.setItem(i, 4, twi)
            this_head.setText(4, str(idx_))
            #twi = self.monnies_twi_factory(cost_vec_l[idx_])
            #twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
            #tw.setItem(i, 5, twi)
            this_head.setText(5, MONNIES_FORMAT.format(round(cost_vec_l[idx_])))
            this_head.setText(6, MONNIES_FORMAT.format(round(mat_cost_vec_l[idx_])))

            this_fail_map = numpy.array(this_gear.gear_type.map)[eh_idx]
            avg_num_fails = numpy.divide(numpy.ones(this_fail_map.shape), this_fail_map) - 1
            #twi = numeric_twi()
            #twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
            #tw.setItem(i, 6, twi)
            #this_head.setText(6, STR_TWO_DEC_FORMAT.format(avg_num_fails[idx_]))
            this_head.setText(7, STR_TWO_DEC_FORMAT.format(avg_num_fails[idx_]))
            #twi = numeric_twi()
            #tw.setItem(i, 7, twi)
            this_head.setText(8, STR_PERCENT_FORMAT.format(this_fail_map[idx_] * 100.0))
            try:

                this_head.setText(9, str(this_gear.using_memfrags))
            except AttributeError:
                pass

        for i in range(0, tw.topLevelItemCount()):
            this_head = tw.topLevelItem(i)
            gear_widget = tw.itemWidget(this_head, 0)
            this_gear = gear_widget.gear
            eh_idx = this_gear.get_enhance_lvl_idx()
            populate_row(this_head, this_gear, eh_idx)
            for j in range(0, this_head.childCount()):
                this_child = this_head.child(j)
                child_gear_widget = tw.itemWidget(this_child, 0)
                child_gear = child_gear_widget.gear
                eh_idx = child_gear.get_enhance_lvl_idx()
                populate_row(this_child, this_gear, eh_idx)



        tw.setSortingEnabled(True)

    def cmdFS_Cost_Clear_clicked(self):
        model = self.model
        settings = model.settings
        frmObj = self.ui
        tw = frmObj.table_FS_Cost

        def kill(x):
            try:
                del settings[settings.P_FS_EXCEPTIONS][x]
            except KeyError:
                pass
        settings.changes_made = True
        list(map(kill, set([r.row() for r in tw.selectedIndexes()])))
        frmObj.cmdFSRefresh.click()

    def add_custom_fs_combobox(self, model, tw, fs_exception_boxes, row_idx):
        settings = model.settings
        fs_exceptions = settings[settings.P_FS_EXCEPTIONS]
        fail_stackers = settings[settings.P_FAIL_STACKERS]
        this_cmb = NoScrollCombo(tw)
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
        tw.setCellWidget(row_idx, 1, this_cmb)

    def cmdFSEdit_clicked(self):
        frmObj = self.ui
        model = self.model
        settings = model.settings
        fs_exception_boxes = self.fs_exception_boxes
        tw = frmObj.table_FS_Cost

        selected_rows = set([r.row() for r in tw.selectedIndexes()])

        for indx in selected_rows:
            model.edit_fs_exception(indx, tw.cellWidget(indx, 0).gear)
            self.add_custom_fs_combobox(model, tw, fs_exception_boxes, indx)

    def cmdFSRefresh_clicked(self):
        frmObj = self.ui
        model = self.model
        fs_exceptions = model.settings[model.settings.P_FS_EXCEPTIONS]
        try:
            model.calcFS()
        except Invalid_FS_Parameters as e:
            self.show_warning_msg(str(e))
            return

        tw = frmObj.table_FS_Cost
        with Qt_common.SpeedUpTable(tw):
            with QBlockSig(tw):
                clear_table(tw)
            fs_items = model.optimal_fs_items
            fs_cost = model.fs_cost
            cum_fs_cost = model.cum_fs_cost
            cum_fs_probs = model.cum_fs_probs
            fs_probs = model.fs_probs
            fs_exception_boxes = self.fs_exception_boxes

            for i, this_gear in enumerate(fs_items):
                rc = tw.rowCount()
                tw.insertRow(rc)
                twi = QTableWidgetItem(str(i+1))
                #twi.__dict__[STR_TW_GEAR] = this_gear
                tw.setItem(rc, 0, twi)
                if i in fs_exceptions:
                    self.add_custom_fs_combobox(model, tw, fs_exception_boxes, i)
                else:
                    two = GearWidget(this_gear, self, edit_able=False, display_full_name=True)
                    two.add_to_table(tw, rc, col=1)
                twi = self.monnies_twi_factory(fs_cost[i])
                tw.setItem(rc, 2, twi)
                twi = self.monnies_twi_factory(cum_fs_cost[i])
                tw.setItem(rc, 3, twi)
                twi = QTableWidgetItem(str(fs_probs[i]))
                tw.setItem(rc, 4, twi)
                twi = QTableWidgetItem(str(cum_fs_probs[i]))
                tw.setItem(rc, 5, twi)
            if model.dragon_scale_30:
                if not 19 in fs_exceptions:
                    tw.item(19, 1).setText('Dragon Scale x30')
            if model.dragon_scale_350:
                if not 39 in fs_exceptions:
                    tw.item(39, 1).setText('Dragon Scale x350')
        tw.setVisible(True)  # Sometimes this is not visible when loading
        frmObj.cmdEquipCost.setEnabled(True)

    def table_cellChanged_proto(self, this_item, col, this_gear):
        if this_item is None:
            return

        if col == 2:
            str_this_item = this_item.text()
            if str_this_item == '': str_val = '0'
            try:
                try:
                    this_gear.set_cost(float(str_this_item))
                except ValueError:
                    self.ui.statusbar.showMessage('Invalid number: {}'.format(str_this_item))
            except ValueError:
                self.show_warning_msg('Cost must be a number.')

    def table_Equip_itemChanged(self, t_item: QTreeWidgetItem, col):
        model = self.model
        tw = self.ui.table_Equip


        gear_widget = tw.itemWidget(t_item, 0)

        this_gear = gear_widget.gear
        if col == 2:
            # columns that are not 0 are non-cosmetic and may change the cost values
            self.invalidate_equiptment(t_item)
            try:
                try:
                    str_val = t_item.text(2).replace(',', '')
                    if str_val == '': str_val='0'
                    this_cost_set = float(str_val)
                    this_gear.set_cost(this_cost_set)
                    with QBlockSig(tw):
                        t_item.setText(2, MONNIES_FORMAT.format(this_cost_set))
                        for i in range(0, t_item.childCount()):
                            this_child = t_item.child(i)
                            this_child_gw = tw.itemWidget(this_child, 0)
                            this_child_gw.gear.set_cost(this_cost_set)
                            this_child.setText(2, MONNIES_FORMAT.format(this_cost_set))
                except ValueError:
                    self.ui.statusbar.showMessage('Invalid number: {}'.format(t_item.text(2)))
            except ValueError:
                self.show_warning_msg('Cost must be a number.')

    def table_FS_cellChanged(self, row, col):
        model = self.model

        tw = self.ui.table_FS

        t_item = tw.cellWidget(row, 0)
        this_gear = t_item.gear
        if col == COL_FS_SALE_SUCCESS:
            str_val = tw.item(row, COL_FS_SALE_SUCCESS).text()
            if str_val == '': str_val='0'
            try:
                this_gear.set_sale_balance(float(str_val))
            except ValueError:
                self.ui.statusbar.showMessage('Invalid number: {}'.format(str_val))
        elif col == COL_FS_SALE_FAIL:
            str_val = tw.item(row, COL_FS_SALE_FAIL).text()
            if str_val == '': str_val = '0'
            try:
                this_gear.set_fail_sale_balance(float(str_val))
            except ValueError:
                self.ui.statusbar.showMessage('Invalid number: {}'.format(str_val))
        elif col == COL_FS_PROC_COST:
            str_val = tw.item(row, COL_FS_PROC_COST).text()
            if str_val == '': str_val = '0'
            try:
                this_gear.set_procurement_cost(float(str_val))
            except ValueError:
                self.ui.statusbar.showMessage('Invalid number: {}'.format(str_val))
        self.table_cellChanged_proto(tw.item(row, col), col, this_gear)
        self.invalidate_fs_list()

    def set_sort_gear_cmbBox(self, this_list, compar_f, current_gear_lvl, cmb_box):
        sorted_list = this_list[:]
        sorted_list.sort(key=compar_f)

        for i, key in enumerate(sorted_list):
            cmb_box.addItem(key)
            if key == current_gear_lvl:
                cmb_box.setCurrentIndex(i)

    def set_cell_lvl_compare(self, twi_lvl, lvl_str):
        txt_c = str(enumerate_gt_lvl(lvl_str))
        twi_lvl.setText(txt_c)

    def get_gt_color_compare(self, gt_str):
        txt_c = gt_str.lower()
        if txt_c.find('white') > -1:
            return 'b'
        elif txt_c.find('green') > -1:
            return 'c'
        elif txt_c.find('blue') > -1:
            return 'd'
        elif txt_c.find('yellow') > -1 or txt_c.find('boss') > -1:
            return 'e'
        else:
            return 'a'

    def set_cell_color_compare(self, twi_gt, gt_str):
        twi_gt.setText(self.get_gt_color_compare(gt_str))

    def cmb_equ_change(self, cmb, txt_c):
        txt_c = txt_c.lower()
        this_pal = cmb.palette()
        this_pal.setColor(QPalette.ButtonText, Qt.black)
        if txt_c.find('white') > -1:
            this_pal.setColor(QPalette.Button, Qt.white)
        elif txt_c.find('green') > -1:
            this_pal.setColor(QPalette.Button, Qt.green)
        elif txt_c.find('blue') > -1:
            this_pal.setColor(QPalette.Button, Qt.blue)
        elif txt_c.find('yellow') > -1 or txt_c.find('boss') > -1:
            this_pal.setColor(QPalette.Button, Qt.yellow)
        else:
            this_pal = get_dark_palette()
        cmb.setPalette(this_pal)

    def table_FS_add_gear(self, this_gear, check_state=Qt.Checked, add_fun=None):
        model = self.model
        settings = model.settings
        r_fail_stackers = settings[settings.P_R_FAIL_STACKERS]
        fail_stackers = settings[settings.P_FAIL_STACKERS]
        tw = self.ui.table_FS
        rc = tw.rowCount()

        with Qt_common.SpeedUpTable(tw):

            tw.insertRow(rc)
            with QBlockSig(tw):
                # If the rows are not initialized then the context menus will bug out
                for i in range(0, tw.columnCount()):
                    twi = QTableWidgetItem('')
                    tw.setItem(rc, i, twi)

            twi_gt = QTableWidgetItem()  # Hidden behind the combo box displays number (for sorting?)
            twi_lvl = QTableWidgetItem()  # Hidden behind the combo box displays number (for sorting?)

            f_two = GearWidget(this_gear, self, default_icon=self.search_icon, check_state=check_state, edit_able=True)
            f_two.create_Cmbs(tw)
            cmb_gt = f_two.cmbType
            cmb_enh = f_two.cmbLevel

            cmb_gt.currentTextChanged.connect(lambda x: self.set_cell_color_compare(twi_gt, x))
            cmb_enh.currentTextChanged.connect(lambda x: self.set_cell_lvl_compare(twi_lvl, x))


            if add_fun is not None:
                add_fun(this_gear)


            with QBlockSig(tw):
                f_two.add_to_table(tw, rc, col=0)

                #tw.setItem(rc, 0, f_twi)
                tw.setCellWidget(rc, 1, cmb_gt)
                twi = self.monnies_twi_factory(this_gear.base_item_cost)
                #twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
                tw.setItem(rc, 2, twi)
                tw.setCellWidget(rc, 3, cmb_enh)
                tw.setItem(rc, 1, twi_gt)
                tw.setItem(rc, 3, twi_lvl)

            self.cmb_equ_change(cmb_gt, cmb_gt.currentText())
            self.set_cell_lvl_compare(twi_lvl, cmb_enh.currentText())
            self.set_cell_color_compare(twi_gt, cmb_gt.currentText())


            cmb_gt.currentTextChanged.connect(lambda x: self.cmb_equ_change(self.sender(), x))


            def chkInclude_stateChanged(state):
                if state == Qt.Checked:
                    try:
                        r_fail_stackers.remove(this_gear)
                    except ValueError:
                        # Item already removed. This is likely not a check change on col 0
                        pass

                    fail_stackers.append(this_gear)
                    settings[settings.P_FAIL_STACKERS] = list(set(fail_stackers))
                    # order here matters to the file is saved after the settings are updated
                    self.invalidate_strategy()
                else:
                    try:
                        fail_stackers.remove(this_gear)
                    except ValueError:
                        # Item already removed. This is likely not a check change on col 0
                        pass

                    r_fail_stackers.append(this_gear)
                    settings[settings.P_R_FAIL_STACKERS] = list(set(r_fail_stackers))
                    # order here matters to the file is saved after the settings are updated
                    self.invalidate_strategy()

            f_two.chkInclude.stateChanged.connect(chkInclude_stateChanged)


            with QBlockSig(tw):
                twi = self.monnies_twi_factory(this_gear.sale_balance)
                #twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
                tw.setItem(rc, 4, twi)
                twi = self.monnies_twi_factory(this_gear.fail_sale_balance)
                #twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
                tw.setItem(rc, 5, twi)
                twi = self.monnies_twi_factory(this_gear.procurement_cost)
                #twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
                tw.setItem(rc, 6, twi)
                tw.cellWidget(rc, 1).currentTextChanged.connect(self.invalidate_fs_list)
                tw.cellWidget(rc, 3).currentTextChanged.connect(self.invalidate_fs_list)
        tw.setVisible(True)
        tw.resizeColumnToContents(0)
        f_two.sig_gear_changed.connect(self.invalidate_fs_list)

    def create_Eq_TreeWidget(self, parent_wid, this_gear, check_state) -> QTreeWidgetItem:
        tw = self.ui.table_Equip
        top_lvl = TreeWidgetGW(parent_wid, [''] * tw.columnCount())
        top_lvl.setFlags(top_lvl.flags() | Qt.ItemIsEditable)

        f_two = GearWidget(this_gear, self, default_icon=self.search_icon, check_state=check_state, edit_able=True)
        f_two.create_Cmbs(tw)
        cmb_gt = f_two.cmbType
        cmb_enh = f_two.cmbLevel

        cmb_gt.currentTextChanged.connect(lambda x: top_lvl.setText(1, self.get_gt_color_compare(x)))
        cmb_enh.currentTextChanged.connect(lambda x: top_lvl.setText(3, self.get_gt_color_compare(x)))

        f_two.add_to_tree(tw, top_lvl, col=0)

        # tw.setItem(rc, 0, f_twi)
        # tw.setCellWidget(rc, 1, cmb_gt)
        tw.setItemWidget(top_lvl, 1, cmb_gt)
        # twi = self.monnies_twi_factory(this_gear.base_item_cost)
        # twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
        # tw.setItem(rc, 2, twi)
        top_lvl.setText(2, MONNIES_FORMAT.format(this_gear.base_item_cost))
        tw.setItemWidget(top_lvl, 3, cmb_enh)

        self.cmb_equ_change(cmb_gt, cmb_gt.currentText())
        # self.set_cell_lvl_compare(twi_lvl, cmb_enh.currentText())
        # self.set_cell_color_compare(twi_gt, cmb_gt.currentText())

        cmb_gt.currentTextChanged.connect(lambda x: self.cmb_equ_change(self.sender(), x))  # Updates color

        two = f_two

        settings = self.model.settings
        r_enhance_me = settings[settings.P_R_ENHANCE_ME]
        enhance_me = settings[settings.P_ENHANCE_ME]

        def chkInclude_stateChanged(state):
            if state == Qt.Checked:
                try:
                    r_enhance_me.remove(this_gear)
                except ValueError:
                    # Item already removed. This is likely not a check change on col 0
                    pass

                enhance_me.append(this_gear)
                settings[settings.P_ENHANCE_ME] = list(set(enhance_me))
                # order here matters to the file is saved after the settings are updated
                self.invalidate_strategy()
            else:
                try:
                    enhance_me.remove(this_gear)
                except ValueError:
                    # Item already removed. This is likely not a check change on col 0
                    pass

                r_enhance_me.append(this_gear)
                settings[settings.P_R_ENHANCE_ME] = list(set(r_enhance_me))
                # order here matters to the file is saved after the settings are updated
                self.invalidate_strategy()

        two.chkInclude.stateChanged.connect(chkInclude_stateChanged)
        return top_lvl

    def table_Eq_add_gear(self, this_gear: Gear, check_state=Qt.Checked):
        model = self.model
        tw = self.ui.table_Equip



        with QBlockSig(tw):
            top_lvl = self.create_Eq_TreeWidget(tw, this_gear, check_state)
            master_gw: GearWidget = tw.itemWidget(top_lvl, 0)
            master_gw.sig_gear_changed.connect(self.master_gw_sig_gear_changed)
            tw.addTopLevelItem(top_lvl)
            self.add_children(top_lvl)
            # lvl_num = this_gear.enhance_lvl_to_number()
            # len_lvls = len(this_gear.gear_type.lvl_map)
            # for i in this_gear.target_lvls:
            #     _gear = this_gear.duplicate()
            #     _gear.set_enhance_lvl(this_gear.gear_type.idx_lvl_map[i])
            #     child = self.create_Eq_TreeWidget(top_lvl, _gear, check_state)
            #     top_lvl.addChild(child)
        tw.resizeColumnToContents(0)
        master_gw.cmbType.currentIndexChanged.connect(lambda: self.invalidate_equiptment(top_lvl))
        master_gw.cmbLevel.currentIndexChanged.connect(lambda: self.invalidate_equiptment(top_lvl))
        #master_gw.cmbType.currentIndexChanged.connect(lambda: add_children(top_lvl))
        #master_gw.cmbLevel.currentIndexChanged.connect(lambda: add_children(top_lvl))

    def add_children(self, top_lvl_wid: QTreeWidgetItem):
        tw = self.ui.table_Equip
        prunes = []
        for i in range(0, top_lvl_wid.childCount()):
            child = top_lvl_wid.child(0)
            child_gw:GearWidget = tw.itemWidget(child, 0)
            top_lvl_wid.takeChild(0)
            if not child_gw.chkInclude.isChecked():
                prunes.append(child_gw.gear.enhance_lvl)
        master_gw = tw.itemWidget(top_lvl_wid, 0)
        this_gear = master_gw.gear
        these_lvls = this_gear.guess_target_lvls()
        this_gear.target_lvls = these_lvls
        for lvl in these_lvls:
            twi = QTreeWidgetItem(top_lvl_wid, [''] * tw.columnCount())
            _gear = this_gear.duplicate()
            _gear.set_enhance_lvl(lvl)
            this_check_state = Qt.Unchecked if lvl in prunes else Qt.Checked
            this_gw = GearWidget(_gear, self, edit_able=False, display_full_name=False,
                                 check_state=this_check_state)
            tw.setItemWidget(twi, 0, this_gw)
            top_lvl_wid.addChild(twi)

            twi.setText(1, master_gw.cmbType.currentText())
            twi.setText(2, top_lvl_wid.text(2))
            twi.setText(3, _gear.enhance_lvl)

    def master_gw_sig_gear_changed(self, gw:GearWidget):
        self.add_children(gw.parent_widget)

    def cmdFSAdd_clicked(self, bool_):
        model = self.model

        gear_type = list(gear_types.items())[0][1]
        enhance_lvl = list(gear_type.lvl_map.keys())[0]
        this_gear = generate_gear_obj(model.settings, base_item_cost=0, enhance_lvl=enhance_lvl, gear_type=gear_type)
        self.table_FS_add_gear(this_gear, add_fun=model.add_fs_item)
        self.invalidate_fs_list()

    def cmdEquipAdd_clicked(self, bool_):
        model = self.model

        gear_type = list(gear_types.items())[0][1]
        enhance_lvl = list(gear_type.lvl_map.keys())[0]

        this_gear = generate_gear_obj(model.settings, base_item_cost=0, enhance_lvl=enhance_lvl, gear_type=gear_type)

        self.table_Eq_add_gear( this_gear)
        model.add_equipment_item(this_gear)

    def invalidate_fs_list(self):
        frmObj = self.ui
        tw = frmObj.table_FS_Cost
        self.model.invalidate_failstack_list()
        with QBlockSig(tw):
            clear_table(tw)
        self.invalidate_strategy()

    def invalidate_equiptment(self, t_item:QTreeWidgetItem):
        frmObj = self.ui
        tw = frmObj.table_Equip
        self.model.invalidate_enahce_list()
        with QBlockSig(tw):
            t_item.setText(4, '')
            t_item.setText(5, '')
            t_item.setText(6, '')
            t_item.setText(7, '')
            t_item.setText(8, '')

        self.invalidate_strategy()

    def invalidate_strategy(self):
        self.eh_c = None
        frmObj = self.ui
        tw = frmObj.table_Strat
        tw_fs = frmObj.table_Strat_FS
        tw_eh = frmObj.table_Strat_Equip
        with QBlockSig(tw):
            clear_table(tw)
        with QBlockSig(tw_eh):
            clear_table(tw_eh)
        with QBlockSig(tw_fs):
            clear_table(tw_fs)
        self.model.save()

    def open_file_dlg(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        model = self.model
        settings = model.settings

        if settings.f_path is None:
            this_open_path = relative_path_convert('./')
        else:
            this_open_path = settings.f_path
        fmt_list = [('Any', '*'),('JSON File', 'json')]
        fileName, _ = QFileDialog.getOpenFileName(self, "Select Input File", this_open_path,
                                                  dlg_format_list(fmt_list),
                                                  options=options, initialFilter=dlg_format_list([fmt_list[1]]))
        if fileName:
            try:
                self.load_file(fileName)
            except IOError:
                self.show_critical_error('File could not be loaded.')
        else:
            self.ui.statusbar.showMessage('Aborted opening file.')

    def clear_all(self):
        frmObj = self.ui
        self.model = None
        list(map(lambda x: clear_table(x), [frmObj.table_FS, frmObj.table_Strat, frmObj.table_FS_Cost,
                                          frmObj.table_Strat_Equip, frmObj.table_Strat_FS]))
        frmObj.table_Equip.clear()
        self.clear_data()
        self.model = Enhance_model()

    def save_file_dlg(self):
        show_mess = self.ui.statusbar.showMessage
        model = self.model
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        format_list = [('Any', '*'),('JSON File', 'json')]
        if model.settings.f_path is None:
            save_path = relative_path_convert('./')
        else:
            save_path = os.path.dirname(model.settings.f_path)
        fileName, _ = QFileDialog.getSaveFileName(self, "Saving", save_path, dlg_format_list(format_list), options=options,
                                                  initialFilter=dlg_format_list([format_list[1]]))
        if fileName:
            if not fileName.lower().endswith('.json'):
                fileName += '.json'
            model.save_to_file(txt_path=fileName)
            self.show_green_msg('Saved: ' + fileName)
        else:
            show_mess('Aborted saving.')

    def load_file(self, str_path):
        self.clear_all()
        model = self.model
        settings = model.settings
        frmObj = self.ui

        try:
            self.model.load_from_file(str_path)
        except ValueError as e:
            print(utilities.fmt_traceback(e.__traceback__))
            self.show_critical_error('Something is wrong with the settings file: ' + str_path)
        except KeyError as e:
            print(utilities.fmt_traceback(e.__traceback__))
            self.show_critical_error('Something is wrong with the settings file: ' + str_path)
            print(e)

        try:
            fail_stackers = settings[settings.P_FAIL_STACKERS]
            enhance_me = settings[settings.P_ENHANCE_ME]
        except KeyError as e:
            self.show_critical_error('Something is wrong with the settings file: ' + str_path)
            print(e)
            for j in self.model.settings:
                print(j)
            return

        tw = frmObj.table_Equip
        for gear in enhance_me:
            with QBlockSig(frmObj.table_Equip):
                self.table_Eq_add_gear(gear)
        for gear in settings[settings.P_R_ENHANCE_ME]:
            with QBlockSig(frmObj.table_Equip):
                self.table_Eq_add_gear(gear, check_state=Qt.Unchecked)
        frmObj.table_FS.setSortingEnabled(False)
        frmObj.table_Equip.setSortingEnabled(False)
        for gear in fail_stackers:
            with QBlockSig(frmObj.table_FS):
                self.table_FS_add_gear(gear)
        for gear in settings[settings.P_R_FAIL_STACKERS]:
            with QBlockSig(frmObj.table_FS):
                self.table_FS_add_gear(gear, check_state=Qt.Unchecked)
        frmObj.table_FS.setSortingEnabled(True)
        frmObj.table_Equip.setSortingEnabled(True)
        if len(fail_stackers) > 0:
            frmObj.cmdFSRefresh.click()
            if len(enhance_me) > 0:
                frmObj.cmdEquipCost.click()

    def load_ui_common(self):
        frmObj = self.ui
        model = self.model
        settings = model.settings
        def cost_mat_gen(unpack):
            txt_box, cost, set_costf, itm_txt = unpack
            txt_box.setValue(cost)

            def spin_Cost_item_textChanged(str_val):
                try:
                    set_costf(str_val)
                    frmObj.statusbar.showMessage('Set '+itm_txt+' cost to: ' + str(str_val))
                except ValueError:
                    self.show_warning_msg(STR_COST_ERROR, silent=True)

            txt_box.valueChanged.connect(spin_Cost_item_textChanged)
            txt_box.editingFinished.connect(model.save)

        def switch_mat_gen(unpack):
            chk_box, cost, set_costf, itm_txt = unpack
            chk_box.setCheckState(Qt.Checked if cost else Qt.Unchecked)

            def chk_box_stateChanged(chk_state):
                try:
                    set_costf(True if chk_state == Qt.Checked else False)
                    frmObj.statusbar.showMessage('Set '+itm_txt+' to: ' + str(chk_state))
                except ValueError:
                    self.show_warning_msg(STR_COST_ERROR, silent=True)
                model.save()

            chk_box.stateChanged.connect(chk_box_stateChanged)

        item_store = settings[settings.P_ITEM_STORE]
        cost_bs_a = item_store.get_cost(ItemStore.P_BLACK_STONE_ARMOR)
        cost_bs_w = item_store.get_cost(ItemStore.P_BLACK_STONE_WEAPON)
        cost_conc_a = item_store.get_cost(ItemStore.P_CONC_ARMOR)
        cost_conc_w = item_store.get_cost(ItemStore.P_CONC_WEAPON)
        cost_cleanse = settings[settings.P_CLEANSE_COST]
        cost_cron = settings[settings.P_CRON_STONE_COST]
        cost_meme = item_store.get_cost(ItemStore.P_MEMORY_FRAG)
        cost_dscale = item_store.get_cost(ItemStore.P_DRAGON_SCALE)

        P_MARKET_TAX = settings[settings.P_MARKET_TAX]
        P_VALUE_PACK = settings[settings.P_VALUE_PACK]
        P_VALUE_PACK_ACTIVE = settings[settings.P_VALUE_PACK_ACTIVE]
        P_MERCH_RING = settings[settings.P_MERCH_RING]
        P_MERCH_RING_ACTIVE = settings[settings.P_MERCH_RING_ACTIVE]

        def updateMarketTaxUI():
            with QBlockSig(frmObj.spinMarketTax):
                frmObj.spinMarketTax.setValue(settings[settings.P_MARKET_TAX])

        list(map(cost_mat_gen, [
            [frmObj.spin_Cost_BlackStone_Armor, cost_bs_a, model.set_cost_bs_a, 'Blackstone Armour'],
            [frmObj.spin_Cost_BlackStone_Weapon, cost_bs_w, model.set_cost_bs_w, 'Blackstone Weapon'],
            [frmObj.spin_Cost_ConcArmor, cost_conc_a, model.set_cost_conc_a, 'Conc Blackstone Armour'],
            [frmObj.spin_Cost_Conc_Weapon, cost_conc_w, model.set_cost_conc_w, 'Conc Blackstone Weapon'],
            [frmObj.spin_Cost_Cleanse, cost_cleanse, model.set_cost_cleanse, 'Gear Cleanse'],
            [frmObj.spin_Cost_Cron, cost_cron, model.set_cost_cron, 'Cron Stone'],
            [frmObj.spin_Cost_MemFrag, cost_meme, model.set_cost_meme, 'Memory Fragment'],
            [frmObj.spin_Cost_Dragon_Scale, cost_dscale, model.set_cost_dragonscale, 'Dragon Scale'],
            [frmObj.spinMarketTax, P_MARKET_TAX, model.set_market_tax, 'Market Tax'],
            [frmObj.spinValuePack, P_VALUE_PACK, model.value_pack_changed, 'Value Pack Gain'],
            [frmObj.spinMerchantsRing, P_MERCH_RING, model.merch_ring_changed, 'Merch Ring Pack Gain']
        ]))

        list(map(switch_mat_gen, [
            [frmObj.chkMerchantsRing, P_MERCH_RING_ACTIVE, model.using_merch_ring, 'Merch Ring'],
            [frmObj.chkValuePack, P_VALUE_PACK_ACTIVE, model.using_value_pack, 'Value Pack']
        ]))

        frmObj.chkValuePack.stateChanged.connect(updateMarketTaxUI)
        frmObj.chkMerchantsRing.stateChanged.connect(updateMarketTaxUI)
        frmObj.spinMerchantsRing.valueChanged.connect(updateMarketTaxUI)
        frmObj.spinValuePack.valueChanged.connect(updateMarketTaxUI)
