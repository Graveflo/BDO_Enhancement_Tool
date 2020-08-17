# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\rammc\Documents\PyCharm3\BDO_Enhancement_Tool\Forms\altWidget.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_alt_Widget(object):
    def setupUi(self, alt_Widget):
        alt_Widget.setObjectName("alt_Widget")
        alt_Widget.resize(320, 355)
        self.verticalLayout = QtWidgets.QVBoxLayout(alt_Widget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.lblPicture = QtWidgets.QLabel(alt_Widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblPicture.sizePolicy().hasHeightForWidth())
        self.lblPicture.setSizePolicy(sizePolicy)
        self.lblPicture.setMinimumSize(QtCore.QSize(0, 250))
        self.lblPicture.setObjectName("lblPicture")
        self.verticalLayout.addWidget(self.lblPicture)
        self.cmdRemove = QtWidgets.QPushButton(alt_Widget)
        self.cmdRemove.setFocusPolicy(QtCore.Qt.NoFocus)
        self.cmdRemove.setObjectName("cmdRemove")
        self.verticalLayout.addWidget(self.cmdRemove)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtWidgets.QLabel(alt_Widget)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_2 = QtWidgets.QLabel(alt_Widget)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.txtName = QtWidgets.QLineEdit(alt_Widget)
        self.txtName.setObjectName("txtName")
        self.gridLayout.addWidget(self.txtName, 0, 1, 1, 1)
        self.spinFS = NonScrollSpin(alt_Widget)
        self.spinFS.setObjectName("spinFS")
        self.gridLayout.addWidget(self.spinFS, 1, 1, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)

        self.retranslateUi(alt_Widget)
        QtCore.QMetaObject.connectSlotsByName(alt_Widget)

    def retranslateUi(self, alt_Widget):
        _translate = QtCore.QCoreApplication.translate
        alt_Widget.setWindowTitle(_translate("alt_Widget", "Form"))
        self.lblPicture.setText(_translate("alt_Widget", "TextLabel"))
        self.cmdRemove.setText(_translate("alt_Widget", "Remove Alt"))
        self.label.setText(_translate("alt_Widget", "Name:"))
        self.label_2.setText(_translate("alt_Widget", "Fail stack: "))

from BDO_Enhancement_Tool.QtCommon.Qt_common import NonScrollSpin
