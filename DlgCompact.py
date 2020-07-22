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

STR_NEXT_PIC = relative_path_convert('Images/next.png')
STR_CHECK_PIC = relative_path_convert('Images/tick.png')


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


class cmdChoseDecision(QtWidgets.QPushButton):
    def __init__(self, txt, decision):
        super(cmdChoseDecision, self).__init__(txt)
        self.decision = decision


class DecisionStep(QtWidgets.QTreeWidgetItem):
    sig_step_finished = QtCore.pyqtSignal(object, name='sig_step_finished')

    def __init__(self, dlg_compact, *args):
        super(DecisionStep, self).__init__(*args)
        self.dlg_compact: Dlg_Compact = dlg_compact

    def get_buttons(self, dlg_compact):
        return []

    def acceptability_criteria(self, dlg_compact):
        return True


class Decision(QtWidgets.QTreeWidgetItem):
    def __init__(self, gear_item, cost, *args):
        super(Decision, self).__init__(*args)
        self.gear_item = None

        self.cost = 0
        self.set_gear_item(gear_item)
        self.set_cost(cost)
        self.current_step = 0

    def set_gear_item(self, gear_item: Gear):
        self.gear_item = gear_item
        self.updte_text()

    def set_cost(self, cost):
        self.cost = cost
        self.updte_text()

    def updte_text(self):
        gear_item = self.gear_item
        cost = self.cost
        self.setText(1, "{} | {:,}".format(gear_item.get_full_name(), int(round(cost))))
        self.setText(0, "{:,}".format(int(round(cost))))

    def __lt__(self, other):
        return self.cost < other.cost

    def get_black_spirit(self):
        return BS


blk_smth_scrt_book = {
    20: 1000000,
    30: 1500000,
    40: 2000000,
    50: 3000000
}


