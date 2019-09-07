#- * -coding: utf - 8 - * -
"""
http://forum.ragezone.com/f1000/release-bdo-item-database-rest-1153913/

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
# TODO: Max number of uses for failstacking item (maybe only in strat mode)
# TODO: Make graphs and menu items work
# TODO: Ability to input custom failstack lists
# TODO: Fail stacks are over prioritized at high levels (real priority is enhancement chance increase not cost) see above

# TODO: Make the separator in the menu a visible color on the dark theme

# TODO: Figure out a probability model for strat simulation
# TODO: Minimal mode window

from Forms.Main_Window import Ui_MainWindow
from Forms.dlg_Sale_Balance import Ui_DlgSaleBalance
from Forms.dlgCompact import Ui_dlgCompact
from dlgAbout import dlg_About
from dlgExport import dlg_Export
from QtCommon import Qt_common
from common import relative_path_convert, gear_types, enumerate_gt_lvl, Classic_Gear, Smashable, enumerate_gt, binVf,\
    ItemStore, generate_gear_obj
from model import Enhance_model, Invalid_FS_Parameters

import numpy, types, os
from PyQt5.QtGui import QPixmap, QPalette
from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView, QSpinBox, QFileDialog, QMenu, QAction, QDialog, QVBoxLayout
from PyQt5.QtCore import Qt
#from PyQt5 import QtWidgets
from DlgCompact import Dlg_Compact

QBlockSig = Qt_common.QBlockSig
NoScrollCombo = Qt_common.NoScrollCombo
clear_table = Qt_common.clear_table
dlg_format_list = Qt_common.dlg_format_list
get_dark_palette = Qt_common.get_dark_palette

QTableWidgetItem_NoEdit = Qt_common.QTableWidgetItem_NoEdit
STR_TW_GEAR = 'gear_item'
STR_COST_ERROR = 'Cost must be a number.'
MONNIES_FORMAT = "{:,}"
STR_TWO_DEC_FORMAT = "{:.2f}"
STR_PERCENT_FORMAT = '{:.0f}%'
STR_INFINITE = 'INF'


COL_GEAR_TYPE = 2
COL_FS_SALE_SUCCESS = 5
COL_FS_SALE_FAIL = 6
COL_FS_PROC_COST = 7


remove_numeric_modifiers = lambda x: x.replace(',', '').replace('%','')

def numeric_less_than(self, y):
    return float(remove_numeric_modifiers(self.text())) <= float(remove_numeric_modifiers(y.text()))

#def color_compare(self, other):
#    print self.cellWidget(self.row(), self.column())


class custom_twi(QTableWidgetItem, QSpinBox):
    pass



class numeric_twi(QTableWidgetItem):
    def __lt__(self, other):
        return numeric_less_than(self, other)


class comma_seperated_twi(numeric_twi):
    def __init__(self, text):
        super(comma_seperated_twi, self).__init__(text)
        self.setText(text)

    def setData(self, role, p_str):
        p_str = remove_numeric_modifiers(p_str)
        if p_str is None or p_str == '':
            super(comma_seperated_twi, self).setData(role, p_str)
        else:
            super(comma_seperated_twi, self).setData(role, MONNIES_FORMAT.format(int(p_str)))

#    def setText(self, p_str):

    
    def text(self):
        return super(comma_seperated_twi, self).text().replace(',','')


class Dlg_Sale_Balance(QDialog):
    def __init__(self, parent, dis_gear, column_head, twi):
        super(Dlg_Sale_Balance, self).__init__(parent)
        self.main_window = parent
        frmObj = Ui_DlgSaleBalance()
        self.ui = frmObj
        frmObj.setupUi(self)

        self.twi = twi
        self.dis_gear = dis_gear
        self.column_head = column_head
        self.balance = 0

        frmObj.buttonBox.accepted.connect(self.buttonBox_accepted)
        frmObj.spinValue.valueChanged.connect(self.spinValue_valueChanged)
        frmObj.spinPercent.valueChanged.connect(self.spinPercent_valueChanged)
        frmObj.chkValuePack.clicked.connect(self.chkValuePack_checkStateSe)

    def spinPercent_valueChanged(self, val):
        self.update_balance()

    def chkValuePack_checkStateSe(self, state):
        self.update_balance()

    def spinValue_valueChanged(self, val):
        self.update_balance()

    def update_balance(self):
        frmObj = self.ui
        percent = frmObj.spinPercent.value() / 100.0
        if frmObj.chkValuePack.isChecked():
            percent += percent * 0.3
        self.balance = int(round(percent * frmObj.spinValue.value()))
        frmObj.lblSale.setText("{}: {:,}".format(self.column_head, self.balance))

    def buttonBox_accepted(self):
        if self.column_head == 'Sale Success':
            self.dis_gear.sale_balance = self.balance
            self.twi.setText(str(self.balance))
        elif self.column_head == 'Sale Fail':
            self.dis_gear.fail_sale_balance = self.balance
            self.twi.setText(str(self.balance))
        elif self.column_head == 'Procurement Cost':
            self.dis_gear.procurement_cost = self.balance
            self.twi.setText(str(self.balance))
        else:
            raise ValueError('Error identifying column name. Update which balance?')


class Frm_Main(Qt_common.lbl_color_MainWindow):
    def __init__(self, app):
        super(Frm_Main, self).__init__()
        frmObj = Ui_MainWindow()
        frmObj.setupUi(self)
        self.ui = frmObj
        self.app = app

        model = Enhance_model()
        self.model = model

        pix = QPixmap(relative_path_convert('title.png'))
        frmObj.label.setPixmap(pix)

        self.clear_data()
        self.fs_c = None
        self.eh_c = None

        self.about_win = dlg_About(self)

        def actionGitHub_README_triggered():
            import webbrowser
            webbrowser.open('https://github.com/ILikesCaviar/BDO_Enhancement_Tool')

        def actionWindow_Always_on_Top_triggered(bowl):
            aot_mask = Qt.WindowStaysOnTopHint
            this_flags = self.windowFlags()
            if bowl:
                self.setWindowFlags(this_flags | aot_mask)
                self.show()
            else:
                self.setWindowFlags(this_flags & (~aot_mask))
                self.show()

        def actionExport_Excel_triggered():
            wind = dlg_Export(self)
            wind.show()

        def actionExport_CSV_triggered():
            wind = dlg_Export(self)
            wind.show()

        frmObj.actionAbout.triggered.connect(self.about_win.show)
        frmObj.actionExit.triggered.connect(app.exit)
        frmObj.actionLoad_Info.triggered.connect(self.open_file_dlg)
        frmObj.actionSave_Info.triggered.connect(self.save_file_dlg)
        frmObj.actionWindow_Always_on_Top.triggered.connect(actionWindow_Always_on_Top_triggered)
        frmObj.actionGitHub_README.triggered.connect(actionGitHub_README_triggered)
        frmObj.actionExport_CSV.triggered.connect(actionExport_CSV_triggered)
        frmObj.actionExport_Excel.triggered.connect(actionExport_Excel_triggered)

        table_Equip = frmObj.table_Equip
        table_FS = frmObj.table_FS
        table_Strat = frmObj.table_Strat
        table_Strat_Equip = frmObj.table_Strat_Equip

        def cmdEquipRemove_clicked():
            tmodel = self.model
            tsettings = tmodel.settings
            tw = frmObj.table_Equip

            effect_list = [i.row() for i in tw.selectedItems()]
            effect_list.sort()
            effect_list.reverse()

            enhance_me = tsettings[tsettings.P_ENHANCE_ME]
            r_enhance_me = tsettings[tsettings.P_R_ENHANCE_ME]

            for i in effect_list:
                thic = tw.item(i, 0).__dict__[STR_TW_GEAR]
                try:
                    enhance_me.remove(thic)
                    tmodel.invalidate_enahce_list()
                except ValueError:
                    pass
                try:
                    r_enhance_me.remove(thic)
                except ValueError:
                    pass
                teem = tw.item(i, 2)
                tw.removeRow(i)
            tsettings.changes_made = True

        def cmdFSRemove_clicked():
            tmodel = self.model
            tsettings = tmodel.settings
            tw = frmObj.table_FS

            effect_list = [i.row() for i in tw.selectedItems()]
            effect_list.sort()
            effect_list.reverse()

            fail_stackers_counts = tsettings[tsettings.P_FAIL_STACKERS_COUNT]
            fail_stackers = tsettings[tsettings.P_FAIL_STACKERS]
            r_fail_stackers = tsettings[tsettings.P_R_FAIL_STACKERS]

            for i in effect_list:
                thic = tw.item(i, 0).__dict__[STR_TW_GEAR]
                try:
                    fail_stackers.remove(thic)
                    tmodel.invalidate_failstack_list()
                except ValueError:
                    pass
                try:
                    r_fail_stackers.remove(thic)
                except ValueError:
                    pass
                try:
                    del fail_stackers_counts[thic]
                except KeyError:
                    pass
                tw.removeRow(i)
            tsettings.changes_made = True

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
        self.compact_window = Dlg_Compact(self)

        def cmdCompact_clicked():
            try:
                fs_order = frmObj.table_Strat.selectedItems()[0].row()
                self.compact_window.ui.spinFS.setValue(fs_order)
            except IndexError:
                pass
            self.compact_window.show()

        frmObj.cmdCompact.clicked.connect(self.cmdStrat_go_clicked)
        frmObj.cmdCompact.clicked.connect(cmdCompact_clicked)
        frmObj.cmdCompact.clicked.connect(self.compact_window.set_frame)

        frmObj.table_FS_Cost.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        frmObj.table_Equip.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        frmObj.table_FS.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        frmObj.table_Strat_FS.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        frmObj.table_Strat.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        frmObj.table_Strat_Equip.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        frmObj.cmd_Strat_Graph.clicked.connect(self.cmd_Strat_Graph_clicked)
        frmObj.table_Equip.setSortingEnabled(True)
        frmObj.table_FS.setSortingEnabled(True)
        frmObj.table_Strat_FS.setSortingEnabled(True)
        frmObj.table_Strat_Equip.setSortingEnabled(True)


        def give_menu_downgrade(root_menu, event_star, this_item):
            dis_gear = this_item.__dict__[STR_TW_GEAR]
            upgrade_action = QAction(root_menu)
            upgrade_action.setText('Upgrade Gear')
            upgrade_action.triggered.connect(lambda: self.upgrade_gear(dis_gear, this_item))
            root_menu.addAction(upgrade_action)

            remove_action = QAction(root_menu)
            remove_action.setText('Downgrade Gear')
            remove_action.triggered.connect(lambda: self.downgrade_gear(dis_gear, this_item))
            root_menu.addAction(remove_action)

        def table_Equip_context_menu(event_star):
            root_menu = QMenu(table_Equip)
            this_item = table_Equip.itemAt(event_star.pos())
            this_item = table_Equip.item(this_item.row(), 0)

            give_menu_downgrade(root_menu, event_star, this_item)

            root_menu.exec_(event_star.globalPos())

        table_Equip.contextMenuEvent = table_Equip_context_menu


        def table_Strat_Equip_context_menu(event_star):
            root_menu = QMenu(table_Equip)
            this_item = table_Strat_Equip.itemAt(event_star.pos())
            this_item = table_Strat_Equip.item(this_item.row(), 0)
            dis_gear = this_item.__dict__[STR_TW_GEAR]
            eq_row = None
            for rew in range(0, table_Equip.rowCount()):
                if dis_gear is table_Equip.item(rew, 0).__dict__[STR_TW_GEAR]:
                    eq_row = table_Equip.item(rew, 0)

            give_menu_downgrade(root_menu, event_star, eq_row)
            for akshon in root_menu.actions():
                akshon.triggered.connect(lambda: frmObj.cmdStrat_go.click())

            root_menu.exec_(event_star.globalPos())

        table_Strat_Equip.contextMenuEvent = table_Strat_Equip_context_menu


        def table_Strat_context_menu(event_star):
            root_menu = QMenu(table_Equip)
            this_item = table_Strat.itemAt(event_star.pos())
            dis_gear = this_item.__dict__[STR_TW_GEAR]
            eq_row = self.get_enhance_table_item(dis_gear)

            give_menu_downgrade(root_menu, event_star, eq_row)
            for akshon in root_menu.actions():
                akshon.triggered.connect(lambda: frmObj.cmdStrat_go.click())

            root_menu.exec_(event_star.globalPos())

        table_Strat.contextMenuEvent = table_Strat_context_menu


        def give_menu_sale_balance(root_menu, dis_gear, column_head, this_item):

            def open_balance_dialog():
                balance_dialog = Dlg_Sale_Balance(self, dis_gear, column_head, this_item)
                balance_dialog.ui.lblSale.setText(column_head)
                balance_dialog.show()

            upgrade_action = QAction(root_menu)
            upgrade_action.setText('Calculate Market Balance')
            upgrade_action.triggered.connect(open_balance_dialog)
            root_menu.addAction(upgrade_action)

        def table_FS_balance_context_menu(event_star):
            root_menu = QMenu(table_Equip)
            this_item = frmObj.table_FS.itemAt(event_star.pos())
            row = this_item.row()
            col = this_item.column()
            if col == COL_FS_SALE_FAIL or col == COL_FS_SALE_SUCCESS:
                root_item = table_FS.item(row, 0)
                dis_gear = root_item.__dict__[STR_TW_GEAR]

                header_txt = table_FS.horizontalHeaderItem(col).text()
                give_menu_sale_balance(root_menu, dis_gear, header_txt, this_item)

                root_menu.exec_(event_star.globalPos())

        table_FS.contextMenuEvent = table_FS_balance_context_menu

    def closeEvent(self, *args, **kwargs):
        model = self.model
        model.save_to_file()
        super(Frm_Main, self).closeEvent(*args, **kwargs)
        self.app.exit()

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

    def upgrade_gear(self, dis_gear, this_item):
        try:
            dis_gear.upgrade()
            self.model.save()
        except KeyError:
            self.show_warning_msg('Cannot upgrade gear past: ' + str(dis_gear.enhance_lvl))
            return
        self.refresh_gear_obj(dis_gear, this_item=this_item)

    def downgrade_gear(self, dis_gear, this_item):
        try:
            dis_gear.downgrade()
            self.model.save()
        except KeyError:
            self.show_warning_msg('Cannot downgrade gear below: ' + str(dis_gear.enhance_lvl))
            return
        self.refresh_gear_obj(dis_gear, this_item=this_item)

    def get_enhance_table_item(self, gear_obj):
        table_Equip = self.ui.table_Equip

        for rew in range(0, table_Equip.rowCount()):
            if gear_obj is table_Equip.item(rew, 0).__dict__[STR_TW_GEAR]:
                return table_Equip.item(rew, 0)

    def refresh_gear_obj(self, dis_gear, this_item=None):
        table_Equip = self.ui.table_Equip
        if this_item is None:
            this_item = self.get_enhance_table_item(dis_gear)

        if this_item is None:
            self.show_critical_error('Gear was not found on the gear list. ' + str(dis_gear.get_full_name()))
        else:
            self.invalidate_equiptment(this_item.row())
            cmb = table_Equip.cellWidget(this_item.row(), 3)
            cmb.setCurrentIndex(dis_gear.get_enhance_lvl_idx())
            self.cmdStrat_go_clicked()

    def clear_data(self):
        self.eh_c = None
        self.fs_exception_boxes = {}

    def monnies_twi_factory(self, i_f_val):
        twi = comma_seperated_twi(str(int(round(i_f_val))))
        return twi

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


        #for i, plowt in enumerate(eh_c):
        #    item = model.enhance_me[i]
        #    ploot = plt.plot(range(0, 121), plowt, label=item.name)
        #    plt.axvline(x=numpy.argmin(item.enhance_cost(model.cum_fs_cost)[item.gear_type.lvl_map[item.enhance_lvl]]),
        #                color=ploot[0].get_color())
        #plt.legend(loc='upper left')
        #plt.show()

    def cmdStrat_go_clicked(self):
        model = self.model
        settings = model.settings
        enhance_me = settings[settings.P_ENHANCE_ME]
        fail_stackers = settings[settings.P_FAIL_STACKERS]
        frmObj = self.ui
        tw = frmObj.table_Strat

        #for row in range(0, tw.rowCount()):
        #    tw.removeRow(0)
        self.invalidate_strategy()

        if not len(model.cum_fs_cost) > 0:
            self.cmdFSRefresh_clicked()
        if not len(model.equipment_costs) > 0:
            self.cmdEquipCost_clicked()

        try:
            fs_c, eh_c = model.calcEnhances()
            self.fs_c = fs_c
            self.eh_c = eh_c
        except Invalid_FS_Parameters as f:
            self.show_warning_msg(str(f))
            return
        fs_c_T = fs_c.T
        eh_c_T = eh_c.T

        this_enhance_me = enhance_me[:]
        this_fail_stackers = fail_stackers[:]

        try:
            tw.currentItemChanged.disconnect()
        except TypeError:
            # This happens the first time because nothing is connected.
            pass
        tw.currentItemChanged.connect(self.table_Strat_selectionChanged)

        for i, ev in enumerate(eh_c_T):
            fv = fs_c_T[i]
            tw.insertRow(i)
            twi = QTableWidgetItem(str(i))
            tw.setItem(i, 0, twi)
            ev_min = numpy.argmin(ev)
            fv_min = numpy.argmin(fv)
            if fv[fv_min] > ev[ev_min]:
                dis_gear = this_enhance_me[ev_min]
                twi = QTableWidgetItem(dis_gear.get_full_name())
                twi2 = QTableWidgetItem("YES")
            else:
                dis_gear = this_fail_stackers[fv_min]
                twi = QTableWidgetItem(dis_gear.get_full_name())
                twi2 = QTableWidgetItem("NO")
            twi.__dict__[STR_TW_GEAR] = dis_gear
            tw.setItem(i, 1, twi)
            tw.setItem(i, 2, twi2)

        self.eh_c = eh_c
        self.adjust_equip_splitter()

    def table_Strat_selectionChanged(self, row_obj):
        if self.eh_c is None or self.fs_c is None:
            self.show_critical_error('No details when strategy is not calculated.')
            return
        frmObj = self.ui
        model = self.model
        settings = model.settings
        enhance_me = settings[settings.P_ENHANCE_ME]
        fail_stackers = settings[settings.P_FAIL_STACKERS]
        this_enhance_me = enhance_me[:]
        this_fail_stackers = fail_stackers[:]
        fs_c_T = self.fs_c.T
        eh_c_T = self.eh_c.T
        tw_eh = frmObj.table_Strat_Equip
        tw_fs = frmObj.table_Strat_FS
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
        tw_eh.setSortingEnabled(False)
        tw_fs.setSortingEnabled(False)
        for i in range(0, len(this_vec)):
            this_sorted_idx = this_sort[i]
            this_sorted_item = this_enhance_me[this_sorted_idx]
            tw_eh.insertRow(i)
            twi = QTableWidgetItem(str(this_sorted_item.get_full_name()))
            twi.__dict__[STR_TW_GEAR] = this_sorted_item
            tw_eh.setItem(i, 0, twi)
            twi = self.monnies_twi_factory(this_vec[this_sorted_idx])
            #twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
            tw_eh.setItem(i, 1, twi)

            eh_idx = this_sorted_item.get_enhance_lvl_idx()
            cost_vec_l = this_sorted_item.cost_vec[eh_idx]
            idx_ = numpy.argmin(cost_vec_l)
            opti_val = cost_vec_l[idx_]
            optimality = (1.0 + ((opti_val - cost_vec_l[p_int]) / opti_val)) * 100
            twi = numeric_twi(STR_PERCENT_FORMAT.format(optimality))
            #twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
            tw_eh.setItem(i, 2, twi)

            this_fail_map = numpy.array(this_sorted_item.gear_type.map)[eh_idx][p_int]
            avg_num_attempt = numpy.divide(1.0, this_fail_map)
            avg_num_fails = avg_num_attempt - 1
            twi = numeric_twi(STR_TWO_DEC_FORMAT.format(avg_num_fails))
            #twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
            tw_eh.setItem(i, 3, twi)

            # attempts = int(numpy.ceil(avg_num_attempt))
            # if attempts == 0:
            #    attempts = 1
            # print 'cdf(1,{},{}) = {} | {} {}'.format(attempts, this_fail_map, binVf(attempts, this_fail_map), avg_num_attempt, this_sorted_item.name)
            confidence = binVf(avg_num_attempt, this_fail_map) * 100
            twi = numeric_twi(STR_PERCENT_FORMAT.format(confidence))
            #twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
            tw_eh.setItem(i, 4, twi)

        this_vec = fs_c_T[p_int]
        this_sort = numpy.argsort(this_vec)

        for i in range(0, len(this_vec)):
            this_sorted_idx = this_sort[i]
            this_sorted_item = this_fail_stackers[this_sorted_idx]
            tw_fs.insertRow(i)
            twi = QTableWidgetItem(str(this_sorted_item.get_full_name()))
            twi.__dict__[STR_TW_GEAR] = this_sorted_item
            tw_fs.setItem(i, 0, twi)
            twi = self.monnies_twi_factory(this_vec[this_sorted_idx])
            #twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
            tw_fs.setItem(i, 1, twi)

            opti_val = this_vec[this_sort[0]]
            optimality = (1.0 - ((opti_val - this_vec[this_sorted_idx]) / opti_val)) * 100
            twi = numeric_twi(STR_PERCENT_FORMAT.format(optimality))
            #twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
            tw_fs.setItem(i, 2, twi)
        tw_eh.setSortingEnabled(True)
        tw_fs.setSortingEnabled(True)

    def cmdEquipCost_clicked(self):
        model = self.model
        frmObj = self.ui
        tw = frmObj.table_Equip

        try:
            model.calc_equip_costs()
        except Invalid_FS_Parameters as f:
            self.show_warning_msg(str(f))
            return
        tw.setSortingEnabled(False)
        for i in range(0, tw.rowCount()):
            this_head = tw.item(i, 0)
            this_gear = this_head.gear_item
            eh_idx = this_gear.get_enhance_lvl_idx()
            cost_vec_l = this_gear.get_cost_obj()[eh_idx]
            idx_ = numpy.argmin(this_gear.cost_vec[eh_idx])
            twi = numeric_twi(str(idx_))
            #twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
            tw.setItem(i, 4, twi)
            twi = self.monnies_twi_factory(cost_vec_l[idx_])
            #twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
            tw.setItem(i, 5, twi)

            this_fail_map = numpy.array(this_gear.gear_type.map)[eh_idx]
            avg_num_fails = numpy.divide(numpy.ones(this_fail_map.shape), this_fail_map) - 1
            twi = numeric_twi(STR_TWO_DEC_FORMAT.format(avg_num_fails[idx_]))
            #twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
            tw.setItem(i, 6, twi)
            try:
                twi = QTableWidgetItem(str(this_gear.using_memfrags))
                tw.setItem(i, 7, twi)
            except AttributeError:
                pass
        tw.setSortingEnabled(True)

    def cmdFS_Cost_Clear_clicked(self):
        model = self.model
        settings = model.settings
        frmObj = self.ui
        tw = frmObj.table_FS_Cost

        def kill(x):
            try:
                del settings[settings.P_FS_EXCEPTIONS][x]
            except KeyError:
                pass
        settings.changes_made = True
        map(kill, set([r.row() for r in tw.selectedIndexes()]))
        frmObj.cmdFSRefresh.click()

    def add_custom_fs_combobox(self, model, tw, fs_exception_boxes, row_idx):
        settings = model.settings
        fs_exceptions = settings[settings.P_FS_EXCEPTIONS]
        fail_stackers = settings[settings.P_FAIL_STACKERS]
        this_cmb = NoScrollCombo(tw)
        this_cmb.setFocusPolicy(Qt.ClickFocus)
        fs_exception_boxes[row_idx] = this_cmb
        this_item = fs_exceptions[row_idx]
        def this_cmb_currentIndexChanged(indx):
            model.edit_fs_exception(row_idx, fail_stackers[indx])

        for i, gear in enumerate(fail_stackers):
            this_cmb.addItem(gear.name)
            if gear is this_item:
                this_cmb.setCurrentIndex(i)
        this_cmb.currentIndexChanged.connect(this_cmb_currentIndexChanged)
        tw.setCellWidget(row_idx, 1, this_cmb)

    def cmdFSEdit_clicked(self):
        frmObj = self.ui
        model = self.model
        settings = model.settings
        fs_exception_boxes = self.fs_exception_boxes
        tw = frmObj.table_FS_Cost

        selected_rows = set([r.row() for r in tw.selectedIndexes()])

        for indx in selected_rows:
            model.edit_fs_exception(indx, tw.item(indx, 0).__dict__[STR_TW_GEAR])
            self.add_custom_fs_combobox(model, tw, fs_exception_boxes, indx)

    def cmdFSRefresh_clicked(self):
        frmObj = self.ui
        model = self.model
        fs_exceptions = model.settings[model.settings.P_FS_EXCEPTIONS]
        try:
            model.calcFS()
        except Invalid_FS_Parameters as e:
            self.show_warning_msg(str(e))
            return

        tw = frmObj.table_FS_Cost
        with QBlockSig(tw):
            clear_table(tw)
        fs_items = model.optimal_fs_items
        fs_cost = model.fs_cost
        cum_fs_cost = model.cum_fs_cost
        cum_fs_probs = model.cum_fs_probs
        fs_probs = model.fs_probs
        fs_exception_boxes = self.fs_exception_boxes

        for i, this_gear in enumerate(fs_items):
            rc = tw.rowCount()
            tw.insertRow(rc)
            twi = QTableWidgetItem(str(i))
            twi.__dict__[STR_TW_GEAR] = this_gear
            tw.setItem(rc, 0, twi)
            if i in fs_exceptions:
                self.add_custom_fs_combobox(model, tw, fs_exception_boxes, i)
            else:
                twi = QTableWidgetItem(this_gear.get_full_name())
                tw.setItem(rc, 1, twi)
            twi = self.monnies_twi_factory(fs_cost[i])
            tw.setItem(rc, 2, twi)
            twi = self.monnies_twi_factory(cum_fs_cost[i])
            tw.setItem(rc, 3, twi)
            twi = QTableWidgetItem(str(fs_probs[i]))
            tw.setItem(rc, 4, twi)
            twi = QTableWidgetItem(str(cum_fs_probs[i]))
            tw.setItem(rc, 5, twi)
        frmObj.cmdEquipCost.setEnabled(True)

    def table_cellChanged_proto(self, row, col, tw, this_gear):
        this_item = tw.item(row, col)
        if this_item is None:
            return
        str_this_item = this_item.text()

        if col == 0:
            this_gear.name = str_this_item
        elif col == 2:
            try:
                this_gear.set_cost(float(str_this_item))
            except ValueError:
                self.show_warning_msg('Cost must be a number.')

    def table_Equip_cellChanged(self, row, col):
        model = self.model
        settings = model.settings
        r_enhance_me = settings[settings.P_R_ENHANCE_ME]
        enhance_me = settings[settings.P_ENHANCE_ME]
        tw = self.ui.table_Equip

        t_item = tw.item(row, 0)
        this_gear = t_item.gear_item
        if col == 0:
            if t_item.checkState() == Qt.Checked:
                try:
                    r_enhance_me.remove(this_gear)
                except ValueError:
                    # Item already removed. This is likely not a check change on col 0
                    pass

                enhance_me.append(this_gear)
                settings[settings.P_ENHANCE_ME] = list(set(enhance_me))
                # order here matters to the file is saved after the settings are updated
                self.invalidate_strategy()
            else:
                try:
                    enhance_me.remove(this_gear)
                except ValueError:
                    # Item already removed. This is likely not a check change on col 0
                    pass

                r_enhance_me.append(this_gear)
                settings[settings.P_R_ENHANCE_ME] = list(set(r_enhance_me))
                # order here matters to the file is saved after the settings are updated
                self.invalidate_strategy()
        elif col == 2:
            # columns that are not 0 are non-cosmetic and may change the cost values
            self.invalidate_equiptment(row)
        self.table_cellChanged_proto(row, col, tw, this_gear)

    def table_FS_cellChanged(self, row, col):
        model = self.model
        settings = model.settings
        r_fail_stackers = settings[settings.P_R_FAIL_STACKERS]
        fail_stackers = settings[settings.P_FAIL_STACKERS]
        tw = self.ui.table_FS

        t_item = tw.item(row, 0)
        this_gear = t_item.gear_item
        if col == 0:
            if t_item.checkState() == Qt.Checked:
                try:
                    r_fail_stackers.remove(this_gear)
                except ValueError:
                    # Item already removed. This is likely not a check change on col 0
                    pass

                fail_stackers.append(this_gear)
                settings[settings.P_FAIL_STACKERS] = list(set(fail_stackers))
                # order here matters to the file is saved after the settings are updated
                self.invalidate_strategy()
            else:
                try:
                    fail_stackers.remove(this_gear)
                except ValueError:
                    # Item already removed. This is likely not a check change on col 0
                    pass

                r_fail_stackers.append(this_gear)
                settings[settings.P_R_FAIL_STACKERS] = list(set(r_fail_stackers))
                # order here matters to the file is saved after the settings are updated
                self.invalidate_strategy()
        elif col == COL_FS_SALE_SUCCESS:
                this_gear.set_sale_balance(float(tw.item(row, 5).text()))
        elif col == COL_FS_SALE_FAIL:
            this_gear.set_fail_sale_balance(float(tw.item(row, 6).text()))
        elif col == COL_FS_PROC_COST:
            this_gear.set_procurement_cost(float(tw.item(row, 7).text()))
        self.table_cellChanged_proto(row, col, tw, this_gear)
        self.invalidate_fs_list()

    def set_sort_gear_cmbBox(self, this_list, compar_f, current_gear_lvl, cmb_box):
        sorted_list = this_list[:]
        sorted_list.sort(key=compar_f)

        for i, key in enumerate(sorted_list):
            cmb_box.addItem(key)
            if key == current_gear_lvl:
                cmb_box.setCurrentIndex(i)

    def table_add_gear(self, edit_func, invalidate_func, tw, this_gear, add_fun=None, check_state=Qt.Checked):
        model = self.model

        rc = tw.rowCount()
        tw.insertRow(rc)
        with QBlockSig(tw):
            # If the rows are not initialized then the context menus will bug out
            for i in range(0, tw.columnCount()):
                twi = QTableWidgetItem('')
                tw.setItem(rc, i, twi)

        cmb_gt = NoScrollCombo(tw)
        cmb_enh = NoScrollCombo(tw)
        twi_gt = QTableWidgetItem()
        twi_lvl = QTableWidgetItem()


        self.set_sort_gear_cmbBox(gear_types.keys(), enumerate_gt, this_gear.gear_type.name, cmb_gt)
        gtype_s = cmb_gt.currentText()


        self.set_sort_gear_cmbBox(gear_types[gtype_s].lvl_map.keys(), enumerate_gt_lvl, this_gear.enhance_lvl, cmb_enh)

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
                self.set_sort_gear_cmbBox(new_gt.lvl_map.keys(), enumerate_gt_lvl, current_enhance_string, cmb_enh)
            this_gear = f_twi.__dict__['gear_item']
            if str_picked.lower().find('accessor') > -1:
                if not isinstance(this_gear, Smashable):
                    old_g = this_gear
                    this_gear = generate_gear_obj(model.settings, base_item_cost=this_gear.base_item_cost, enhance_lvl=cmb_enh.currentText(),
                                                        gear_type=gear_types[str_picked], name=this_gear.name,
                                                        sale_balance=this_gear.sale_balance)
                    edit_func(old_g, this_gear)
                else:
                    this_gear.set_gear_params(gear_types[str_picked], cmb_enh.currentText())
            else:
                if not isinstance(this_gear, Classic_Gear):
                    old_g = this_gear
                    this_gear = generate_gear_obj(model.settings, base_item_cost=this_gear.base_item_cost, enhance_lvl=cmb_enh.currentText(),
                                                        gear_type=gear_types[str_picked], name=this_gear.name)
                    edit_func(old_g, this_gear)
                else:
                    this_gear.set_gear_params(gear_types[str_picked], cmb_enh.currentText())
            f_twi.__dict__['gear_item'] = this_gear
            invalidate_func()
            # Sets the hidden value of the table widget so that colors are sorted in the right order
            self.set_cell_color_compare(twi_gt, str_picked)

        def cmb_enh_currentTextChanged(str_picked):
            # could throw key error
            this_gear = f_twi.__dict__['gear_item']
            try:
                this_gear.set_enhance_lvl(str_picked)
                self.set_cell_lvl_compare(twi_lvl, str_picked)
            except KeyError:
                self.show_critical_error('Enhance level does not appear to be valid.')

        with QBlockSig(tw):
            tw.setItem(rc, 0, f_twi)
            tw.setCellWidget(rc, 1, cmb_gt)
            twi = self.monnies_twi_factory(this_gear.base_item_cost)
            #twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
            tw.setItem(rc, 2, twi)
            tw.setCellWidget(rc, 3, cmb_enh)
            tw.setItem(rc, 1, twi_gt)
            tw.setItem(rc, 3, twi_lvl)

        self.cmb_equ_change(cmb_gt, cmb_gt.currentText())
        self.set_cell_lvl_compare(twi_lvl, cmb_enh.currentText())
        self.set_cell_color_compare(twi_gt, cmb_gt.currentText())

        cmb_gt.currentTextChanged.connect(cmb_gt_currentTextChanged)
        cmb_enh.currentTextChanged.connect(cmb_enh_currentTextChanged)
        cmb_gt.currentTextChanged.connect(lambda x: self.cmb_equ_change(self.sender(), x))

    def set_cell_lvl_compare(self, twi_lvl, lvl_str):
        txt_c = str(enumerate_gt_lvl(lvl_str))
        twi_lvl.setText(txt_c)

    def set_cell_color_compare(self, twi_gt, gt_str):
        txt_c = gt_str.lower()
        if txt_c.find('white') > -1:
            twi_gt.setText('b')
        elif txt_c.find('green') > -1:
            twi_gt.setText('c')
        elif txt_c.find('blue') > -1:
            twi_gt.setText('d')
        elif txt_c.find('yellow') > -1 or txt_c.find('boss') > -1:
            twi_gt.setText('e')
        else:
            twi_gt.setText('a')

    def cmb_equ_change(self, cmb, txt_c):
        txt_c = txt_c.lower()
        this_pal = cmb.palette()
        this_pal.setColor(QPalette.ButtonText, Qt.black)
        if txt_c.find('white') > -1:
            this_pal.setColor(QPalette.Button, Qt.white)
        elif txt_c.find('green') > -1:
            this_pal.setColor(QPalette.Button, Qt.green)
        elif txt_c.find('blue') > -1:
            this_pal.setColor(QPalette.Button, Qt.blue)
        elif txt_c.find('yellow') > -1 or txt_c.find('boss') > -1:
            this_pal.setColor(QPalette.Button, Qt.yellow)
        else:
            this_pal = get_dark_palette()
        cmb.setPalette(this_pal)

    def table_FS_add_gear(self, this_gear, check_state=Qt.Checked, add_fun=None):
        model = self.model
        tw = self.ui.table_FS
        rc = tw.rowCount()
        self.table_add_gear(model.edit_fs_item, model.invalidate_failstack_list, tw, this_gear,
                            check_state=check_state, add_fun=add_fun)
        def valueChanged_connect(val):
            settings = model.settings
            fail_stackers_counts = settings[settings.P_FAIL_STACKERS_COUNT]
            if val == 0:
                try:
                    del fail_stackers_counts[this_gear]
                except KeyError:
                    pass
            else:
                fail_stackers_counts[this_gear] = val
            settings.changes_made = True
            self.invalidate_fs_list()
        with QBlockSig(tw):
            thisspin = QSpinBox()
            thisspin.setMaximum(120)
            thisspin.setSpecialValueText(STR_INFINITE)
            settings = model.settings
            fail_stackers_counts = settings[settings.P_FAIL_STACKERS_COUNT]
            try:
                this_val = fail_stackers_counts[this_gear]
                thisspin.setValue(this_val)
            except KeyError:
                pass
            thisspin.valueChanged.connect(valueChanged_connect)
            tw.setCellWidget(rc, 4, thisspin)
            twi = self.monnies_twi_factory(this_gear.sale_balance)
            #twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
            tw.setItem(rc, 5, twi)
            twi = self.monnies_twi_factory(this_gear.fail_sale_balance)
            #twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
            tw.setItem(rc, 6, twi)
            twi = self.monnies_twi_factory(this_gear.procurement_cost)
            #twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
            tw.setItem(rc, 7, twi)
            tw.cellWidget(rc, 1).currentTextChanged.connect(self.invalidate_fs_list)
            tw.cellWidget(rc, 3).currentTextChanged.connect(self.invalidate_fs_list)

    def table_Eq_add_gear(self, this_gear, check_state=Qt.Checked, add_fun=None):
        model = self.model
        tw = self.ui.table_Equip
        rc = tw.rowCount()
        self.table_add_gear(model.edit_enhance_item, model.invalidate_enahce_list, tw, this_gear,
                            check_state=check_state, add_fun=add_fun)

        with QBlockSig(tw):
            tw.cellWidget(rc, 1).currentTextChanged.connect(lambda: self.invalidate_equiptment(rc))
            tw.cellWidget(rc, 3).currentTextChanged.connect(lambda: self.invalidate_equiptment(rc))

    def cmdFSAdd_clicked(self, bool_):
        model = self.model

        gear_type = gear_types.items()[0][1]
        enhance_lvl = gear_type.lvl_map.keys()[0]
        this_gear = generate_gear_obj(model.settings, base_item_cost=0, enhance_lvl=enhance_lvl, gear_type=gear_type)
        self.table_FS_add_gear(this_gear, add_fun=model.add_fs_item)
        self.invalidate_fs_list()

    def cmdEquipAdd_clicked(self, bool_):
        model = self.model

        gear_type = gear_types.items()[0][1]
        enhance_lvl = gear_type.lvl_map.keys()[0]

        this_gear = generate_gear_obj(model.settings, base_item_cost=0, enhance_lvl=enhance_lvl, gear_type=gear_type)

        self.table_Eq_add_gear( this_gear, add_fun=model.add_equipment_item)

    def invalidate_fs_list(self):
        frmObj = self.ui
        tw = frmObj.table_FS_Cost
        self.model.invalidate_failstack_list()
        with QBlockSig(tw):
            clear_table(tw)
        self.invalidate_strategy()

    def invalidate_equiptment(self, row_idx):
        frmObj = self.ui
        tw = frmObj.table_Equip
        self.model.invalidate_enahce_list()
        with QBlockSig(tw):
            tw.takeItem(row_idx, 4)
            tw.takeItem(row_idx, 5)
            tw.takeItem(row_idx, 6)
            tw.takeItem(row_idx, 7)
        self.invalidate_strategy()

    def invalidate_strategy(self):
        self.eh_c = None
        frmObj = self.ui
        tw = frmObj.table_Strat
        tw_fs = frmObj.table_Strat_FS
        tw_eh = frmObj.table_Strat_Equip
        with QBlockSig(tw):
            clear_table(tw)
        with QBlockSig(tw_eh):
            clear_table(tw_eh)
        with QBlockSig(tw_fs):
            clear_table(tw_fs)
        self.model.save()

    def open_file_dlg(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        model = self.model
        settings = model.settings

        if settings.f_path is None:
            this_open_path = relative_path_convert('./')
        else:
            this_open_path = settings.f_path
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
        if model.settings.f_path is None:
            save_path = relative_path_convert('./')
        else:
            save_path = os.path.dirname(model.settings.f_path)
        fileName, _ = QFileDialog.getSaveFileName(self, "Saving", save_path, dlg_format_list(format_list), options=options,
                                                  initialFilter=dlg_format_list([format_list[1]]))
        if fileName:
            if not fileName.lower().endswith('.json'):
                fileName += '.json'
            model.save_to_file(txt_path=fileName)
            self.show_green_msg('Saved: ' + fileName)
        else:
            show_mess('Aborted saving.')

    def load_file(self, str_path):
        self.clear_all()
        model = self.model
        settings = model.settings
        frmObj = self.ui

        try:
            self.model.load_from_file(str_path)
        except ValueError:
            self.show_critical_error('Something is wrong with the settings file: ' + str_path)
        except KeyError as e:
            self.show_critical_error('Something is wrong with the settings file: ' + str_path)
            print e

        self.load_ui_common()

        try:
            fail_stackers = settings[settings.P_FAIL_STACKERS]
            enhance_me = settings[settings.P_ENHANCE_ME]
        except KeyError as e:
            self.show_critical_error('Something is wrong with the settings file: ' + str_path)
            print e
            for j in self.model.settings:
                print j
            return

        tw = frmObj.table_Equip
        for gear in enhance_me:
            with QBlockSig(frmObj.table_Equip):
                self.table_Eq_add_gear(gear)
        for gear in settings[settings.P_R_ENHANCE_ME]:
            with QBlockSig(frmObj.table_Equip):
                self.table_Eq_add_gear(gear, check_state=Qt.Unchecked)
        frmObj.table_FS.setSortingEnabled(False)
        frmObj.table_Equip.setSortingEnabled(False)
        for gear in fail_stackers:
            with QBlockSig(frmObj.table_FS):
                self.table_FS_add_gear(gear)
        for gear in settings[settings.P_R_FAIL_STACKERS]:
            with QBlockSig(frmObj.table_FS):
                self.table_FS_add_gear(gear, check_state=Qt.Unchecked)
        frmObj.table_FS.setSortingEnabled(True)
        frmObj.table_Equip.setSortingEnabled(True)
        if len(fail_stackers) > 0:
            frmObj.cmdFSRefresh.click()
            if len(enhance_me) > 0:
                frmObj.cmdEquipCost.click()

    def load_ui_common(self):
        frmObj = self.ui
        model = self.model
        settings = model.settings
        def cost_mat_gen(unpack):
            txt_box, cost, set_costf, itm_txt = unpack
            txt_box.setValue(cost)

            def spin_Cost_item_textChanged(str_val):
                try:
                    set_costf(str_val)
                    frmObj.statusbar.showMessage('Set '+itm_txt+' cost to: ' + str(str_val))
                except ValueError:
                    self.show_warning_msg(STR_COST_ERROR, silent=True)

            txt_box.valueChanged.connect(spin_Cost_item_textChanged)
            txt_box.editingFinished.connect(model.save)

        item_store = settings[settings.P_ITEM_STORE]
        cost_bs_a = item_store.get_cost(ItemStore.P_BLACK_STONE_ARMOR)
        cost_bs_w = item_store.get_cost(ItemStore.P_BLACK_STONE_WEAPON)
        cost_conc_a = item_store.get_cost(ItemStore.P_CONC_ARMOR)
        cost_conc_w = item_store.get_cost(ItemStore.P_CONC_WEAPON)
        cost_cleanse = settings[settings.P_CLEANSE_COST]
        cost_cron = settings[settings.P_CRON_STONE_COST]
        cost_meme = item_store.get_cost(ItemStore.P_MEMORY_FRAG)
        cost_dscale = item_store.get_cost(ItemStore.P_DRAGON_SCALE)
        map(cost_mat_gen, [
            [frmObj.spin_Cost_BlackStone_Armor, cost_bs_a, model.set_cost_bs_a, 'Blackstone Armour'],
            [frmObj.spin_Cost_BlackStone_Weapon, cost_bs_w, model.set_cost_bs_w, 'Blackstone Weapon'],
            [frmObj.spin_Cost_ConcArmor, cost_conc_a, model.set_cost_conc_a, 'Conc Blackstone Armour'],
            [frmObj.spin_Cost_Conc_Weapon, cost_conc_w, model.set_cost_conc_w, 'Conc Blackstone Weapon'],
            [frmObj.spin_Cost_Cleanse, cost_cleanse, model.set_cost_cleanse, 'Gear Cleanse'],
            [frmObj.spin_Cost_Cron, cost_cron, model.set_cost_cron, 'Cron Stone'],
            [frmObj.spin_Cost_MemFrag, cost_meme, model.set_cost_meme, 'Memory Fragment'],
            [frmObj.spin_Cost_Dragon_Scale, cost_dscale, model.set_cost_dragonscale, 'Dragon Scale'],
        ])
