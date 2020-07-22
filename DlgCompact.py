#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
from PyQt5 import QtWidgets, Qt, QtCore, QtGui
from PyQt5.QtCore import Qt
from .common import Classic_Gear, Smashable, relative_path_convert

from .QtCommon.Qt_common import QBlockSort, QBlockSig
from .Forms.dlgCompact import Ui_dlgCompact
import typing
from .model import Enhance_model, Gear
import numpy

QWidget = QtWidgets.QWidget
MONNIES_FORMAT = "{:,}"
BS_CHEER = relative_path_convert('Images/B.S.Happy.png')
BS_AW_MAN = relative_path_convert('Images/B.S. Awh Man.png')
BS_FACE_PALM = relative_path_convert('Images/B.S. Face Palm.png')
BS_HMM = relative_path_convert('Images/B.S. Hmmmm.png')
BS = relative_path_convert('Images/B.S.png')


class BSWidget(QtWidgets.QWidget):
    def __init__(self, parent, pixmap=None):
        super(BSWidget, self).__init__(parent)
        self.pixmap:QtGui.QPixmap = pixmap
        if pixmap is not None:
            self.set_pixmap(pixmap)

    def set_pixmap(self, pixmap:QtGui.QPixmap):
        self.pixmap = pixmap
        self.setMinimumSize(self.pixmap.size())
        self.update()

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
        if self.pixmap is not None:
            p = QtGui.QPainter(self)
            p.drawPixmap(0,0, self.pixmap)
            self.setMinimumSize(self.pixmap.size())


class DecisionStep(QtWidgets.QTreeWidgetItem):
    def __init__(self, dlg_compact, *args):
        super(DecisionStep, self).__init__(*args)
        self.dlg_compact: Dlg_Compact = dlg_compact

    def get_buttons(self):
        pass


class LossPreventionEnhancement(DecisionStep):
    def __init__(self, this_gear, sub_gear, *args):
        super(LossPreventionEnhancement, self).__init__(*args)
        self.gear = this_gear
        self.sub_gear = sub_gear
        self.setText(1, 'Consider {} instead of {}'.format(this_gear.get_full_name(),sub_gear.get_full_name()))


class AttemptEnhancement(DecisionStep):
    def __init__(self, this_gear, *args):
        super(AttemptEnhancement, self).__init__(*args)
        self.gear = this_gear
        self.setText(1, 'Attempt {}'.format(this_gear.get_full_name()))


class SwitchAlt(DecisionStep):
    def __init__(self, alt_idx, alts, *args):
        super(SwitchAlt, self).__init__(*args)
        self.alt_idx = alt_idx
        self.alts = alts
        self.setText(1, 'Switch to alt {}'.format(self.get_name()))

    def get_name(self):
        return self.alts[self.alt_idx][1]

    def get_picture_path(self):
        return self.alts[self.alt_idx][0]

    def get_fs(self):
        return self.alts[self.alt_idx][2]


class ValksFailStack(DecisionStep):
    pass


class StackFails(DecisionStep):
    def __init__(self, gear_item, times, *args):
        super(StackFails, self).__init__(*args)
        self.gear_item = gear_item
        self.times = 0
        self.set_num_times(times)


    def set_num_times(self, times):
        self.times = times
        self.setText(1, 'Fail {} times on {}'.format(times, self.gear_item.get_full_name()))


class Decision(QtWidgets.QTreeWidgetItem):
    def __init__(self, gear_item, cost, *args):
        super(Decision, self).__init__(*args)
        self.gear_item = None
        self.set_gear_item(gear_item)
        self.cost = 0
        self.set_cost(cost)

    def set_gear_item(self, gear_item:Gear):
        self.gear_item = gear_item
        self.setText(1, gear_item.get_full_name())

    def set_cost(self, cost):
        self.cost = cost
        self.setText(0, "{:,}".format(int(round(cost))))

    def __lt__(self, other):
        return self.cost < other.cost

    def get_black_spirit(self):
        return BS