class Dlg_Compact(QtWidgets.QDialog):
    def __init__(self, frmMain):
        super(Dlg_Compact, self).__init__()
        frmObj = Ui_dlgCompact()
        self .ui = frmObj
        frmObj.setupUi(self)
        self.frmMain = frmMain
        model = frmMain.model
        self.selected_gear = None
        self.selected_decision: Decision = None
        self.abort_decision = None

        settings = model.settings
        num_fs = settings[settings.P_NUM_FS]
        frmObj.spinFS.setMaximum(num_fs)
        self.not_included = []

        self.icon_check = QtGui.QIcon(STR_CHECK_PIC)
        self.icon_next = QtGui.QIcon(STR_NEXT_PIC)

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
                self.update_curent_step()

        def spinFS_valueChanged(val):
            if val is not None:
                settings = self.frmMain.model.settings
                alts = settings[settings.P_ALTS]
                alts[self.current_alt][2] = val
                self.invalidate_decisions()
                if self.selected_decision is None:
                    self.update_decision_tree()
                else:
                    self.update_curent_step()

        frmObj.cmbalts.currentIndexChanged.connect(cmbalts_currentIndexChanged)
        frmObj.spinFS.valueChanged.connect(spinFS_valueChanged)

        self.decisions: typing.List[Decision] = []
        self.current_alt = None

    def showEvent(self, a0: QtGui.QShowEvent) -> None:
        super(Dlg_Compact, self).showEvent(a0)
        model: Enhance_model = self.frmMain.model
        settings = model.settings
        alts = settings[settings.P_ALTS]
        with QBlockSig(self.ui.cmbalts):
            self.ui.cmbalts.clear()
            self.ui.cmbalts.setIconSize(QtCore.QSize(80, 80))
            for alt in alts:
                self.ui.cmbalts.addItem(QtGui.QIcon(alt[0]), alt[1])
        self.current_alt = self.ui.cmbalts.currentIndex()
        with QBlockSig(self.ui.spinFS):
            self.ui.spinFS.setMinimum(model.get_min_fs())
            self.ui.spinFS.setValue(alts[self.current_alt][2])
        self.update_decision_tree()
        self.frmMain.hide()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        super(Dlg_Compact, self).closeEvent(a0)
        self.frmMain.show()

    def gear_changed(self):
        self.not_included = None
        self.update_decision_tree()
        self.invalidate_decisions()

    def invalidate_decisions(self):
        self.decisions = None

    def get_fs_attempt(self, fs_lvl, best_fser_idxs, best_enh_idxs, fs_c_T, eh_c_T, mod_fail_stackers, mod_enhance_split_idx, enhance_me):
        best_fser_idx = best_fser_idxs[fs_lvl]
        best_enh_idx = best_enh_idxs[fs_lvl]
        this_fsers = fs_c_T[fs_lvl]

        this_gear: Gear = mod_fail_stackers[best_fser_idx]
        this_decision = Decision(this_gear, this_fsers[best_enh_idx], self.ui.treeWidget)
        fs_decision = StackFails(this_gear, 0, this_decision, alt_cur_fs=fs_lvl)
        this_decision.addChild(fs_decision)
        attempt_found = False
        tot_num_times = 0
        cost_total = 0
        num_times = 0
        fs_accum = 0
        # Run through the decision idex for future and current fs level and count fails
        test_best_fs_idx = best_fser_idx
        cost_failstack = fs_c_T[fs_lvl][best_fser_idx]
        i = fs_lvl
        # for i in range(fs_lvl, len(best_fs_idxs)):
        while i < len(best_fser_idxs) and not attempt_found:
            cost_enhance = eh_c_T[i][best_enh_idxs[i]]
            still_failing = cost_failstack < cost_enhance
            if not still_failing:
                fs_decision.set_num_times(num_times)
                fs_decision.set_fs_gain(fs_accum)
                fs_accum = 0
                cost_total += cost_enhance
                attempt_found = True
                break
            if test_best_fs_idx == best_fser_idx:
                tot_num_times += 1
                num_times += 1
                this_gain = mod_fail_stackers[test_best_fs_idx].fail_FS_accum()
                fs_accum += this_gain
                i += this_gain
                cost_total += cost_failstack + 1  # The +1 to beat higher step count when cost is 0
            else:
                fs_decision.set_num_times(num_times)
                fs_decision.set_fs_gain(fs_accum)

                best_fser_idx = test_best_fs_idx
                cost_failstack = fs_c_T[i][best_fser_idx]
                cost_total += cost_failstack
                this_gear: Gear = mod_fail_stackers[best_fser_idx]

                this_gain = mod_fail_stackers[test_best_fs_idx].fail_FS_accum()
                fs_accum = this_gain
                i += this_gain
                num_times = 1

                fs_decision = StackFails(this_gear, 0, this_decision, alt_cur_fs=i)
                this_decision.addChild(fs_decision)
        if attempt_found:
            chosen_attempt_idx = best_enh_idxs[fs_lvl + i]
            if chosen_attempt_idx < mod_enhance_split_idx:  # This section only applies for best_enh_idxs != best_real_enh_idxs
                attempt_gear = enhance_me[chosen_attempt_idx]
                this_decision.set_gear_item(attempt_gear)
                this_decision.set_cost(cost_total)
                enhance_decision = AttemptEnhancement(attempt_gear, this_decision, on_fs=i)
                this_decision.addChild(enhance_decision)
                return this_decision
            else:
                return None
        else:
            return None

    def test_for_loss_pre_dec(self, fs_lvl, this_gear, best_enh_idx, eh_c_T, excluded, enhance_me) -> typing.List[Decision]:
        finds = []
        for excl_gear in excluded:
            eh_idx = excl_gear.get_enhance_lvl_idx()
            cost_vec_l = excl_gear.cost_vec[eh_idx]
            idx_ = numpy.argmin(cost_vec_l)
            opti_val = cost_vec_l[idx_]
            optimality = (1.0 + ((opti_val - cost_vec_l[fs_lvl]) / opti_val))
            if optimality >= 0.95:
                index = enhance_me.index(excl_gear)
                this_decision = Decision(excl_gear,  eh_c_T[fs_lvl][index] - eh_c_T[fs_lvl][best_enh_idx], self.ui.treeWidget)
                loss_prev_enh_step = LossPreventionEnhancement(excl_gear, this_gear, this_decision)
                print(loss_prev_enh_step.text(1))
                print('{} | {}'.format(eh_c_T[fs_lvl][index], eh_c_T[fs_lvl][best_enh_idx]))
                this_decision.addChild(loss_prev_enh_step)
                enhance_decision = AttemptEnhancement(excl_gear, this_decision, on_fs=fs_lvl)
                this_decision.addChild(enhance_decision)
                finds.append(this_decision)
        return finds

    def check_out_fs_lvl(self, fs_lvl, alt_idx, alts, fs_c_T, eh_c_T, excluded, enhance_me, best_fs_idxs,
                         best_enh_idxs, mod_enhance_split_idx, mod_enhance_me, mod_fail_stackers):
        these_fs_decisions = []
        these_decisions = []
        these_loss_prev_dec = []

        this_fsers = fs_c_T[fs_lvl]
        this_enhancers = eh_c_T[fs_lvl]

        best_fser_idx = best_fs_idxs[fs_lvl]
        best_enh_idx = best_enh_idxs[fs_lvl]

        if this_fsers[best_fser_idx] < this_enhancers[best_enh_idx]:
            this_decision = self.get_fs_attempt(fs_lvl, best_fs_idxs, best_enh_idxs, fs_c_T, eh_c_T, mod_fail_stackers,
                                                mod_enhance_split_idx, enhance_me)
            if this_decision is not None:
                # this_decision = fs_data
                # chosen_attempt_idx = best_enh_idxs[fs_lvl+tot_num_times]
                for i in range(0, this_decision.childCount()):
                    child = this_decision.child(i)
                    if isinstance(child, StackFails):
                        child.set_alt_idx(alt_idx)
                switch_alt_step = SwitchAlt(alt_idx, alts, this_decision)
                this_decision.insertChild(0, switch_alt_step)
                # this_decision.set_gear_item(enhance_me[chosen_attempt_idx])
                these_fs_decisions.append(this_decision)
        else:
            is_fake_enh_gear = best_enh_idx >= mod_enhance_split_idx
            this_gear: Gear = mod_enhance_me[best_enh_idx]
            if not is_fake_enh_gear:
                this_decision = Decision(this_gear, this_enhancers[best_enh_idx], self.ui.treeWidget)
                switch_alt_step = SwitchAlt(alt_idx, alts, this_decision)
                this_decision.addChild(switch_alt_step)
                enhance_decision = AttemptEnhancement(this_gear, this_decision, on_fs=fs_lvl)
                this_decision.addChild(enhance_decision)
                these_decisions.append(this_decision)
            # Check loss prevention enhancements
            prevs = self.test_for_loss_pre_dec(fs_lvl, this_gear, best_enh_idx, eh_c_T, excluded, enhance_me)
            for lprev in prevs:
                switch_alt_step = SwitchAlt(alt_idx, alts, lprev)
                lprev.insertChild(1, switch_alt_step)
                these_loss_prev_dec.append(lprev)

        return these_fs_decisions, these_decisions, these_loss_prev_dec

    def insert_after_swap(self, insert_me, decision):
        for i in range(0, decision.childCount()):
            child = decision.child(i)
            if isinstance(child, SwitchAlt):
                decision.insertChild(i + 1, insert_me)
                return True
        return False

    def decide(self):
        frmMain = self.frmMain
        model:Enhance_model  = frmMain.model
        settings = model.settings
        alts = settings[settings.P_ALTS]
        enhance_me = settings[settings.P_ENHANCE_ME]
        s_valks = settings[settings.P_VALKS]
        #mod_enhance_me = frmMain.mod_enhance_me

        min_fs = model.get_min_fs()


        fs_c_T = frmMain.fs_c.T
        eh_c_T = frmMain.eh_c.T
        mod_enhance_me = frmMain.mod_enhance_me
        mod_enhance_split_idx = frmMain.mod_enhance_split_idx
        mod_fail_stackers = frmMain.mod_fail_stackers

        included = set()
        frmMain_table_Strat:QtWidgets.QTableWidget = frmMain.ui.table_Strat
        for i in range(min_fs, frmMain_table_Strat.rowCount()):
            included.add(frmMain_table_Strat.cellWidget(i, 1).gear)
        excluded = set([x for x in enhance_me if x not in included])

        best_fs_idxs = numpy.argmin(fs_c_T, axis=1)
        best_enh_idxs = numpy.argmin(eh_c_T, axis=1)
        best_real_enh_idxs = numpy.argmin(eh_c_T.T[:mod_enhance_split_idx].T, axis=1)

        decisions = []
        fs_decisions = []
        loss_prev_dec = []
        ground_up_dec = []

        alt_dict = {a[2]:(i, a[0], a[1]) for i,a in enumerate(alts)}  # TODO: reverse this order so laters dont overwrite priors

        found_mins = False

        for fs_lvl,pack in alt_dict.items():
            if fs_lvl <= min_fs and not found_mins:
                this_decision = self.get_fs_attempt(min_fs, best_fs_idxs, best_enh_idxs, fs_c_T, eh_c_T, mod_fail_stackers,
                                                    mod_enhance_split_idx, enhance_me)
                alt_idx, alt_pic, alt_name = alt_dict[min_fs]
                if this_decision is not None:
                    for i in range(0, this_decision.childCount()):
                        child = this_decision.child(i)
                        if isinstance(child, StackFails):
                            child.set_alt_idx(alt_idx)

                    switch_alt_step = SwitchAlt(alt_idx, alts, this_decision)
                    this_decision.insertChild(0, switch_alt_step)
                    ground_up_dec.append(this_decision)

                for valk_lvl in set(s_valks):
                    these_fs_decisions, these_decisions, these_loss_prev_dec = self.check_out_fs_lvl(valk_lvl+min_fs, alt_idx, alts,
                                                                                                     fs_c_T, eh_c_T,
                                                                                                     excluded, enhance_me,
                                                                                                     best_fs_idxs,
                                                                                                     best_enh_idxs,
                                                                                                     mod_enhance_split_idx,
                                                                                                     mod_enhance_me,
                                                                                                     mod_fail_stackers)
                    for this_decision in these_fs_decisions:
                        valks_step = ValksFailStack(valk_lvl, this_decision, alt_idx=alt_idx)
                        if not self.insert_after_swap(valks_step, this_decision):
                            this_decision.insertChild(0, valks_step)
                        fs_decisions.append(this_decision)

                    for this_decision in these_decisions:
                        valks_step = ValksFailStack(valk_lvl, this_decision, alt_idx=alt_idx)
                        if not self.insert_after_swap(valks_step, this_decision):
                            this_decision.insertChild(0, valks_step)
                        decisions.append(this_decision)

                    for this_decision in these_loss_prev_dec:
                        valks_step = ValksFailStack(valk_lvl, this_decision, alt_idx=alt_idx)
                        if not self.insert_after_swap(valks_step, this_decision):
                            this_decision.insertChild(0, valks_step)
                        loss_prev_dec.append(this_decision)

                    #self.test_for_loss_pre_dec(fs_lvl, this_gear, eh_c_T, excluded, enhance_me)

                found_mins = True
            else:
                alt_idx,alt_pic,alt_name = pack
                alt = alts[alt_idx]
                fs_lvl = alt[2]  # TODO: This fail stack val cannot be larger then the global fs limit
                these_fs_decisions, these_decisions, these_loss_prev_dec = self.check_out_fs_lvl(fs_lvl, alt_idx,alts,
                                                                                                 fs_c_T, eh_c_T, excluded,
                                                                                                 enhance_me, best_fs_idxs,
                                                                                                 best_enh_idxs,
                                                                                                 mod_enhance_split_idx,
                                                                                                 mod_enhance_me, mod_fail_stackers)
                fs_decisions.extend(these_fs_decisions)
                decisions.extend(these_decisions)
                loss_prev_dec.extend(these_loss_prev_dec)


        if len(decisions) <= 0 and len(fs_decisions) <= 0 and len(ground_up_dec) <= 0:
            for fs_lvl, pack in alt_dict.items():
                if fs_lvl > min_fs:
                    found = None
                    for book_s in blk_smth_scrt_book.keys():
                        if book_s >= fs_lvl:
                            found = book_s
                            break
                    if found is not None:
                        cost = blk_smth_scrt_book[book_s]
                        this_decision = self.get_fs_attempt(min_fs, best_fs_idxs, best_enh_idxs, fs_c_T, eh_c_T,
                                                            mod_fail_stackers,
                                                            mod_enhance_split_idx, enhance_me)
                        alt_idx, alt_pic, alt_name = alt_dict[fs_lvl]
                        if this_decision is not None:
                            this_decision.set_cost(this_decision.cost + cost)
                            for i in range(0, this_decision.childCount()):
                                child = this_decision.child(i)
                                if isinstance(child, StackFails):
                                    child.set_alt_idx(alt_idx)

                            switch_alt_step = SwitchAlt(alt_idx, alts, this_decision)
                            this_decision.insertChild(0, switch_alt_step)

                            bsb = UseBlacksmithBook(fs_lvl, this_decision, alt_idx=alt_idx)
                            this_decision.insertChild(1, bsb)
                            ground_up_dec.append(this_decision)



        return decisions + fs_decisions + ground_up_dec + loss_prev_dec

    def decision_clicked(self):
        btn: cmdChoseDecision = self.sender()
        decision: Decision = btn.decision
        frmObj = self.ui
        self.bs_wid.set_pixmap(self.black_spirits[decision.get_black_spirit()])
        self.selected_decision = decision
        for i in range(0, frmObj.treeWidget.topLevelItemCount()):
            frmObj.treeWidget.takeTopLevelItem(0)
        frmObj.treeWidget.addTopLevelItem(decision)
        decision.setExpanded(True)
        self.abort_decision = QtWidgets.QPushButton('Abort')
        self.abort_decision.clicked.connect(self.abort_decision_clicked)
        frmObj.treeWidget.setItemWidget(decision, 0, self.abort_decision)
        self.set_step()

    def set_step(self):
        self.update_curent_step()
        self.clear_button_box()
        frmObj = self.ui
        current_decision: Decision = frmObj.treeWidget.topLevelItem(0)
        this_step: DecisionStep = current_decision.child(current_decision.current_step)
        for btn in this_step.get_buttons(self):
            frmObj.widButtonBox.layout().addWidget(btn)

    def clear_button_box(self):
        layout = self.ui.widButtonBox.layout()
        k:QtWidgets.QWidget = layout.takeAt(0)
        while k is not None:
            k.widget().deleteLater()
            k = layout.takeAt(0)

    def update_curent_step(self):
        if self.selected_decision is not None:
            frmObj = self.ui
            current_decision: Decision = frmObj.treeWidget.topLevelItem(0)
            this_step: DecisionStep = current_decision.child(current_decision.current_step)
            if this_step.acceptability_criteria(self):
                self.step_finished(this_step)
            else:
                this_step.setIcon(0, self.icon_next)

    def step_finished(self, step:DecisionStep):
        frmObj = self.ui
        current_decision:Decision = frmObj.treeWidget.topLevelItem(0)
        current_step = current_decision.child(current_decision.current_step)
        current_step.setIcon(0, self.icon_check)
        current_decision.current_step += 1
        if current_decision.current_step < current_decision.childCount():

            self.set_step()
        else:
            self.decisions = []
            self.abort_decision_clicked()

    def abort_decision_clicked(self):
        self.clear_button_box()
        self.bs_wid.set_pixmap(self.black_spirits[BS_HMM])
        selected_decision: Decision = self.selected_decision
        selected_decision.current_step = 0
        for i in range(selected_decision.childCount()):
            child: DecisionStep = selected_decision.child(i)
            child.setIcon(0, QtGui.QIcon())
        self.selected_decision = None
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

    def get_cur_fs(self):
        return self.ui.spinFS.value()


