# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import os

import urllib3
from .DlgAddGear import gears, pix_overlay_enhance, Dlg_AddGear, imgs
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QThread, pyqtSignal, QSize, Qt
from PyQt5.QtGui import QPixmap, QIcon, QPalette, QColor
from PyQt5.QtWidgets import QTableWidgetItem, QSpinBox, QTreeWidgetItem, QWidget, QMenu, QAction
from .QtCommon import Qt_common
from .common import relative_path_convert, Gear, GEAR_ID_FMT, IMG_TMP, gear_types, enumerate_gt, \
    Smashable, generate_gear_obj, Classic_Gear, Gear_Type
from .model import Enhance_model

QBlockSig = Qt_common.QBlockSig
NoScrollCombo = Qt_common.NoScrollCombo
lbl_color_MainWindow = Qt_common.lbl_color_MainWindow
MONNIES_FORMAT = "{:,}"
STR_TWO_DEC_FORMAT = "{:.2f}"
STR_PERCENT_FORMAT = '{:.2f}%'
STR_LENS_PATH  = relative_path_convert('Images/lens2.png')
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
    def __init__(self, text):
        super(comma_seperated_twi, self).__init__(text)
        self.setText(text)

    def setData(self, role, p_str):
        p_str = remove_numeric_modifiers(p_str)
        if p_str is None or p_str == '':
            super(comma_seperated_twi, self).setData(role, p_str)
        else:
            super(comma_seperated_twi, self).setData(role, MONNIES_FORMAT.format(int(float(p_str))))

