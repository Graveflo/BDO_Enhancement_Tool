# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import os
from typing import List, Dict, Union
import numpy
from .DlgAddGear import imgs
from .bdo_database.gear_database import class_grade_to_gt_str, grade_enum_to_str, class_enum_to_str

from .qt_UI_Common import STR_PIC_VALKS, pix, ITEM_PIC_DIR

from .Forms.altWidget import Ui_alt_Widget
from .Forms.dlg_Manage_Alts import Ui_dlg_Manage_Alts
from .Forms.dlg_Manage_Valks import Ui_dlg_Manage_Valks
from .Forms.dlg_Sale_Balance import Ui_DlgSaleBalance
from .Forms.dlg_Probability import Ui_dlgProbability
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import pyqtSignal, QSize
from PyQt5.QtWidgets import QDialog, QWidget, QTableWidgetItem, QSpinBox, QTreeWidget, QHBoxLayout, QTreeWidgetItem
from .Qt_common import clear_table, NoScrollSpin, SpeedUpTable
from .WidgetTools import QImageLabel, QBlockSig, STR_PERCENT_FORMAT, MONNIES_FORMAT
from .common import relative_path_convert, IMG_TMP, GEAR_DB_MANAGER, GtGearData
from .Core.Gear import GearType, gear_types
from .Core.ItemStore import ItemStore, STR_FMT_ITM_ID
from .model import Enhance_model


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


class DlgManageAlts(QDialog):
    def __init__(self, frmMain):
        super(DlgManageAlts, self).__init__(parent=frmMain)
        frmObj = Ui_dlg_Manage_Alts()
        frmObj.setupUi(self)
        self.ui = frmObj
        self.frmMain = frmMain

        frmObj.scrollArea.setStyleSheet('''
        QLabel {
        border: 1px solid white;
        }''')

        frmObj.cmdOk.clicked.connect(self.hide)
        def cmdAdd_clicked():
            settings = self.frmMain.model.settings
            settings[settings.P_ALTS].append(['', '', 0])
            settings.invalidate()
            self.add_row()
        frmObj.cmdAdd.clicked.connect(cmdAdd_clicked)
        frmObj.cmdImport.clicked.connect(self.cmdImport_clicked)

        self.alt_widgets: List[AltWidget] = []

    def cmdImport_clicked(self):
        userprof = os.environ['userprofile']
        chk_path = os.path.expanduser('~/Documents/Black Desert/FaceTexture')
        QFileDialog = QtWidgets.QFileDialog
        chk_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Open Folder", chk_path, QFileDialog.DirectoryOnly | QFileDialog.DontUseNativeDialog | QFileDialog.DontResolveSymlinks)

        settings = self.frmMain.model.settings
        alts = settings[settings.P_ALTS]
        if os.path.isdir(chk_path):
            for fil in os.listdir(chk_path):
                fil = os.path.join(chk_path, fil)
                if fil.endswith('.bmp'):
                    if os.path.isfile(fil):
                        self.add_row(picture=fil)
                        alts.append([fil, '', self.frmMain.model.get_min_fs()])

    def cmdRemove_clicked(self, wid):
        frmObj = self.ui
        settings = self.frmMain.model.settings

        frmObj.layoutAlts.removeWidget(wid)
        idx = self.alt_widgets.index(wid)
        self.alt_widgets.remove(wid)

        settings[settings.P_ALTS].pop(idx)
        settings.invalidate()

    def add_row(self, picture=None, name='', fs=None):
        alt_wid = AltWidget(self, img_path=picture, name=name, fs=fs)
        alt_wid.sig_remove_me.connect(self.cmdRemove_clicked)
        self.alt_widgets.append(alt_wid)
        self.ui.layoutAlts.addWidget(alt_wid)

    def showEvent(self, a0: QtGui.QShowEvent) -> None:
        for wid in self.alt_widgets:
            self.ui.layoutAlts.removeWidget(wid)
        self.alt_widgets = []

        settings = self.frmMain.model.settings
        alts = settings[settings.P_ALTS]
        for picture,name,fs in alts:
            row = self.add_row(picture=picture, name=name, fs=fs)

    def update_fs_min(self):
        settings = self.frmMain.model.settings
        min_fs = settings[settings.P_QUEST_FS_INC]
        for wid in self.alt_widgets:
            wid.ui.spinFS.setMinimum(min_fs)