class LossPreventionEnhancement(DecisionStep):
    def __init__(self, this_gear, sub_gear, *args):
        super(LossPreventionEnhancement, self).__init__(*args)
        self.gear = this_gear
        self.sub_gear = sub_gear
        self.setText(1, 'Consider {} instead of {}'.format(this_gear.get_full_name(), sub_gear.get_full_name()))


class AttemptEnhancement(DecisionStep):
    def __init__(self, this_gear, *args, on_fs=None):
        super(AttemptEnhancement, self).__init__(*args)
        self.gear:Gear = this_gear
        self.on_fs = on_fs
        self.update_txt()
        self.attempt_made = False

    def set_gear(self, gear:Gear):
        self.gear = gear
        self.update_txt()

    def set_on_fs(self, on_fs):
        self.on_fs = on_fs
        self.update_txt()

    def update_txt(self):
        self.setText(1, 'Attempt {} on (+{})'.format(self.gear.get_full_name(), self.on_fs))

    def acceptability_criteria(self, dlg_compact):
        return self.attempt_made

    def get_buttons(self, dlg_compact: Dlg_Compact):
        cmdSucceed = QtWidgets.QPushButton('Success')
        cmdFail = QtWidgets.QPushButton('Fail')

        def cmdSucceed_clicked():
            self.attempt_made = True
            dlg_compact.frmMain.simulate_success_gear(self.gear)
            dlg_compact.ui.spinFS.setValue(dlg_compact.ui.spinFS.minimum())
            dlg_compact.bs_wid.set_pixmap(dlg_compact.black_spirits[BS_CHEER])

        def cmdFail_clicked():
            self.attempt_made = True
            gain = self.gear.fs_gain()
            dlg_compact.frmMain.simulate_fail_gear(self.gear)
            dlg_compact.ui.spinFS.setValue(dlg_compact.ui.spinFS.value()+gain)
            dlg_compact.bs_wid.set_pixmap(dlg_compact.black_spirits[BS_AW_MAN])

        dlg_compact.bs_wid.set_pixmap(dlg_compact.black_spirits[BS_FACE_PALM])

        cmdSucceed.clicked.connect(cmdSucceed_clicked)
        cmdFail.clicked.connect(cmdFail_clicked)

        return[cmdFail, cmdSucceed]


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

    def get_buttons(self, dlg_compact: Dlg_Compact):
        cmdSwitch = QtWidgets.QPushButton('Swap')
        def cmdSwitch_clicked():
            dlg_compact.ui.cmbalts.setCurrentIndex(self.alt_idx)
        cmdSwitch.clicked.connect(cmdSwitch_clicked)
        return [cmdSwitch]

    def acceptability_criteria(self, dlg_compact: Dlg_Compact):
        return dlg_compact.current_alt == self.alt_idx


