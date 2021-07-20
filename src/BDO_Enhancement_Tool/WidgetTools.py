# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import os
import urllib3
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QThread, pyqtSignal, QSize, Qt, QPoint
from PyQt5.QtGui import QPixmap, QIcon, QPalette, QColor, QPainter
from PyQt5.QtWidgets import QTableWidgetItem, QSpinBox, QTreeWidgetItem, QWidget

from .bdo_database.gear_database import GearData
from .Core.ItemStore import STR_FMT_ITM_ID
from .Core.Gear import Gear, generate_gear_obj, GearType, gear_types

from .qt_UI_Common import STR_LENS_PATH, pix
from .DlgAddGear import pix_overlay_enhance, Dlg_AddGear, imgs
from .Qt_common import QBlockSig, NoScrollCombo, lbl_color_MainWindow, set_sort_cmb_box, get_dark_palette, CLabel, FocusLineEdit
from .common import IMG_TMP, GEAR_DB_MANAGER
from .model import Enhance_model


MONNIES_FORMAT = "{0:,.0f}"
STR_TWO_DEC_FORMAT = "{:.2f}"
STR_PERCENT_FORMAT = '{:.2%}'
remove_numeric_modifiers = lambda x: x.replace(',', '').replace('%','')


def numeric_less_than(self, y):
    return float(remove_numeric_modifiers(self.text())) <= float(remove_numeric_modifiers(y.text()))


def gt_str_to_q_color(gt_str) -> QColor:
    txt_c = gt_str.lower()
    color = Qt.white
    if txt_c.find('white') > -1:
        color = Qt.white
    elif txt_c.find('green') > -1:
        color = Qt.green
    elif txt_c.find('blue') > -1:
        color = Qt.blue
    elif txt_c.find('yellow') > -1 or txt_c.find('boss') > -1:
        color = Qt.yellow
    elif txt_c.find('blackstar') > -1 or txt_c.find('orange') > -1 or txt_c.find('fallen god') > -1:
        color = Qt.red
    return QColor(color)

class ImageLoadThread(QThread):
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


class MPThread(QThread):
    sig_done = pyqtSignal(object, object, name='sig_done')

    def __init__(self, func, *args, **kwargs):
        super(MPThread, self).__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self) -> None:
        try:
            ret = self.func(*self.args, **self.kwargs)
            self.sig_done.emit(self, ret)
        except Exception as e:
            self.sig_done.emit(self, e)


class custom_twi(QTableWidgetItem, QSpinBox):
    pass


class numeric_twi(QTableWidgetItem):
    def __lt__(self, other):
        return numeric_less_than(self, other)


class comma_seperated_twi(numeric_twi):
    def __init__(self, numba):
        super(comma_seperated_twi, self).__init__(MONNIES_FORMAT.format(numba))

    def setData(self, role, p_str):
        if role == Qt.DisplayRole:
            p_str = remove_numeric_modifiers(p_str)
            if p_str is None or p_str == '':
                return super(comma_seperated_twi, self).setData(role, MONNIES_FORMAT.format(p_str))
        return super(comma_seperated_twi, self).setData(role, p_str)

    def text(self):
        return super(comma_seperated_twi, self).text().replace(',','')


class TableWidgetGW(QTableWidgetItem):
    def __lt__(self, other):
        this_gw: GearWidget = self.gw()
        this_gw_name = str(this_gw.gear.name)
        try:
            other_gw: GearWidget = other.gw()
        except AttributeError:
            return this_gw_name < ''

        other_gw_name = str(other_gw.gear.name)
        if this_gw_name == other_gw_name:
            return this_gw.gear.get_enhance_lvl_idx() < other_gw.gear.get_enhance_lvl_idx()
        else:
            return this_gw_name < other_gw_name

    def gw(self):
        row = self.row()
        col = self.column()
        return self.tableWidget().cellWidget(row, col)


class TreeWidgetGW(QTreeWidgetItem):
    def __lt__(self, other):
        this_gw:GearWidget = self.gw()
        this_gw_name = str(this_gw.gear.name)
        try:
            other_gw:GearWidget = other.gw()
        except AttributeError:
            return this_gw_name < ''
        if other_gw is None:
            return this_gw_name < ''

        other_gw_name = str(other_gw.gear.name)
        if this_gw_name == other_gw_name:
            return this_gw.gear.get_enhance_lvl_idx() < other_gw.gear.get_enhance_lvl_idx()
        else:
            return this_gw_name < other_gw_name

    def gw(self):
        return self.treeWidget().itemWidget(self, 0)


