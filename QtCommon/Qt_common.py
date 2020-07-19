#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
relative_path_add = lambda str_path: sys.path.append(
    os.path.abspath(os.path.join(os.path.split(__file__)[0], str_path)))
import sys, os, types

from PyQt5 import QtGui, QtCore, QtWidgets
Qt = QtCore.Qt
ItemIsEditable = Qt.ItemIsEditable

QTableWidgetItem_NoEdit = lambda x: x.setFlags(x.flags() & ~ItemIsEditable)

class CLabel(QtWidgets.QLabel):
    sigMouseDoubleClick = QtCore.pyqtSignal(object, name="sigMouseDoubleClick")
    sigMouseClick = QtCore.pyqtSignal(object, name="sigMouseClick")

    def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
        super(CLabel, self).mouseReleaseEvent(ev)
        self.sigMouseClick.emit(ev)

    def mouseDoubleClickEvent(self, QMouseEvent):
        super(CLabel, self).mouseDoubleClickEvent(QMouseEvent)
        self.sigMouseDoubleClick.emit(QMouseEvent)


class FocusLineEdit(QtWidgets.QLineEdit):
    sig_lost_focus = QtCore.pyqtSignal(object, name='sig_lost_focus')

    def focusOutEvent(self, a0: QtGui.QFocusEvent) -> None:
        super(FocusLineEdit, self).focusOutEvent(a0)
        self.sig_lost_focus.emit(a0)


class EventDock(QtWidgets.QDockWidget):
    sigCloseEvent = QtCore.pyqtSignal(object, name="sigCloseEvent")
    sigShow = QtCore.pyqtSignal(name='sigShow')
    def closeEvent(self, event):
        self.sigCloseEvent.emit(event)
        super(EventDock, self).closeEvent(event)
    def show(self):
        self.sigShow.emit()
        super(EventDock, self).show()


class NoScrollCombo(QtWidgets.QComboBox):
    def __init__(self, scroll_passthru, *args, **kargs):
        super(NoScrollCombo, self).__init__(*args, **kargs)
        self.scroll_pass_thru = scroll_passthru

    def wheelEvent(self, *args, **kargs):
        self.scroll_pass_thru.wheelEvent(*args, **kargs)

def check_win_icon(class_string, app, main_win, path):
    icon2 = QtGui.QIcon()
    icon2.addPixmap(QtGui.QPixmap(path), QtGui.QIcon.Normal,
                    QtGui.QIcon.Off)
    icon2.addFile(path, QtCore.QSize(16, 16))
    icon2.addFile(path, QtCore.QSize(24, 24))
    icon2.addFile(path, QtCore.QSize(32, 32))
    icon2.addFile(path, QtCore.QSize(48, 48))
    icon2.addFile(path, QtCore.QSize(256, 256))
    if sys.platform == 'win32':
        import ctypes

        myappid = class_string  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    app.setWindowIcon(icon2)
    main_win.setWindowIcon(icon2)

def get_dark_palette():
    """
    Creates a basic 'dark themed' pallete for Qt Widgets.
    :return: QPalette
    """
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor(53, 53, 53))
    palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
    palette.setColor(QtGui.QPalette.Base, QtGui.QColor(15, 15, 15))
    palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(53, 53, 53))
    palette.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.white)
    palette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
    palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
    palette.setColor(QtGui.QPalette.Button, QtGui.QColor(53, 53, 53))
    palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
    palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
    palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(142, 45, 197).lighter())
    palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.black)

    disabled_text = QtGui.QColor(140, 11, 11)
    disabled_bg =  QtGui.QColor(105,105,105)

    palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Text, disabled_text)
    palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Button, disabled_bg)
    palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, disabled_text)
    palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Window, disabled_bg)
    palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.WindowText, disabled_text)
    palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Base, disabled_bg)
    palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.AlternateBase, QtGui.QColor(47, 79, 79))
    return palette

def set_button_color(QTObject, color):
    """
    Setts the background color of a button while preserving it's other pallette settings.
    :param QTObject: QPushButton: The QPushButton object or any QWidget with QtGui.QPalette.Button setting in it's pallette
    :param color: QColor: The color to set
    :return: QPushButton: The button is altered and NOT copied. Do not need to use the return.
    """
    palette_new = QTObject.palette()
    palette_new.setColor(QtGui.QPalette.Button, color)
    QTObject.setPalette(palette_new)
    return QTObject

def setIcon(control, iconpath):
    """
    Simply sets the icon property of a QWidget based on path
    :param control: Control with setIcon method
    :param iconpath: str: path of icon
    :return: QPixmap: the icon
    """
    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(iconpath), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    control.setIcon(icon)
    return icon


class StringBuilder(object):
    """
    An object that attempts to simplify the join() string concatenation method
    """
    def __init__(self, joiner='', *args):
        self.array_ = []
        self.joiner = joiner
        self.add(*args)
        self.altered = True  # must create local variable to initialize (in __str__)

    def add(self, *args):
        for arg in args:
            self.array_.append(arg)
        self.altered = True

    def pop(self):
        return self.array_.pop()

    def addC(self, *args):
        self.array_.append(''.join(args))
        self.altered = True

    def join(self, str_):
        self.altered = True
        return str_.join(self.array_)

    def __str__(self):
        """
        Don't punish repeated calls to __str__ without alterations to the final product.
        :return:
        """
        altered = self.altered
        if altered:
            tmp_str = self.joiner.join(self.array_)
            self.tmp_str = tmp_str
            self.altered = False
            return tmp_str
        else:
            return self.tmp_str

    def __len__(self):
        return len(self.__str__())


