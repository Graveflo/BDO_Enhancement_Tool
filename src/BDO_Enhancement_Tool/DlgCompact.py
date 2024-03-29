#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑  ❧
"""
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import Qt
from .qt_UI_Common import BS_CHEER, BS_AW_MAN, BS_FACE_PALM, BS_HMM, BS, pix, \
    STR_NEXT_PIC, STR_CHECK_PIC

from .Qt_common import QBlockSig
from .Forms.dlgCompact import Ui_dlgCompact
import typing
from .model import Enhance_model, StrategySolution
from .Core.Gear import Gear

QWidget = QtWidgets.QWidget
MONNIES_FORMAT = "{:,}"


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

    def __init__(self, *args):
        super(DecisionStep, self).__init__(*args)
        #self.dlg_compact: Dlg_Compact = dlg_compact

    def get_buttons(self, dlg_compact):
        return []

    def acceptability_criteria(self, dlg_compact):
        return True

    def get_description(self):
        return self.text(1)


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
        self.setText(1, gear_item.get_full_name())
        self.setText(0, "")
        self.setText(2, "{:,}".format(int(round(cost))))

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

        self.selected_gear = None
        self.selected_decision: Decision = None
        self.abort_decision = None



        self.not_included = []
        self.always_on_top = None
        self.follow_gear = None
        self.alt_save = None
        self.icon_check = pix.get_icon(STR_CHECK_PIC)
        self.icon_next = pix.get_icon(STR_NEXT_PIC)

        self.cmd_buttons: typing.List[cmdChoseDecision] = []

        self.black_spirits = {x: QtGui.QPixmap(x).scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
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
                self.update_current_step()
                if frmObj.chkStayOnAlt.isChecked():
                    if self.selected_decision is None:
                        self.update_decision_tree()
                self.alt_save = frmObj.cmbalts.currentText()

        def spinFS_valueChanged(val):
            if val is not None:
                settings = self.frmMain.model.settings
                alts = settings[settings.P_ALTS]
                alts[self.current_alt][2] = val
                self.invalidate_decisions()
                if self.selected_decision is None:
                    self.update_decision_tree()
                else:
                    self.update_current_step()

        frmObj.cmbalts.currentIndexChanged.connect(cmbalts_currentIndexChanged)
        frmObj.spinFS.valueChanged.connect(spinFS_valueChanged)

        self.decisions: typing.List[Decision] = []
        self.current_alt = None
        frmObj.treeWidget.itemExpanded.connect(lambda: frmObj.treeWidget.resizeColumnToContents(1))
        frmObj.cmdOnTop.clicked.connect(self.cmdOnTop_clicked)

        def chkStayOnAlt_clicked():
            if self.selected_decision is None:
                self.update_decision_tree()

        frmObj.chkStayOnAlt.clicked.connect(chkStayOnAlt_clicked)

        #def chkFollowTrack_clicked():
        #    if not frmObj.chkStayOnAlt.isChecked():
        #        frmObj.chkStayOnAlt.setChecked(True)

        #frmObj.chkFollowTrack.clicked.connect(chkFollowTrack_clicked)

    def set_common(self, model):
        frmObj = self.ui
        self.model = model
        model = model
        settings = model.settings
        num_fs = settings[settings.P_NUM_FS]
        frmObj.spinFS.setMaximum(num_fs)

    def cmdOnTop_clicked(self, chked):
        self.always_on_top = chked
        self.show()

    def show(self) -> None:
        frmObj = self.ui
        this_flags = self.windowFlags()
        aot_mask = Qt.WindowType.WindowStaysOnTopHint

        if self.always_on_top is None:
            self.always_on_top = frmObj.cmdOnTop.isChecked()
        else:
            with QBlockSig(frmObj.cmdOnTop):
                frmObj.cmdOnTop.setChecked(self.always_on_top)


        if self.always_on_top:
            self.setWindowFlags(this_flags | aot_mask)
        else:
            self.setWindowFlags(this_flags & (~aot_mask))
        super(Dlg_Compact, self).show()

    def showEvent(self, a0: QtGui.QShowEvent) -> None:
        super(Dlg_Compact, self).showEvent(a0)
        model: Enhance_model = self.frmMain.model
        settings = model.settings
        alts = settings[settings.P_ALTS]

        if not self.validate():
            return

        with QBlockSig(self.ui.cmbalts):
            self.ui.cmbalts.clear()
            self.ui.cmbalts.setIconSize(QtCore.QSize(80, 80))
            for alt in alts:
                self.ui.cmbalts.addItem(pix.get_icon(alt[0]), alt[1])
        if self.alt_save is not None:
            tryind = self.ui.cmbalts.findText(self.alt_save)
            if tryind >= 0:
                self.ui.cmbalts.setCurrentIndex(tryind)
        self.current_alt = self.ui.cmbalts.currentIndex()

        with QBlockSig(self.ui.spinFS):
            self.ui.spinFS.setMinimum(model.get_min_fs())
            self.ui.spinFS.setValue(alts[self.current_alt][2])
        if self.selected_decision is None:
            self.update_decision_tree()

        self.frmMain.hide()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        super(Dlg_Compact, self).closeEvent(a0)
        self.frmMain.show()

    def event(self, a0: QtCore.QEvent) -> bool:
        if isinstance(a0, QtGui.QKeyEvent):
            if a0.key() == Qt.Key.Key_Escape:
                a0.ignore()
                return True
        return super(Dlg_Compact, self).event(a0)

    def gear_changed(self):
        self.not_included = None
        self.update_decision_tree()
        self.invalidate_decisions()

    def invalidate_decisions(self):
        self.decisions = None

    def get_fs_attempt(self, fs_lvl, strat: StrategySolution, only_real=True, loss_prev=False):
        sols, enh = strat.eval_fs_attempt(fs_lvl, saves=not only_real, collapse=True, loss_prev=loss_prev)
        if enh is None:
            return None
        else:
            parent_decision = Decision(enh.gear, 0, self.ui.treeWidget)
            #parent = parent_decision
            cost_total = 0
            for times, sol in sols:
                this_gear = sol.gear
                fs_gain = this_gear.fs_gain()
                fs_decision = StackFails(this_gear, times, parent_decision, alt_cur_fs=fs_lvl, fs_gain=fs_gain*times)
                parent_decision.addChild(fs_decision)
                cost_total += sol.cost
                fs_lvl += times * fs_gain
            parent_decision.set_cost(cost_total + enh.cost)
            enhance_decision = AttemptEnhancement(enh.gear, parent_decision, on_fs=fs_lvl)
            enhance_decision.set_fs_cost(cost_total)
            parent_decision.addChild(enhance_decision)
            return parent_decision

    def get_loss_prev_fs_attempt(self, fs_lvl, strat:StrategySolution):
        parent_dec = self.get_fs_attempt(fs_lvl, strat, loss_prev=True)
        if parent_dec is None:
            return None

        enh_dec: AttemptEnhancement = parent_dec.takeChild(parent_dec.childCount()-1)
        return self.get_loss_prev_attempt(parent_dec, enh_dec, strat)

    def get_loss_prev_attempt(self, parent_dec:Decision, enh_dec, strat:StrategySolution):
        decs = []
        if not strat.is_fake(enh_dec.gear):
            return None

        enh_fs = enh_dec.on_fs
        fs_cost = enh_dec.fs_cost
        opt_gear = enh_dec.gear
        opt_dec_cost = parent_dec.cost
        loss_prevs = strat.get_loss_prevs(enh_fs)
        for sol in loss_prevs:
            this_gear = sol.gear
            cost = sol.cost + fs_cost
            this_decision = Decision(this_gear, cost, self.ui.treeWidget)
            optimality = (1.0 + ((opt_dec_cost - cost) / opt_dec_cost))
            loss_prev_enh_step = LossPreventionEnhancement(this_gear, opt_gear, this_decision, cost_diff=cost-opt_dec_cost,
                                                           loss_prev=optimality)
            this_decision.addChild(loss_prev_enh_step)
            for i in range(0, parent_dec.childCount()):
                child:StackFails = parent_dec.child(i)
                fs_dec = StackFails(child.gear_item, child.times, this_decision, alt_cur_fs=child.alt_cur_fs, fs_gain=child.fs_gain)
                this_decision.addChild(fs_dec)

            enhance_decision = AttemptEnhancement(this_gear, this_decision, on_fs=enh_dec.on_fs)
            this_decision.addChild(enhance_decision)
            decs.append(this_decision)
        if len(decs) > 0:
            return decs
        else:
            return None

    def check_out_fs_lvl(self, fs_lvl, alt_idx, alts, strat: StrategySolution):
        these_fs_decisions = []
        these_decisions = []
        these_loss_prev_dec = []

        this_best_fs_solution = strat.get_best_fs_solution(fs_lvl)
        this_best_enh_solution = strat.get_best_enh_solution(fs_lvl)
        #best_fs_gear = this_best_fs_solution.gear
        best_fs_cost = this_best_fs_solution.cost
        best_enh_gear = this_best_enh_solution.gear
        best_enh_cost = this_best_enh_solution.cost

        if best_fs_cost < best_enh_cost:
            this_decision = self.get_fs_attempt(fs_lvl, strat)
            if this_decision is not None:
                for i in range(0, this_decision.childCount()):
                    child = this_decision.child(i)
                    if isinstance(child, StackFails):
                        child.set_alt_idx(alt_idx)
                switch_alt_step = SwitchAlt(alt_idx, alts)
                this_decision.insertChild(0, switch_alt_step)
                these_fs_decisions.append(this_decision)
        else:
            is_fake_enh_gear = strat.is_fake(best_enh_gear)
            if not is_fake_enh_gear:
                this_decision = Decision(best_enh_gear, best_enh_cost, self.ui.treeWidget)
                switch_alt_step = SwitchAlt(alt_idx, alts, this_decision)
                this_decision.addChild(switch_alt_step)
                enhance_decision = AttemptEnhancement(best_enh_gear, this_decision, on_fs=fs_lvl)
                this_decision.addChild(enhance_decision)
                these_decisions.append(this_decision)
        # Check loss prevention enhancements
        prevs = self.get_loss_prev_fs_attempt(fs_lvl, strat)
        for lprev in prevs:
                switch_alt_step = SwitchAlt(alt_idx, alts)
                lprev.insertChild(1, switch_alt_step)
                these_loss_prev_dec.append(lprev)

        return these_fs_decisions, these_decisions, these_loss_prev_dec

    def insert_after_swap(self, insert_me, decision):
        for i in range(0, decision.childCount()):
            child = decision.child(i)
            if isinstance(child, SwitchAlt):
                decision.insertChild(i + 1, insert_me)
                return i+1
        decision.insertChild(0, insert_me)
        return 0

    def validate(self):
        settings = self.frmMain.model.settings
        alts = settings[settings.P_ALTS]

        if self.frmMain.strat_solution is None:
            self.frmMain.show_warning_msg('Cannot calculate strategy. Check fail stacking and enhancement equipment.')
            self.ui.spinFS.setEnabled(False)
            return False

        if len(alts) <= 0:
            self.frmMain.show_warning_msg('You must have at least one alt/toon registered to do this.')
            self.ui.spinFS.setEnabled(False)
            return False
        else:
            self.ui.spinFS.setEnabled(True)
            return True

    def decide(self):
        if not self.validate():
            return
        frmMain = self.frmMain
        model:Enhance_model  = frmMain.model
        settings = model.settings
        alts = settings[settings.P_ALTS]
        enhance_me = settings[settings.P_ENHANCE_ME]
        s_valks = settings[settings.P_VALKS]
        s_naderr = settings[settings.P_NADERR_BAND]

        min_fs = model.get_min_fs()
        strat: StrategySolution = self.frmMain.strat_solution

        decisions = []
        fs_decisions = []
        loss_prev_dec = []
        ground_up_dec = []

        alt_dict = {}
        for i, a in enumerate(alts):
            num_fs = max(a[2], min_fs)
            if num_fs not in alt_dict:
                alt_dict[num_fs] = (i, a[0], a[1])

        found_mins = False

        for fs_lvl, pack in alt_dict.items():
            if fs_lvl <= min_fs and not found_mins:
                fs_lvl = min_fs
                alt_idx, alt_pic, alt_name = alt_dict[min_fs]

                this_decision = self.get_fs_attempt(min_fs, strat)
                if this_decision is not None:
                    for i in range(0, this_decision.childCount()):
                        child = this_decision.child(i)
                        if isinstance(child, StackFails):
                            child.set_alt_idx(alt_idx)

                    switch_alt_step = SwitchAlt(alt_idx, alts)
                    this_decision.insertChild(0, switch_alt_step)
                    ground_up_dec.append(this_decision)

                loss_decs = self.get_loss_prev_fs_attempt(fs_lvl, strat)
                if loss_decs is not None:
                    for loss_dec in loss_decs:
                        for i in range(0, loss_dec.childCount()):
                            child = loss_dec.child(i)
                            if isinstance(child, StackFails):
                                child.set_alt_idx(alt_idx)
                                break
                        switch_alt_step = SwitchAlt(alt_idx, alts)
                        loss_dec.insertChild(1, switch_alt_step)
                        loss_prev_dec.append(loss_dec)

                for valk_lvl in s_valks:
                    if valk_lvl not in alt_dict:  # If an alt has this exact stack then don't valks
                        these_fs_decisions, these_decisions, these_loss_prev_dec = self.check_out_fs_lvl(valk_lvl+min_fs, alt_idx, alts,
                                                                                                         strat)
                        for this_decision in these_fs_decisions:
                            this_decision.set_cost(this_decision.cost-1)
                            valks_step = ValksFailStack(valk_lvl, alt_idx=alt_idx)
                            self.insert_after_swap(valks_step, this_decision)
                            fs_decisions.append(this_decision)

                        for this_decision in these_decisions:
                            this_decision.set_cost(this_decision.cost - 1)
                            valks_step = ValksFailStack(valk_lvl, alt_idx=alt_idx)
                            self.insert_after_swap(valks_step, this_decision)
                            decisions.append(this_decision)

                        for this_decision in these_loss_prev_dec:
                            this_decision.set_cost(this_decision.cost - 1)
                            valks_step = ValksFailStack(valk_lvl, alt_idx=alt_idx)
                            self.insert_after_swap(valks_step, this_decision)
                            loss_prev_dec.append(this_decision)


                found_mins = True
            else:
                alt_idx,alt_pic,alt_name = pack
                alt = alts[alt_idx]
                fs_lvl = alt[2]  # TODO: This fail stack val cannot be larger then the global fs limit
                these_fs_decisions, these_decisions, these_loss_prev_dec = self.check_out_fs_lvl(fs_lvl, alt_idx,alts,
                                                                                                 strat)
                fs_decisions.extend(these_fs_decisions)
                decisions.extend(these_decisions)
                loss_prev_dec.extend(these_loss_prev_dec)

        del pack
        del alt_idx
        del alt_name
        del alt_pic
        alt_idx = -1
        for fs_lvl in [x for x in s_naderr if x not in alt_dict]:
            if fs_lvl <= min_fs and not found_mins:  # want this to carry over from before. Just one ground up stack
                fs_lvl = min_fs
                this_decision = self.get_fs_attempt(min_fs, strat)
                if this_decision is not None:
                    for i in range(0, this_decision.childCount()):
                        child = this_decision.child(i)
                        if isinstance(child, StackFails):
                            child.set_alt_idx(alt_idx)

                    switch_alt_step = SwitchAlt(alt_idx, None)
                    this_decision.insertChild(0, switch_alt_step)
                    this_decision.insertChild(1, NaderrsBand(fs_lvl))
                    ground_up_dec.append(this_decision)

                loss_decs = self.get_loss_prev_fs_attempt(fs_lvl, strat)
                if loss_decs is not None:
                    for loss_dec in loss_decs:
                        for i in range(0, loss_dec.childCount()):
                            child = loss_dec.child(i)
                            if isinstance(child, StackFails):
                                child.set_alt_idx(alt_idx)
                                break
                        switch_alt_step = SwitchAlt(alt_idx, alts)
                        loss_dec.insertChild(1, switch_alt_step)
                        this_decision.insertChild(2, NaderrsBand(fs_lvl))
                        loss_prev_dec.append(loss_dec)

                found_mins = True
            else:
                these_fs_decisions, these_decisions, these_loss_prev_dec = self.check_out_fs_lvl(fs_lvl, -1, None,
                                                                                                 strat)
                for dec in these_fs_decisions:
                    self.insert_after_swap(NaderrsBand(fs_lvl), dec)
                    fs_decisions.append(dec)

                for dec in these_decisions:
                    self.insert_after_swap(NaderrsBand(fs_lvl), dec)
                    decisions.append(dec)

                for dec in these_loss_prev_dec:
                    self.insert_after_swap(NaderrsBand(fs_lvl), dec)
                    loss_prev_dec.append(dec)


        last_book = 0
        avail_fs = [x for x in alt_dict.keys()] + s_naderr
        if len(avail_fs) > 0 and min_fs < min(avail_fs):
            for book_s in blk_smth_scrt_book.keys():
                for fs_lvl, pack in alt_dict.items():
                    if fs_lvl > min_fs and book_s >= fs_lvl and fs_lvl > last_book:
                        cost = blk_smth_scrt_book[book_s]
                        alt_idx, alt_pic, alt_name = pack

                        this_decision = self.get_fs_attempt(min_fs, strat, only_real=True)
                        if this_decision is not None:
                            for i in range(0, this_decision.childCount()):
                                child = this_decision.child(i)
                                if isinstance(child, StackFails):
                                    child.set_alt_idx(alt_idx)

                            switch_alt_step = SwitchAlt(alt_idx, alts)
                            this_decision.insertChild(0, switch_alt_step)
                            this_decision.set_cost(this_decision.cost + cost)
                            bsb = UseBlacksmithBook(book_s, alt_idx=alt_idx)
                            this_decision.insertChild(1, bsb)
                            ground_up_dec.append(this_decision)
                            ground_up_dec.append(this_decision)

                        loss_decs = self.get_loss_prev_fs_attempt(fs_lvl, strat)
                        if loss_decs is not None:
                            for loss_dec in loss_decs:
                                for i in range(0, loss_dec.childCount()):
                                    child = loss_dec.child(i)
                                    if isinstance(child, StackFails):
                                        child.set_alt_idx(alt_idx)
                                        break
                                switch_alt_step = SwitchAlt(alt_idx, alts)
                                loss_dec.insertChild(1, switch_alt_step)
                                loss_dec.set_cost(loss_dec.cost + cost)
                                bsb = UseBlacksmithBook(book_s, alt_idx=alt_idx)
                                loss_dec.insertChild(2, bsb)
                                ground_up_dec.append(loss_dec)

                        for valk_lvl in s_valks:
                            if valk_lvl not in alt_dict:  # If an alt has this exact stack then don't valks
                                these_fs_decisions, these_decisions, these_loss_prev_dec = self.check_out_fs_lvl(
                                    valk_lvl + min_fs, alt_idx, alts, strat)
                                for this_decision in these_fs_decisions:
                                    this_decision.set_cost(this_decision.cost - 1)
                                    valks_step = ValksFailStack(valk_lvl, alt_idx=alt_idx)
                                    idx_ = self.insert_after_swap(valks_step, this_decision)
                                    bsb = UseBlacksmithBook(book_s, alt_idx=alt_idx)
                                    this_decision.insertChild(idx_, bsb)
                                    this_decision.set_cost(this_decision.cost + cost)
                                    ground_up_dec.append(this_decision)

                                for this_decision in these_decisions:
                                    this_decision.set_cost(this_decision.cost - 1)
                                    valks_step = ValksFailStack(valk_lvl, alt_idx=alt_idx)
                                    idx_ = self.insert_after_swap(valks_step, this_decision)
                                    bsb = UseBlacksmithBook(book_s, alt_idx=alt_idx)
                                    this_decision.insertChild(idx_, bsb)
                                    this_decision.set_cost(this_decision.cost + cost)
                                    ground_up_dec.append(this_decision)

                                for this_decision in these_loss_prev_dec:
                                    this_decision.set_cost(this_decision.cost - 1)
                                    valks_step = ValksFailStack(valk_lvl, alt_idx=alt_idx)
                                    idx_ = self.insert_after_swap(valks_step, this_decision)
                                    bsb = UseBlacksmithBook(book_s, alt_idx=alt_idx)
                                    this_decision.insertChild(idx_, bsb)
                                    this_decision.set_cost(this_decision.cost + cost)
                                    ground_up_dec.append(this_decision)
                last_book = book_s

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
        frmObj.treeWidget.resizeColumnToContents(1)
        self.set_step()

    def set_step(self):
        self.update_current_step()
        self.clear_button_box()
        frmObj = self.ui
        current_decision: Decision = frmObj.treeWidget.topLevelItem(0)
        this_step: DecisionStep = current_decision.child(current_decision.current_step)
        frmObj.lblInfo.setText(this_step.get_description())
        for btn in this_step.get_buttons(self):
            frmObj.widButtonBox.layout().addWidget(btn)

    def clear_button_box(self):
        layout = self.ui.widButtonBox.layout()
        k:QtWidgets.QWidget = layout.takeAt(0)
        while k is not None:
            k.widget().deleteLater()
            k = layout.takeAt(0)

    def update_current_step(self):
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
            track_gear = None
            if frmObj.chkFollowTrack.isChecked():
                track_gear = current_decision.gear_item
            self.abort_decision_clicked()
            if track_gear is not None:
                for i in range(frmObj.treeWidget.topLevelItemCount()):
                    child = frmObj.treeWidget.topLevelItem(i)
                    if child.gear_item is track_gear:
                        frmObj.treeWidget.itemWidget(child, 0).click()
                        break

    def abort_decision_clicked(self):

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
        self.clear_button_box()
        self.selected_decision = None
        if self.decisions is None or len(self.decisions) <= 0:
            self.decisions = self.decide()

        for i in range(frmObj.treeWidget.topLevelItemCount()):
            frmObj.treeWidget.takeTopLevelItem(0)

        self.cmd_buttons.clear()
        self.ui.lblInfo.clear()

        on_alt = frmObj.chkStayOnAlt.isChecked()

        for decision in self.decisions:
            proceed = True
            if on_alt:
                for i in range(decision.childCount()):
                    child = decision.child(i)
                    if isinstance(child, SwitchAlt):
                        if not child.alt_idx == frmObj.cmbalts.currentIndex():
                            proceed = False
            if proceed:
                frmObj.treeWidget.addTopLevelItem(decision)
                cmd_button = cmdChoseDecision('Accept', decision)
                cmd_button.clicked.connect(self.decision_clicked)
                self.cmd_buttons.append(cmd_button)
                frmObj.treeWidget.setItemWidget(decision, 0, cmd_button)

        frmObj.treeWidget.sortItems(2, Qt.SortOrder.AscendingOrder)
        frmObj.treeWidget.resizeColumnToContents(1)

    def invalidate(self):
        frmObj = self.ui
        self.decisions = None
        self.selected_decision = None
        for i in range(frmObj.treeWidget.topLevelItemCount()):
            frmObj.treeWidget.takeTopLevelItem(0)

        self.cmd_buttons.clear()
        self.ui.lblInfo.clear()
        self.bs_wid.set_pixmap(self.black_spirits[BS_HMM])

    def get_cur_fs(self):
        return self.ui.spinFS.value()


class LossPreventionEnhancement(DecisionStep):
    DESR = 'Go for this item even if {} is ~{:,} silver more effiecent? Do this for items that are not effiecent in gerneal or when you need to rush. Loss prevention: {}'
    def __init__(self, this_gear, sub_gear, *args, cost_diff=None, loss_prev=None):
        super(LossPreventionEnhancement, self).__init__(*args)
        self.gear = this_gear
        self.sub_gear = sub_gear
        self.update_text()
        self.ok = False
        self.cost_diff = cost_diff
        self.loss_prev = loss_prev

    def set_loss_prev(self, loss_prev):
        self.loss_prev = loss_prev

    def update_text(self):
        this_gear = self.gear
        sub_gear = self.sub_gear
        self.setText(1, 'Consider {} instead of {}'.format(sub_gear.get_full_name(), this_gear.get_full_name()))

    def set_cost_diff(self, cost_diff):
        self.cost_diff = cost_diff

    def acceptability_criteria(self, dlg_compact):
        return self.ok

    def get_buttons(self, dlg_compact: Dlg_Compact):
        cmdSucceed = QtWidgets.QPushButton('Okay')

        def cmdSucceed_clicked():
            self.ok = True
            dlg_compact.update_current_step()

        cmdSucceed.clicked.connect(cmdSucceed_clicked)

        return[cmdSucceed]

    def get_description(self):
        return self.DESR.format(self.sub_gear.get_full_name(), int(round(self.cost_diff)), self.loss_prev)


class AttemptEnhancement(DecisionStep):
    def __init__(self, this_gear, *args, on_fs=None):
        super(AttemptEnhancement, self).__init__(*args)
        self.gear:Gear = this_gear
        self.on_fs = on_fs
        self.update_txt()
        self.attempt_made = False
        self.fs_cost = 0

    def set_gear(self, gear:Gear):
        self.gear = gear
        self.update_txt()

    def set_on_fs(self, on_fs):
        self.on_fs = on_fs
        self.update_txt()

    def set_fs_cost(self, fs_cost):
        self.fs_cost = fs_cost

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
            dlg_compact.invalidate_decisions()

        def cmdFail_clicked():
            self.attempt_made = True
            gain = self.gear.fs_gain()
            dlg_compact.frmMain.simulate_fail_gear(self.gear)
            dlg_compact.ui.spinFS.setValue(dlg_compact.ui.spinFS.value()+gain)
            dlg_compact.bs_wid.set_pixmap(dlg_compact.black_spirits[BS_AW_MAN])
            dlg_compact.invalidate_decisions()

        dlg_compact.bs_wid.set_pixmap(dlg_compact.black_spirits[BS_FACE_PALM])

        cmdSucceed.clicked.connect(cmdSucceed_clicked)
        cmdFail.clicked.connect(cmdFail_clicked)

        return[cmdFail, cmdSucceed]


class SwitchAlt(DecisionStep):
    def __init__(self, alt_idx, alts, *args):
        super(SwitchAlt, self).__init__(*args)
        self.alt_idx = alt_idx
        self.alts = alts
        self.setText(1, 'Switch to {} alt'.format(self.get_name()))
        self.tagged = False

    def get_name(self):
        alt_idx= self.alt_idx
        if alt_idx > -1:
            return self.alts[self.alt_idx][1]
        else:
            return "~ANY~"

    def get_picture_path(self):
        if self.alts is None:
            return None
        return self.alts[self.alt_idx][0]

    def get_fs(self):
        if self.alts is None:
            return None
        return self.alts[self.alt_idx][2]

    def get_buttons(self, dlg_compact: Dlg_Compact):
        cmdSwitch = QtWidgets.QPushButton('Swap')
        def cmdSwitch_clicked():
            if self.alt_idx > -1:
                dlg_compact.ui.cmbalts.setCurrentIndex(self.alt_idx)
            else:
                self.tagged = True
                dlg_compact.update_current_step()
        cmdSwitch.clicked.connect(cmdSwitch_clicked)
        return [cmdSwitch]

    def acceptability_criteria(self, dlg_compact: Dlg_Compact):
        return dlg_compact.current_alt == self.alt_idx or (self.alt_idx == -1 and self.tagged)


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
            valks = settings[settings.P_VALKS]
            num_now = valks[self.fs_lvl] - 1
            if num_now > 0:
                valks[self.fs_lvl] = num_now
            else:
                valks.pop(self.fs_lvl)
            settings.invalidate()
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
            model: Enhance_model = dlg_compact.frmMain.model
            settings = model.settings
            dlg_compact.ui.spinFS.setValue(settings[settings.P_QUEST_FS_INC])
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
        flag &= dlg_compact.get_cur_fs() <= model.get_min_fs()
        return flag

    def get_buttons(self, dlg_compact: Dlg_Compact):
        cmdSucceed = QtWidgets.QPushButton('Okay')


        def cmdSucceed_clicked():
            model: Enhance_model = dlg_compact.frmMain.model
            settings = model.settings
            cur_fs = dlg_compact.ui.spinFS.value() - model.get_min_fs()
            valks = settings[settings.P_VALKS]
            if cur_fs in valks:
                valks[cur_fs] += 1
            else:
                valks[cur_fs] = 1
            settings.invalidate()
            dlg_compact.ui.spinFS.setValue(model.get_min_fs())
            dlg_compact.invalidate_decisions()


        cmdSucceed.clicked.connect(cmdSucceed_clicked)

        return[cmdSucceed]

    def get_description(self):
        return 'Buy a Blacksmith\'s Secret Book - {} from a blacksmith and go to BS->Enahancment->Extract->Blacksmith\'s Secret Book'.format(self.fs_lvl)


class NaderrsBand(DecisionStep):
    def __init__(self, fs_lvl, *args):
        super(NaderrsBand, self).__init__(*args)
        self.fs_lvl = 0
        self.set_fs_lvl(fs_lvl)

    def set_fs_lvl(self, fs_lvl):
        self.fs_lvl = fs_lvl
        self.setText(1, 'Swap with Naderr\'s Band (+{})'.format(fs_lvl))

    def acceptability_criteria(self, dlg_compact):
        model: Enhance_model = dlg_compact.frmMain.model
        return dlg_compact.get_cur_fs() == self.fs_lvl

    def get_buttons(self, dlg_compact: Dlg_Compact):
        cmdSucceed = QtWidgets.QPushButton('Okay')

        def cmdSucceed_clicked():
            model: Enhance_model = dlg_compact.frmMain.model
            settings = model.settings
            curr = dlg_compact.ui.spinFS.value()
            dlg_compact.ui.spinFS.setValue(max(self.fs_lvl, model.get_min_fs()))
            naderr = settings[settings.P_NADERR_BAND]
            nad_idx = naderr.index(self.fs_lvl)
            naderr[nad_idx] = curr
            settings.invalidate()
            dlg_compact.invalidate_decisions()

        cmdSucceed.clicked.connect(cmdSucceed_clicked)

        return[cmdSucceed]