class AltWidget(QWidget):
    sig_remove_me = pyqtSignal(object, name='sig_remove_me')
    def __init__(self, dlgAlts:DlgManageAlts, img_path=None, name='', fs=None):
        super(AltWidget, self).__init__(dlgAlts.ui.scrollArea)
        frmObj = Ui_alt_Widget()
        frmObj.setupUi(self)
        self.ui = frmObj
        self.dlgAlts = dlgAlts
        frmMain = dlgAlts.frmMain
        self.frmMain = frmMain

        settings = frmMain.model.settings
        num_fs = settings[settings.P_NUM_FS]

        self.setObjectName('AltWidget')


        min_fs = frmMain.model.get_min_fs()

        if fs is None:
            fs = min_fs
        frmObj.spinFS.setMinimum(min_fs)
        frmObj.spinFS.setMaximum(num_fs)
        frmObj.spinFS.setValue(fs)
        frmObj.txtName.setText(name)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)

        self.picture_lbl  = QImageLabel(img_path=img_path)
        self.picture_lbl.setMinimumHeight(250)
        self.picture_lbl.setSizePolicy(sizePolicy)
        self.picture_lbl.sig_picture_changed.connect(self.lbl_sig_picture_changed)
        frmObj.verticalLayout.replaceWidget(frmObj.lblPicture, self.picture_lbl)
        frmObj.lblPicture.deleteLater()
        frmObj.spinFS.valueChanged.connect(self.spin_changed)
        frmObj.txtName.textChanged.connect(self.txtName_textChanged)
        frmObj.cmdRemove.clicked.connect(self.cmdRemove_clicked)

    def event(self, a0: QtCore.QEvent) -> bool:
        if isinstance(a0, QtGui.QWheelEvent):
            sd = a0.angleDelta().y()
            sb = self.dlgAlts.ui.scrollArea.horizontalScrollBar()
            if sb is not None:
                sb.setValue(sb.value() + sd)
            a0.accept()
            return True
        else:
            return super(AltWidget, self).event(a0)

    def cmdRemove_clicked(self):
        self.ui.cmdRemove.setEnabled(False)
        self.hide()
        self.sig_remove_me.emit(self)

    def txtName_textChanged(self, txt):
        settings = self.frmMain.model.settings
        alts = settings[settings.P_ALTS]
        row = self.dlgAlts.ui.layoutAlts.indexOf(self)
        alts[row][1] = txt
        self.frmMain.invalidate_strategy()

    def lbl_sig_picture_changed(self, lbl, path):
        dlgalts = self.dlgAlts
        idx = dlgalts.ui.layoutAlts.indexOf(self)
        settings = self.frmMain.model.settings
        settings[[settings.P_ALTS, idx, 0]] = path

    def spin_changed(self, pint):
        settings = self.frmMain.model.settings
        row = self.dlgAlts.ui.layoutAlts.indexOf(self)
        settings[[settings.P_ALTS, row, 2]] = pint
        self.frmMain.invalidate_strategy()


class ValksTwi(QTableWidgetItem):
    def __init__(self, fs, *args):
        super(ValksTwi, self).__init__(*args)
        self.fs = fs

    def __lt__(self, other):
        if isinstance(other, ValksTwi):
            return self.fs < other.fs
        else:
            return super(ValksTwi, self).__lt__(other)

    def text(self):
        return 'Advice of Valks (+{})'.format(self.fs)


