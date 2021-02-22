#- * -coding: utf - 8 - * -
"""
http://forum.ragezone.com/f1000/release-bdo-item-database-rest-1153913/

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
# TODO: Make graphs
# TODO: Make the separator in the menu a visible color on the dark theme
# TODO: Tooltip
# TODO: Custom gear in compact window
# TODO: Detect user logout from CM
# TODO: Undo / Redo functions
import sys
from typing import List

from .qt_UI_Common import STR_PIC_BSA, STR_PIC_BSW, STR_PIC_CBSA, STR_PIC_CBSW, STR_PIC_HBCS, STR_PIC_SBCS, \
    STR_PIC_CAPH, \
    STR_PIC_CRON, STR_PIC_MEME, STR_PIC_PRIEST, STR_PIC_DRAGON_SCALE, STR_PIC_VALUE_PACK, STR_PIC_RICH_MERCH_RING, \
    STR_PIC_MARKET_TAX, STR_PIC_BARTALI, pix, STR_PIC_VALKS

from .WidgetTools import STR_TWO_DEC_FORMAT, STR_PERCENT_FORMAT

from .DialogWindows import Dlg_Sale_Balance, DlgManageAlts, DlgManageValks, DlgManageNaderr, DlgGearTypeProbability
from .WidgetTools import QBlockSig, MONNIES_FORMAT, MPThread, numeric_twi, \
    GearWidget, monnies_twi_factory

from .Forms.Main_Window import Ui_MainWindow
from .dlgAbout import dlg_About
from .dlgExport import dlg_Export
from .QtCommon import Qt_common
from .common import relative_path_convert, Classic_Gear, Smashable, binVf, \
    ItemStore, USER_DATA_PATH, utils, DEFAULT_SETTINGS_PATH, Gear
from .model import Enhance_model, SettingsException, StrategySolution

import numpy, os, shutil, time
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView, QFileDialog, QTreeWidgetItem
from PyQt5.QtCore import Qt, QSize, QThread
from PyQt5 import QtGui

import urllib3
#from PyQt5 import QtWidgets
from .DlgCompact import Dlg_Compact
from .mp_login import DlgMPLogin
from .utilities import open_folder
import json
from packaging.version import Version
import webbrowser

clear_table = Qt_common.clear_table
dlg_format_list = Qt_common.dlg_format_list
get_dark_palette = Qt_common.get_dark_palette

QTableWidgetItem_NoEdit = Qt_common.QTableWidgetItem_NoEdit
#STR_TW_GEAR = 'gear_item'
STR_URL_UPDATE_HOST = r'https://api.github.com/'
STR_URL_UPDATE_LOC = '/repos/ILikesCaviar/BDO_Enhancement_Tool/releases/latest'
STR_COST_ERROR = 'Cost must be a number.'
STR_INFINITE = 'INF'

COL_GEAR_TYPE = 2
COL_FS_SALE_SUCCESS = 4
COL_FS_SALE_FAIL = 5
COL_FS_PROC_COST = 6


#def color_compare(self, other):
#    print self.cellWidget(self.row(), self.column())


class Frm_Main(Qt_common.lbl_color_MainWindow):
    def __init__(self, app, version, file=None):
        super(Frm_Main, self).__init__()
        frmObj = Ui_MainWindow()
        frmObj.setupUi(self)
        self.ui = frmObj
        self.app = app
        self.version = version

        self.setStyleSheet('''
        QMenu::separator {
    height: 1px;
    background: white;
    margin-left: 5px;
    margin-right: 5px;
    margin-top: 5px;
    margin-bottom: 5px;
}
        ''')

        if file is None:
            file = DEFAULT_SETTINGS_PATH
        self.model:Enhance_model = None


        title_pix = QPixmap(relative_path_convert('title.png'))
        frmObj.label.setPixmap(title_pix)

        #self.pool_size = 5
        #self.connection = urllib3.HTTPSConnectionPool('bdocodex.com', maxsize=self.pool_size, block=True)

        self.clear_data()
        self.strat_solution: StrategySolution = None
        self.evolve_threads = []

        self.strat_go_mode = False  # The strategy has been calculated and needs to be updated

        self.about_win = dlg_About(self)
        self.dlg_gt_prob = DlgGearTypeProbability(self)

        def actionGitHub_README_triggered():
            webbrowser.open('https://github.com/ILikesCaviar/BDO_Enhancement_Tool')

        def actionDownload_Latest_triggered():
            webbrowser.open(r'https://github.com/ILikesCaviar/BDO_Enhancement_Tool/releases/')

        def actionWindow_Always_on_Top_triggered(bowl):
            aot_mask = Qt.WindowStaysOnTopHint
            this_flags = self.windowFlags()
            if bowl:
                self.setWindowFlags(this_flags | aot_mask)
                if self.dlg_valks.isVisible():
                    self.dlg_valks.setWindowFlags(self.dlg_valks.windowFlags() | aot_mask)
                    self.dlg_valks.show()
                if self.dlg_alts.isVisible():
                    self.dlg_alts.setWindowFlags(self.dlg_alts.windowFlags() | aot_mask)
                    self.dlg_alts.show()
            else:
                self.setWindowFlags(this_flags & (~aot_mask))
                if self.dlg_valks.isVisible():
                    self.dlg_valks.setWindowFlags(self.dlg_valks.windowFlags() & (~aot_mask))
                    self.dlg_valks.show()
                if self.dlg_alts.isVisible():
                    self.dlg_alts.setWindowFlags(self.dlg_alts.windowFlags() & (~aot_mask))
                    self.dlg_alts.show()
            self.show()

        def actionExport_Excel_triggered():
            wind = dlg_Export(self)
            wind.show()

        def actionExport_CSV_triggered():
            wind = dlg_Export(self)
            wind.show()

        def actionMarket_Tax_Calc_triggered():
            slg = Dlg_Sale_Balance(self, 'Profit')
            slg.ui.buttonBox.setEnabled(False)
            slg.ui.buttonBox.setVisible(False)
            slg.show()

        def actionGear_Type_Probability_Table_triggered():
            self.dlg_gt_prob.show()

        frmObj.lblBlackStoneArmorPic.setPixmap(pix[STR_PIC_BSA].scaled(32, 32, transformMode=Qt.SmoothTransformation))
        frmObj.lblBlackStoneWeaponPic.setPixmap(pix[STR_PIC_BSW].scaled(32, 32, transformMode=Qt.SmoothTransformation))
        frmObj.lblConcBlackStoneArmorPic.setPixmap(pix[STR_PIC_CBSA].scaled(32, 32, transformMode=Qt.SmoothTransformation))
        frmObj.lblConcBlackStoneWeaponPic.setPixmap(pix[STR_PIC_CBSW].scaled(32, 32, transformMode=Qt.SmoothTransformation))

        frmObj.lblSharpPic.setPixmap(pix[STR_PIC_SBCS].scaled(32, 32, transformMode=Qt.SmoothTransformation))
        frmObj.lblHardPic.setPixmap(pix[STR_PIC_HBCS].scaled(32, 32, transformMode=Qt.SmoothTransformation))

        frmObj.lblCaphStonePic.setPixmap(pix[STR_PIC_CAPH].scaled(32, 32, transformMode=Qt.SmoothTransformation))

        frmObj.lblCronStonePic.setPixmap(pix[STR_PIC_CRON].scaled(32, 32, transformMode=Qt.SmoothTransformation))
        frmObj.lblMemoryFragmentPic.setPixmap(pix[STR_PIC_MEME].scaled(32, 32, transformMode=Qt.SmoothTransformation))
        frmObj.lblGearCleansePic.setPixmap(
            pix[STR_PIC_PRIEST].scaled(32, 32, transformMode=Qt.SmoothTransformation))
        frmObj.lblDragonScalePic.setPixmap(
            pix[STR_PIC_DRAGON_SCALE].scaled(32, 32, transformMode=Qt.SmoothTransformation))

        frmObj.lblMarketTaxPic.setPixmap(
            pix[STR_PIC_MARKET_TAX].scaled(32, 32, transformMode=Qt.SmoothTransformation))
        frmObj.chkValuePackPic.setPixmap(
            pix[STR_PIC_VALUE_PACK].scaled(32, 32, transformMode=Qt.SmoothTransformation))
        frmObj.chkMerchantsRingPic.setPixmap(
            pix[STR_PIC_RICH_MERCH_RING].scaled(32, 32, transformMode=Qt.SmoothTransformation))
        frmObj.lblQuestFSIncPic.setPixmap(
            pix[STR_PIC_BARTALI].scaled(32, 32, transformMode=Qt.SmoothTransformation))

        self.dlg_login = DlgMPLogin(self)
        self.dlg_login.sig_Market_Ready.connect(self.dlg_login_sig_Market_Ready)

        def actionSign_in_to_MP_triggered():
            self.dlg_login.show()

        def actionOpen_Settings_Directory_triggered():
            open_folder(USER_DATA_PATH)

        def actionOpen_Log_File_triggered():
            open_folder(os.path.join(USER_DATA_PATH,'LOG.log'))

        frmObj.actionAbout.triggered.connect(self.about_win.show)
        frmObj.actionExit.triggered.connect(app.exit)
        frmObj.actionLoad_Info.triggered.connect(self.open_file_dlg)
        frmObj.actionSave_Info.triggered.connect(self.save_file_dlg)
        frmObj.actionWindow_Always_on_Top.triggered.connect(actionWindow_Always_on_Top_triggered)
        frmObj.actionGitHub_README.triggered.connect(actionGitHub_README_triggered)
        frmObj.actionDownload_Latest.triggered.connect(actionDownload_Latest_triggered)
        frmObj.actionExport_CSV.triggered.connect(actionExport_CSV_triggered)
        frmObj.actionExport_Excel.triggered.connect(actionExport_Excel_triggered)
        frmObj.actionMarket_Tax_Calc.triggered.connect(actionMarket_Tax_Calc_triggered)
        frmObj.actionSign_in_to_MP.triggered.connect(actionSign_in_to_MP_triggered)
        frmObj.actionGear_Type_Probability_Table.triggered.connect(actionGear_Type_Probability_Table_triggered)
        frmObj.actionOpen_Settings_Directory.triggered.connect(actionOpen_Settings_Directory_triggered)
        frmObj.actionOpen_Log_File.triggered.connect(actionOpen_Log_File_triggered)

        table_Equip = frmObj.table_Equip

        self.dlg_alts = DlgManageAlts(self)
        self.dlg_valks = DlgManageValks(self)
        self.dlg_naderr = DlgManageNaderr(self)
        frmObj.cmdAlts.clicked.connect(self.dlg_alts.show)
        frmObj.cmdAdviceValks.clicked.connect(self.dlg_valks.show)
        frmObj.cmdNaderr.clicked.connect(self.dlg_naderr.show)

        for i in range(table_Equip.columnCount()):
            table_Equip.header().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        table_Equip.header().setSectionResizeMode(0, QHeaderView.Interactive)
        table_Equip.header().setSectionResizeMode(2, QHeaderView.Interactive)



        frmObj.cmdStrat_go.clicked.connect(self.cmdStrat_go_clicked)

        self.mp_threads = []

        frmObj.cmdMPUpdateMonnies.clicked.connect(self.cmdMPUpdateMonnies_clicked)


        self.compact_window = Dlg_Compact(self)

        def cmdCompact_clicked():
            self.cmdStrat_go_clicked()
            with QBlockSig(self.compact_window.ui.cmdOnTop):
                self.compact_window.ui.cmdOnTop.setChecked(frmObj.actionWindow_Always_on_Top.isChecked())
            self.compact_window.show()

        frmObj.cmdCompact.clicked.connect(cmdCompact_clicked)


        #frmObj.table_Equip.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        #frmObj.table_FS.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        frmObj.table_Strat_FS.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        frmObj.table_Strat.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        frmObj.table_Strat_Equip.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        frmObj.cmd_Strat_Graph.clicked.connect(self.cmd_Strat_Graph_clicked)
        frmObj.table_Equip.setSortingEnabled(True)
        frmObj.table_genome.sig_selected_genome_changed.connect(self.table_genome_sig_selected_genome_changed)
        frmObj.table_FS_Cost.sig_fs_calculated.connect(self.table_FS_Cost_sig_fs_calculated)
        frmObj.table_Equip.sig_fs_list_updated.connect(frmObj.table_FS_Cost.reload_list)
        frmObj.treeFS_Secondary.sig_fsl_invalidated.connect(self.treeFS_Secondary_sig_fsl_invalidated)

        frmObj.table_Strat_FS.setSortingEnabled(True)
        frmObj.table_Strat_Equip.setSortingEnabled(True)
        frmObj.table_Equip.setIconSize(QSize(32, 32))
        try:
            self.open_file(file)
        except (IOError, SettingsException):
            self.show_warning_msg('Running for the first time? Could not load the settings file. One will be created.')

    def treeFS_Secondary_sig_fsl_invalidated(self):
        self.ui.table_genome.fls_invalidated()
        self.invalidate_equipment()
        self.ui.table_FS_Cost_Secondary.cmdFSRefresh_clicked()

    def table_FS_Cost_sig_fs_calculated(self):
        self.ui.table_genome.fs_list_updated()
        self.invalidate_equipment()
        self.ui.table_FS_Cost_Secondary.cmdFSRefresh_clicked()

    def table_genome_sig_selected_genome_changed(self):
        #self.model.invalidate_secondary_fs()
        self.invalidate_equipment()
        self.ui.table_FS_Cost_Secondary.cmdFSRefresh_clicked()
        self.ui.treeFS_Secondary.refresh_strat()

    def evolve_thread_created(self, thrd):
        self.evolve_threads.append(thrd)

    def evolve_thread_destroyed(self, thrd):
        self.evolve_threads.remove(thrd)

    def dlg_login_sig_Market_Ready(self, mk_updator):
        settings = self.model.settings
        itm_store = settings[settings.P_ITEM_STORE]
        itm_store.price_updator = mk_updator
        self.show_green_msg('Connected to Central Market')
        self.ui.cmdMPUpdateMonnies.setEnabled(True)
        self.cmdMPUpdateMonnies_clicked()

    def cmdMPUpdateMonnies_callback(self, thread, ret):
        if isinstance(ret, Exception):
            print(ret)
            self.show_critical_error('Error contacting central market')
        else:
            self.update_item_store_incl_ui()
            self.model.settings.invalidate()
            self.ui.statusbar.showMessage('Material item prices updated')
        thread.wait(2000)
        if thread.isRunning():
            thread.terminate()
        self.mp_threads.remove(thread)

    def cmdMPUpdateMonnies_clicked(self):
        thread = MPThread(self.get_item_store_incl)
        self.mp_threads.append(thread)
        thread.sig_done.connect(self.cmdMPUpdateMonnies_callback)
        thread.start()

    def get_mp_thread(self, gear_list:List[Gear]):
        thread = MPThread(self.model.update_costs, gear_list)
        self.mp_threads.append(thread)
        thread.sig_done.connect(self.mp_thread_callback)
        return thread

    def mp_thread_callback(self, thread:QThread, ret):
        if isinstance(ret, Exception):
            print(ret)
            self.show_critical_error('Error contacting central market')
        thread.wait(2000)
        if thread.isRunning():
            thread.terminate()
        self.mp_threads.remove(thread)

    def closeEvent(self, *args, **kwargs):
        model = self.model
        for thrd in self.evolve_threads:
            thrd.pull_the_plug()
            thrd.wait()
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
                self.load_file_unsafe(this_file)
            except IOError:
                self.show_warning_msg('Cannot load file. A settings JSON file is expected.')

    def showEvent(self, a0: QtGui.QShowEvent) -> None:
        super(Frm_Main, self).showEvent(a0)
        update_con = urllib3.connection_from_url(STR_URL_UPDATE_HOST)
        try:
            response = update_con.request('GET', STR_URL_UPDATE_LOC, headers={
                'User-Agent': 'Mozilla/5.0'
            })
            str_json = response.data.decode('utf-8')
            obj = json.loads(str_json)
            tag_name = obj['tag_name']
            if Version(tag_name) > Version(self.version):
                self.show_warning_msg('A new version is available for download. Click "Help" -> "Download Updates" on the main menu.')
        finally:
            update_con.close()

    def upgrade_gear(self, dis_gear, this_item=None):
        table_Equip = self.ui.table_Equip
        if this_item is None:
            try:
                this_item = table_Equip.find_top_lvl_item_from_gear(dis_gear)
            except Exception as e:
                self.show_critical_error(str(e))
                return None
        try:
            dis_gear.upgrade()
            self.model.save()
        except KeyError:
            self.show_warning_msg('Cannot upgrade gear past: ' + str(dis_gear.enhance_lvl))
            return
        self.refresh_gear_obj(dis_gear, this_item=this_item)

    def downgrade_gear(self, dis_gear, this_item=None):
        table_Equip = self.ui.table_Equip
        if this_item is None:
            try:
                this_item = table_Equip.find_top_lvl_item_from_gear(dis_gear)
            except Exception as e:
                self.show_critical_error(str(e))
                return None
        try:
            dis_gear.downgrade()
            self.model.save()
        except KeyError:
            self.show_warning_msg('Cannot downgrade gear below: ' + str(dis_gear.enhance_lvl))
            return
        self.refresh_gear_obj(dis_gear, this_item=this_item)

    def simulate_fail_gear(self, dis_gear, this_item=None):
        frmObj = self.ui
        table_Equip = frmObj.table_Equip
        if this_item is None:
            try:
                this_item = table_Equip.find_top_lvl_item_from_gear(dis_gear)
            except Exception as e:
                self.show_critical_error(str(e))
                return None

        gw: GearWidget = table_Equip.itemWidget(this_item, 0)
        if isinstance(dis_gear, Classic_Gear):
            if gw.gear.get_enhance_lvl_idx() >= gw.gear.get_backtrack_start():
                self.downgrade_gear(dis_gear, this_item=this_item)
        elif isinstance(dis_gear, Smashable):
            gw.chkInclude.setCheckState(Qt.Unchecked)
            self.model.save()
            self.refresh_gear_obj(dis_gear, this_item=this_item)

    def simulate_success_gear(self, dis_gear, this_item=None):
        frmObj = self.ui
        table_Equip = frmObj.table_Equip
        if this_item is None:
            try:
                this_item = table_Equip.find_top_lvl_item_from_gear(dis_gear)
            except Exception as e:
                self.show_critical_error(str(e))
                return None

        gw: GearWidget = table_Equip.itemWidget(this_item, 0)
        gear = gw.gear
        lvl_index = gear.get_enhance_lvl_idx() + 1
        if lvl_index >= len(gear.gear_type.lvl_map):
            gw.chkInclude.setCheckState(Qt.Unchecked)
        else:
            gw.cmbLevel.setCurrentIndex(lvl_index)
        self.model.save()
        self.refresh_gear_obj(dis_gear, this_item=this_item)

    def refresh_gear_obj(self, dis_gear, this_item=None):
        """
        This change can be in the strat window or in the minimal window. The gear widget object may need to be
        syncronized

        :param dis_gear:
        :param this_item:
        :return:
        """
        table_Equip = self.ui.table_Equip
        if this_item is None:
            try:
                this_item = table_Equip.find_top_lvl_item_from_gear(dis_gear)
            except Exception as e:
                self.show_critical_error(str(e))

        self.invalidate_equipment(this_item)
        gw = table_Equip.itemWidget(this_item, 0)
        gw.update_data()
        if self.strat_go_mode:
            self.cmdStrat_go_clicked()

    def clear_data(self):
        self.eh_c = None
        self.ui.table_FS_Cost.reset_exception_boxes()

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

    def cmdStrat_go_clicked(self):
        model = self.model
        settings = model.settings
        enhance_me = settings[settings.P_ENHANCE_ME]
        fail_stackers = settings[settings.P_FAIL_STACKERS]
        frmObj = self.ui
        tw = frmObj.table_Strat

        self.strat_go_mode = True

        #for row in range(0, tw.rowCount()):
        #    tw.removeRow(0)
        self.invalidate_strategy()

        if not len(model.cum_fs_cost) > 0:
            frmObj.table_FS_Cost.cmdFSRefresh_clicked()
        if model.gear_cost_needs_update:
            try:
                frmObj.table_Equip.cmdEquipCost_clicked()
            except ValueError as e:
                self.show_warning_msg(str(e))
                return

        mod_idx_gear_map = {}

        mod_enhance_me = enhance_me[:]
        current_gear_idx = len(enhance_me)
        self.mod_enhance_split_idx = current_gear_idx
        for i in range(0, frmObj.table_Equip.topLevelItemCount()):
            twi = frmObj.table_Equip.topLevelItem(i)
            master_gw: GearWidget = frmObj.table_Equip.itemWidget(twi, 0)
            if master_gw.chkInclude.checkState() == Qt.Checked:
                master_gear = master_gw.gear
                if master_gear not in enhance_me:
                    continue
                for j in range(0, twi.childCount()):
                    child = twi.child(j)
                    child_gw: GearWidget = frmObj.table_Equip.itemWidget(child, 0)
                    if child_gw.chkInclude.checkState() == Qt.Checked:
                        child_gear = child_gw.gear

                        child_gear.cost_vec = numpy.array(master_gear.cost_vec, copy=True)
                        child_gear.restore_cost_vec = numpy.array(master_gear.restore_cost_vec, copy=True)
                        child_gear.cost_vec_min = numpy.array(master_gear.cost_vec_min, copy=True)
                        child_gear.restore_cost_vec_min = numpy.array(master_gear.restore_cost_vec_min, copy=True)
                        mod_idx_gear_map[len(mod_enhance_me)] = child_gear
                        mod_enhance_me.append(child_gear)

        #try:
        strat = model.calcEnhances(enhance_me=mod_enhance_me)
        self.strat_solution = strat
        #except ValueError as f:
        #    self.show_warning_msg(str(f))
        #    return

        try:
            tw.currentItemChanged.disconnect()
        except TypeError:
            # This happens the first time because nothing is connected.
            pass
        tw.itemSelectionChanged.connect(self.table_Strat_selectionChanged)

        with Qt_common.SpeedUpTable(tw):
            for i, ev in enumerate(strat.iter_best_solutions()):
                fs_gear, fs_val, enh_gear, enh_val, cron = ev
                tw.insertRow(i)
                twi = QTableWidgetItem(str(i))
                tw.setItem(i, 0, twi)
                if fs_val >= enh_val:
                    is_fake_enh_gear = strat.is_fake(enh_gear)
                    two = self.make_gw(enh_gear, model, is_fake_enh_gear, cron)
                    if is_fake_enh_gear:
                        twi2 = QTableWidgetItem("YES")
                    twi2 = QTableWidgetItem("CRON")
                else:
                    two = GearWidget(fs_gear, model, edit_able=False, display_full_name=True)
                    twi2 = QTableWidgetItem("NO")
                two.add_to_table(tw, i, col=1)
                tw.setItem(i, 2, twi2)

        #tw.setVisible(True)
        self.adjust_equip_splitter()

    def make_gw(self, gear, model, is_fake, is_cron) -> GearWidget:
        two = GearWidget(gear, model, edit_able=False, display_full_name=True)
        if is_fake:
            two.enhance_overlay = False
            two.set_icon(pix.get_icon(STR_PIC_VALKS), enhance_overlay=False)
            two.lblName.setText('Save Stack: {}'.format(two.lblName.text()))
        if is_cron:
            two.set_trinket(pix[STR_PIC_CRON])
        return two

    def table_Strat_selectionChanged(self):
        row_obj = self.ui.table_Strat.selectedItems()[0]
        strat:StrategySolution = self.strat_solution

        if strat is None:
            self.show_critical_error('No details when strategy is not calculated.')
            return
        frmObj = self.ui
        model = self.model

        tw_eh = frmObj.table_Strat_Equip
        tw_fs = frmObj.table_Strat_FS
        if row_obj is None:
            # null selection is possible
            return
        p_int = row_obj.row()

        with QBlockSig(tw_eh):
            clear_table(tw_eh)
        with QBlockSig(tw_fs):
            clear_table(tw_fs)
        #tw_eh.setSortingEnabled(False)
        #tw_fs.setSortingEnabled(False)
        with Qt_common.SpeedUpTable(tw_eh):
            for i, ev in enumerate(strat.it_sort_enh_fs_lvl(p_int)):
                this_solution, best_solution = ev
                gear = this_solution.gear
                gear_cost = this_solution.cost
                gear_is_cron = this_solution.is_cron
                is_real_gear = strat.is_fake(gear)

                tw_eh.insertRow(i)
                two = self.make_gw(gear, model, is_real_gear, gear_is_cron)
                two.add_to_table(tw_eh, i, col=0)

                twi = monnies_twi_factory(gear_cost)
                tw_eh.setItem(i, 1, twi)

                eh_idx = gear.get_enhance_lvl_idx()
                cost_vec_l = gear.cost_vec[eh_idx]
                idx_ = numpy.argmin(cost_vec_l)
                opti_val = cost_vec_l[idx_]
                optimality = (1.0 + ((opti_val - cost_vec_l[p_int]) / opti_val)) * 100
                twi = numeric_twi(STR_PERCENT_FORMAT.format(optimality))
                tw_eh.setItem(i, 2, twi)

                this_fail_map = numpy.array(gear.gear_type.map)[eh_idx][p_int]
                avg_num_attempt = numpy.divide(1.0, this_fail_map)
                avg_num_fails = avg_num_attempt - 1
                twi = numeric_twi(STR_TWO_DEC_FORMAT.format(avg_num_fails))
                tw_eh.setItem(i, 3, twi)

                confidence = binVf(avg_num_attempt, this_fail_map) * 100
                twi = numeric_twi(STR_PERCENT_FORMAT.format(confidence))
                tw_eh.setItem(i, 4, twi)

                twi = monnies_twi_factory(gear_cost - best_solution.cost)
                tw_eh.setItem(i, 5, twi)

        with Qt_common.SpeedUpTable(tw_fs):

            for i, ev in enumerate(strat.it_sort_fs_fs_lvl(p_int)):
                this_solution, best_solution = ev
                gear = this_solution.gear
                gear_cost = this_solution.cost
                gear_is_cron = this_solution.is_cron

                tw_fs.insertRow(i)
                two = self.make_gw(gear, model, False, gear_is_cron)
                two.add_to_table(tw_fs, i, col=0)


                twi = monnies_twi_factory(gear_cost)
                tw_fs.setItem(i, 1, twi)

                opti_val = best_solution.cost
                epsilon = numpy.finfo(numpy.float32).eps
                if abs(opti_val) <= epsilon:
                    if abs(gear_cost) <= epsilon:
                        optimality = 100
                    else:
                        optimality = -float('inf')
                else:
                    optimality = (1.0 - ((opti_val - gear_cost) / opti_val)) * 100
                twi = numeric_twi(STR_PERCENT_FORMAT.format(optimality))
                tw_fs.setItem(i, 2, twi)

    def downgrade(self, gw: GearWidget):
        try:
            gw.gear.downgrade()
        except KeyError:
            return
        gw.fix_cmb_lvl()
        self.refresh_gear_obj(gw.gear)
        gw.sig_gear_changed.emit(gw)

    def invalidate_fs_list(self):
        frmObj = self.ui
        tw = frmObj.table_FS_Cost
        self.model.invalidate_failstack_list()
        with QBlockSig(tw):
            clear_table(tw)
        self.invalidate_equipment()

    def invalidate_equipment(self, t_item:QTreeWidgetItem=None):
        frmObj = self.ui
        tw = frmObj.table_Equip
        if t_item is None:
            t_item = []
            for i in range(0, tw.topLevelItemCount()):
                t_item.append(tw.topLevelItem(i))
        elif isinstance(t_item, QTreeWidgetItem):
            t_item = [t_item]

        self.model.invalidate_enahce_list()
        for itm in t_item:
            gw = tw.itemWidget(itm, 0)
            gear = gw.gear
            gear.costs_need_update = True
            tw.invalidated_gear.add(gw.gear)
            parent_cost = int(round(gear.base_item_cost))
            str_monies = MONNIES_FORMAT.format(parent_cost)
            with QBlockSig(tw):
                itm.setText(2, str_monies)
                itm.setText(4, '')
                itm.setText(5, '')
                itm.setText(6, '')
                itm.setText(7, '')
                itm.setText(8, '')
                itm.setText(9, '')
                itm.setText(10, '')
                for i in range(0, itm.childCount()):
                    child = itm.child(i)
                    child_gw = tw.itemWidget(child, 0)
                    child_gw.gear.set_base_item_cost(parent_cost)
                    child.setText(2, str_monies)
                    child.setText(4, '')
                    child.setText(5, '')
                    child.setText(6, '')
                    child.setText(7, '')
                    child.setText(8, '')
                    child.setText(9, '')
                    child.setText(10, '')
        self.invalidate_strategy()

    def invalidate_strategy(self):
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
        self.compact_window.invalidate()
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
            self.open_file(fileName)
        else:
            self.ui.statusbar.showMessage('Aborted opening file.')

    def open_file(self, fileName):
        try:
            self.load_file_unsafe(fileName)
        except IOError:
            self.show_critical_error('Settings file could not be loaded.')
        except Exception as e:
            new_pat = self.backup_settings(fileName)
            self.show_critical_error(
                'Bad settings file. Please see "File"->"Open Log File" | Created backup: {}'.format(new_pat))
            print(e)
            print('### ERROR INFO ###')
            exec_info = sys.exc_info()[0]
            print("Traceback: ", exec_info)
            print(utils.getStackTrace())
            if hasattr(e, 'embedded'):
                print(e.embedded)
            for j in self.model.settings:
                print(j)
            print('### ###')
            return

    def clear_all(self):
        frmObj = self.ui
        self.model = None
        list(map(lambda x: clear_table(x), [frmObj.table_Strat, frmObj.table_FS_Cost,
                                          frmObj.table_Strat_Equip, frmObj.table_Strat_FS]))
        frmObj.table_Equip.clear()
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

    def backup_settings(self, str_path):
        new_path = str_path+str(time.time()) + '_backup'
        shutil.copyfile(str_path, new_path)
        return new_path

    def load_file_unsafe(self, str_path):
        self.clear_all()
        model = self.model
        settings = model.settings
        frmObj = self.ui

        try:
            if model is None:
                self.model = Enhance_model(file=str_path)
            else:
                self.model.load_from_file(str_path)
        except Exception as e:
            self.model = Enhance_model()
            raise SettingsException('Model could not load settings file', e)

        self.load_ui_common()

    def get_item_store_incl(self):
        settings = self.model.settings
        item_store = settings[settings.P_ITEM_STORE]
        cost_bs_a = item_store.get_cost(ItemStore.P_BLACK_STONE_ARMOR)
        cost_bs_w = item_store.get_cost(ItemStore.P_BLACK_STONE_WEAPON)
        cost_conc_a = item_store.get_cost(ItemStore.P_CONC_ARMOR)
        cost_conc_w = item_store.get_cost(ItemStore.P_CONC_WEAPON)

        cost_hard = item_store.get_cost(ItemStore.P_HARD_BLACK)
        cost_sharp = item_store.get_cost(ItemStore.P_SHARP_BLACK)

        cost_meme = item_store.get_cost(ItemStore.P_MEMORY_FRAG)
        cost_dscale = item_store.get_cost(ItemStore.P_DRAGON_SCALE)
        cost_caph = item_store.get_cost(ItemStore.P_CAPH_STONE)
        return cost_bs_a, cost_bs_w, cost_conc_a, cost_conc_w, cost_hard, cost_sharp, cost_meme, cost_dscale, cost_caph

    def update_item_store_incl_ui(self):
        ret = self.get_item_store_incl()
        frmObj = self.ui
        ui_list = [
            frmObj.spin_Cost_BlackStone_Armor,
            frmObj.spin_Cost_BlackStone_Weapon,
            frmObj.spin_Cost_ConcArmor,
            frmObj.spin_Cost_Conc_Weapon,
            frmObj.spinHard,
            frmObj.spinSharp,
            frmObj.spin_Cost_MemFrag,
            frmObj.spin_Cost_Dragon_Scale,
            frmObj.spin_Cost_CaphStone
        ]
        def blockset(z):
            x,y = z
            with QBlockSig(y):
                y.setValue(x)
        no_effect = [_ for _ in map(blockset, zip(ret, ui_list))]

    def load_ui_common(self):
        frmObj = self.ui
        model = self.model
        settings = model.settings

        frmObj.table_FS.set_common(model, self)
        frmObj.table_FS_Cost.set_common(model, self)
        frmObj.treeFS_Secondary.set_common(model, self)
        frmObj.table_Equip.set_common(model, self)
        frmObj.table_genome.set_common(model, self)
        frmObj.table_FS_Cost_Secondary.set_common(model, self)

        self.compact_window.set_common(model)
        self.dlg_gt_prob.set_common(model)

        def cost_mat_gen(unpack):
            txt_box, cost, set_costf, itm_txt = unpack
            with QBlockSig(txt_box):
                txt_box.setValue(cost)

            def spin_Cost_item_textChanged(str_val):
                try:
                    set_costf(str_val)
                    frmObj.statusbar.showMessage('Set '+itm_txt+' cost to: ' + str(str_val))
                    self.invalidate_fs_list()
                except ValueError:
                    self.show_warning_msg(STR_COST_ERROR, silent=True)
            try:
                txt_box.valueChanged.disconnect()
                txt_box.editingFinished.disconnect()
            except TypeError:
                pass  # First time loading. No signals
            txt_box.valueChanged.connect(spin_Cost_item_textChanged)
            txt_box.editingFinished.connect(model.save)

        def switch_mat_gen(unpack):
            chk_box, cost, set_costf, itm_txt = unpack
            with QBlockSig(chk_box):
                chk_box.setCheckState(Qt.Checked if cost else Qt.Unchecked)

            def chk_box_stateChanged(chk_state):
                try:
                    set_costf(True if chk_state == Qt.Checked else False)
                    frmObj.statusbar.showMessage('Set '+itm_txt+' to: ' + str(chk_state))
                    self.invalidate_fs_list()
                except ValueError:
                    self.show_warning_msg(STR_COST_ERROR, silent=True)
                model.save()

            try:
                chk_box.stateChanged.disconnect()
            except TypeError:
                pass  # First time loading. No signals
            chk_box.stateChanged.connect(chk_box_stateChanged)


        #item_store = settings[settings.P_ITEM_STORE]
        cost_cleanse = settings[settings.P_CLEANSE_COST]
        cost_cron = settings[settings.P_CRON_STONE_COST]
        cost_bs_a, cost_bs_w, cost_conc_a, cost_conc_w, cost_hard, cost_sharp, cost_meme, cost_dscale, cost_caph = self.get_item_store_incl()

        P_MARKET_TAX = settings[settings.P_MARKET_TAX]
        P_VALUE_PACK = settings[settings.P_VALUE_PACK]
        P_VALUE_PACK_ACTIVE = settings[settings.P_VALUE_PACK_ACTIVE]
        P_MERCH_RING = settings[settings.P_MERCH_RING]
        P_MERCH_RING_ACTIVE = settings[settings.P_MERCH_RING_ACTIVE]

        P_QUEST_FS_INC = settings[settings.P_QUEST_FS_INC]


        def updateMarketTaxUI():
            with QBlockSig(frmObj.spinMarketTax):
                frmObj.spinMarketTax.setValue(settings[settings.P_MARKET_TAX])

        list(map(cost_mat_gen, [
            [frmObj.spin_Cost_BlackStone_Armor, cost_bs_a, lambda x: self.model.set_cost_bs_a(x), 'Blackstone Armour'],
            [frmObj.spin_Cost_BlackStone_Weapon, cost_bs_w, lambda x: self.model.set_cost_bs_w(x), 'Blackstone Weapon'],
            [frmObj.spin_Cost_ConcArmor, cost_conc_a, lambda x: self.model.set_cost_conc_a(x), 'Conc Blackstone Armour'],
            [frmObj.spin_Cost_Conc_Weapon, cost_conc_w, lambda x: self.model.set_cost_conc_w(x), 'Conc Blackstone Weapon'],

            [frmObj.spinHard, cost_hard, lambda x: self.model.set_cost_hard(x),
             frmObj.lblHard.text()],
            [frmObj.spinSharp, cost_sharp, lambda x: self.model.set_cost_sharp(x),
             frmObj.lblSharp.text()],
            [frmObj.spin_Cost_CaphStone, cost_caph, lambda x: self.model.set_cost_caph(x),
             frmObj.lblCaphStone.text()],

            [frmObj.spin_Cost_Cleanse, cost_cleanse, lambda x: self.model.set_cost_cleanse(x), 'Gear Cleanse'],
            [frmObj.spin_Cost_Cron, cost_cron, lambda x: self.model.set_cost_cron(x), 'Cron Stone'],
            [frmObj.spin_Cost_MemFrag, cost_meme, lambda x: self.model.set_cost_meme(x), 'Memory Fragment'],
            [frmObj.spin_Cost_Dragon_Scale, cost_dscale, lambda x: self.model.set_cost_dragonscale(x), 'Dragon Scale'],
            [frmObj.spinMarketTax, P_MARKET_TAX, lambda x: self.model.set_market_tax(x), 'Market Tax'],
            [frmObj.spinValuePack, P_VALUE_PACK, lambda x: self.model.value_pack_changed(x), 'Value Pack Gain'],
            [frmObj.spinMerchantsRing, P_MERCH_RING, lambda x: self.model.merch_ring_changed(x), 'Merch Ring Pack Gain'],
            [frmObj.spinQuestFSInc, P_QUEST_FS_INC, lambda x: self.model.quest_fs_inc_changed(x), 'Quest FS Increase']
        ]))

        list(map(switch_mat_gen, [
            [frmObj.chkMerchantsRing, P_MERCH_RING_ACTIVE, lambda x: self.model.using_merch_ring(x), 'Merch Ring'],
            [frmObj.chkValuePack, P_VALUE_PACK_ACTIVE, lambda x: self.model.using_value_pack(x), 'Value Pack']
        ]))

        frmObj.chkValuePack.stateChanged.connect(updateMarketTaxUI)
        frmObj.chkMerchantsRing.stateChanged.connect(updateMarketTaxUI)
        frmObj.spinMerchantsRing.valueChanged.connect(updateMarketTaxUI)
        frmObj.spinValuePack.valueChanged.connect(updateMarketTaxUI)

        def fs_inc_change():
            self.dlg_alts.update_fs_min()
            self.dlg_naderr.update_fs_min()
            self.model.clean_min_fs()

        frmObj.spinQuestFSInc.valueChanged.connect(fs_inc_change)
        updateMarketTaxUI()