def clear_table(tw):
    for i in range(0, tw.rowCount()):
        tw.removeRow(0)

def dlg_format_list(strct_, include_all=False):
    """
    This method formats a list of file types and descritpions for use in a file dialog. The file types are parsed by ;;
    and the extentions are parsed by being surrounded by () and a *. prefix if applicable.
    :param strct_: array(tuple(str, str)): each element has a description and an extention
    :param include_all: bool: If this option is True then an All Files () option is added with ONLY the other listed formats in one place
    :return: str: formatted for a file dialog
    """
    this_return = StringBuilder(joiner=';;')
    if include_all:
        comb = StringBuilder(joiner=' ')
        for type_in in strct_:
            comb.addC('*.', type_in[1])
        this_return.addC('Any Acceptable', ' (', str(comb), ')')
    for type_in in strct_:
        this_return.addC(type_in[0], ' (*.', type_in[1], ')')
    return str(this_return)


class lbl_color_MainWindow(QtWidgets.QMainWindow):
    def change_statusbar_proto(self, statusbar, WindowText, Background, message, print_msg=False):
        try:
            orig = statusbar.__dict__['orig_showMessage']
        except KeyError:
            orig = None
        if orig is None:
            orig = statusbar.showMessage
            this_pal = statusbar.palette()
            statusbar.__dict__['orig_WindowText'] = this_pal.color(QtGui.QPalette.WindowText)
            statusbar.__dict__['orig_background'] = this_pal.color(QtGui.QPalette.Background)
            statusbar.__dict__['orig_showMessage'] = orig

            def stat_msg(self, msg):
                this_pal = self.palette()
                this_pal.setColor(QtGui.QPalette.WindowText, self.orig_WindowText)
                this_pal.setColor(QtGui.QPalette.Background, self.orig_background)
                self.setPalette(this_pal)
                self.showMessage = orig
                self.setAutoFillBackground(False)
                orig(msg)
                self.__dict__['orig_showMessage'] = None

            statusbar.showMessage = types.MethodType(stat_msg, statusbar)
        this_pal = statusbar.palette()
        this_pal.setColor(QtGui.QPalette.WindowText, WindowText)
        this_pal.setColor(QtGui.QPalette.Background, Background)
        statusbar.setPalette(this_pal)
        statusbar.setAutoFillBackground(True)
        if print_msg is not False:
            print(print_msg)
        orig(message)

    def show_critical_error(self, str_msg, silent=False):
        if silent is False:
            print_msg = print_msg='Critical Message: ' + str_msg
        else:
            print_msg = False
        self.change_statusbar_proto(self.ui.statusbar, Qt.black, Qt.red, str_msg,
                                    print_msg=print_msg)

    def show_warning_msg(self, str_msg, silent=False):
        if silent is False:
            print_msg = 'Warning Message: ' + str_msg
        else:
            print_msg = False
        self.change_statusbar_proto(self.ui.statusbar, Qt.black, Qt.yellow, str_msg,
                                    print_msg=print_msg)

    def show_green_msg(self, str_msg):
        self.change_statusbar_proto(self.ui.statusbar, Qt.black, Qt.green, str_msg)

def set_qwidget_color(widg, color):
    widg.setAutoFillBackground(True)
    pal = get_dark_palette()
    pal.setColor(QtGui.QPalette.Background, color)
    pal.setColor(QtGui.QPalette.Button, color)
    widg.setPalette(pal)

def center_window(qwind, app):
    screen_geo = app.desktop().screenGeometry()
    screen_height = screen_geo.height()
    screen_width = screen_geo.width()
    try_width = qwind.width()
    try_height = qwind.height()
    HALF_SCREEN_WIDTH = int(round(screen_width / 2.0))
    HALF_SCREEN_HEIGHT = int(round(screen_height / 2.0))
    try_x = HALF_SCREEN_WIDTH - int(round(try_width / 2.0))
    try_y = HALF_SCREEN_HEIGHT - int(round(try_height / 2.0))
    qwind.setGeometry(try_x, try_y,
                     try_width, try_height)


class QBlockSig(object):
    """
    A simple wrapper for the BlockSignals method in QWidgets
    """
    def __init__(self, *qobj):
        self.obj = qobj
        blk = []
        for obj in qobj:
            blk.append(obj.signalsBlocked())
        self.blk = blk

    def __enter__(self):
        for _obj in self.obj:
            _obj.blockSignals(True)

    def __exit__(self, exc_type, exc_val, exc_tb):
        for _blk, _obj in zip(self.blk, self.obj):
            _obj.blockSignals(_blk)


class QBlockSort(object):
    def __init__(self, *qobj):
        self.obj = qobj
        blk = []
        for obj in qobj:
            blk.append(obj.isSortingEnabled())
        self.blk = blk

    def __enter__(self):
        for _obj in self.obj:
            _obj.setSortingEnabled(False)

    def __exit__(self, exc_type, exc_val, exc_tb):
        for _blk, _obj in zip(self.blk, self.obj):
            _obj.setSortingEnabled(_blk)


class SpeedUpTable(object):
    def __init__(self, tbl):
        self.tble = tbl
        self.prev_vis = True
        self.prev_updates = True
        self.prev_sort = False

    def __enter__(self):
        self.prev_vis = self.tble.isVisible()
        self.prev_updates = self.tble.updatesEnabled()
        self.prev_sort = self.tble.isSortingEnabled()

        self.tble.setVisible(False)
        self.tble.setSortingEnabled(False)
        self.tble.setUpdatesEnabled(False)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.tble.setVisible(self.prev_vis)
        self.tble.setSortingEnabled(self.prev_sort)
        self.tble.setUpdatesEnabled(self.prev_updates)

