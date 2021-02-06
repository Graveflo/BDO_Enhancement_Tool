# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import os
from ast import literal_eval
import time
from queue import Empty

import numpy
from PyQt5.QtCore import QThread, pyqtSignal, QModelIndex, Qt
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import QMenu, QAction, QTableWidgetItem, QTreeWidget, \
    QTreeWidgetItem, QColorDialog, QDialog
from BDO_Enhancement_Tool.model import Enhance_model, evolve_p_s, FailStackList, fitness_func, EvolveSettings, \
    fitness_funcs
from QtCommon.Qt_common import lbl_color_MainWindow
from BDO_Enhancement_Tool.WidgetTools import GearWidget, QBlockSig
from BDO_Enhancement_Tool.common import Gear, GEAR_ID_FMT, IMG_TMP
from Forms.GeneticSettings import Ui_Dialog
from pyqtgraph import PlotWidget, mkPen, PlotItem

from .Abstract_Table import AbstractTable

HEADER_NAME = 'Name'
HEADER_GENOME = 'Genome'
HEADER_FITNESS = 'Fitness'


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

    def pull_the_plug(self):
        self.live = False


class GearAction(QAction):
    spec_triggered = pyqtSignal(object, name='')
    def __init__(self, gear:Gear, *args, **kwargs):
        super(GearAction, self).__init__(*args, **kwargs)
        self.gear = gear
        if gear.item_id is not None:
            fn = GEAR_ID_FMT.format(gear.item_id)
            icon_path = os.path.join(IMG_TMP, fn + '.png')
            if os.path.isfile(icon_path):
                self.setIcon(QIcon(icon_path))
        self.triggered.connect(self.emitit)

    def emitit(self):
        self.spec_triggered.emit(self.gear)


class AbstractETWI(QTreeWidgetItem):
    def __init__(self, model:Enhance_model, *args, **kwargs):
        super(AbstractETWI, self).__init__(*args, **kwargs)
        self.model = model
        self.setFlags(self.flags() | Qt.ItemIsEditable)

    def edit_request(self, column):
        return True


class EvolveSolutionWidget(AbstractETWI):
    def __init__(self, model:Enhance_model, *args, **kwargs):
        self.plt = None
        self.genome = None
        self.fsl = None
        self.invalidated = True  # Random edits will trigger re-draw (dont want that)
        self.checked = True
        super(EvolveSolutionWidget, self).__init__(model, *args, **kwargs)

    def set_gear(self, gear:Gear):
        if gear is None:
            self.invalidate_plot()
        model = self.model
        tree = self.treeWidget()
        idx_NAME = tree.get_header_index(HEADER_NAME)
        this_gw = GearWidget(gear, self.model, edit_able=False, display_full_name=False, enhance_overlay=False, check_state=Qt.Checked)
        this_gw.chkInclude.stateChanged.connect(self.gear_widget_chkInclude_stateChanged)
        with QBlockSig(tree):
            self.setText(idx_NAME, '')
            tree.setItemWidget(self, idx_NAME, this_gw)
        self.fsl = FailStackList(model.settings, gear, model.optimal_fs_items, model.primary_fs_cost, model.primary_cum_fs_cost)
        self.invalidated = True
        if self.genome is not None:
            self.set_gnome(self.genome)

    def gear_widget_chkInclude_stateChanged(self, state):
        if state:
            self.checked = True
            self.check_error()
        else:
            self.checked = False
            self.invalidate_plot()

    def set_gnome(self, genome):
        self.genome = genome
        self.invalidated = True
        tree = self.treeWidget()
        idx_GENOME = tree.get_header_index(HEADER_GENOME)
        with QBlockSig(self.treeWidget()):
            self.setText(idx_GENOME, str(genome))
        if self.fsl is not None:
            try:
                self.fsl.set_gnome(genome)
            except IndexError:
                pass
            except ValueError:
                pass
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
            self.invalidate_plot()
            parent: GenomeGroupTreeWidget = self.parent()
            graph = parent.graph
            fsl:FailStackList = self.fsl
            fsl.evaluate_map()
            self.plt = graph.plot(numpy.arange(1, len(fsl.fs_cost) + 1), fsl.fs_cum_cost, pen=mkPen(parent.color))
            self.invalidated = False

    def check_error(self):
        idx_GENOME = self.treeWidget().get_header_index(HEADER_GENOME)
        self.setForeground(idx_GENOME, QColor(Qt.black))
        if self.fsl is not None:
            if self.fsl.validate():
                idx_GENOME = self.treeWidget().get_header_index(HEADER_GENOME)
                self.setBackground(idx_GENOME, QColor(Qt.green).lighter())
                self.plot()
                return
        idx_GENOME = self.treeWidget().get_header_index(HEADER_GENOME)
        self.setBackground(idx_GENOME, QColor(Qt.red).lighter())

    def make_menu(self, menu:QMenu):
        pass


