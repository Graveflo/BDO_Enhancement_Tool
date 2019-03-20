#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
# TODO: Make it obvious when updates are needed to the system
# TODO: Maybe update the list before the enhancement strat is created
# TODO: Remove items
# TODO: Graphs
# TODO: Max number of uses for failstacking item
# TODO: Replace lists with generators
# TODO: Make graphs and menu items work

from Forms.Main_Window import Ui_MainWindow
from dlgAbout import dlg_About
from common import Qt_common, relative_path_covnert, gear_types, enumerate_gt_lvl, Classic_Gear, Smashable, \
    DEFAULT_SETTINGS_PATH
from model import Enhance_model, Invalid_FS_Parameters

import numpy, types, os
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView, QSpinBox, QFileDialog
from PyQt5.QtCore import pyqtSignal, Qt
from scipy.stats import binom

QBlockSig = Qt_common.QBlockSig
NoScrollCombo = Qt_common.NoScrollCombo
clear_table = Qt_common.clear_table
dlg_format_list = Qt_common.dlg_format_list

QTableWidgetItem_NoEdit = Qt_common.QTableWidgetItem_NoEdit
STR_TW_GEAR = 'gear_item'
STR_COST_ERROR = 'Cost must be a number.'
MONNIES_FORMAT = "{:,.0f}"
STR_TWO_DEC_FORMAT = "{:.2f}"
STR_PERCENT_FORMAT = '{:.0f}%'
STR_INFINITE = 'INF'


def numeric_less_than(self, y):
    return float(self.text().replace(',', '').replace('%','')) <= float(y.text().replace(',', '').replace('%',''))