class ValksFailStack(DecisionStep):
    def __init__(self, fs_lvl, *args, alt_idx=None):
        super(ValksFailStack, self).__init__(*args)
        self.fs_lvl = 0
        self.alt_idx = alt_idx
        self.set_fs_lvl(fs_lvl)

    def set_alt_idx(self, alt_idx):
        self.alt_idx = alt_idx

    def set_fs_lvl(self, fs_lvl):
        self.fs_lvl = fs_lvl
        self.setText(1, 'Apply (+{}) Advice of Valks'.format(fs_lvl))

    def acceptability_criteria(self, dlg_compact):
        model: Enhance_model = dlg_compact.frmMain.model
        flag = self.alt_idx is None or dlg_compact.current_alt == self.alt_idx
        flag &= dlg_compact.get_cur_fs() == self.fs_lvl + model.get_min_fs()
        return flag

    def get_buttons(self, dlg_compact: Dlg_Compact):
        cmdSucceed = QtWidgets.QPushButton('Okay')


        def cmdSucceed_clicked():
            model: Enhance_model = dlg_compact.frmMain.model
            settings = model.settings
            dlg_compact.ui.spinFS.setValue(self.fs_lvl + model.get_min_fs())
            settings[settings.P_VALKS].remove(self.fs_lvl)
            dlg_compact.invalidate_decisions()


        cmdSucceed.clicked.connect(cmdSucceed_clicked)

        return[cmdSucceed]