class GenomeTreeWidgetItem(EvolveSolutionWidget):
    def __init__(self, model:Enhance_model, *args, **kwargs):
        super(GenomeTreeWidgetItem, self).__init__(model, *args, **kwargs)

    def edit_request(self, column):
        super(GenomeTreeWidgetItem, self).edit_request(column)
        idx_GENOME = self.treeWidget().get_header_index(HEADER_GENOME)
        if column == idx_GENOME:
            self.genome = None
            try:
                self.set_gnome(literal_eval(self.text(column)))
            except SyntaxError:
                self.check_error()
            except ValueError:
                self.check_error()

    def make_menu(self, menu:QMenu):
        menu.addSeparator()
        menu_gear_list_gear = QMenu('Set Gear', menu)
        menu.addMenu(menu_gear_list_gear)
        model = self.model
        settings = model.settings
        for gear in settings[settings.P_FAIL_STACKER_SECONDARY]:
            this_action = GearAction(gear, gear.name, menu_gear_list_gear)
            this_action.spec_triggered.connect(self.set_gear)
            menu_gear_list_gear.addAction(this_action)


class GenomeGroupTreeWidget(AbstractETWI):
    def __init__(self, model:Enhance_model, graph: PlotWidget, *args, color=None, grp_name=None, **kwargs):
        super(GenomeGroupTreeWidget, self).__init__(model, *args, **kwargs)
        if color is None:
            color = QColor(Qt.blue)
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
        cd.exec_()
        this_color = cd.selectedColor()
        if this_color.isValid():
            idx_GENOME = self.treeWidget().get_header_index(HEADER_GENOME)
            self.setBackground(idx_GENOME, this_color)
            self.color = this_color
            for i in range(0, self.childCount()):
                child = self.child(i)
                if child.plt is not None:
                    child.plt.setPen(mkPen(color=self.color))

    def action_remove_selected_triggered(self):
        pass


class UserGroupTreeWidgetItem(GenomeGroupTreeWidget):

    def __init__(self, model:Enhance_model, graph: PlotWidget, *args, **kwargs):
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