class QImageLabel(QtWidgets.QLabel):
    sig_picture_changed = QtCore.pyqtSignal(object, str, name='sig_picture_changed')

    def __init__(self, img_path=None):
        super(QImageLabel, self).__init__()
        if img_path is None:
            img_path = ''
        self.img_path = img_path
        self.set_pic_path(img_path)

    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        if os.path.isfile(self.img_path):
            chk_path = os.path.dirname(self.img_path)
        else:
            chk_path = os.path.expanduser('~/Documents/Black Desert/FaceTexture')
        chk_path = QtWidgets.QFileDialog.getOpenFileName(self, 'Open Picture', chk_path)[0]
        if os.path.isfile(chk_path):
            self.set_pic_path(chk_path)

    def set_pic_path(self, str_path):
        if os.path.isfile(str_path):
            default_img = pix[str_path].scaled(QSize(250, 250), transformMode=Qt.SmoothTransformation,
                                                             aspectRatioMode=Qt.KeepAspectRatio)
            if not default_img.isNull():
                self.setPixmap(default_img)
                self.img_path = str_path
                self.sig_picture_changed.emit(self, str_path)
        else:
            default_img = pix[STR_LENS_PATH].scaled(QSize(50, 50), transformMode=Qt.SmoothTransformation,
                                                        aspectRatioMode=Qt.KeepAspectRatio)
            self.setPixmap(default_img)

    def get_path(self):
        return self.img_path


class GearTypeCmb(NoScrollCombo):
    def __init__(self, passthrough, *args, default=None):
        super(GearTypeCmb, self).__init__(passthrough, *args)
        self.update_gear_types(default)
        self.cmb_equ_change(self.currentText())
        self.currentTextChanged.connect(self.cmb_equ_change)

    def update_gear_types(self, default):
        type_s = list(gear_types.keys())
        set_sort_cmb_box(type_s, enumerate_gt, default, self)
        for i in range(0, self.count()):
            txt = self.itemText(i)
            color = QtGui.QColor(self.get_color(txt)).lighter()
            if color is not None:
                brush = QtGui.QBrush(color)
                self.setItemData(i, brush, Qt.TextColorRole)

    def cmb_equ_change(self, txt_c=None):
        if txt_c is None:
            txt_c = self.currentText()
        txt_c = txt_c.lower()
        this_pal = self.palette()
        this_pal.setColor(QPalette.ButtonText, Qt.black)
        c = self.get_color(txt_c)
        if c is None:
            this_pal = get_dark_palette()
        else:
            this_pal.setColor(QPalette.Button, c)
        self.setPalette(this_pal)

    def get_color(self, txt_c):
        return gt_str_to_q_color(txt_c)


