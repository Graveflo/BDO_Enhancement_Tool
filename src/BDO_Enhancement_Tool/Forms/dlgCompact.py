# Form implementation generated from reading ui file 'c:\users\rammc\documents\pycharm3\bdo_enhancement_tool\src\BDO_Enhancement_Tool\Forms\dlgCompact.ui'
#
# Created by: PyQt6 UI code generator 6.3.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_dlgCompact(object):
    def setupUi(self, dlgCompact):
        dlgCompact.setObjectName("dlgCompact")
        dlgCompact.resize(816, 268)
        self.ParentLayout = QtWidgets.QHBoxLayout(dlgCompact)
        self.ParentLayout.setObjectName("ParentLayout")
        self.widget = QtWidgets.QWidget(dlgCompact)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.widget.setObjectName("widget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.widget_2 = QtWidgets.QWidget(self.widget)
        self.widget_2.setObjectName("widget_2")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.widget_2)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label = QtWidgets.QLabel(self.widget_2)
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.horizontalLayout_4.addWidget(self.label)
        self.spinFS = NoScrollSpin(self.widget_2)
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(False)
        font.setWeight(50)
        self.spinFS.setFont(font)
        self.spinFS.setMaximum(999)
        self.spinFS.setObjectName("spinFS")
        self.horizontalLayout_4.addWidget(self.spinFS)
        self.verticalLayout.addWidget(self.widget_2)
        self.cmbalts = QtWidgets.QComboBox(self.widget)
        self.cmbalts.setObjectName("cmbalts")
        self.verticalLayout.addWidget(self.cmbalts)
        self.chkStayOnAlt = QtWidgets.QCheckBox(self.widget)
        self.chkStayOnAlt.setObjectName("chkStayOnAlt")
        self.verticalLayout.addWidget(self.chkStayOnAlt)
        self.chkFollowTrack = QtWidgets.QCheckBox(self.widget)
        self.chkFollowTrack.setObjectName("chkFollowTrack")
        self.verticalLayout.addWidget(self.chkFollowTrack)
        self.cmdOnTop = QtWidgets.QCheckBox(self.widget)
        self.cmdOnTop.setEnabled(True)
        self.cmdOnTop.setCheckable(True)
        self.cmdOnTop.setChecked(False)
        self.cmdOnTop.setObjectName("cmdOnTop")
        self.verticalLayout.addWidget(self.cmdOnTop)
        self.ParentLayout.addWidget(self.widget)
        self.widget_5 = QtWidgets.QWidget(dlgCompact)
        self.widget_5.setObjectName("widget_5")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.widget_5)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setSpacing(2)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.ParentLayout.addWidget(self.widget_5)
        self.widget_6 = QtWidgets.QWidget(dlgCompact)
        self.widget_6.setMinimumSize(QtCore.QSize(250, 250))
        self.widget_6.setObjectName("widget_6")
        self.ParentLayout.addWidget(self.widget_6)
        self.widget_3 = QtWidgets.QWidget(dlgCompact)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_3.sizePolicy().hasHeightForWidth())
        self.widget_3.setSizePolicy(sizePolicy)
        self.widget_3.setObjectName("widget_3")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.widget_3)
        self.verticalLayout_3.setContentsMargins(5, 5, 5, 5)
        self.verticalLayout_3.setSpacing(5)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.treeWidget = QtWidgets.QTreeWidget(self.widget_3)
        self.treeWidget.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.treeWidget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.treeWidget.setObjectName("treeWidget")
        self.verticalLayout_3.addWidget(self.treeWidget)
        self.lblInfo = QtWidgets.QLabel(self.widget_3)
        self.lblInfo.setText("")
        self.lblInfo.setWordWrap(True)
        self.lblInfo.setObjectName("lblInfo")
        self.verticalLayout_3.addWidget(self.lblInfo)
        self.widButtonBox = QtWidgets.QWidget(self.widget_3)
        self.widButtonBox.setObjectName("widButtonBox")
        self.ButtonBoxLayout = QtWidgets.QHBoxLayout(self.widButtonBox)
        self.ButtonBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.ButtonBoxLayout.setObjectName("ButtonBoxLayout")
        self.verticalLayout_3.addWidget(self.widButtonBox)
        self.ParentLayout.addWidget(self.widget_3)

        self.retranslateUi(dlgCompact)
        QtCore.QMetaObject.connectSlotsByName(dlgCompact)

    def retranslateUi(self, dlgCompact):
        _translate = QtCore.QCoreApplication.translate
        dlgCompact.setWindowTitle(_translate("dlgCompact", "Graveflo Enhance Calc"))
        self.label.setText(_translate("dlgCompact", "FS:"))
        self.spinFS.setToolTip(_translate("dlgCompact", "Current Failstack Value"))
        self.chkStayOnAlt.setText(_translate("dlgCompact", "Stay on Alt"))
        self.chkFollowTrack.setText(_translate("dlgCompact", "Follow Track"))
        self.cmdOnTop.setText(_translate("dlgCompact", "Stay On Top"))
        self.treeWidget.headerItem().setText(0, _translate("dlgCompact", ":)"))
        self.treeWidget.headerItem().setText(1, _translate("dlgCompact", "Instruction"))
        self.treeWidget.headerItem().setText(2, _translate("dlgCompact", "Attempt Cost"))
from BDO_Enhancement_Tool.Qt_common import NoScrollSpin