class EvolveTreeWidget(GenomeGroupTreeWidget):
    def __init__(self,sig_thread_created, sig_thread_destroyed, model:Enhance_model, graph:PlotWidget, *args, color=None, grp_name=None, **kwargs):
        if color is None:
            color = QColor(Qt.white)
        if grp_name is None:
            grp_name = 'Optimizer'
        super(EvolveTreeWidget, self).__init__(model, graph, *args, color=color, grp_name=grp_name, **kwargs)
        self.setText(2, 'Stopped')
        self.gnome_thread = None
        self.settings_dlg = DlgEvolveSettings()
        self.fit_func = None
        self.current_best = None
        self.sig_thread_created = sig_thread_created
        self.sig_thread_destroyed = sig_thread_destroyed

    def make_menu(self, menu: QMenu):
        super(EvolveTreeWidget, self).make_menu(menu)
        menu.addSeparator()
        action_set_parameters = QAction('Set Parameters', menu)
        action_set_parameters.triggered.connect(self.action_set_parameters_callback)
        menu.addAction(action_set_parameters)
        action_start_calculation = QAction('Start Calculation', menu)
        action_start_calculation.triggered.connect(self.action_start_calculation_callback)
        menu.addAction(action_start_calculation)
        action_stop_calculation = QAction('Stop Calculating', menu)
        action_stop_calculation.triggered.connect(self.action_stop_calculation_callback)
        menu.addAction(action_stop_calculation)

    def action_set_parameters_callback(self):
        self.settings_dlg.exec_()

    def action_start_calculation_callback(self):
        if self.gnome_thread is None:
            do = True
        elif not self.gnome_thread.isRunning():
            do = True
        else:
            do = False
        if do:
            ev_set = self.settings_dlg.get_settings_obj()
            self.fit_func = fitness_funcs[ev_set.fitness_function]
            self.gnome_thread = FslThread(self.model, ev_set)
            self.gnome_thread.sig_solution_found.connect(self.gnome_thread_sig_solution_found)
            self.gnome_thread.sig_going_down.connect(self.gnome_thread_sig_going_down)
            self.sig_thread_created.emit(self.gnome_thread)
            self.gnome_thread.start()

    def gnome_thread_sig_solution_found(self, optim, gnome):
        if self.current_best is not None and optim <= self.current_best:
            return
        if self.childCount() > 5:
            itm:EvolveSolutionWidget = self.child(0)
            itm.invalidate_plot()
            self.removeChild(itm)

        self.current_best = optim
        secondary_gear = self.gnome_thread.gl[gnome[0]]
        twi_gnome = EvolveSolutionWidget(self.model)
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

    def action_stop_calculation_callback(self):
        if self.gnome_thread is not None:
            self.gnome_thread.pull_the_plug()



class TableGenome(QTreeWidget, AbstractTable):
    sig_thread_created = pyqtSignal(object, name='sig_thread_created')
    sig_thread_destroyed = pyqtSignal(object, name='sig_thread_destroyed')
    HEADERS = [HEADER_NAME, HEADER_GENOME, HEADER_FITNESS]

    def __init__(self, *args, **kwargs):
        self.pool_size = 4
        super(TableGenome, self).__init__(*args, **kwargs)
        self.graph: PlotWidget = None
        self.itemChanged.connect(self.itemChanged_callback)

    def make_menu(self, menu: QMenu):
        super(TableGenome, self).make_menu(menu)
        menu.addSeparator()
        action_add_group = QAction('Add Group', menu)
        action_add_group.triggered.connect(self.action_add_group_triggered)
        menu.addAction(action_add_group)
        action_add_optimizer = QAction('Add Optimizer', menu)
        action_add_optimizer.triggered.connect(self.action_add_optimizer_triggered)
        menu.addAction(action_add_optimizer)
        action_remove_selected = QAction('Remove Selected', menu)
        action_remove_selected.triggered.connect(self.action_remove_selected_triggered)
        menu.addAction(action_remove_selected)

    def dropEvent(self, event) -> None:
        print(event)

    def check_index_widget_menu(self, index:QModelIndex, menu:QMenu):
        itm = self.itemFromIndex(index)
        if itm is not None and hasattr(itm, 'make_menu'):
            itm.make_menu(menu)

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
            if isinstance(itm, GenomeTreeWidgetItem):
                itm.invalidate_plot()
            if itm.parent() is None:
                rems.append(itm)
            else:
                itm.parent().removeChild(itm)
        for itm in rems:
            self.takeTopLevelItem(self.indexOfTopLevelItem(itm))

    def get_ev_beg_idx(self):
        return 0

    def action_add_group_triggered(self):
        model = self.enh_model
        itm = UserGroupTreeWidgetItem(model, self.graph, self, ['']*self.columnCount())
        self.addTopLevelItem(itm)

    def set_common(self, model: Enhance_model, frmMain: lbl_color_MainWindow):
        super(TableGenome, self).set_common(model, frmMain)
        self.graph = frmMain.ui.graph_genome
        self.sig_thread_created.connect(frmMain.evolve_thread_created)
        self.sig_thread_destroyed.connect(frmMain.evolve_thread_destroyed)