class GearWidget(QWidget):
    sig_gear_changed = pyqtSignal(object, object, name='sig_gear_changed')
    sig_layout_changed = pyqtSignal(name='sig_layout_changed')
    sig_error = pyqtSignal(int, str, name='sig_error')
    #sig_gear_clicked = pyqtSignal(object, name='sig_gear_clicked')

    def __init__(self, gear: Gear, model, parent=None, edit_able=False, default_icon=None, display_full_name=False,
                 check_state=None, enhance_overlay=True):
        super(GearWidget, self).__init__(parent=parent)
        self.gear = None
        self.model: Enhance_model = model  # TODO: Accept a settings object not a model object
        self.table_widget = None
        self.icon = None
        self.col = None
        self.cmbLevel = None
        self.cmbType = None
        self.pixmap = None
        self.horizontalLayout = QtWidgets.QHBoxLayout(self)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.display_full_name = display_full_name
        self.edit_able = edit_able
        self.trinket = None

        self.chkInclude: QtWidgets.QCheckBox = None
        self.labelIcon = None
        self.txtEditName = None
        self.load_thread = None
        self.dlg_chose_gear = None
        self.parent_widget = None
        self.enhance_overlay = enhance_overlay
        self.cmbType: QtWidgets.QComboBox  = None
        self.cmbLevel: QtWidgets.QComboBox = None
        self.url = None

        self.lblName = CLabel(self)
        self.horizontalLayout.addWidget(self.lblName)

        self.lblName.sigMouseDoubleClick.connect(self.lblName_sigMouseDoubleClick)

        if check_state is not None:
            self.setCheckState(check_state)

        if default_icon is not None:
            self.set_icon(default_icon)

        self.set_gear(gear)

    def row(self):
        return self.parent_widget.row()

    def fix_cmb_lvl(self):
        if self.cmbLevel is not None:
            idx = self.cmbLevel.findText(self.gear.enhance_lvl)
            if not idx == self.cmbLevel.currentIndex():
                self.cmbLevel.setCurrentIndex(idx)

    def lblName_sigMouseDoubleClick(self, ev):
        if self.edit_able:
            self.txtEditName = FocusLineEdit(self)
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
            self.lblName = CLabel(self)
            new_name = self.txtEditName.text()
            self.lblName.setText(new_name)
            self.gear.name = new_name
            self.horizontalLayout.replaceWidget(self.txtEditName, self.lblName)
            self.lblName.sigMouseDoubleClick.connect(self.lblName_sigMouseDoubleClick)
            self.txtEditName.deleteLater()
            self.txtEditName = None
            self.sig_layout_changed.emit()

    def load_gear_icon(self):
        if self.gear.item_id is not None:
            item_id = self.gear.item_id
            pad_item_id = STR_FMT_ITM_ID.format(item_id)
            try:
                gd = GEAR_DB_MANAGER.lookup_id(item_id)
            except KeyError:
                return
            icon_path = os.path.join(IMG_TMP, pad_item_id + '.png')

            imgs.sig_image_load.connect(self.image_loaded)
            self.url = gd.icon_url
            imgs.get_icon(self.url, icon_path)

    def image_loaded(self, url, icon_path):
        if url == self.url:
            self.set_icon(pix.get_icon(icon_path))
            imgs.sig_image_load.disconnect(self.image_loaded)

    def set_editable(self, editable:bool):
        if self.edit_able:
            if self.labelIcon is not None:
                try:
                    self.labelIcon.sigMouseLeftClick.disconnect(self.labelIcon_sigMouseClick)
                except TypeError:
                    pass
        self.edit_able = editable

    def set_icon(self, icon: QIcon, enhance_overlay=None):
        self.icon = icon
        self.set_pixmap(icon.pixmap(QSize(32, 32)), enhance_overlay=enhance_overlay)

    def set_trinket(self, pix:QPixmap):
        if pix is None:
            self.trinket = pix
        else:
            self.trinket = pix.scaled(20, 20)
        self.set_pixmap()

    def set_pixmap(self, pixmap:QPixmap=None, enhance_overlay=None):
        if enhance_overlay is None:
            enhance_overlay = self.enhance_overlay

        if self.pixmap is None:
            self.labelIcon = CLabel(self)
            self.labelIcon.setMinimumSize(QSize(32, 32))
            self.labelIcon.setMaximumSize(QSize(32, 32))
            self.labelIcon.setText("")
            if self.chkInclude is None:
                self.horizontalLayout.insertWidget(0, self.labelIcon)
            else:
                self.horizontalLayout.insertWidget(1, self.labelIcon)
            if self.edit_able:
                self.labelIcon.sigMouseLeftClick.connect(self.labelIcon_sigMouseClick)
            if pixmap is None:
                pixmap = QPixmap()
        else:
            if pixmap is None:
                pixmap = self.pixmap

        self.pixmap = pixmap

        this_pix = pixmap
        if enhance_overlay or self.trinket is not None:
            this_pix = QPixmap(QtCore.QSize(32, 32))
            this_pix.fill(QtCore.Qt.transparent)
            painter = QPainter(this_pix)
            painter.drawPixmap(QPoint(0, 0), pixmap)
            if self.trinket is not None:
                painter.drawPixmap(0, 12, self.trinket)
            if self.gear is not None and enhance_overlay:
                fp = pix_overlay_enhance(self.gear)
                if fp is not None:
                    painter.drawPixmap(QPoint(0, 0), QPixmap(fp))
            painter.end()

        self.labelIcon.setPixmap(this_pix)

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
        self.sig_layout_changed.emit()
        self.fix_cmb_lvl()
        self.load_gear_icon()

    def labelIcon_sigMouseClick(self, ev):
        if self.edit_able:
            if self.dlg_chose_gear is not None:
                self.dlg_chose_gear.close()
                self.dlg_chose_gear.deleteLater()
            self.dlg_chose_gear = Dlg_AddGear()
            self.dlg_chose_gear.sig_gear_chosen.connect(self.dlg_chose_gear_sig_gear_chosen)
            self.dlg_chose_gear.show()

    def dlg_chose_gear_sig_gear_chosen(self, gd:GearData):
        if self.gear.name is None or self.gear.name == '':
            self.gear.name = gd.name
        type_str = gd.get_gt_str()
        self.set_gear_type_str(type_str, itm_id=gd.item_id)  # will fire sig_gear_changed
        self.update_data()

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
        self.parent_widget = TableWidgetGW('')
        table_widget.setItem(row, col, self.parent_widget)
        if self.icon is not None:
            table_widget.setRowHeight(row, 45)
        self.table_widget = table_widget
        self.col = col

    def set_gear_type_str(self, str_picked, enhance_lvl=None, itm_id=None):
        this_gear = self.gear
        old_gear = this_gear
        if enhance_lvl is None:
            enhance_lvl = this_gear.enhance_lvl
        if itm_id is None:
            itm_id = this_gear.item_id

        new_gt = gear_types[str_picked]
        if enhance_lvl in new_gt.lvl_map:
            this_lvl = enhance_lvl
        else:
            this_lvl = new_gt.idx_lvl_map[0]

        this_gear = generate_gear_obj(self.model.settings, base_item_cost=this_gear.base_item_cost, enhance_lvl=this_lvl,
                                      gear_type=new_gt, name=this_gear.name, sale_balance=this_gear.sale_balance, id=itm_id)
        if self.cmbType is not None:
            idx = self.cmbType.findText(str_picked)
            with QBlockSig(self.cmbType):
                self.cmbType.setCurrentIndex(idx)
            self.cmbType.cmb_equ_change()
        self.set_gear(this_gear)
        self.sig_gear_changed.emit(self, old_gear)

    def create_gt_cmb(self, tw) -> GearTypeCmb:
        gear = self.gear
        cmb_gt = GearTypeCmb(tw, default=gear.gear_type.name)
        self.cmbType = cmb_gt

        def cmb_gt_currentTextChanged(str_picked):
            new_gt = gear_types[str_picked]
            cmb_enh = self.cmbLevel
            this_lvl = gear.enhance_lvl
            if cmb_enh is not None:
                with QBlockSig(cmb_enh):
                    set_sort_cmb_box(list(new_gt.lvl_map.keys()), new_gt.enumerate_gt_lvl, this_lvl, cmb_enh)
            self.set_gear_type_str(str_picked)
            # Sets the hidden value of the table widget so that colors are sorted in the right order
        cmb_gt.currentTextChanged.connect(cmb_gt_currentTextChanged)
        return cmb_gt

    def create_lvl_cmb(self, tw) -> NoScrollCombo:
        gear = self.gear
        gtype_s = gear.gear_type.name
        cmb_enh = NoScrollCombo(tw)

        self.cmbLevel = cmb_enh
        set_sort_cmb_box(list(gear_types[gtype_s].lvl_map.keys()), gear.gear_type.enumerate_gt_lvl,
                                   gear.enhance_lvl, cmb_enh)

        def cmb_enh_currentTextChanged(str_picked):
            this_gear = self.gear
            try:
                this_gear.set_enhance_lvl(str_picked)
                self.load_gear_icon()
            except KeyError:
                self.sig_error.emit(lbl_color_MainWindow.CRITICAL,'Enhance level does not appear to be valid.')
            self.sig_gear_changed.emit(self, this_gear)

        cmb_enh.currentTextChanged.connect(cmb_enh_currentTextChanged)
        return cmb_enh

    def create_Cmbs(self, tw):
        self.create_lvl_cmb(tw)
        self.create_gt_cmb(tw)

    def add_to_tree(self, tree, item, col=0):
        tree.setItemWidget(item, col, self)
        self.table_widget = tree
        self.parent_widget = item
        self.col = col