class Frm_Main(Qt_common.lbl_color_MainWindow):
    def __init__(self, app):
        super(Frm_Main, self).__init__()
        frmObj = Ui_MainWindow()
        frmObj.setupUi(self)
        self.ui = frmObj
        self.app = app

        model = Enhance_model()
        self.model = model

        pix = QPixmap(relative_path_covnert('title.png'))
        frmObj.label.setPixmap(pix)

        self.clear_data()

        self.about_win = dlg_About(self)

        frmObj.actionAbout.triggered.connect(self.about_win.show)
        frmObj.actionExit.triggered.connect(app.exit)
        frmObj.actionLoad_Info.triggered.connect(self.open_file_dlg)
        frmObj.actionSave_Info.triggered.connect(self.save_file_dlg)

        def cmdEquipRemove_clicked():
            tmodel = self.model
            tw = frmObj.table_Equip

            effect_list = [i.row() for i in tw.selectedItems()]
            effect_list.sort()
            effect_list.reverse()

            for i in effect_list:
                thic = tw.item(i, 0).__dict__[STR_TW_GEAR]
                try:
                    tmodel.enhance_me.remove(thic)
                    tmodel.invalidate_enahce_list()
                except ValueError:
                    pass
                try:
                    tmodel.r_enhance_me.remove(thic)
                except ValueError:
                    pass
                tw.removeRow(i)


        def cmdFSRemove_clicked():
            tmodel = self.model
            tw = frmObj.table_FS

            effect_list = [i.row() for i in tw.selectedItems()]
            effect_list.sort()
            effect_list.reverse()

            for i in effect_list:
                thic = tw.item(i, 0).__dict__[STR_TW_GEAR]
                try:
                    tmodel.fail_stackers.remove(thic)
                    tmodel.invalidate_failstack_list()
                except ValueError:
                    pass
                try:
                    tmodel.r_fail_stackers.remove(thic)
                except ValueError:
                    pass
                try:
                    del tmodel.fail_stackers_counts[thic]
                except KeyError:
                    pass
                tw.removeRow(i)

        frmObj.cmdEquipRemove.clicked.connect(cmdEquipRemove_clicked)
        frmObj.cmdFSRemove.clicked.connect(cmdFSRemove_clicked)

        frmObj.cmdFSAdd.clicked.connect(self.cmdFSAdd_clicked)
        frmObj.cmdEquipAdd.clicked.connect(self.cmdEquipAdd_clicked)
        frmObj.table_FS.cellChanged.connect(self.table_FS_cellChanged)
        frmObj.table_Equip.cellChanged.connect(self.table_Equip_cellChanged)
        frmObj.cmdFSRefresh.clicked.connect(self.cmdFSRefresh_clicked)
        frmObj.cmdFSEdit.clicked.connect(self.cmdFSEdit_clicked)
        frmObj.cmdFS_Cost_Clear.clicked.connect(self.cmdFS_Cost_Clear_clicked)
        frmObj.cmdEquipCost.clicked.connect(self.cmdEquipCost_clicked)
        frmObj.cmdStrat_go.clicked.connect(self.cmdStrat_go_clicked)
        frmObj.table_FS_Cost.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        frmObj.table_Equip.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        frmObj.table_FS.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        frmObj.table_Strat_FS.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        frmObj.table_Strat.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        frmObj.table_Strat_Equip.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        frmObj.cmd_Strat_Graph.clicked.connect(self.cmd_Strat_Graph_clicked)
        frmObj.table_Equip.setSortingEnabled(True)
        frmObj.table_FS.setSortingEnabled(True)

    def clear_data(self):
        self.eh_c = None
        self.fs_exception_boxes = {}

    def ensurePolished(self):
        super(Frm_Main, self).ensurePolished()
        self.adjust_equip_splitter()

    def closeEvent(self, *args, **kwargs):
        model = self.model

        model.save_to_file()
        super(Frm_Main, self).closeEvent(*args, **kwargs)

    def dragEnterEvent(self, e):
        """
        When the user drags anything over the window this event triggers. It accepts 'text/uri-list' for a list of files.
        :param e: EventParams
        :return: None
        """
        if e.mimeData().hasFormat('text/uri-list'):
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, *event):
        """
        This event fires when an accepted drop is actuated.
        :param event:
        :return: None
        """
        super(Frm_Main, self).dropEvent(*event)
        files = [x.toLocalFile() for x in list(event[0].mimeData().urls())]
        this_file = files[0]
        if os.path.isfile(this_file):
            try:
                self.load_file(this_file)
            except IOError:
                self.show_warning_msg('Cannot load file. A settings JSON file is expected.')

    def adjust_equip_splitter(self):
        frmObj = self.ui
        tw = self.ui.table_Strat

        tot = numpy.sum(frmObj.splitter.sizes())
        h_ = tw.horizontalHeader().length() + 2
        if tw.verticalScrollBar().isVisible():
            h_ += tw.verticalScrollBar().width()
        frmObj.splitter.setSizes([h_, tot - h_])

    def cmd_Strat_Graph_clicked(self):
        model = self.model
        eh_c = self.eh_c

        if eh_c is None:
            self.show_warning_msg('Need to calculate the strategy first.')
            return

        import matplotlib.pyplot as plt

        for i, plowt in enumerate(eh_c):
            item = model.enhance_me[i]
            ploot = plt.plot(range(0, 121), plowt, label=item.name)
            plt.axvline(x=numpy.argmin(item.enhance_cost(model.cum_fs_cost)[item.gear_type.lvl_map[item.enhance_lvl]]),
                        color=ploot[0].get_color())
        plt.legend(loc='upper left')
        plt.show()

    def cmdStrat_go_clicked(self):
        model = self.model
        frmObj = self.ui
        tw = frmObj.table_Strat

        for row in range(0, tw.rowCount()):
            tw.removeRow(0)

        if not len(model.cum_fs_cost) > 0:
            self.cmdFSRefresh_clicked()
        if not len(model.equipment_costs) > 0:
            self.cmdEquipCost_clicked()

        fs_c, eh_c = model.calcEnhances()
        fs_c_T = fs_c.T
        eh_c_T = eh_c.T

        tw_eh = frmObj.table_Strat_Equip
        tw_fs = frmObj.table_Strat_FS

        def tw_selectionChanged(row_obj):
            if row_obj is None:
                # null selection is possible
                return
            p_int = row_obj.row()
            this_vec = eh_c_T[p_int]
            this_sort = numpy.argsort(this_vec)

            with QBlockSig(tw_eh):
                clear_table(tw_eh)
            with QBlockSig(tw_fs):
                clear_table(tw_fs)
            for i in range(0, len(this_vec)):
                this_sorted_idx = this_sort[i]
                this_sorted_item = model.enhance_me[this_sorted_idx]
                tw_eh.insertRow(i)
                twi = QTableWidgetItem(str(this_sorted_item.name))
                twi.__dict__['dis_gear'] = this_sorted_item
                tw_eh.setItem(i, 0, twi)
                twi = QTableWidgetItem(MONNIES_FORMAT.format(this_vec[this_sorted_idx]))
                tw_eh.setItem(i, 1, twi)

                eh_idx = this_sorted_item.get_enhance_lvl_idx()
                cost_vec_l = this_sorted_item.cost_vec[eh_idx]
                idx_ = numpy.argmin(cost_vec_l)
                opti_val = cost_vec_l[idx_]
                optimality = (1.0 + ((opti_val - cost_vec_l[p_int]) / opti_val)) * 100
                twi = QTableWidgetItem(STR_PERCENT_FORMAT.format(optimality))
                tw_eh.setItem(i, 2, twi)

                this_fail_map = numpy.array(this_sorted_item.gear_type.map)[eh_idx][p_int]
                avg_num_attempt = numpy.divide(1.0, this_fail_map)
                avg_num_fails = avg_num_attempt - 1
                twi = QTableWidgetItem(STR_TWO_DEC_FORMAT.format(avg_num_fails))
                tw_eh.setItem(i, 3, twi)

                confidence = binom.cdf(1, int(round(avg_num_attempt)), this_fail_map) * 100
                twi = QTableWidgetItem(STR_PERCENT_FORMAT.format(confidence))
                tw_eh.setItem(i, 4, twi)

            this_vec = fs_c_T[p_int]
            this_sort = numpy.argsort(this_vec)

            for i in range(0, len(this_vec)):
                this_sorted_idx = this_sort[i]
                this_sorted_item = model.fail_stackers[this_sorted_idx]
                tw_fs.insertRow(i)
                twi = QTableWidgetItem(str(this_sorted_item.name))
                twi.__dict__['dis_gear'] = this_sorted_item
                tw_fs.setItem(i, 0, twi)
                twi = QTableWidgetItem(MONNIES_FORMAT.format(this_vec[this_sorted_idx]))
                tw_fs.setItem(i, 1, twi)

                opti_val = this_vec[this_sort[0]]
                optimality = (1.0 - ((opti_val - this_vec[this_sorted_idx]) / opti_val)) * 100
                twi = QTableWidgetItem(STR_PERCENT_FORMAT.format(optimality))
                tw_fs.setItem(i, 2, twi)
        try:
            tw.currentItemChanged.disconnect()
        except TypeError:
            # This happens the first time because nothing is connected.
            pass
        tw.currentItemChanged.connect(tw_selectionChanged)

        for i, ev in enumerate(eh_c_T):
            fv = fs_c_T[i]
            tw.insertRow(i)
            twi = QTableWidgetItem(str(i))
            tw.setItem(i, 0, twi)
            ev_min = numpy.argmin(ev)
            fv_min = numpy.argmin(fv)
            if fv[fv_min] > ev[ev_min]:
                twi = QTableWidgetItem(model.enhance_me[ev_min].name)
                twi2 = QTableWidgetItem("YES")
            else:
                twi = QTableWidgetItem(model.fail_stackers[fv_min].name)
                twi2 = QTableWidgetItem("NO")
            tw.setItem(i, 1, twi)
            tw.setItem(i, 2, twi2)

        self.eh_c = eh_c
        self.adjust_equip_splitter()


    def cmdEquipCost_clicked(self):
        model = self.model
        frmObj = self.ui
        tw = frmObj.table_Equip

        model.calc_equip_costs()
        for i in range(0, tw.rowCount()):
            this_head = tw.item(i, 0)
            this_gear = this_head.gear_item
            eh_idx = this_gear.get_enhance_lvl_idx()
            cost_vec_l = this_gear.cost_vec[eh_idx]
            idx_ = numpy.argmin(cost_vec_l)
            twi = QTableWidgetItem(str(idx_))
            twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
            tw.setItem(i, 4, twi)
            twi = QTableWidgetItem(MONNIES_FORMAT.format(cost_vec_l[idx_]))
            twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
            tw.setItem(i, 5, twi)

            this_fail_map = numpy.array(this_gear.gear_type.map)[eh_idx]
            avg_num_fails = numpy.divide(numpy.ones(this_fail_map.shape), this_fail_map) - 1
            twi = QTableWidgetItem(STR_TWO_DEC_FORMAT.format(avg_num_fails[idx_]))
            twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
            tw.setItem(i, 6, twi)
            try:
                twi = QTableWidgetItem(str(this_gear.using_memfrags))
                tw.setItem(i, 7, twi)
            except AttributeError:
                pass

    def cmdFS_Cost_Clear_clicked(self):
        model = self.model
        frmObj = self.ui
        tw = frmObj.table_FS_Cost

        def kill(x):
            try:
                del model.fs_exceptions[x]
            except KeyError:
                pass

        map(kill, set([r.row() for r in tw.selectedIndexes()]))
        frmObj.cmdFSRefresh.click()

    def add_custom_fs_combobox(self, model, tw, fs_exception_boxes, row_idx):
        this_cmb = NoScrollCombo(tw)
        this_cmb.setFocusPolicy(Qt.ClickFocus)
        fs_exception_boxes[row_idx] = this_cmb
        this_item = model.fs_exceptions[row_idx]
        def this_cmb_currentIndexChanged(indx):
            model.fs_exceptions[row_idx] = model.fail_stackers[indx]

        for i, gear in enumerate(model.fail_stackers):
            this_cmb.addItem(gear.name)
            if gear is this_item:
                this_cmb.setCurrentIndex(i)
        this_cmb.currentIndexChanged.connect(this_cmb_currentIndexChanged)
        tw.setCellWidget(row_idx, 1, this_cmb)

    def cmdFSEdit_clicked(self):
        frmObj = self.ui
        model = self.model
        fs_exception_boxes = self.fs_exception_boxes
        tw = frmObj.table_FS_Cost

        selected_rows = set([r.row() for r in tw.selectedIndexes()])

        for indx in selected_rows:
            model.fs_exceptions[indx] = tw.item(indx, 0).dis_gear
            self.add_custom_fs_combobox(model, tw, fs_exception_boxes, indx)

    def cmdFSRefresh_clicked(self):
        frmObj = self.ui
        model = self.model
        try:
            model.calcFS()
        except Invalid_FS_Parameters as e:
            self.show_critical_error(str(e))
            return

        tw = frmObj.table_FS_Cost
        with QBlockSig(tw):
            clear_table(tw)
        fs_items = model.fs_items
        fs_cost = model.fs_cost
        cum_fs_cost = model.cum_fs_cost
        cum_fs_probs = model.cum_fs_probs
        fs_probs = model.fs_probs
        fs_exception_boxes = self.fs_exception_boxes

        for i, this_gear in enumerate(fs_items):
            rc = tw.rowCount()
            tw.insertRow(rc)
            twi = QTableWidgetItem(str(i))
            twi.__dict__['dis_gear'] = this_gear
            tw.setItem(rc, 0, twi)
            if i in model.fs_exceptions:
                self.add_custom_fs_combobox(model, tw, fs_exception_boxes, i)
            else:
                twi = QTableWidgetItem(this_gear.name)
                tw.setItem(rc, 1, twi)
            twi = QTableWidgetItem(MONNIES_FORMAT.format(fs_cost[i]))
            tw.setItem(rc, 2, twi)
            twi = QTableWidgetItem(MONNIES_FORMAT.format(cum_fs_cost[i]))
            tw.setItem(rc, 3, twi)
            twi = QTableWidgetItem(str(fs_probs[i]))
            tw.setItem(rc, 4, twi)
            twi = QTableWidgetItem(str(cum_fs_probs[i]))
            tw.setItem(rc, 5, twi)
        frmObj.cmdEquipCost.setEnabled(True)

    def table_cellChanged_proto(self, row, col, tw, this_gear):
        tw = self.sender()
        str_this_item = tw.item(row, col).text()

        if col == 0:
            this_gear.name = str_this_item
        elif col == 2:
            try:
                this_gear.set_cost(float(str_this_item))
            except ValueError:
                self.show_warning_msg('Cost must be a number.')

    def table_Equip_cellChanged(self, row, col):
        model = self.model
        tw = self.sender()

        t_item = tw.item(row, 0)
        this_gear = t_item.gear_item
        if col == 0:
            if t_item.checkState() == Qt.Checked:
                try:
                    model.r_enhance_me.remove(this_gear)
                except ValueError:
                    pass
                model.enhance_me.append(this_gear)
                model.enhance_me = list(set(model.enhance_me))
            else:
                try:
                    model.enhance_me.remove(this_gear)
                except ValueError:
                    pass
                model.r_enhance_me.append(this_gear)
                model.r_enhance_me = list(set(model.r_enhance_me))

        self.table_cellChanged_proto(row, col, tw, this_gear)

    def table_FS_cellChanged(self, row, col):
        model = self.model
        tw = self.sender()

        t_item = tw.item(row, 0)
        this_gear = t_item.gear_item
        if col == 0:
            if t_item.checkState() == Qt.Checked:
                try:
                    model.r_fail_stackers.remove(this_gear)
                except ValueError:
                    pass
                model.fail_stackers.append(this_gear)
                model.fail_stackers = list(set(model.fail_stackers))
            else:
                try:
                    model.fail_stackers.remove(this_gear)
                except ValueError:
                    pass
                model.r_fail_stackers.append(this_gear)
                model.r_fail_stackers = list(set(model.r_fail_stackers))

        self.table_cellChanged_proto(row, col, tw, this_gear)

    def table_add_gear(self, edit_func, tw, this_gear, add_fun=None, check_state=Qt.Checked):
        model = self.model

        rc = tw.rowCount()
        tw.insertRow(rc)

        cmb_gt = NoScrollCombo(tw)
        cmb_enh = NoScrollCombo(tw)

        for i,key in enumerate(gear_types.keys()):
            cmb_gt.addItem(key)
            if key == this_gear.gear_type.name:
                cmb_gt.setCurrentIndex(i)
        gtype_s = cmb_gt.currentText()

        sorted_list = gear_types[gtype_s].lvl_map.keys()
        sorted_list.sort(key=enumerate_gt_lvl)

        for i, key in enumerate(sorted_list):
            cmb_enh.addItem(key)
            if key == this_gear.enhance_lvl:
                cmb_enh.setCurrentIndex(i)

        name = this_gear.name
        f_twi = QTableWidgetItem(name)
        f_twi.setCheckState(check_state)
        f_twi.__dict__[STR_TW_GEAR] = this_gear
        if add_fun is not None:
            add_fun(this_gear)

        def cmb_gt_currentTextChanged(str_picked):
            current_enhance_string = cmb_enh.currentText()
            new_gt = gear_types[str_picked]
            with QBlockSig(cmb_enh):
                cmb_enh.clear()
                sorted_list = new_gt.lvl_map.keys()
                sorted_list.sort(key=enumerate_gt_lvl)
                for i, key in enumerate(sorted_list):
                    cmb_enh.addItem(key)
                    if key == current_enhance_string:
                        cmb_enh.setCurrentIndex(i)
            this_gear = f_twi.__dict__['gear_item']
            if str_picked.lower().find('accessor') > -1:
                if not isinstance(this_gear, Smashable):
                    old_g = this_gear
                    this_gear = model.generate_gear_obj(item_cost=this_gear.cost, enhance_lvl=cmb_enh.currentText(),
                                                        gear_type=gear_types[str_picked], name=this_gear.name)
                    edit_func(old_g, this_gear)
                else:
                    this_gear.set_gear_params(gear_types[str_picked], cmb_enh.currentText())
            else:
                if not isinstance(this_gear, Classic_Gear):
                    old_g = this_gear
                    this_gear = model.generate_gear_obj(item_cost=this_gear.cost, enhance_lvl=cmb_enh.currentText(),
                                                        gear_type=gear_types[str_picked], name=this_gear.name)
                    edit_func(old_g, this_gear)
                else:
                    this_gear.set_gear_params(gear_types[str_picked], cmb_enh.currentText())
            f_twi.__dict__['gear_item'] = this_gear

        def cmb_enh_currentTextChanged(str_picked):
            # could throw key error
            this_gear = f_twi.__dict__['gear_item']
            try:
                this_gear.set_enhance_lvl(str_picked)
            except KeyError:
                self.show_critical_error('Enhance level does not appear to be valid.')

        with QBlockSig(tw):
            tw.setItem(rc, 0, f_twi)
            tw.setCellWidget(rc, 1, cmb_gt)
            twi = QTableWidgetItem(MONNIES_FORMAT.format(int(round(this_gear.cost))))
            twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
            tw.setItem(rc, 2, twi)
            tw.setCellWidget(rc, 3, cmb_enh)
        cmb_gt.currentTextChanged.connect(cmb_gt_currentTextChanged)
        cmb_enh.currentTextChanged.connect(cmb_enh_currentTextChanged)

    def table_FS_add_gear(self, this_gear, check_state=Qt.Checked, add_fun=None):
        model = self.model
        tw = self.ui.table_FS
        rc = tw.rowCount()
        self.table_add_gear(model.edit_fs_item, tw, this_gear, check_state=check_state, add_fun=add_fun)
        def valueChanged_connect(val):
            if val == 0:
                try:
                    del model.fail_stackers_counts[this_gear]
                except KeyError:
                    pass
            else:
                model.fail_stackers_counts[this_gear] = val
        with QBlockSig(tw):
            thisspin = QSpinBox()
            thisspin.setMaximum(120)
            thisspin.setSpecialValueText(STR_INFINITE)
            try:
                this_val = model.fail_stackers_counts[this_gear]
                thisspin.setValue(this_val)
            except KeyError:
                pass
            thisspin.valueChanged.connect(valueChanged_connect)
            tw.setCellWidget(rc, 4, thisspin)

    def cmdFSAdd_clicked(self, bool_):
        model = self.model

        gear_type = gear_types.items()[0][1]
        enhance_lvl = gear_type.lvl_map.keys()[0]
        this_gear = model.generate_gear_obj(0, enhance_lvl, gear_type)
        self.table_FS_add_gear(this_gear, add_fun=model.add_fs_item)

    def cmdEquipAdd_clicked(self, bool_):
        model = self.model
        frmObj = self.ui
        tw = frmObj.table_Equip

        gear_type = gear_types.items()[0][1]
        enhance_lvl = gear_type.lvl_map.keys()[0]

        this_gear = model.generate_gear_obj(0, enhance_lvl, gear_type)

        self.table_add_gear(model.edit_enhance_item, tw, this_gear, add_fun=model.add_equipment_item)

    def open_file_dlg(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        model = self.model

        if model.current_path is None:
            this_open_path = relative_path_covnert('./')
        else:
            this_open_path = model.current_path
        fmt_list = [('Any', '*'),('JSON File', 'json')]
        fileName, _ = QFileDialog.getOpenFileName(self, "Select Input File", this_open_path,
                                                  dlg_format_list(fmt_list),
                                                  options=options, initialFilter=dlg_format_list([fmt_list[1]]))
        if fileName:
            try:
                self.load_file(fileName)
            except IOError:
                self.show_critical_error('File could not be loaded.')
        else:
            self.ui.statusbar.showMessage('Aborted opening file.')

    def clear_all(self):
        frmObj = self.ui
        self.model = None
        map(lambda x: clear_table(x), [frmObj.table_FS, frmObj.table_Strat, frmObj.table_Equip, frmObj.table_FS_Cost,
                                          frmObj.table_Strat_Equip, frmObj.table_Strat_FS])
        self.clear_data()
        self.model = Enhance_model()

    def save_file_dlg(self):
        show_mess = self.ui.statusbar.showMessage
        model = self.model
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        format_list = [('Any', '*'),('JSON File', 'json')]
        if model.current_path is None:
            save_path = relative_path_covnert('./')
        else:
            save_path = os.path.dirname(model.current_path)
        fileName, _ = QFileDialog.getSaveFileName(self, "Saving", save_path, dlg_format_list(format_list), options=options,
                                                  initialFilter=dlg_format_list([format_list[1]]))
        if fileName:
            model.save_to_file(fileName)
            self.show_green_msg('Saved: ' + fileName)
        else:
            show_mess('Aborted saving.')

    def load_file(self, str_path):
        self.clear_all()
        model = self.model
        frmObj = self.ui

        try:
            self.model.load_from_file(str_path)
        except ValueError:
            self.show_critical_error('Something is wrong with the settings file: ' + str_path)

        self.load_ui_common()

        tw = frmObj.table_Equip
        for gear in model.enhance_me:
            self.table_add_gear(model.edit_enhance_item, tw, gear)
        for gear in model.r_enhance_me:
            self.table_add_gear(model.edit_enhance_item, tw, gear, check_state=Qt.Unchecked)
        for gear in model.fail_stackers:
            self.table_FS_add_gear(gear)
        for gear in model.r_fail_stackers:
            self.table_FS_add_gear(gear, check_state=Qt.Unchecked)

        if len(model.fail_stackers) > 0:
            frmObj.cmdFSRefresh.click()
            if len(model.enhance_me) > 0:
                frmObj.cmdEquipCost.click()

    def load_ui_common(self):
        frmObj = self.ui
        model = self.model
        def cost_mat_gen(unpack):
            txt_box, cost, set_costf, itm_txt = unpack
            txt_box.setText(str(cost))

            def txt_Cost_BlackStone_Armor_textChanged(str_val):
                try:
                    set_costf(str_val)
                    frmObj.statusbar.showMessage('Set '+itm_txt+' cost to: ' + str(str_val))
                except ValueError:
                    self.show_warning_msg(STR_COST_ERROR, silent=True)

            txt_box.textChanged.connect(txt_Cost_BlackStone_Armor_textChanged)

        map(cost_mat_gen, [
            [frmObj.txt_Cost_BlackStone_Armor, model.cost_bs_a, model.set_cost_bs_a, 'Blackstone Armour'],
            [frmObj.txt_Cost_BlackStone_Weapon, model.cost_bs_w, model.set_cost_bs_w, 'Blackstone Weapon'],
            [frmObj.txt_Cost_ConcArmor, model.cost_conc_a, model.set_cost_conc_a, 'Conc Blackstone Armour'],
            [frmObj.txt_Cost_Conc_Weapon, model.cost_conc_w, model.set_cost_conc_w, 'Conc Blackstone Weapon'],
            [frmObj.txt_Cost_Cleanse, model.cost_cleanse, model.set_cost_cleanse, 'Gear Cleanse'],
            [frmObj.txt_Cost_Cron, model.cost_cron, model.set_cost_cron, 'Cron Stone'],
            [frmObj.txt_Cost_MemFrag, model.cost_meme, model.set_cost_meme, 'Memory Fragment'],
        ])


