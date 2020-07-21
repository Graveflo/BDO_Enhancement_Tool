# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\rammc\Documents\Pycharm3\BDO_Enhancement_Tool\Forms\dlg_Manage_Alts.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_dlg_Manage_Alts(object):
    def setupUi(self, dlg_Manage_Alts):
        dlg_Manage_Alts.setObjectName("dlg_Manage_Alts")
        dlg_Manage_Alts.resize(723, 501)
        self.verticalLayout = QtWidgets.QVBoxLayout(dlg_Manage_Alts)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tableWidget = QtWidgets.QTableWidget(dlg_Manage_Alts)
        self.tableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tableWidget.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(2, item)
        self.verticalLayout.addWidget(self.tableWidget)
        self.widget = QtWidgets.QWidget(dlg_Manage_Alts)
        self.widget.setObjectName("widget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.widget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.cmdAdd = QtWidgets.QPushButton(self.widget)
        self.cmdAdd.setObjectName("cmdAdd")
        self.horizontalLayout.addWidget(self.cmdAdd)
        self.cmdImport = QtWidgets.QPushButton(self.widget)
        self.cmdImport.setObjectName("cmdImport")
        self.horizontalLayout.addWidget(self.cmdImport)
        self.cmdRemove = QtWidgets.QPushButton(self.widget)
        self.cmdRemove.setObjectName("cmdRemove")
        self.horizontalLayout.addWidget(self.cmdRemove)
        spacerItem = QtWidgets.QSpacerItem(314, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.cmdOk = QtWidgets.QPushButton(self.widget)
        self.cmdOk.setObjectName("cmdOk")
        self.horizontalLayout.addWidget(self.cmdOk)
        self.verticalLayout.addWidget(self.widget)

        self.retranslateUi(dlg_Manage_Alts)
        QtCore.QMetaObject.connectSlotsByName(dlg_Manage_Alts)

    def retranslateUi(self, dlg_Manage_Alts):
        _translate = QtCore.QCoreApplication.translate
        dlg_Manage_Alts.setWindowTitle(_translate("dlg_Manage_Alts", "Manage Alts"))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("dlg_Manage_Alts", "Picture"))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("dlg_Manage_Alts", "Name"))
        item = self.tableWidget.horizontalHeaderItem(2)
        item.setText(_translate("dlg_Manage_Alts", "Fail Stack"))
        self.cmdAdd.setText(_translate("dlg_Manage_Alts", "Add Alt"))
        self.cmdImport.setText(_translate("dlg_Manage_Alts", "Import From Game Files"))
        self.cmdRemove.setText(_translate("dlg_Manage_Alts", "Remove Alt"))
        self.cmdOk.setText(_translate("dlg_Manage_Alts", "OK"))