def set_cell_lvl_compare(twi_lvl, lvl_str, gear_type:GearType):
    txt_c = str(gear_type.enumerate_gt_lvl(lvl_str))
    twi_lvl.setText(txt_c)


def get_gt_color_compare(gt_str):
    txt_c = gt_str.lower()
    if txt_c.find('white') > -1:
        return 'b'
    elif txt_c.find('green') > -1:
        return 'c'
    elif txt_c.find('blue') > -1:
        return 'd'
    elif txt_c.find('yellow') > -1 or txt_c.find('boss') > -1:
        return 'e'
    elif txt_c.find('fallen god') > -1 or txt_c.find('blackstar') > -1:
        return 'f'
    else:
        return 'a'


def set_cell_color_compare(twi_gt, gt_str):
    twi_gt.setText(get_gt_color_compare(gt_str))


def monnies_twi_factory(i_f_val):
    twi = comma_seperated_twi(i_f_val)
    return twi


def enumerate_gt(g1):
    txt_c = g1.lower()
    if txt_c.find('white') > -1:
        return 0
    elif txt_c.find('green') > -1:
        return 1
    elif txt_c.find('blue') > -1:
        return 2
    elif txt_c.find('yellow') > -1 or txt_c.find('boss') > -1:
        return 3
    else:
        return -1