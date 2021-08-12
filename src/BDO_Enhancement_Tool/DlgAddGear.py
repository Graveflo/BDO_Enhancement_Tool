#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import os
from time import time
from typing import List

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QObject
import math
import queue
import urllib3
from fuzzywuzzy import process

from .Forms.dlg_add_gear import Ui_dlgSearchGear
from .bdo_database.gear_database import GearData
from .Core.Gear import Gear
from .qt_UI_Common import pix
from .Qt_common import QBlockSig
from .common import IMG_TMP, ENH_IMG_PATH, GEAR_DB_MANAGER

urllib3.disable_warnings()


class FuzzyMatcher(object):
    def __init__(self, gear_data:List[GearData]):
        self.data = {x:x.name for x in gear_data}

    def search(self, str_query) -> List[GearData]:
        sadf = process.extract(str_query, self.data, limit=None)
        parts = list(zip(*sadf))
        return parts[2]


GEAR_DB_MANAGER.dump_all()
matcher = FuzzyMatcher(list(GEAR_DB_MANAGER.id_cache.values()))


class ImageQueueThread(QtCore.QThread):
    DEATH = -42069
    sig_icon_ready = QtCore.pyqtSignal(str, str)

    def __init__(self, connection_pool, que):
        super(ImageQueueThread, self).__init__()
        self.que = que
        self.live = True
        self.connection_pool:urllib3.HTTPSConnectionPool = connection_pool

    def run(self) -> None:
        while self.live:
            item = self.que.get(block=True)
            try:
                if item is not self.DEATH:
                    url, str_pth = item
                    number_part = int(url[url.rfind('/')+1:url.rfind('.')])
                    dat = self.connection_pool.request('GET', '/icons/{}.png'.format(number_part), preload_content=False)
                    with open(str_pth, 'wb') as f:
                        for chunk in dat.stream(512):
                            f.write(chunk)
                    self.sig_icon_ready.emit(url, str_pth)
            finally:
                self.que.task_done()

    def pull_the_plug(self):
        self.live = False


def pix_overlay_enhance(gear:Gear):
    enh_lvl_n = gear.enhance_lvl_to_number()
    if enh_lvl_n > 0:
        enhance_lvl = gear.enhance_lvl_from_number(enh_lvl_n - 1)
        enh_p = os.path.join(ENH_IMG_PATH, enhance_lvl + ".png")
        if os.path.isfile(enh_p):
            return enh_p


class ImageLoader(QObject):
    sig_image_load = QtCore.pyqtSignal(str, str, name='sig_image_load')

    def __init__(self, url):
        super(ImageLoader, self).__init__()
        self.url = url
        self.loaded = {}

        self.pool_size = 4
        self.connection = None
        self.time_open = time()

        self.sig_image_load.connect(self.loaded_callback)

        self.image_que = queue.Queue()
        self.image_threads = []

        for i in range(0, self.pool_size):
            th = ImageQueueThread(self.connection, self.image_que)
            th.sig_icon_ready.connect(self.sig_image_load)
            self.image_threads.append(th)
            th.start()

    def get_icon(self, url, file_path):
        self.time_open = time()
        if url in self.loaded:
            if isinstance(self.loaded[url], str):
                self.sig_image_load.emit(url, self.loaded[url])
        else:
            if os.path.isfile(file_path):
                self.sig_image_load.emit(url, file_path)
                return
            self.loaded[url] = False
            if self.connection is None:
                self.connection = urllib3.HTTPSConnectionPool(self.url, maxsize=self.pool_size, block=True)
                for th in self.image_threads:
                    th.connection_pool = self.connection
                self.time_open = time()
            self.image_que.put((url, file_path))

    def loaded_callback(self, url, str_path):
        self.loaded[url] = str_path
        self.check_connection_close()

    def check_connection_close(self):
        if (time() - self.time_open) > 60 and self.image_que.empty() and (self.connection is not None):
            self.connection.close()

    def kill_pool(self):
        for th in self.image_threads:
            th.pull_the_plug()
        for i in range(0, len(self.image_threads)):
            self.image_que.put_nowait(ImageQueueThread.DEATH)


imgs = ImageLoader('cdn.arsha.io')