class DlgManageValks(QDialog):
    STR_VALKS_STR = 'Advice of Valks (+{})'

    def __init__(self, frmMain):
        super(DlgManageValks, self).__init__(parent=frmMain)
        frmObj = Ui_dlg_Manage_Valks()
        frmObj.setupUi(self)
        self.ui = frmObj
        self.frmMain = frmMain

        self.icon_l = pix.get_icon(STR_PIC_VALKS)

        frmObj.cmdOk.clicked.connect(self.hide)
        def cmdAdd_clicked():
            settings = self.frmMain.model.settings
            valks = settings[settings.P_VALKS]
            fs = frmObj.spinFS.value()
            if fs in valks:
                self.select_valks(fs)
            else:
                valks[fs] = 1
                settings.invalidate()
                self.add_row(fs)

        frmObj.cmdAdd.clicked.connect(cmdAdd_clicked)
        frmObj.cmdRemove.clicked.connect(self.cmdRemove_clicked)
        frmObj.tableWidget.setIconSize(QSize(32,32))
        frmObj.tableWidget.itemChanged.connect(self.tableWidget_itemChanged)
        self.spin_dict: Dict[QSpinBox, ValksTwi] = {}

    def hideEvent(self, a0: QtGui.QHideEvent) -> None:
        self.frmMain.model.save()

    def showEvent(self, a0: QtGui.QShowEvent) -> None:
        tw = self.ui.tableWidget
        clear_table(tw)
        settings = self.frmMain.model.settings
        valks = settings[settings.P_VALKS]
        self.ui.spinFS.setMinimum(settings[settings.P_QUEST_FS_INC])
        self.ui.spinFS.setMaximum(settings[settings.P_NUM_FS])
        for fs in valks:
            self.add_row(fs)
            #row = self.add_row(fs)
            #self.spins[-1].setValue(fs)

    def tableWidget_itemChanged(self, item:QTableWidgetItem):
        self.ui.tableWidget.resizeColumnToContents(item.column())

    def cmdRemove_clicked(self):
        frmObj = self.ui
        tw = frmObj.tableWidget

        settings = self.frmMain.model.settings

        sels  = list(set([x.row() for x in tw.selectedIndexes()]))
        sels.sort(reverse=True)
        for sel in sels:
            this_spin = tw.cellWidget(sel, 1)
            self.spin_dict.pop(this_spin)
            wid = frmObj.tableWidget.item(sel, 0)
            tw.removeRow(sel)
            #this_spin.deleteLater()
            settings[settings.P_VALKS].pop(wid.fs)
            settings.invalidate()

    def spin_changed(self, pint):
        twi = self.spin_dict[self.sender()]
        settings = self.frmMain.model.settings
        valks = settings[settings.P_VALKS]

        fs = twi.fs
        valks[fs] = pint
        settings.invalidate()
        twi_spin = self.ui.tableWidget.item(twi.row(), 1)
        twi_spin.setText(str(pint))
        #twi.setText(self.STR_VALKS_STR.format(pint))
        self.frmMain.invalidate_strategy()

    def select_valks(self, fs):
        frmObj = self.ui

        for i in range(0, frmObj.tableWidget.rowCount()):
            wid = frmObj.tableWidget.item(i, 0)
            if isinstance(wid, ValksTwi) and wid.fs == fs:
                frmObj.tableWidget.selectRow(i)

    def add_row(self, fs) -> int:
        tw = self.ui.tableWidget
        row = tw.rowCount()
        settings = self.frmMain.model.settings
        valks = settings[settings.P_VALKS]
        num_valks = valks[fs]

        with QBlockSig(tw):

            tw.insertRow(row)
            twi = ValksTwi(fs, self.STR_VALKS_STR.format(fs))
            twi.setIcon(self.icon_l)
            tw.setItem(row, 0, twi)
            twi_num = QTableWidgetItem(str(fs))
            tw.setItem(row, 1, twi_num)

            this_spin = NoScrollSpin(tw, self)
            this_spin.setMaximum(10000)
            this_spin.setMinimum(1)
            this_spin.setValue(num_valks)
            self.spin_dict[this_spin] = twi
            this_spin.valueChanged.connect(self.spin_changed)
            #self.spins.append(this_spin)
            tw.setCellWidget(row, 1, this_spin)
            tw.setRowHeight(row, 32)
        self.tableWidget_itemChanged(twi)
        tw.clearSelection()
        this_spin.setFocus()
        this_spin.selectAll()
        return row


