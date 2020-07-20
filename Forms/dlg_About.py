# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\rammc\Documents\PyCharm3\BDO_Enhancement_Tool\Forms\dlg_About.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(882, 348)
        self.horizontalLayout = QtWidgets.QHBoxLayout(Dialog)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lblPicture = QtWidgets.QLabel(Dialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblPicture.sizePolicy().hasHeightForWidth())
        self.lblPicture.setSizePolicy(sizePolicy)
        self.lblPicture.setText("")
        self.lblPicture.setPixmap(QtGui.QPixmap("../Graveflo.png"))
        self.lblPicture.setObjectName("lblPicture")
        self.horizontalLayout.addWidget(self.lblPicture)
        self.widget = QtWidgets.QWidget(Dialog)
        self.widget.setObjectName("widget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.textEdit = QtWidgets.QTextEdit(self.widget)
        font = QtGui.QFont()
        font.setFamily("Consolas")
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.textEdit.setFont(font)
        self.textEdit.setReadOnly(True)
        self.textEdit.setObjectName("textEdit")
        self.verticalLayout.addWidget(self.textEdit)
        self.horizontalLayout.addWidget(self.widget)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "About"))
        self.textEdit.setHtml(_translate("Dialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Consolas\'; font-size:12pt; font-weight:600; font-style:normal;\">\n"
"<p align=\"center\" style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">BDO Enhancement Calculator</p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Courier New\';\">This is a simple tool to help optimize enhancing in Black Desert Online. I created this tool to attempt at getting a more objective strategy when enhacing multiple items. I decided to write my own code when the enahcement chances were released as there are plenty of other calculators.<br /><br /><br />@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧<br /><br />Thank you:<br />Inspiration: (</span><a href=\"https://docs.google.com/spreadsheets/d/1WzAeIFslcWhZ-TudUTrvt4S6ejGF8Uo5FwVqNivfHK0/edit#gid=0\"><span style=\" font-family:\'Courier New\'; text-decoration: underline; color:#0000ff;\">https://docs.google.com/spreadsheets/d/1WzAeIFslcWhZ-TudUTrvt4S6ejGF8Uo5FwVqNivfHK0/edit#gid=0</span></a><span style=\" font-family:\'Courier New\';\">)<br />Data tables: (</span><a href=\"https://docs.google.com/spreadsheets/d/1folCDSzYD8JQMT9tJHxJtmwy9CXVAO3SQegdESQKLk4\"><span style=\" font-family:\'Courier New\'; text-decoration: underline; color:#0000ff;\">https://docs.google.com/spreadsheets/d/1folCDSzYD8JQMT9tJHxJtmwy9CXVAO3SQegdESQKLk4)</span></a><br /><br /><span style=\" font-weight:400;\">Testers:<br />Isaacvithurston (reddit</span><span style=\" font-family:\'Courier New\'; font-weight:400;\">)</span></p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Courier New\'; font-weight:400;\">d3lak (GitHub)</span></p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Courier New\'; font-weight:400;\">hiLLo612 (BDO)</span></p></body></html>"))

