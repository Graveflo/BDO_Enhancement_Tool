# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '..\QtCommon\forms\dlg_Track_Selection.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog_TrackSelection(object):
    def setupUi(self, Dialog_TrackSelection):
        Dialog_TrackSelection.setObjectName("Dialog_TrackSelection")
        Dialog_TrackSelection.resize(274, 65)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog_TrackSelection.sizePolicy().hasHeightForWidth())
        Dialog_TrackSelection.setSizePolicy(sizePolicy)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog_TrackSelection)
        self.verticalLayout.setObjectName("verticalLayout")
        self.table_main = QtWidgets.QTableWidget(Dialog_TrackSelection)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.table_main.sizePolicy().hasHeightForWidth())
        self.table_main.setSizePolicy(sizePolicy)
        self.table_main.setMinimumSize(QtCore.QSize(0, 25))
        self.table_main.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.table_main.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.table_main.setAlternatingRowColors(True)
        self.table_main.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table_main.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table_main.setColumnCount(0)
        self.table_main.setObjectName("table_main")
        self.table_main.setRowCount(0)
        self.table_main.horizontalHeader().setMinimumSectionSize(30)
        self.verticalLayout.addWidget(self.table_main)
        self.widget = QtWidgets.QWidget(Dialog_TrackSelection)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.widget.setObjectName("widget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.widget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.chkSelectEdit = QtWidgets.QCheckBox(self.widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.chkSelectEdit.sizePolicy().hasHeightForWidth())
        self.chkSelectEdit.setSizePolicy(sizePolicy)
        self.chkSelectEdit.setMinimumSize(QtCore.QSize(0, 16))
        font = QtGui.QFont()
        font.setFamily("Lucida Fax")
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.chkSelectEdit.setFont(font)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("../Resources/lock.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.chkSelectEdit.setIcon(icon)
        self.chkSelectEdit.setIconSize(QtCore.QSize(16, 16))
        self.chkSelectEdit.setChecked(True)
        self.chkSelectEdit.setObjectName("chkSelectEdit")
        self.horizontalLayout.addWidget(self.chkSelectEdit)
        self.verticalLayout.addWidget(self.widget)

        self.retranslateUi(Dialog_TrackSelection)
        QtCore.QMetaObject.connectSlotsByName(Dialog_TrackSelection)

    def retranslateUi(self, Dialog_TrackSelection):
        _translate = QtCore.QCoreApplication.translate
        Dialog_TrackSelection.setWindowTitle(_translate("Dialog_TrackSelection", "Select Data Track"))
        self.table_main.setSortingEnabled(True)
        self.chkSelectEdit.setText(_translate("Dialog_TrackSelection", "(Select) / Edit"))

