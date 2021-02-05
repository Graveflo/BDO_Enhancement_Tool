# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import time
from queue import Empty

import numpy
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QPen, QColor
from PyQt5.QtWidgets import QMenu, QAction, QTableWidgetItem, QTableWidget, QWidgetAction, QSpinBox
from BDO_Enhancement_Tool.model import Enhance_model, evolve_p_s, FailStackList, fitness_func
from QtCommon.Qt_common import lbl_color_MainWindow
from BDO_Enhancement_Tool.WidgetTools import GearWidget
from pyqtgraph import PlotWidget, PlotItem, mkPen

from .Abstract_Table import AbstractTable

HEADER_NAME = 'Name'
HEADER_GENOME = 'Genome'
HEADER_FITNESS = 'Fitness'


class FslThread(QThread):
    sig_solution_found = pyqtSignal(float, object, name='sig_solution_found')
    sig_going_down = pyqtSignal(name='sig_going_down')

    def __init__(self, model, num_procs=4):
        super(FslThread, self).__init__()
        self.num_procs = num_procs
        self.model: Enhance_model  = model
        settings = model.settings
        self.settings = settings
        self.gl = settings[settings.P_FAIL_STACKER_SECONDARY].copy()
        self.live = True

    def run(self) -> None:
        model = self.model
        settings = self.settings
        retn_q, procs = evolve_p_s(self.num_procs, settings, model.primary_fs_cost, model.primary_cum_fs_cost, secondaries=self.gl)
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


class TableGenome(QTableWidget, AbstractTable):
    HEADERS = [HEADER_NAME, HEADER_GENOME, HEADER_FITNESS]

    def __init__(self, *args, **kwargs):
        self.pool_size = 4
        super(TableGenome, self).__init__(*args, **kwargs)
        self.graph: PlotWidget = None
        self.gnome_thread: FslThread = None
        self.working_list = []
        self.plot_items = []
        self.chosen_fsl: FailStackList = None
        self.chosen_plot = None
        self.watch_list_fsl = []
        self.watch_list_plots = []

    def make_menu(self, menu: QMenu):
        action_add_watch_list = QAction('Add Watch List', menu)
        action_add_watch_list.triggered.connect(self.action_add_watch_list_triggered)
        menu.addAction(action_add_watch_list)
        action_remove_selected = QAction('Remove Selected', menu)
        action_remove_selected.triggered.connect(self.action_remove_selected_triggered)
        menu.addAction(action_remove_selected)
        menu.addSeparator()
        menu_pool_size = QMenu('Process Pool Size', menu)
        menu.addMenu(menu_pool_size)
        action_pool_size = QWidgetAction(menu)
        pool_size_spin = QSpinBox(menu_pool_size)
        action_pool_size.setDefaultWidget(pool_size_spin)
        pool_size_spin.setValue(self.pool_size)
        pool_size_spin.valueChanged.connect(self.pool_size_spin_valueChanged)
        menu_pool_size.addAction(action_pool_size)

        action_start_calculation = QAction('Start Calculation', menu)
        action_start_calculation.triggered.connect(self.action_update_costs_callback)
        menu.addAction(action_start_calculation)
        action_stop_calculation = QAction('Stop Calculating', menu)
        action_stop_calculation.triggered.connect(self.action_stop_calculation_callback)
        menu.addAction(action_stop_calculation)
        menu.addSeparator()
        action_set_color = QAction('Set Color', menu)
        action_set_color.triggered.connect(self.action_set_color_triggered)
        menu.addAction(action_set_color)

    def pool_size_spin_valueChanged(self, val):
        self.pool_size = val

    def action_set_color_triggered(self):
        pass

    def action_remove_selected_triggered(self):
        pass

    def get_ev_beg_idx(self):
        return 0

    def action_add_watch_list_triggered(self):
        plt = self.graph.plot(numpy.arange(1, len(self.enh_model.primary_fs_cost) + 1), self.enh_model.primary_fs_cost)
        self.plt = plt

    def action_update_costs_callback(self):
        if self.gnome_thread is None:
            do = True
        elif not self.gnome_thread.isRunning():
            do = True
        else:
            do = False
        if do:
            self.gnome_thread = FslThread(self.enh_model, num_procs=8)
            self.gnome_thread.sig_solution_found.connect(self.gnome_thread_sig_solution_found)
            self.gnome_thread.sig_going_down.connect(self.gnome_thread_sig_going_down)
            self.gnome_thread.start()

    def gnome_thread_sig_solution_found(self, optim, gnome):
        if len(self.working_list) > 0 and optim <= fitness_func(self.working_list[-1].fs_cost):
            return
        if len(self.plot_items) > 5:
            self.graph.removeItem(self.plot_items[0])
            self.plot_items = self.plot_items[1:]
            self.removeRow(0)
            self.working_list = self.working_list[1:]
        twi_gnome = QTableWidgetItem(str(gnome[1:]))
        rc = self.rowCount()
        self.insertRow(rc)
        secondary_gear = self.gnome_thread.gl[gnome[0]]
        two = GearWidget(secondary_gear, self.frmMain, edit_able=False, display_full_name=False, enhance_overlay=False)
        two.add_to_table(self, rc, col=0)
        fsl = FailStackList(self.enh_model.settings, secondary_gear, self.enh_model.optimal_fs_items, self.enh_model.primary_fs_cost, self.enh_model.primary_cum_fs_cost)
        fsl.set_gnome(gnome[1:])
        #fsl.starting_pos = gnome[1]
        #fsl.secondary_map = gnome[2:]

        fsl.evaluate_map()
        self.working_list.append(fsl)
        plt = self.graph.plot(numpy.arange(1, len(fsl.fs_cost) + 1), fsl.fs_cum_cost)
        #plt = self.graph.plot(numpy.arange(1, len(self.enh_model.primary_fs_cost) + 1), self.enh_model.primary_fs_cost)
        self.plot_items.append(plt)
        self.setItem(rc, 1, twi_gnome)
        self.setItem(rc, 2, QTableWidgetItem(str(-optim)))

        opac = 255
        for plt in reversed(self.plot_items):
            this_pen = mkPen(255, 255, 255, opac)
            plt.setPen(this_pen)
            opac *= 0.65
            opac = int(round(opac))

    def gnome_thread_sig_going_down(self):
        if self.gnome_thread is not None:
            self.gnome_thread.wait()
            self.gnome_thread = None

    def action_stop_calculation_callback(self):
        if self.gnome_thread is not None:
            self.gnome_thread.pull_the_plug()

    def set_common(self, model: Enhance_model, frmMain: lbl_color_MainWindow):
        super(TableGenome, self).set_common(model, frmMain)
        self.graph = frmMain.ui.graph_genome