class Dlg_AddGear(QtWidgets.QDialog):
    sig_gear_chosen = QtCore.pyqtSignal(object, name='sig_gear_chosen')

    def __init__(self, parent=None):
        super(Dlg_AddGear, self).__init__(parent=parent)
        frmObj = Ui_dlgSearchGear()
        self .ui = frmObj
        frmObj.setupUi(self)

        self.search_results:List[GearData] = []
        self.url_twis = {}
        imgs.sig_image_load.connect(self.icon_ready)

        frmObj.cmdSearch.clicked.connect(self.cmdSearch_clicked)
        frmObj.spinPages.valueChanged.connect(self.update_table)
        frmObj.spinResultsPerPage.valueChanged.connect(self.spinResultsPerPage_valueChanged)
        frmObj.lstGear.setIconSize(QtCore.QSize(32, 32))

        frmObj.lstGear.itemDoubleClicked.connect(self.lstGear_itemDoubleClicked)

    def lstGear_itemDoubleClicked(self, item):
        frmObj = self.ui
        frmObj.txtSearch.setEnabled(False)
        frmObj.cmdSearch.setEnabled(False)
        frmObj.spinPages.setEnabled(False)
        frmObj.spinResultsPerPage.setEnabled(False)
        frmObj.cmdNext.setEnabled(False)
        frmObj.cmdPrev.setEnabled(False)
        row = item.row()
        twi_id = frmObj.lstGear.item(row, 3)
        self.sig_gear_chosen.emit(twi_id.__dict__['gd'])
        self.close()

    def closeEvent(self, a0) -> None:
        super(Dlg_AddGear, self).closeEvent(a0)

    def icon_ready(self, url, path):
        if url in self.url_twis:
            this_icon = pix.get_icon(path)
            for twi in self.url_twis[url]:
                try:
                    twi.setIcon(this_icon)
                except RuntimeError as e:
                    print(e)
            del self.url_twis[url]

    def spinResultsPerPage_valueChanged(self):
        self.update_spins()
        self.update_table()

    def cmdSearch_clicked(self):
        frmObj = self.ui
        search_text = frmObj.txtSearch.text()
        self.search_results = matcher.search(search_text)
        self.update_spins()
        with QBlockSig(frmObj.spinPages):
            frmObj.spinPages.setValue(1)
        self.update_table()

    def update_spins(self):
        frmObj = self.ui
        spin_results_pp = frmObj.spinResultsPerPage.value()
        pages = int(math.ceil(len(self.search_results) / spin_results_pp))
        frmObj.spinPages.setMaximum(pages)

    def update_table(self):
        frmObj = self.ui
        spin_page = frmObj.spinPages.value()
        results_per_page = frmObj.spinResultsPerPage.value()

        chunk_start = max(0, (spin_page-1) * results_per_page)
        chunk_end = chunk_start + results_per_page

        lstGear = frmObj.lstGear
        lstGear.clear()
        lstGear.setHorizontalHeaderLabels(['Name', 'Class', 'Grade', 'ID'])

        this_page = self.search_results[chunk_start: chunk_end]
        list_max_idx = lstGear.rowCount() - 1
        for i,result in enumerate(this_page):
            if i > list_max_idx:
                list_max_idx += 1
                lstGear.insertRow(list_max_idx)
            itm_id = result.item_id
            name_item = QtWidgets.QTableWidgetItem(str(result.name))
            name_p_str = f'{itm_id:08}'
            class_item = QtWidgets.QTableWidgetItem(result.get_class_str())
            grade_item = QtWidgets.QTableWidgetItem(result.get_grade_str())
            id_item = QtWidgets.QTableWidgetItem(name_p_str)
            id_item.__dict__['gd'] = result
            lstGear.setItem(i, 0, name_item)
            lstGear.setItem(i, 1, class_item)
            lstGear.setItem(i, 2, grade_item)
            lstGear.setItem(i, 3, id_item)

            img_file_name = os.path.join(IMG_TMP, name_p_str+'.png')
            url = result.icon_url
            if url in self.url_twis:
                self.url_twis[url].append(name_item)
            else:
                self.url_twis[url] = [name_item]
            imgs.get_icon(url, img_file_name)
        lstGear.resizeColumnToContents(1)