class DlgManageNaderr(QDialog):
    def __init__(self, frmMain):
        super(DlgManageNaderr, self).__init__(parent=frmMain)
        frmObj = Ui_dlg_Manage_Valks()
        frmObj.setupUi(self)
        self.ui = frmObj
        frmObj.cmdAdd.setText('Add Page')
        frmObj.cmdRemove.setText('Remove Page')
        frmObj.spinFS.hide()
        frmObj.lblValksChance.hide()
        frmObj.tableWidget.setSortingEnabled(False)
        self.setWindowTitle('Manage Naderr\'s Band')
        frmObj.tableWidget.horizontalHeaderItem(1).setText('Fail stack')
        self.frmMain = frmMain

        self.icon_l = pix.get_icon(STR_PIC_VALKS)

        frmObj.cmdOk.clicked.connect(self.hide)
        def cmdAdd_clicked():
            settings = self.frmMain.model.settings
            min_fs = self.frmMain.model.get_min_fs()
            settings[settings.P_NADERR_BAND].append(min_fs)
            settings.invalidate()
            self.add_row(min_fs)

        frmObj.cmdAdd.clicked.connect(cmdAdd_clicked)
        frmObj.cmdRemove.clicked.connect(self.cmdRemove_clicked)
        frmObj.tableWidget.setIconSize(QSize(32, 32))
        frmObj.tableWidget.itemChanged.connect(self.tableWidget_itemChanged)
        self.spin_dict: Dict[QSpinBox, QTableWidgetItem] = {}

    def hideEvent(self, a0: QtGui.QHideEvent) -> None:
        self.frmMain.model.save()

    def tableWidget_itemChanged(self, item:QTableWidgetItem):
        self.ui.tableWidget.resizeColumnToContents(item.column())

    def cmdRemove_clicked(self):
        frmObj = self.ui
        tw = frmObj.tableWidget

        settings = self.frmMain.model.settings

        sels  = list(set([x.row() for x in tw.selectedIndexes()]))
        sels.sort(reverse=True)
        for sel in sels:
            this_spin = tw.cellWidget(sel, 1)
            self.spin_dict.pop(this_spin)
            tw.removeRow(sel)
            #this_spin.deleteLater()
            settings[settings.P_NADERR_BAND].pop(sel)
            settings.invalidate()

    def spin_changed(self, pint):
        twi:QTableWidgetItem = self.spin_dict[self.sender()]
        settings = self.frmMain.model.settings

        row = twi.row()
        twi_desc = self.ui.tableWidget.item(row, 0)
        settings[[settings.P_NADERR_BAND, row]] = pint
        twi.setText(str(pint))
        self.frmMain.invalidate_strategy()

    def add_row(self, fs) -> int:
        tw = self.ui.tableWidget
        row = tw.rowCount()
        settings = self.frmMain.model.settings
        min_fs = settings[settings.P_QUEST_FS_INC]

        with QBlockSig(tw):
            tw.insertRow(row)
            twi = QTableWidgetItem('Naderr Page')
            tw.setItem(row, 0, twi)
            twi_num = QTableWidgetItem(str(fs))
            tw.setItem(row, 1, twi_num)

            this_spin = NoScrollSpin(tw, self)
            this_spin.setMinimum(min_fs)
            this_spin.setMaximum(10000)
            this_spin.setValue(fs)
            self.spin_dict[this_spin] = twi_num
            this_spin.valueChanged.connect(self.spin_changed)
            #self.spins.append(this_spin)
            tw.setCellWidget(row, 1, this_spin)
            tw.setRowHeight(row, 32)
        self.tableWidget_itemChanged(twi)
        tw.clearSelection()
        tw.selectRow(row)
        this_spin.setFocus()
        this_spin.selectAll()
        return row

    def showEvent(self, a0: QtGui.QShowEvent) -> None:
        tw = self.ui.tableWidget
        clear_table(tw)
        settings = self.frmMain.model.settings
        alts = settings[settings.P_NADERR_BAND]
        for fs in alts:
            self.add_row(fs)
        self.update_fs_min()

    def update_fs_min(self):
        settings = self.frmMain.model.settings
        min_fs = settings[settings.P_QUEST_FS_INC]
        for spin in self.spin_dict.keys():
            spin.setMinimum(min_fs)


