# Form implementation generated from reading ui file 'c:\users\rammc\documents\pycharm3\bdo_enhancement_tool\src\BDO_Enhancement_Tool\Forms\EnhGearWindow.ui'
#
# Created by: PyQt6 UI code generator 6.3.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_dlgGearWindow(object):
    def setupUi(self, dlgGearWindow):
        dlgGearWindow.setObjectName("dlgGearWindow")
        dlgGearWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(dlgGearWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.tableEnhanceCosts = QtWidgets.QTableWidget(self.centralwidget)
        self.tableEnhanceCosts.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.tableEnhanceCosts.setObjectName("tableEnhanceCosts")
        self.tableEnhanceCosts.setColumnCount(3)
        self.tableEnhanceCosts.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tableEnhanceCosts.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableEnhanceCosts.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableEnhanceCosts.setHorizontalHeaderItem(2, item)
        self.verticalLayout_2.addWidget(self.tableEnhanceCosts)
        dlgGearWindow.setCentralWidget(self.centralwidget)
        self.dockWidget = QtWidgets.QDockWidget(dlgGearWindow)
        self.dockWidget.setObjectName("dockWidget")
        self.dockWidgetContents = QtWidgets.QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout.setObjectName("verticalLayout")
        self.widget = QtWidgets.QWidget(self.dockWidgetContents)
        self.widget.setObjectName("widget")
        self.gridLayout = QtWidgets.QGridLayout(self.widget)
        self.gridLayout.setObjectName("gridLayout")
        self.lblGearType = QtWidgets.QLabel(self.widget)
        self.lblGearType.setObjectName("lblGearType")
        self.gridLayout.addWidget(self.lblGearType, 0, 1, 1, 1)
        self.lblItemID = QtWidgets.QLabel(self.widget)
        self.lblItemID.setObjectName("lblItemID")
        self.gridLayout.addWidget(self.lblItemID, 1, 1, 1, 1)
        self.label = QtWidgets.QLabel(self.widget)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.widget)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.label_3 = QtWidgets.QLabel(self.widget)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)
        self.lblDestroysOnFail = QtWidgets.QLabel(self.widget)
        self.lblDestroysOnFail.setObjectName("lblDestroysOnFail")
        self.gridLayout.addWidget(self.lblDestroysOnFail, 2, 1, 1, 1)
        self.label_6 = QtWidgets.QLabel(self.widget)
        self.label_6.setObjectName("label_6")
        self.gridLayout.addWidget(self.label_6, 3, 0, 1, 1)
        self.lblCronDG = QtWidgets.QLabel(self.widget)
        self.lblCronDG.setObjectName("lblCronDG")
        self.gridLayout.addWidget(self.lblCronDG, 3, 1, 1, 1)
        self.verticalLayout.addWidget(self.widget)
        self.tableLvlInfo = QtWidgets.QTableWidget(self.dockWidgetContents)
        self.tableLvlInfo.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.tableLvlInfo.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableLvlInfo.setObjectName("tableLvlInfo")
        self.tableLvlInfo.setColumnCount(7)
        self.tableLvlInfo.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tableLvlInfo.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableLvlInfo.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableLvlInfo.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableLvlInfo.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableLvlInfo.setHorizontalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableLvlInfo.setHorizontalHeaderItem(5, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableLvlInfo.setHorizontalHeaderItem(6, item)
        self.tableLvlInfo.verticalHeader().setVisible(False)
        self.verticalLayout.addWidget(self.tableLvlInfo)
        self.dockWidget.setWidget(self.dockWidgetContents)
        dlgGearWindow.addDockWidget(QtCore.Qt.DockWidgetArea(1), self.dockWidget)

        self.retranslateUi(dlgGearWindow)
        QtCore.QMetaObject.connectSlotsByName(dlgGearWindow)

    def retranslateUi(self, dlgGearWindow):
        _translate = QtCore.QCoreApplication.translate
        dlgGearWindow.setWindowTitle(_translate("dlgGearWindow", "Gear Window"))
        item = self.tableEnhanceCosts.horizontalHeaderItem(0)
        item.setText(_translate("dlgGearWindow", "FS"))
        item = self.tableEnhanceCosts.horizontalHeaderItem(1)
        item.setText(_translate("dlgGearWindow", "Cost"))
        item = self.tableEnhanceCosts.horizontalHeaderItem(2)
        item.setText(_translate("dlgGearWindow", "Restore Cost"))
        self.lblGearType.setText(_translate("dlgGearWindow", "<a>TextLabel</a>"))
        self.lblItemID.setText(_translate("dlgGearWindow", "TextLabel"))
        self.label.setText(_translate("dlgGearWindow", "Gear Type: "))
        self.label_2.setText(_translate("dlgGearWindow", "Item ID: "))
        self.label_3.setText(_translate("dlgGearWindow", "Destroys on Fail: "))
        self.lblDestroysOnFail.setText(_translate("dlgGearWindow", "TextLabel"))
        self.label_6.setText(_translate("dlgGearWindow", "Cron Downgrade: "))
        self.lblCronDG.setText(_translate("dlgGearWindow", "TextLabel"))
        item = self.tableLvlInfo.horizontalHeaderItem(0)
        item.setText(_translate("dlgGearWindow", "Level"))
        item = self.tableLvlInfo.horizontalHeaderItem(1)
        item.setText(_translate("dlgGearWindow", "MP: Cost"))
        item = self.tableLvlInfo.horizontalHeaderItem(2)
        item.setText(_translate("dlgGearWindow", "Cron Stones"))
        item = self.tableLvlInfo.horizontalHeaderItem(3)
        item.setText(_translate("dlgGearWindow", "Cumulative Cost"))
        item = self.tableLvlInfo.horizontalHeaderItem(4)
        item.setText(_translate("dlgGearWindow", "Cumulative Material Cost"))
        item = self.tableLvlInfo.horizontalHeaderItem(5)
        item.setText(_translate("dlgGearWindow", "Fail Durability"))
        item = self.tableLvlInfo.horizontalHeaderItem(6)
        item.setText(_translate("dlgGearWindow", "Materials"))