class cmdChoseDecision(QtWidgets.QPushButton):
    def __init__(self, txt, decision):
        super(cmdChoseDecision, self).__init__(txt)
        self.decision = decision


class Dlg_Compact(QtWidgets.QDialog):
    def __init__(self, frmMain):
        super(Dlg_Compact, self).__init__()
        frmObj = Ui_dlgCompact()
        self .ui = frmObj
        frmObj.setupUi(self)
        self.frmMain = frmMain
        model = frmMain.model
        self.selected_gear = None
        self.selected_decision = None
        self.abort_decision = None

        settings = model.settings
        num_fs = settings[settings.P_NUM_FS]
        frmObj.spinFS.setMaximum(num_fs)
        self.not_included = []

        self.cmd_buttons: typing.List[cmdChoseDecision] = []

        self.black_spirits = {x: QtGui.QPixmap(x).scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                              for x in [BS, BS_HMM, BS_AW_MAN, BS_CHEER, BS_FACE_PALM]
        }

        self.bs_wid = BSWidget(self, pixmap=self.black_spirits[BS_HMM])
        frmObj.ParentLayout.replaceWidget(frmObj.widget_6, self.bs_wid)
        frmObj.widget_6.setParent(None)
        frmObj.widget_6.deleteLater()

        def cmbalts_currentIndexChanged(idx):
            if idx is not None:
                self.current_alt = idx
                settings = self.frmMain.model.settings
                alts = settings[settings.P_ALTS]
                with QBlockSig(frmObj.spinFS):
                    frmObj.spinFS.setValue(alts[idx][2])

        def spinFS_valueChanged(val):
            settings = self.frmMain.model.settings
            alts = settings[settings.P_ALTS]
            alts[self.current_alt][2] = val

        frmObj.cmbalts.currentIndexChanged.connect(cmbalts_currentIndexChanged)
        frmObj.spinFS.valueChanged.connect(spinFS_valueChanged)

        self.decisions: typing.List[Decision] = []
        self.current_alt = None

    def showEvent(self, a0: QtGui.QShowEvent) -> None:
        super(Dlg_Compact, self).showEvent(a0)
        model: Enhance_model = self.frmMain.model
        settings = model.settings
        alts = settings[settings.P_ALTS]
        self.ui.cmbalts.clear()
        self.ui.cmbalts.setIconSize(QtCore.QSize(80, 80))
        for alt in alts:
            self.ui.cmbalts.addItem(QtGui.QIcon(alt[0]), alt[1])
        self.frmMain.hide()
        self.update_decision_tree()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        super(Dlg_Compact, self).closeEvent(a0)
        self.frmMain.show()

    def gear_changed(self):
        self.not_included = None
        self.decisions = self.decide()
        self.update_decision_tree()

    def decide(self):
        frmMain = self.frmMain
        model:Enhance_model  = frmMain.model
        settings = model.settings
        alts = settings[settings.P_ALTS]
        enhance_me = settings[settings.P_ENHANCE_ME]
        #mod_enhance_me = frmMain.mod_enhance_me


        fs_c_T = frmMain.fs_c.T
        eh_c_T = frmMain.eh_c.T
        mod_enhance_me = frmMain.mod_enhance_me
        mod_enhance_split_idx = frmMain.mod_enhance_split_idx
        mod_fail_stackers = frmMain.mod_fail_stackers

        included = set()
        frmMain_table_Strat:QtWidgets.QTableWidget = frmMain.ui.table_Strat
        for i in range(0, frmMain_table_Strat.rowCount()):
            included.add(frmMain_table_Strat.cellWidget(i, 1).gear)
        excluded = set([x for x in enhance_me if x not in included])

        best_fs_idxs = numpy.argmin(fs_c_T, axis=1)
        best_enh_idxs = numpy.argmin(eh_c_T, axis=1)
        best_real_enh_idxs = numpy.argmin(eh_c_T.T[:mod_enhance_split_idx].T, axis=1)

        decisions = []

        fs_decisions = []
        loss_prev_dec = []

        alt_dict = {a[2]:(i, a[0], a[1]) for i,a in enumerate(alts)}  # TODO: reverse this order so laters dont overwrite priors


        def get_fs_attempt(fs_lvl, best_fser_idxs, best_enh_idxs):
            best_fser_idx = best_fser_idxs[fs_lvl]
            best_enh_idx = best_enh_idxs[fs_lvl]
            this_fsers = fs_c_T[fs_lvl]

            this_gear: Gear = mod_fail_stackers[best_fser_idx]
            this_decision = Decision(this_gear, this_fsers[best_enh_idx], self.ui.treeWidget)
            fs_decision = StackFails(this_gear, 0, this_decision)
            this_decision.addChild(fs_decision)
            tot_num_times = 0
            cost_total = 0
            num_times = 0
            # Run through the decision idex for future and current fs level and count fails
            test_best_fs_idx = best_fser_idx
            cost_failstack = fs_c_T[fs_lvl][best_fser_idx]
            for i in range(fs_lvl, len(best_fs_idxs)):
                cost_enhance = eh_c_T[i][best_enh_idxs[i]]
                still_failing = cost_failstack < cost_enhance
                if not still_failing:
                    fs_decision.set_num_times(num_times)
                    cost_total += cost_enhance
                    break
                if test_best_fs_idx == best_fser_idx:
                    tot_num_times += 1
                    num_times += 1
                    cost_total += cost_failstack
                else:
                    fs_decision.set_num_times(num_times)
                    num_times = 0
                    best_fser_idx = test_best_fs_idx
                    cost_failstack = fs_c_T[i][best_fser_idx]
                    this_gear: Gear = mod_fail_stackers[best_fser_idx]
                    fs_decision = StackFails(this_gear, 0, this_decision)
                    this_decision.addChild(fs_decision)
            chosen_attempt_idx = best_enh_idxs[fs_lvl + tot_num_times]
            if chosen_attempt_idx < mod_enhance_split_idx:  # This section only applies for best_enh_idxs != best_real_enh_idxs
                attempt_gear = enhance_me[chosen_attempt_idx]
                this_decision.set_gear_item(attempt_gear)
                this_decision.set_cost(cost_total)
                enhance_decision = AttemptEnhancement(attempt_gear, this_decision)
                this_decision.addChild(enhance_decision)
                return this_decision
            else:
                return None


        def test_for_loss_pre_dec(fs_lvl) -> typing.List[Decision]:
            finds = []
            for excl_gear in excluded:
                eh_idx = excl_gear.get_enhance_lvl_idx()
                cost_vec_l = excl_gear.cost_vec[eh_idx]
                idx_ = numpy.argmin(cost_vec_l)
                opti_val = cost_vec_l[idx_]
                optimality = (1.0 + ((opti_val - cost_vec_l[fs_lvl]) / opti_val))
                if optimality >= 0.95:
                    index = enhance_me.index(excl_gear)
                    this_decision = Decision(excl_gear, eh_c_T[fs_lvl][index], self.ui.treeWidget)
                    loss_prev_enh_step = LossPreventionEnhancement(excl_gear, this_gear, this_decision)
                    this_decision.addChild(loss_prev_enh_step)
                    enhance_decision = AttemptEnhancement(excl_gear, this_decision)
                    this_decision.addChild(enhance_decision)
                    loss_prev_dec.append(this_decision)
                    finds.append(this_decision)
            return finds

        for fs_lvl,pack in alt_dict.items():
            alt_idx,alt_pic,alt_name = pack
            alt = alts[alt_idx]
            fs_lvl = alt[2]  # TODO: This fail stack val cannot be larger then the global fs limit
            this_fsers = fs_c_T[fs_lvl]
            this_enhancers = eh_c_T[fs_lvl]

            best_fser_idx = best_fs_idxs[fs_lvl]
            best_enh_idx = best_enh_idxs[fs_lvl]

            if this_fsers[best_fser_idx] < this_enhancers[best_enh_idx]:
                fs_data = get_fs_attempt(fs_lvl, best_fs_idxs, best_enh_idxs)
                if fs_data is not None:
                    this_decision = fs_data
                    #chosen_attempt_idx = best_enh_idxs[fs_lvl+tot_num_times]
                    switch_alt_step = SwitchAlt(alt_idx, alts, this_decision)
                    this_decision.insertChild(0, switch_alt_step)
                    #this_decision.set_gear_item(enhance_me[chosen_attempt_idx])
                    fs_decisions.append(this_decision)
            else:
                is_fake_enh_gear = best_enh_idx >= mod_enhance_split_idx
                this_gear: Gear = mod_enhance_me[best_enh_idx]
                if not is_fake_enh_gear:

                    this_decision = Decision(this_gear, this_enhancers[best_enh_idx], self.ui.treeWidget)
                    switch_alt_step = SwitchAlt(alt_idx, alts, this_decision)
                    this_decision.addChild(switch_alt_step)
                    enhance_decision = AttemptEnhancement(this_gear, this_decision)
                    this_decision.addChild(enhance_decision)
                    decisions.append(this_decision)
                # Check loss prevention enhancements
                prevs = test_for_loss_pre_dec(fs_lvl)
                for lprev in prevs:
                    switch_alt_step = SwitchAlt(alt_idx, alts, lprev)
                    lprev.insertChild(1, switch_alt_step)

        ground_up_dec = []
        if len(decisions) <= 0:

            this_decision = get_fs_attempt(0, best_fs_idxs, best_real_enh_idxs)
            if this_decision is not None:
                # find an alt for this
                if 0 in alt_dict:
                    alt_idx, alt_pic, alt_name = alt_dict[0]
                    switch_alt_step = SwitchAlt(alt_idx, alts, this_decision)
                    this_decision.insertChild(0, switch_alt_step)
                    ground_up_dec.append(this_decision)
                else:
                    #black smits book here
                    pass

            # insert alternate gear suggestions

        return decisions + fs_decisions + ground_up_dec + loss_prev_dec

    def decision_clicked(self):
        btn: cmdChoseDecision = self.sender()
        decision: Decision = btn.decision
        frmObj = self.ui
        self.bs_wid.set_pixmap(self.black_spirits[decision.get_black_spirit()])
        print(decision.text(1))
        for i in range(0, frmObj.treeWidget.topLevelItemCount()):
            frmObj.treeWidget.takeTopLevelItem(0)
        frmObj.treeWidget.addTopLevelItem(decision)
        decision.setExpanded(True)
        self.abort_decision = QtWidgets.QPushButton('Abort')
        self.abort_decision.clicked.connect(self.abort_decision_clicked)
        frmObj.treeWidget.setItemWidget(decision, 0, self.abort_decision)




    def abort_decision_clicked(self):
        self.bs_wid.set_pixmap(self.black_spirits[BS_HMM])
        self.update_decision_tree()

    def update_decision_tree(self):
        frmObj = self.ui
        if self.decisions is None or len(self.decisions) <= 0:
            self.decisions = self.decide()

        for i in range(frmObj.treeWidget.topLevelItemCount()):
            frmObj.treeWidget.takeTopLevelItem(0)

        self.cmd_buttons.clear()

        for decision in self.decisions:
            frmObj.treeWidget.addTopLevelItem(decision)
            cmd_button = cmdChoseDecision('Accept', decision)
            cmd_button.clicked.connect(self.decision_clicked)
            self.cmd_buttons.append(cmd_button)
            frmObj.treeWidget.setItemWidget(decision, 0, cmd_button)

        frmObj.treeWidget.sortItems(0, Qt.AscendingOrder)
        frmObj.treeWidget.resizeColumnToContents(1)