class StackFails(DecisionStep):
    def __init__(self, gear_item, times, *args, alt_idx=None, alt_cur_fs=None, fs_gain=None):
        super(StackFails, self).__init__(*args)
        self.gear_item = gear_item
        self.times = 0
        self.alt_idx = alt_idx
        self.alt_cur_fs = alt_cur_fs
        self.fs_gain = fs_gain
        self.set_num_times(times)

    def set_alt_idx(self, alt_idx):
        self.alt_idx = alt_idx

    def set_fs_gain(self, fs_gain):
        self.fs_gain = fs_gain

    def set_num_times(self, times):
        self.times = times
        self.setText(1, 'Fail {} times on {}'.format(times, self.gear_item.get_full_name()))

    def acceptability_criteria(self, dlg_compact):
        flag = self.alt_idx is None or dlg_compact.current_alt == self.alt_idx
        flag &= self.alt_cur_fs is None or self.fs_gain is None or dlg_compact.get_cur_fs() == self.alt_cur_fs + self.fs_gain
        return flag

    def get_buttons(self, dlg_compact: Dlg_Compact):
        cmdSucceed = QtWidgets.QPushButton('Okay')
        cmdFail = QtWidgets.QPushButton('uhhh..')

        def cmdSucceed_clicked():
            dlg_compact.ui.spinFS.setValue(dlg_compact.ui.spinFS.value()+self.fs_gain)

        def cmdFail_clicked():
            dlg_compact.abort_decision_clicked()

        cmdSucceed.clicked.connect(cmdSucceed_clicked)
        cmdFail.clicked.connect(cmdFail_clicked)

        return[cmdFail, cmdSucceed]