#    def setText(self, p_str):


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
            default_img = QPixmap(str_path).scaled(QSize(250, 250), transformMode=Qt.SmoothTransformation,
                                                             aspectRatioMode=Qt.KeepAspectRatio)
            if not default_img.isNull():
                self.setPixmap(default_img)
                self.img_path = str_path
                self.sig_picture_changed.emit(self, str_path)
        else:
            default_img = QPixmap(STR_LENS_PATH).scaled(QSize(50, 50), transformMode=Qt.SmoothTransformation,
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
        Qt_common.set_sort_cmb_box(type_s, enumerate_gt, default, self)
        for i in range(0, self.count()):
            txt = self.itemText(i)
            color = QtGui.QColor(self.get_color(txt)).lighter()
            if color is not None:
                brush = QtGui.QBrush(color)
                self.setItemData(i, brush, Qt.TextColorRole)

    def cmb_equ_change(self, txt_c):
        txt_c = txt_c.lower()
        this_pal = self.palette()
        this_pal.setColor(QPalette.ButtonText, Qt.black)
        c = self.get_color(txt_c)
        if c is None:
            this_pal = Qt_common.get_dark_palette()
        else:
            this_pal.setColor(QPalette.Button, c)
        self.setPalette(this_pal)

    def get_color(self, txt_c):
        return gt_str_to_q_color(txt_c)


class GearWidget(QWidget):
    sig_gear_changed = pyqtSignal(object, name='sig_gear_changed')
    sig_layout_changed = pyqtSignal(name='sig_layout_changed')
    sig_error = pyqtSignal(int, str, name='sig_error')

    def __init__(self, gear: Gear, model, parent=None, edit_able=False, default_icon=None, display_full_name=False,
                 check_state=None, enhance_overlay=True):
        super(GearWidget, self).__init__(parent=parent)
        self.gear = None
        self.model: Enhance_model = model
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

    def row(self):
        return self.parent_widget.row()

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
            self.horizontalLayout.replaceWidget(self.txtEditName, self.lblName)
            self.lblName.sigMouseDoubleClick.connect(self.lblName_sigMouseDoubleClick)
            self.txtEditName.deleteLater()
            self.txtEditName = None
            self.sig_layout_changed.emit()

    def load_gear_icon(self):
        if self.gear.item_id is not None:
            item_id = self.gear.item_id
            pad_item_id = GEAR_ID_FMT.format(item_id)
            try:
                name, grade,url,itype = gears[item_id]
            except KeyError:
                return
            icon_path = os.path.join(IMG_TMP, pad_item_id + '.png')

            imgs.sig_image_load.connect(self.image_loaded)
            self.url = url
            imgs.get_icon(url, icon_path)

    def image_loaded(self, url, icon_path):
        if url == self.url:
            self.set_icon(QIcon(icon_path))
            imgs.sig_image_load.disconnect(self.image_loaded)

    def set_icon(self, icon: QIcon, enhance_overlay=None):
        self.icon = icon
        self.set_pixmap(icon.pixmap(QSize(32, 32)), enhance_overlay=enhance_overlay)

    def set_pixmap(self, pixmap:QPixmap, enhance_overlay=None):
        if enhance_overlay is None:
            enhance_overlay = self.enhance_overlay
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
            pixmap = pix_overlay_enhance(pixmap, self.gear)
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

    def dlg_chose_gear_sig_gear_chosen(self, name, item_class, item_grade, item_id):
        self.gear.set_item_id(item_id)
        if self.gear.name is None or self.gear.name == '':
            self.gear.name = name
        if item_grade == 'Yellow':
            item_grade = 'Boss'
        if item_grade == 'Orange':
            if name.lower().find('fallen god') > -1:
                item_grade = 'Fallen God'
            else:
                item_grade = 'Blackstar'
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
        self.parent_widget = TableWidgetGW('')
        table_widget.setItem(row, col, self.parent_widget)
        if self.icon is not None:
            table_widget.setRowHeight(row, 45)
        self.table_widget = table_widget
        self.col = col

    def create_gt_cmb(self, tw, model_edit_func=None):
        if model_edit_func is None:
            model_edit_func = self.model.swap_gear
        gear = self.gear
        cmb_gt = GearTypeCmb(tw, default=gear.gear_type.name)
        self.cmbType = cmb_gt

        def cmb_gt_currentTextChanged(str_picked):
            new_gt = gear_types[str_picked]
            cmb_enh = self.cmbLevel
            if cmb_enh is not None:
                current_enhance_string = cmb_enh.currentText()
                with QBlockSig(cmb_enh):
                    #cmb_enh.clear()
                    Qt_common.set_sort_cmb_box(list(new_gt.lvl_map.keys()), new_gt.enumerate_gt_lvl, current_enhance_string, cmb_enh)
                this_lvl = cmb_enh.currentText()
            else:
                this_lvl = gear.enhance_lvl
                if this_lvl not in new_gt.lvl_map:
                    this_lvl = new_gt.idx_lvl_map[0]

            this_gear = self.gear
            if str_picked.lower().find('accessor') > -1 or str_picked.lower().find('life') > -1 or str_picked.lower().find('fallen god') > -1:
                if not isinstance(this_gear, Smashable):
                    old_g = this_gear
                    this_gear = generate_gear_obj(self.model.settings, base_item_cost=this_gear.base_item_cost, enhance_lvl=this_lvl,
                                                        gear_type=gear_types[str_picked], name=this_gear.name,
                                                        sale_balance=this_gear.sale_balance, id=this_gear.item_id)
                    model_edit_func(old_g, this_gear)
                else:
                    this_gear.set_gear_params(gear_types[str_picked], this_lvl)
            else:
                if not isinstance(this_gear, Classic_Gear):
                    old_g = this_gear
                    this_gear = generate_gear_obj(self.model.settings, base_item_cost=this_gear.base_item_cost, enhance_lvl=this_lvl,
                                                        gear_type=gear_types[str_picked], name=this_gear.name, id=this_gear.item_id)
                    model_edit_func(old_g, this_gear)
                else:
                    this_gear.set_gear_params(gear_types[str_picked], this_lvl)
            self.set_gear(this_gear)
            self.sig_gear_changed.emit(self)
            # Sets the hidden value of the table widget so that colors are sorted in the right order

        cmb_gt.currentTextChanged.connect(cmb_gt_currentTextChanged)

    def create_lvl_cmb(self, tw):
        gear = self.gear
        gtype_s = gear.gear_type.name
        cmb_enh = NoScrollCombo(tw)

        self.cmbLevel = cmb_enh
        Qt_common.set_sort_cmb_box(list(gear_types[gtype_s].lvl_map.keys()), gear.gear_type.enumerate_gt_lvl,
                                   gear.enhance_lvl, cmb_enh)

        def cmb_enh_currentTextChanged(str_picked):
            this_gear = self.gear
            try:
                this_gear.set_enhance_lvl(str_picked)

                self.load_gear_icon()
            except KeyError:
                self.sig_error.emit(lbl_color_MainWindow.CRITICAL,'Enhance level does not appear to be valid.')
            self.sig_gear_changed.emit(self)

        cmb_enh.currentTextChanged.connect(cmb_enh_currentTextChanged)

    def create_Cmbs(self, tw, model_edit_func=None):
        self.create_lvl_cmb(tw)
        self.create_gt_cmb(tw, model_edit_func=model_edit_func)

    def add_to_tree(self, tree, item, col=0):
        tree.setItemWidget(item, col, self)
        self.table_widget = tree
        self.parent_widget = item
        self.col = col


def set_cell_lvl_compare(twi_lvl, lvl_str, gear_type:Gear_Type):
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
    twi = comma_seperated_twi(str(int(round(i_f_val))))
    return twi