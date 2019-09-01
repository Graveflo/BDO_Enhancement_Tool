#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
from PyQt5 import QtCore, QtGui, QtWidgets
pyqtSignal = QtCore.pyqtSignal


class modWidget(QtWidgets.QWidget):
    def __init__(self, frmObj, *args, **kwargs):
        super(modWidget, self).__init__(*args, **kwargs)
        frmObj.setupUi(self)
        self.frmObj = frmObj


class WidgetTether(modWidget):
    sigShow = pyqtSignal(name='sigShow')

    DEFAULT_SNAP_POSITION_LEFT = 0
    DEFAULT_SNAP_POSITION_RIGHT = 1
    DEFAULT_SNAP_POSITION_UP = 2
    DEFAULT_SNAP_POSITION_DOWN = 3

    #TODO: Consider making the settings variables static so that all instances of the GUI have consistent values

    def __init__(self, anchor_widget, frmObj, *args, **kwargs):
        if 'flags' not in kwargs or kwargs['kwargs'] == None:
            WindowFlags = QtCore.Qt.Sheet
            mask = ~ QtCore.Qt.WindowStaysOnTopHint
            WindowFlags |= QtCore.Qt.CustomizeWindowHint
            WindowFlags &= mask
            WindowFlags |= QtCore.Qt.FramelessWindowHint
            kwargs['flags'] = WindowFlags

        super(WidgetTether, self).__init__(frmObj, *args, **kwargs)
        self.setWindowModality(QtCore.Qt.NonModal)

        self.anchor_widget = anchor_widget
        self.anchored_side = None

    def show(self, side=DEFAULT_SNAP_POSITION_LEFT):
        if self.anchored_side is None:
            self.snap_to_side(side=side)
        super(WidgetTether, self).show()
        self.sigShow.emit()

    def snap_to_side(self, side=None):
        # TODO: This is where the element calculates the position of itself in regards to the anchor object. The object is snapped
        if side == None:
            side = self.anchored_side
        else:
            self.anchored_side = side
        anchor_widget = self.anchor_widget
        this_anchor_geo = anchor_widget.geometry()
        button_position = anchor_widget.parent().mapToGlobal(this_anchor_geo.topLeft())
        anchor_width = this_anchor_geo.width()
        anchor_height = this_anchor_geo.height()
        #this_window_geo = self.geometry()
        selection_widget_height = self.sizeHint().height()
        selection_widget_width = self.sizeHint().width()
        #this_window_geo.setTopLeft(button_position)
        newx = 0
        newy = 0
        if side == WidgetTether.DEFAULT_SNAP_POSITION_RIGHT:
            newx = button_position.x() + anchor_width
        elif side == WidgetTether.DEFAULT_SNAP_POSITION_LEFT:
            # The size hint is not going to be the best way of calculating this. Since it is a tooltip it may not be on 
            # a layout making the sizehint accurate. It would be better to find a way to get the chosen size.
            newx = button_position.x() - self.sizeHint().width()
        else:
            mid_button = int(round((anchor_width / 2.0)))
            half_width = int(round(self.sizeHint().width() / 2.0))
            newx = mid_button + button_position.x() - half_width
        # --- --- ---
        if side == WidgetTether.DEFAULT_SNAP_POSITION_DOWN:
            newy = button_position.y() + anchor_height
        elif side == WidgetTether.DEFAULT_SNAP_POSITION_UP:

            newy = button_position.y() - selection_widget_height
        else:
            mid_button = int(round((anchor_height / 2.0)))
            selection_widget_height = int(round(self.sizeHint().height() / 2.0))
            newy = mid_button + button_position.y() - selection_widget_height
        self.setGeometry(newx, newy, selection_widget_width, selection_widget_height)

