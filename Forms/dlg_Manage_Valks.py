# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\rammc\Documents\Pycharm3\BDO_Enhancement_Tool\Forms\dlg_Manage_Valks.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_dlg_Manage_Valks(object):
    def setupUi(self, dlg_Manage_Valks):
        dlg_Manage_Valks.setObjectName("dlg_Manage_Valks")
        dlg_Manage_Valks.resize(573, 472)
        self.verticalLayout = QtWidgets.QVBoxLayout(dlg_Manage_Valks)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tableWidget = QtWidgets.QTableWidget(dlg_Manage_Valks)
        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, item)
        self.tableWidget.verticalHeader().setVisible(False)
        self.verticalLayout.addWidget(self.tableWidget)
        self.widget = QtWidgets.QWidget(dlg_Manage_Valks)
        self.widget.setObjectName("widget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.widget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.cmdAdd = QtWidgets.QPushButton(self.widget)
        self.cmdAdd.setObjectName("cmdAdd")
        self.horizontalLayout.addWidget(self.cmdAdd)
        self.cmdRemove = QtWidgets.QPushButton(self.widget)
        self.cmdRemove.setObjectName("cmdRemove")
        self.horizontalLayout.addWidget(self.cmdRemove)
        spacerItem = QtWidgets.QSpacerItem(291, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.cmdOk = QtWidgets.QPushButton(self.widget)
        self.cmdOk.setObjectName("cmdOk")
        self.horizontalLayout.addWidget(self.cmdOk)
        self.verticalLayout.addWidget(self.widget)

        self.retranslateUi(dlg_Manage_Valks)
        QtCore.QMetaObject.connectSlotsByName(dlg_Manage_Valks)

    def retranslateUi(self, dlg_Manage_Valks):
        _translate = QtCore.QCoreApplication.translate
        dlg_Manage_Valks.setWindowTitle(_translate("dlg_Manage_Valks", "Manage Valks Failstacks"))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("dlg_Manage_Valks", "Item"))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("dlg_Manage_Valks", "Value"))
        self.cmdAdd.setText(_translate("dlg_Manage_Valks", "Add Valks"))
        self.cmdRemove.setText(_translate("dlg_Manage_Valks", "Remove Valks"))
        self.cmdOk.setText(_translate("dlg_Manage_Valks", "ok"))