class DlgGearTypeProbability(QDialog):
    def __init__(self, frmMain):
        super(DlgGearTypeProbability, self).__init__()
        frmObj = Ui_dlgProbability()
        frmObj.setupUi(self)
        self.ui = frmObj
        self.frmMain = frmMain
        self.model: Enhance_model = frmMain.model

        self.gt = None

        frmObj.spinFS.setMinimum(0)
        frmObj.spinProb.setMinimum(0)
        frmObj.spinProb.setMaximum(1.0)

        frmObj.cmbGearType.currentTextChanged.connect(self.cmbGearType_currentTextChanged)

        self.action_deselect = QtWidgets.QAction('Deselect')
        self.deselect_keybind = QtGui.QKeySequence('Ctrl+Shift+A')
        self.action_deselect.setShortcut(self.deselect_keybind)
        self.action_deselect.triggered.connect(self.action_deselect_triggered)
        frmObj.tableWidget.addAction(self.action_deselect)
        frmObj.tableWidget.cellClicked.connect(self.tableWidget_cellClicked)
        frmObj.spinProb.valueChanged.connect(self.spinProb_valueChanged)
        frmObj.spinFS.valueChanged.connect(self.spinFS_valueChanged)
        frmObj.cmbLvl.currentIndexChanged.connect(lambda: self.spinFS_valueChanged(frmObj.spinFS.value()))
        frmObj.cmdLoadFile.clicked.connect(self.cmdLoadFile_clicked)

    def set_common(self, model:Enhance_model):
        self.model = model
        self.cmbGearType_currentTextChanged(self.ui.cmbGearType.currentText())

    def cmdLoadFile_clicked(self):
        chk_path = QtWidgets.QFileDialog.getOpenFileName(self, 'Open Picture', relative_path_convert('Data/'))[0]
        if os.path.isfile(chk_path):
            self.gt = GearType(name=os.path.basename(chk_path))
            with open(chk_path, 'r') as f:
                try:
                    self.gt.load_txt(f.read())
                except:
                    self.frmMain.show_warning_msg('Invalid file.')
                    self.gt = None
                    self.ui.cmbGearType.setCurrentIndex(-1)
                    self.populate_table()
                    return
            self.populate_table()
            self.ui.cmbGearType.setCurrentText(self.gt.name)

    def action_deselect_triggered(self):
        frmObj = self.ui
        frmObj.tableWidget.clearSelection()

    def spinFS_valueChanged(self, val):
        frmObj = self.ui
        lvl = frmObj.cmbLvl.currentText()
        gt = self.gt
        if gt is None:
            return
        if lvl not in gt.lvl_map:
            return
        lvl_idx = gt.lvl_map[lvl]
        map_lvl = gt.map[lvl_idx]
        with QBlockSig(frmObj.spinProb):
            frmObj.spinProb.setValue(map_lvl[val])
        frmObj.tableWidget.setCurrentCell(val, lvl_idx)

    def spinProb_valueChanged(self, val):
        frmObj = self.ui
        lvl = frmObj.cmbLvl.currentText()
        gt = self.gt
        if gt is None:
            return
        if lvl not in gt.lvl_map:
            return
        lvl_idx = gt.lvl_map[lvl]
        map_lvl = gt.map[lvl_idx]
        sort_idx = numpy.searchsorted(map_lvl, val)
        with QBlockSig(frmObj.spinFS):
            frmObj.spinFS.setValue(sort_idx)
        frmObj.tableWidget.setCurrentCell(sort_idx, lvl_idx)

    def tableWidget_cellClicked(self, row, col):
        frmObj = self.ui

        gt = self.gt
        if gt is None:
            return

        map = gt.map
        with QBlockSig(frmObj.spinProb, frmObj.spinFS, frmObj.cmbLvl):
            frmObj.spinProb.setValue(map[col][row])
            frmObj.spinFS.setValue(row)
            frmObj.cmbLvl.setCurrentIndex(frmObj.cmbLvl.findText(gt.idx_lvl_map[col]))

    def cmbGearType_currentTextChanged(self, txt):
        frmObj = self.ui
        self.gt = None


        try:
            gt = gear_types[txt]
        except KeyError:
            return
        self.gt = gt
        self.populate_table()

    def populate_table(self):
        frmObj = self.ui
        with QBlockSig(frmObj.spinProb, frmObj.cmbLvl, frmObj.tableWidget):
            frmObj.tableWidget.clear()
            prev_lvl = frmObj.cmbLvl.currentText()
            frmObj.cmbLvl.clear()
            frmObj.spinProb.setValue(0.0)
        gt = self.gt
        if gt is None:
            return


        num_fs = self.model.get_max_fs()
        frmObj.spinFS.setMaximum(num_fs)


        map = gt.map
        lvls = gt.lvl_map.keys()
        sorted_lvls = []
        with QBlockSig(frmObj.cmbLvl):
            for i in range(0, len(map)):
                map[i][num_fs]
                lvl_text = gt.idx_lvl_map[i]
                sorted_lvls.append(lvl_text)
                frmObj.cmbLvl.addItem(lvl_text)

        map = numpy.array(gt.map)

        capped_brush = QtGui.QBrush(QtGui.QColor(QtCore.Qt.darkRed))
        with SpeedUpTable(frmObj.tableWidget):
            frmObj.tableWidget.setColumnCount(len(sorted_lvls))
            frmObj.tableWidget.setRowCount(num_fs)
            frmObj.tableWidget.setHorizontalHeaderLabels(sorted_lvls)

            for col in range(len(sorted_lvls)):
                down_cap = gt.map[col].down_cap
                for row in range(num_fs):
                    val = map[col][row]
                    twi = QTableWidgetItem(STR_PERCENT_FORMAT.format(val))
                    frmObj.tableWidget.setItem(row, col, twi)
                    if val > down_cap:
                        twi.setData(QtCore.Qt.BackgroundColorRole, capped_brush)
        frmObj.tableWidget.setVerticalHeaderLabels([str(x) for x in range(0, num_fs)])

        idx = frmObj.cmbLvl.findText(prev_lvl)
        if idx > -1:
            frmObj.cmbLvl.setCurrentIndex(idx)


