# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑  ❧
"""
import os
from ast import literal_eval
import time
from queue import Empty
from typing import Set
import numpy
from pyqtgraph import PlotWidget, mkPen, PlotItem
from PyQt6.QtCore import QThread, pyqtSignal, QModelIndex, Qt, QSize
from PyQt6.QtGui import QColor, QIcon, QAction
from PyQt6.QtWidgets import QMenu, QTreeWidget, \
    QTreeWidgetItem, QColorDialog, QDialog

from BDO_Enhancement_Tool.model import Enhance_model
from BDO_Enhancement_Tool.fsl import FailStackList
from BDO_Enhancement_Tool.EvolveFsl import EvolveSettings, evolve_p_s, fitness_funcs
from BDO_Enhancement_Tool.Qt_common import lbl_color_MainWindow, RGBA_to_Qcolor
from BDO_Enhancement_Tool.WidgetTools import GearWidget, QBlockSig
from BDO_Enhancement_Tool.common import IMG_TMP
from BDO_Enhancement_Tool.Core.ItemStore import STR_FMT_ITM_ID
from BDO_Enhancement_Tool.Core.Gear import Gear
from BDO_Enhancement_Tool.Forms.GeneticSettings import Ui_Dialog
from BDO_Enhancement_Tool.qt_UI_Common import pix, STR_PLUS_PIC, STR_CHECK_PIC, STR_MINUS_PIC, STR_CALC_PIC, \
    STR_STOP_PIC, STR_DIAL_PIC

from .Abstract_Table import AbstractTable

HEADER_NAME = 'Name'
HEADER_GENOME = 'Genome'
HEADER_FITNESS = 'Fitness'
HEADER_NUM_FS = '# FS'


class DlgEvolveSettings(QDialog):
    def __init__(self, *args, **kwargs):
        super(DlgEvolveSettings, self).__init__(*args, **kwargs)
        frmObj = Ui_Dialog()
        self.ui = frmObj
        frmObj.setupUi(self)
        counter = 0
        for key in fitness_funcs:
            frmObj.comboFitnessFunction.addItem(key)
            if key == 'avg':
                frmObj.comboFitnessFunction.setCurrentIndex(counter)
            counter += 1

    def get_settings_obj(self) -> EvolveSettings:
        frmObj = self.ui
        settings = EvolveSettings()
        settings.num_procs = frmObj.spinNumProcs.value()
        settings.num_fs = frmObj.spinFS.value()
        settings.pop_size = frmObj.spinPopulationSize.value()
        settings.num_elites = frmObj.spinNumElites.value()
        settings.brood_size = frmObj.spinBroodSize.value()
        settings.ultra_elite = frmObj.spinUltraElite.value()
        settings.mutation_rate = frmObj.spinMutationRate.value()
        settings.extinction_epoch = frmObj.spinExtinctionEpoch.value()
        settings.trait_dom = frmObj.spinTraitDom.value()
        settings.max_mutation = frmObj.spinMaxMutation.value()
        settings.penalize_supremacy = frmObj.chkSupremacy.isChecked()
        settings.oppressive_mode = frmObj.chkOpress.isChecked()
        settings.fitness_function = frmObj.comboFitnessFunction.currentText()
        return settings


class FslThread(QThread):
    sig_solution_found = pyqtSignal(float, object, name='sig_solution_found')
    sig_going_down = pyqtSignal(name='sig_going_down')

    def __init__(self, model: Enhance_model, ev_set:EvolveSettings):
        super(FslThread, self).__init__()
        self.ev_set = ev_set
        self.model = model
        settings = model.settings
        self.settings = settings
        self.gl = settings[settings.P_FAIL_STACKER_SECONDARY].copy()
        self.live = True

    def run(self) -> None:
        model = self.model
        settings = self.settings
        retn_q, procs = evolve_p_s(settings, model.primary_fs_cost, model.primary_cum_fs_cost, self.ev_set, secondaries=self.gl)
        for i in procs:
            i.start()
        while self.live:
            try:
                gnome = retn_q.get(block=False)
                self.sig_solution_found.emit(gnome[0], gnome[2])
            except Empty:
                time.sleep(1)
        for p in procs:
            p.terminate()
        self.sig_going_down.emit()

    def pull_the_plug(self):
        self.live = False


class GearAction(QAction):
    spec_triggered = pyqtSignal(object, name='')
    def __init__(self, gear:Gear, *args, **kwargs):
        super(GearAction, self).__init__(*args, **kwargs)
        self.gear = gear
        if gear.item_id is not None:
            fn = STR_FMT_ITM_ID.format(gear.item_id)
            icon_path = os.path.join(IMG_TMP, fn + '.png')
            if os.path.isfile(icon_path):
                self.setIcon(pix.get_icon(icon_path))
        self.triggered.connect(self.emitit)

    def emitit(self):
        self.spec_triggered.emit(self.gear)


class AbstractETWI(QTreeWidgetItem):
    def __init__(self, model:Enhance_model, *args, **kwargs):
        super(AbstractETWI, self).__init__(*args, **kwargs)
        self.model = model
        self.setFlags(self.flags() | Qt.ItemFlag.ItemIsEditable)
        self.ohhash = time.time()

    def __hash__(self):
        return hash(self.ohhash)

    def edit_request(self, column):
        return True


class EvolveSolutionWidget(AbstractETWI):
    def __init__(self, model:Enhance_model, *args, fsl=None, checked=True, **kwargs):
        self.plt = None
        self.genome = None
        if fsl is None:
            fsl = FailStackList(model.settings, None, None, None, None)
        self.fsl: FailStackList = fsl
        self.invalidated = True  # Random edits will trigger re-draw (dont want that)
        self.checked = checked
        super(EvolveSolutionWidget, self).__init__(model, *args, **kwargs)

    def set_gear(self, gear: Gear):
        if gear is None:
            self.invalidate_plot()
        self.fsl.secondary_gear = gear
        self.update_gw()
        if self.genome is not None:
            self.check_error()

    def update_data(self):
        self.update_gw()
        self.update_genome()
        self.update_num_fs()

    def update_num_fs(self):
        tree = self.treeWidget()
        idx_NUM_FS = tree.get_header_index(HEADER_NUM_FS)
        with QBlockSig(self.treeWidget()):
            self.setText(idx_NUM_FS, str(self.fsl.num_fs))

    def update_gw(self):
        gear = self.fsl.secondary_gear
        tree = self.treeWidget()
        idx_NAME = tree.get_header_index(HEADER_NAME)
        if gear is not None:
            this_gw = GearWidget(gear, self.model, edit_able=False, display_full_name=False, enhance_overlay=False,
                                 check_state=Qt.CheckState.Checked if self.checked else Qt.CheckState.Unchecked)
            this_gw.chkInclude.stateChanged.connect(self.gear_widget_chkInclude_stateChanged)
            with QBlockSig(tree):
                self.setText(idx_NAME, '')
                tree.setItemWidget(self, idx_NAME, this_gw)
            tree.updateGeometry()
            if self.checked:
                self.check_error()
        else:
            tree.removeItemWidget(self, idx_NAME)

    def update_genome(self):
        tree = self.treeWidget()
        idx_GENOME = tree.get_header_index(HEADER_GENOME)
        with QBlockSig(self.treeWidget()):
            self.setText(idx_GENOME, str(self.fsl.get_gnome()))

    def set_fsl(self, fsl: FailStackList):
        self.fsl = fsl
        self.set_gear(fsl.secondary_gear)
        self.set_gnome(fsl.get_gnome())

    def gear_widget_chkInclude_stateChanged(self, state):
        if state:
            self.checked = True
            self.check_error()
        else:
            self.checked = False
            self.invalidate_plot()

    def set_gnome(self, genome):
        if genome == self.fsl.get_gnome():
            return
        self.gnome = genome
        self.fsl.set_gnome(genome)
        self.invalidate_plot()
        self.update_genome()
        try:
            self.fsl.set_gnome(genome)
        except IndexError:
            pass
        except ValueError:
            pass
        if self.fsl.secondary_gear is not None:
            self.check_error()

    def invalidate_plot(self):
        self.invalidated = True
        if self.plt is not None:
            parent: GenomeGroupTreeWidget = self.parent()
            graph = parent.graph
            graph.removeItem(self.plt)
            self.plt = None

    def plot(self):
        if self.invalidated and self.checked == True:
            parent: GenomeGroupTreeWidget = self.parent()
            graph = parent.graph
            fsl:FailStackList = self.fsl
            model = self.model
            model.check_calc_fs()
            if not self.fsl.has_ran():
                self.fsl.set_primary_data(model.optimal_fs_items, model.primary_fs_cost, model.primary_cum_fs_cost)
                fsl.evaluate_map()
            self.plt = graph.plot(numpy.arange(1, len(fsl.fs_cost) + 1), fsl.fs_cum_cost, pen=mkPen(parent.color))
            self.invalidated = False

    def check_error(self):
        tree = self.treeWidget()
        idx_GENOME = tree.get_header_index(HEADER_GENOME)
        self.setForeground(idx_GENOME, QColor(Qt.GlobalColor.black))
        if self.fsl.validate():
            settings = self.model.settings
            if self.fsl in settings[settings.P_GENOME_FS] and not self.fsl.has_ran():
                self.model.invalidate_secondary_fs()
                tree.sig_selected_genome_changed.emit()
            idx_GENOME = self.treeWidget().get_header_index(HEADER_GENOME)
            self.setBackground(idx_GENOME, QColor(Qt.GlobalColor.green).lighter())
            self.plot()
        else:
            idx_GENOME = self.treeWidget().get_header_index(HEADER_GENOME)
            self.setBackground(idx_GENOME, QColor(Qt.GlobalColor.red).lighter())

    def make_menu(self, menu: QMenu):
        menu.addSeparator()
        action_make_default = QAction('Use this solution', menu)
        action_make_default.setIcon(pix.get_icon(STR_CHECK_PIC))
        action_make_default.triggered.connect(self.action_make_default_triggered)
        menu.addAction(action_make_default)
        action_rem_default = QAction('Don\'t Use this solution', menu)
        action_rem_default.setIcon(pix.get_icon(STR_MINUS_PIC))
        action_rem_default.triggered.connect(self.remove_default_triggered)
        menu.addAction(action_rem_default)

    def remove_default_triggered(self):
        self.treeWidget().remove_default(self)

    def action_make_default_triggered(self):
        self.treeWidget().make_default(self)


class GenomeTreeWidgetItem(EvolveSolutionWidget):
    def __init__(self, model: Enhance_model, *args, **kwargs):
        if 'checked' not in kwargs:
            kwargs['checked'] = False
        super(GenomeTreeWidgetItem, self).__init__(model, *args, **kwargs)

    def edit_request(self, column):
        super(GenomeTreeWidgetItem, self).edit_request(column)
        idx_GENOME = self.treeWidget().get_header_index(HEADER_GENOME)
        if column == idx_GENOME:
            self.genome = None
            try:
                self.set_gnome(literal_eval(self.text(column)))
                self.treeWidget().check_selected_changed(self)
            except SyntaxError:
                self.check_error()
            except ValueError:
                self.check_error()

    def set_gear_action_triggered(self, gear):
        self.set_gear(gear)
        self.treeWidget().check_selected_changed(self)

    def make_menu(self, menu: QMenu):
        super(GenomeTreeWidgetItem, self).make_menu(menu)
        menu.addSeparator()
        menu_gear_list_gear = QMenu('Set Gear', menu)
        menu.addMenu(menu_gear_list_gear)
        model = self.model
        settings = model.settings
        for gear in settings[settings.P_FAIL_STACKER_SECONDARY]:
            this_action = GearAction(gear, gear.name, menu_gear_list_gear)
            this_action.spec_triggered.connect(self.set_gear_action_triggered)
            menu_gear_list_gear.addAction(this_action)


class GenomeGroupTreeWidget(AbstractETWI):
    def __init__(self, model: Enhance_model, graph: PlotWidget, *args, color=None, grp_name=None, **kwargs):
        super(GenomeGroupTreeWidget, self).__init__(model, *args, **kwargs)
        if color is None:
            color = QColor(Qt.GlobalColor.blue)
        if grp_name is None:
            grp_name = 'Unnamed'
        self.color = color
        self.graph = graph
        self.setText(0, grp_name)
        self.setBackground(1, color)

    def make_menu(self, menu: QMenu):
        menu.addSeparator()
        action_set_color = QAction('Set Color', menu)
        action_set_color.triggered.connect(self.action_set_color_triggered)
        menu.addAction(action_set_color)

    def action_set_color_triggered(self):
        cd = QColorDialog(self.color)
        cd.exec()
        this_color = cd.selectedColor()
        if this_color.isValid():
            idx_GENOME = self.treeWidget().get_header_index(HEADER_GENOME)
            self.setBackground(idx_GENOME, this_color)
            self.color = this_color
            for i in range(0, self.childCount()):
                child = self.child(i)
                if child.plt is not None:
                    child.plt.setPen(mkPen(color=self.color))


class UserGroupTreeWidgetItem(GenomeGroupTreeWidget):
    def __init__(self, model: Enhance_model, graph: PlotWidget, *args, **kwargs):
        super(UserGroupTreeWidgetItem, self).__init__(model, graph, *args, **kwargs)

    def make_menu(self, menu: QMenu):
        menu.addSeparator()
        action_add_genome = QAction('Add Genome', menu)
        action_add_genome.triggered.connect(self.action_add_genome_triggered)
        menu.addAction(action_add_genome)
        super(UserGroupTreeWidgetItem, self).make_menu(menu)

    def action_add_genome_triggered(self):
        new_item = GenomeTreeWidgetItem(self.model, self, ['right click to set gear', '<gnome here>', ''])
        #self.sig_item_added.emit(new_item)
        self.addChild(new_item)
        self.setExpanded(True)


class EvolveTreeWidget(GenomeGroupTreeWidget):
    def __init__(self,sig_thread_created, sig_thread_destroyed, model:Enhance_model, graph:PlotWidget, *args, color=None, grp_name=None, **kwargs):
        if color is None:
            color = QColor(Qt.GlobalColor.white)
        if grp_name is None:
            grp_name = 'Optimizer'
        super(EvolveTreeWidget, self).__init__(model, graph, *args, color=color, grp_name=grp_name, **kwargs)
        self.setText(2, 'Stopped')
        self.gnome_thread = None
        self.settings_dlg = DlgEvolveSettings()

        settings = model.settings
        num_fs = settings[settings.P_NUM_FS]
        self.settings_dlg.ui.spinFS.setMaximum(num_fs)
        self.settings_dlg.ui.spinFS.setMinimum(0)
        self.settings_dlg.ui.spinFS.setValue(num_fs)

        self.fit_func = None
        self.current_best = None
        self.sig_thread_created = sig_thread_created
        self.sig_thread_destroyed = sig_thread_destroyed

    def make_menu(self, menu: QMenu):
        super(EvolveTreeWidget, self).make_menu(menu)
        menu.addSeparator()
        action_set_parameters = QAction('Set Parameters', menu)
        action_set_parameters.setIcon(pix.get_icon(STR_DIAL_PIC))
        action_set_parameters.triggered.connect(self.action_set_parameters_callback)
        menu.addAction(action_set_parameters)
        action_start_calculation = QAction('Start Calculation', menu)
        action_start_calculation.triggered.connect(self.action_start_calculation_callback)
        action_start_calculation.setIcon(pix.get_icon(STR_CALC_PIC))
        menu.addAction(action_start_calculation)
        action_stop_calculation = QAction('Stop Calculating', menu)
        action_stop_calculation.setIcon(pix.get_icon(STR_STOP_PIC))
        action_stop_calculation.triggered.connect(self.action_stop_calculation_callback)
        menu.addAction(action_stop_calculation)

    def action_set_parameters_callback(self):
        self.settings_dlg.exec()

    def action_start_calculation_callback(self):
        if self.gnome_thread is None:
            do = True
        elif not self.gnome_thread.isRunning():
            do = True
        else:
            do = False
        if do:
            self.model.check_calc_fs()
            ev_set = self.settings_dlg.get_settings_obj()
            self.fit_func = fitness_funcs[ev_set.fitness_function]
            self.gnome_thread = FslThread(self.model, ev_set)
            self.gnome_thread.sig_solution_found.connect(self.gnome_thread_sig_solution_found)
            self.gnome_thread.sig_going_down.connect(self.gnome_thread_sig_going_down)
            self.sig_thread_created.emit(self.gnome_thread)
            self.gnome_thread.start()
            self.setExpanded(True)
            idx_FITNESS = self.treeWidget().get_header_index(HEADER_FITNESS)
            self.setText(idx_FITNESS, 'Started...')

    def gnome_thread_sig_solution_found(self, optim, gnome):
        if self.current_best is None:
            idx_FITNESS = self.treeWidget().get_header_index(HEADER_FITNESS)
            self.setText(idx_FITNESS, 'Running')
        elif optim <= self.current_best:
            return
        if self.childCount() > 5:
            itm:EvolveSolutionWidget = self.child(0)
            itm.invalidate_plot()
            self.removeChild(itm)

        self.current_best = optim
        secondary_gear = self.gnome_thread.gl[gnome[0]]
        fsl = FailStackList(self.model.settings, None, None, None, None, num_fs=self.gnome_thread.ev_set.num_fs)
        twi_gnome = EvolveSolutionWidget(self.model, fsl=fsl)
        self.addChild(twi_gnome)
        twi_gnome.set_gear(secondary_gear)
        twi_gnome.set_gnome(gnome[1:])
        twi_gnome.setText(2, str(-optim))

        opac = 255
        for twi_idx in reversed(range(0, self.childCount())):
            twi:EvolveSolutionWidget = self.child(twi_idx)
            plt:PlotItem = twi.plt
            if plt is not None:
                this_color = QColor(self.color)
                this_color.setAlpha(opac)
                this_pen = mkPen(this_color)
                plt.setPen(this_pen)
                opac *= 0.65
                opac = int(round(opac))

    def gnome_thread_sig_going_down(self):
        if self.gnome_thread is not None:
            self.gnome_thread.wait()
            self.sig_thread_destroyed.emit(self.gnome_thread)
            self.gnome_thread = None
        idx_FITNESS = self.treeWidget().get_header_index(HEADER_FITNESS)
        self.setText(idx_FITNESS, 'Stopped')

    def action_stop_calculation_callback(self):
        if self.gnome_thread is not None:
            self.gnome_thread.pull_the_plug()


class TableGenome(QTreeWidget, AbstractTable):
    sig_thread_created = pyqtSignal(object, name='sig_thread_created')
    sig_thread_destroyed = pyqtSignal(object, name='sig_thread_destroyed')
    sig_selected_genome_changed = pyqtSignal(name='sig_selected_genome_changed')
    sig_item_clicked = pyqtSignal(object, name='sig_item_clicked')
    HEADERS = [HEADER_NAME, HEADER_GENOME, HEADER_FITNESS, HEADER_NUM_FS]

    def __init__(self, *args, **kwargs):
        self.pool_size = 4
        super(TableGenome, self).__init__(*args, **kwargs)
        self.graph: PlotWidget = None
        self.itemChanged.connect(self.itemChanged_callback)
        self.chosen_twis:Set[EvolveSolutionWidget] = set()
        self.setIconSize(QSize(15,15))
        self.setColumnWidth(0, 230)
        self.clicked.connect(self.clicked_cb)

    def clicked_cb(self, index):
        twi = self.itemFromIndex(index)
        if isinstance(twi, EvolveSolutionWidget):
            fsl = twi.fsl
            if fsl.validate():
                self.sig_item_clicked.emit(fsl)

    def mouseReleaseEvent(self, a0) -> None:
        super(TableGenome, self).mouseReleaseEvent(a0)
        AbstractTable.mouseReleaseEvent(self, a0)

    def check_selected_changed(self, twi:EvolveSolutionWidget):
        if twi in self.chosen_twis:
            self.sig_selected_genome_changed.emit()

    def make_menu(self, menu: QMenu):
        super(TableGenome, self).make_menu(menu)
        menu.addSeparator()
        action_add_group = QAction('Add Group', menu)
        action_add_group.triggered.connect(self.action_add_group_triggered)
        action_add_group.setIcon(pix.get_icon(STR_PLUS_PIC))
        menu.addAction(action_add_group)
        action_add_optimizer = QAction('Add Optimizer', menu)
        action_add_optimizer.triggered.connect(self.action_add_optimizer_triggered)
        action_add_optimizer.setIcon(pix.get_icon(STR_PLUS_PIC))
        menu.addAction(action_add_optimizer)
        action_remove_selected = QAction('Remove Selected', menu)
        action_remove_selected.triggered.connect(self.action_remove_selected_triggered)
        action_remove_selected.setIcon(pix.get_icon(STR_MINUS_PIC))
        menu.addAction(action_remove_selected)

    def dropEvent(self, event) -> None:
        dragonto = self.itemAt(event.pos())
        if dragonto is None:
            event.ignore()
        else:
            event.accept()
            model = self.enh_model
            if isinstance(dragonto, UserGroupTreeWidgetItem):
                for i in self.selectedItems():
                    if i is dragonto:
                        continue  # don't drag a section onto itself

                    settings = self.enh_model.settings
                    fsls = settings[settings.P_GENOME_FS]
                    if isinstance(i, EvolveSolutionWidget):
                        parent = i.parent()
                        i.invalidate_plot()
                        i = parent.takeChild(parent.indexOfChild(i))
                        fsl = i.fsl
                        itm = GenomeTreeWidgetItem(model, dragonto, [''] * self.columnCount(), fsl=fsl)
                        if fsl in fsls:
                            itm.setIcon(0, pix.get_icon(STR_CHECK_PIC))
                            self.chosen_twis.remove(i)
                            self.chosen_twis.add(itm)
                        dragonto.addChild(itm)
                        itm.update_data()
                        itm.check_error()
                    elif isinstance(i, GenomeGroupTreeWidget):
                        for j in reversed(range(0, i.childCount())):
                            this_twi = i.child(j)
                            this_twi.invalidate_plot()
                            this_twi:EvolveSolutionWidget = i.takeChild(j)
                            fsl = this_twi.fsl
                            itm = GenomeTreeWidgetItem(model, dragonto, ['']*self.columnCount(), fsl=fsl)
                            if fsl in fsls:
                                itm.setIcon(0, pix.get_icon(STR_CHECK_PIC))
                                self.chosen_twis.remove(i)
                                self.chosen_twis.add(itm)
                            dragonto.addChild(itm)
                            itm.update_data()
                            itm.check_error()
                        self.takeTopLevelItem(self.indexOfTopLevelItem(i))
                self.update()

    def check_index_widget_menu(self, index:QModelIndex, menu:QMenu):
        itm = self.itemFromIndex(index)
        if itm is not None and hasattr(itm, 'make_menu'):
            itm.make_menu(menu)

    def gear_invalidated(self, gear:Gear):
        for i in range(0, self.topLevelItemCount()):
            tli = self.topLevelItem(i)
            for j in range(0, tli.childCount()):
                child = tli.child(j)
                if isinstance(child, EvolveSolutionWidget):
                    geer = child.fsl.secondary_gear
                    if geer is gear:
                        child.update_data()

    def fs_list_updated(self):
        for i in range(0, self.topLevelItemCount()):
            tli = self.topLevelItem(i)
            for j in range(0, tli.childCount()):
                itm = tli.child(j)
                if isinstance(itm, EvolveSolutionWidget):
                    itm.invalidate_plot()
                    itm.check_error()

    def itemChanged_callback(self, item:QTreeWidgetItem, col):
        self.clearSelection()
        if isinstance(item, GenomeTreeWidgetItem):
            item.edit_request(col)

    def action_add_optimizer_triggered(self):
        model = self.enh_model
        itm = EvolveTreeWidget(self.sig_thread_created, self.sig_thread_destroyed, model, self.graph, self, [''] * self.columnCount())

        self.addTopLevelItem(itm)

    def action_remove_selected_triggered(self):
        rems = []
        for itm in self.selectedItems():
            if isinstance(itm, EvolveTreeWidget):
                itm.action_stop_calculation_callback()
            if isinstance(itm, EvolveSolutionWidget):
                itm.invalidate_plot()
            if itm.parent() is None:
                rems.append(itm)
            else:
                itm.parent().removeChild(itm)
                if itm in self.chosen_twis:
                    self.chosen_twi = None
                    settings = self.enh_model.settings
                    if itm.fsl in settings[settings.P_GENOME_FS]:
                        self.enh_model.remove_fsl(itm.fsl)
                        self.sig_selected_genome_changed.emit()
        for itm in rems:
            for i in range(0, itm.childCount()):
                itm_c = itm.child(i)
                if isinstance(itm_c, EvolveSolutionWidget):
                    itm_c.invalidate_plot()
            self.takeTopLevelItem(self.indexOfTopLevelItem(itm))

    def make_default(self, twi:EvolveSolutionWidget):
        model = self.enh_model
        model.set_fsl(twi.fsl)
        self.chosen_twis.add(twi)
        twi.setIcon(0, pix.get_icon(STR_CHECK_PIC))
        self.sig_selected_genome_changed.emit()

    def remove_default(self, twi:EvolveSolutionWidget):
        model = self.enh_model
        if model.remove_fsl(twi.fsl):
            self.chosen_twis.remove(twi)
            twi.setIcon(0, QIcon())
            self.sig_selected_genome_changed.emit()

    def action_add_group_triggered(self):
        model = self.enh_model
        itm = UserGroupTreeWidgetItem(model, self.graph, self, ['']*self.columnCount())
        self.addTopLevelItem(itm)
        settings = model.settings
        fsl_l = settings[settings.P_FSL_L]

    def set_common(self, model: Enhance_model, frmMain: lbl_color_MainWindow):
        super(TableGenome, self).set_common(model, frmMain)
        self.graph = frmMain.ui.graph_genome
        self.sig_thread_created.connect(frmMain.evolve_thread_created)
        self.sig_thread_destroyed.connect(frmMain.evolve_thread_destroyed)

        settings = model.settings

        self.clear()

        fsl_l = settings[settings.P_FSL_L]
        checked = set()
        for name, color, children in fsl_l:
            itm = UserGroupTreeWidgetItem(model, self.graph, self, [''] * self.columnCount(), color=RGBA_to_Qcolor(color),
                                          grp_name=name)
            self.addTopLevelItem(itm)
            for child_obj in children:
                itmc = GenomeTreeWidgetItem(model, itm, [''] * self.columnCount(), checked=False)
                itm.addChild(itmc)

                if isinstance(child_obj, dict):
                    fsl = FailStackList(settings, None, None, None,None)
                    fsl.set_state_json(child_obj)
                else:
                    fsl = settings[settings.P_GENOME_FS][child_obj]
                    self.chosen_twis.add(itmc)
                    itmc.setIcon(0, pix.get_icon(STR_CHECK_PIC))
                checked.add(fsl)
                itmc.set_fsl(fsl)
                itmc.update_data()
            itm.setExpanded(True)

        unaccount = [x for x in settings[settings.P_GENOME_FS] if x not in checked]
        if len(unaccount) > 0:
            itm = UserGroupTreeWidgetItem(model, self.graph, self, [''] * self.columnCount(),
                                          color=QColor(Qt.GlobalColor.red),
                                          grp_name='Current Setting')
            self.addTopLevelItem(itm)
            for fsl in unaccount:
                itmc = GenomeTreeWidgetItem(model, itm, [''] * self.columnCount(), checked=False)
                itm.addChild(itmc)
                self.chosen_twis.add(itmc)
                itmc.setIcon(0, pix.get_icon(STR_CHECK_PIC))
                itmc.set_fsl(fsl)
                itmc.update_data()
            itm.setExpanded(True)