class UseBlacksmithBook(DecisionStep):
    def __init__(self, fs_lvl, *args, alt_idx=None):
        super(UseBlacksmithBook, self).__init__(*args)
        self.fs_lvl = 0
        self.alt_idx = alt_idx
        self.set_fs_lvl(fs_lvl)

    def set_alt_idx(self, alt_idx):
        self.alt_idx = alt_idx

    def set_fs_lvl(self, fs_lvl):
        self.fs_lvl = fs_lvl
        self.setText(1, 'Blacksmith\'s Secret Book - {}'.format(fs_lvl))

    def acceptability_criteria(self, dlg_compact):
        model: Enhance_model = dlg_compact.frmMain.model
        flag = self.alt_idx is None or dlg_compact.current_alt == self.alt_idx
        flag &= dlg_compact.get_cur_fs() <= self.fs_lvl
        return flag

    def get_buttons(self, dlg_compact: Dlg_Compact):
        cmdSucceed = QtWidgets.QPushButton('Okay')


        def cmdSucceed_clicked():
            model: Enhance_model = dlg_compact.frmMain.model
            settings = model.settings
            spin_val = dlg_compact.ui.spinFS.value()
            dlg_compact.ui.spinFS.setValue(model.get_min_fs())
            settings[settings.P_VALKS].append(self.fs_lvl)
            dlg_compact.invalidate_decisions()


        cmdSucceed.clicked.connect(cmdSucceed_clicked)

        return[cmdSucceed]
