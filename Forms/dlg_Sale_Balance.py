# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\rammc\Documents\Pycharm3\BDO_Enhancement_Tool\Forms\dlg_Sale_Balance.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_DlgSaleBalance(object):
    def setupUi(self, DlgSaleBalance):
        DlgSaleBalance.setObjectName("DlgSaleBalance")
        DlgSaleBalance.resize(470, 160)
        self.verticalLayout = QtWidgets.QVBoxLayout(DlgSaleBalance)
        self.verticalLayout.setObjectName("verticalLayout")
        self.widget = QtWidgets.QWidget(DlgSaleBalance)
        self.widget.setObjectName("widget")
        self.gridLayout = QtWidgets.QGridLayout(self.widget)
        self.gridLayout.setObjectName("gridLayout")
        self.lblPercent = QtWidgets.QLabel(self.widget)
        self.lblPercent.setObjectName("lblPercent")
        self.gridLayout.addWidget(self.lblPercent, 1, 0, 1, 1)
        self.spinPercent = QtWidgets.QDoubleSpinBox(self.widget)
        self.spinPercent.setPrefix("")
        self.spinPercent.setMaximum(100.0)
        self.spinPercent.setProperty("value", 65.0)
        self.spinPercent.setObjectName("spinPercent")
        self.gridLayout.addWidget(self.spinPercent, 1, 1, 1, 1)
        self.lblSaleVale = QtWidgets.QLabel(self.widget)
        self.lblSaleVale.setObjectName("lblSaleVale")
        self.gridLayout.addWidget(self.lblSaleVale, 0, 0, 1, 1)
        self.chkValuePack = QtWidgets.QCheckBox(self.widget)
        self.chkValuePack.setChecked(True)
        self.chkValuePack.setObjectName("chkValuePack")
        self.gridLayout.addWidget(self.chkValuePack, 2, 0, 1, 1)
        self.widget_2 = QtWidgets.QWidget(self.widget)
        self.widget_2.setObjectName("widget_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.widget_2)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lblSale = QtWidgets.QLabel(self.widget_2)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.lblSale.setFont(font)
        self.lblSale.setObjectName("lblSale")
        self.horizontalLayout.addWidget(self.lblSale)
        self.txtProfit = QtWidgets.QLineEdit(self.widget_2)
        self.txtProfit.setCursor(QtGui.QCursor(QtCore.Qt.IBeamCursor))
        self.txtProfit.setReadOnly(True)
        self.txtProfit.setObjectName("txtProfit")
        self.horizontalLayout.addWidget(self.txtProfit)
        self.gridLayout.addWidget(self.widget_2, 3, 1, 1, 1)
        self.spinValue = QtWidgets.QDoubleSpinBox(self.widget)
        self.spinValue.setProperty("showGroupSeparator", True)
        self.spinValue.setMaximum(1000000000000.0)
        self.spinValue.setObjectName("spinValue")
        self.gridLayout.addWidget(self.spinValue, 0, 1, 1, 1)
        self.verticalLayout.addWidget(self.widget)
        self.buttonBox = QtWidgets.QDialogButtonBox(DlgSaleBalance)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(DlgSaleBalance)
        self.buttonBox.accepted.connect(DlgSaleBalance.accept)
        self.buttonBox.rejected.connect(DlgSaleBalance.reject)
        QtCore.QMetaObject.connectSlotsByName(DlgSaleBalance)

    def retranslateUi(self, DlgSaleBalance):
        _translate = QtCore.QCoreApplication.translate
        DlgSaleBalance.setWindowTitle(_translate("DlgSaleBalance", "Sale Balance Calculator"))
        self.lblPercent.setText(_translate("DlgSaleBalance", "Base %:"))
        self.spinPercent.setSuffix(_translate("DlgSaleBalance", "%"))
        self.lblSaleVale.setText(_translate("DlgSaleBalance", "Sale Value:"))
        self.chkValuePack.setText(_translate("DlgSaleBalance", "Value Pack"))
        self.lblSale.setText(_translate("DlgSaleBalance", "Sale Balance:"))