class DlgItemStore(QDialog):
    def __init__(self, *args):
        super(DlgItemStore, self).__init__(*args)
        self.model:Enhance_model = None
        self.tree = QTreeWidget(self)
        self.layout = QHBoxLayout(self)
        self.setLayout(self.layout)
        self.layout.addWidget(self.tree)
        self.tree.setHeaderLabels(['ID', 'Item', 'Cost', 'Expires'])
        self.twi_urls = {}
        self.setWindowTitle('Item Store')

    def set_common(self, model:Enhance_model, frmMain):
        self.model = model
        self.frmMain = frmMain

    def show(self) -> None:
        self.populate()

        super(DlgItemStore, self).show()

    def populate(self):
        model = self.model
        settings = model.settings
        item_store:ItemStore = settings[settings.P_ITEM_STORE]
        self.tree.clear()

        imgs.sig_image_load.connect(self.image_loaded)

        for k,v in item_store.store_items.items():
            prices = v.prices
            if prices is not None:
                tli = QTreeWidgetItem(self.tree, [k, v.name, '', str(v.expires)])
                self.tree.addTopLevelItem(tli)
                gd = self.load_gear_icon(k, tli)
                tli.setText(2, MONNIES_FORMAT.format(prices[0]))
                for i,p in enumerate(v.prices[1:]):
                    twi = QTreeWidgetItem(['', v.name, MONNIES_FORMAT.format(p), ''])
                    tli.addChild(twi)
                if gd is not None:  # If ret is none this is a gear item not a material
                    gear_type = gd.get_gear_type()
                    for idx, lvl in gear_type.idx_lvl_map.items():
                        if idx == 0:
                            continue
                        lvl_e_t = gear_type.bin_mp(idx)
                        child = tli.child(lvl_e_t-1)
                        if child is not None:
                            lvl = gear_type.idx_lvl_map[idx-1]  # MP cost of PRI is, target DUO's cost
                            prev_text = child.text(0)
                            if prev_text.strip() == '':
                                text = str(lvl)
                            else:
                                text = '{}, {}'.format(prev_text, lvl)
                            child.setText(0,  text)
                    child = tli.child(tli.childCount()-1)
                    child.setText(0, gear_type.idx_lvl_map[len(gear_type.map)-1])

    def load_gear_icon(self, item_id, tli) -> Union[None, GtGearData]:
        item_id = int(item_id)
        pad_item_id = STR_FMT_ITM_ID.format(item_id)
        icon_path = os.path.join(IMG_TMP, pad_item_id + '.png')
        try:
            gd = GEAR_DB_MANAGER.lookup_id(item_id)
        except KeyError:
            if os.path.isfile(icon_path):
                tli.setIcon(0, pix.get_icon(icon_path))
            icon_path = os.path.join(ITEM_PIC_DIR, pad_item_id + '.png')
            if os.path.isfile(icon_path):
                tli.setIcon(0, pix.get_icon(icon_path))
            return
        url = gd.icon_url
        if url in self.twi_urls:
            self.twi_urls[url].append(tli)
        else:
            self.twi_urls[url] = [tli]
        imgs.get_icon(url, icon_path)
        return gd

    def image_loaded(self, url, icon_path):
        if url in self.twi_urls:
            for i in self.twi_urls[url]:
                i.setIcon(0, pix.get_icon(icon_path))
            del self.twi_urls[url]
        #if len(self.twi_urls) <= 0:
        #    imgs.sig_image_load.disconnect(self.image_loaded)