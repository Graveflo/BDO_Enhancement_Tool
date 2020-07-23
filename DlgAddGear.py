#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import os
from PyQt5 import QtWidgets, Qt, QtCore
from PyQt5.QtGui import QIcon, QPixmap, QPainter
import math
from .QtCommon.Qt_common import QBlockSig
from .Forms.dlg_add_gear import Ui_dlgSearchGear
import queue
import sqlite3
import urllib3
from .common import DB_FOLDER, IMG_TMP, ENH_IMG_PATH, Gear
import encodings.idna  # This is for binaries created my pyinstaller. Forced mod load encodings

import operator
from fuzzywuzzy import process


urllib3.disable_warnings()


class UniqueList(list):
    def __init__(self, iterable=None):
        super(UniqueList, self).__init__()
        self.set = set()
        lne = 0
        if iterable is not None:
            for i in iterable:
                self.set.add(i)
                this_len = len(self.set)
                if this_len>lne:
                    super(UniqueList, self).append(i)
                lne = this_len

    def append(self, key):
        if key not in self.set:
            super(UniqueList, self).append(key)
            self.set.add(key)

    def pop(self, index=None):
        item = super(UniqueList, self).pop(index)
        self.set.remove(item)
        return item

    def insert(self, index, object):
        try:
            index = self.index(object)
            super(UniqueList, self).pop(index)
        except ValueError:
            self.set.add(object)
        super(UniqueList, self).insert(index, object)


class FuzzyMatcher(object):
    def __init__(self, items=None, items_str=None, split_token=' '):
        if items is None:
            items = UniqueList()
        else:
            items = UniqueList(items)
        if items_str is None:
            items_str = []
        else:
            items_str = items_str
        self.items = items
        self.split_token = split_token
        self.items_str = items_str
        self.lookup = None
        self.tokens = set()

    def add_item(self, item, item_str):
        self.items.insert(0, item)
        self.items_str.insert(0, item_str)

    def clear(self):
        self.items = UniqueList()
        self.items_str = []
        self.lookup = None
        self.tokens = set()

    def insert_many(self, items, items_str):
        list(map(lambda x: self.add_item(*x), list(zip(items, items_str))))

    def insert_many_f(self, items, str_f):
        self.insert_many(items, list(map(str_f, items)))

    def compute_lookup_table(self):
        lookup = {}
        tokens = self.tokens
        items_str = self.items_str
        for i,item in enumerate(self.items):
            this_tokens = items_str[i].split(self.split_token)
            for token in this_tokens:
                try:
                    ar = lookup[token]
                except KeyError:
                    ar = []
                    lookup[token] = ar
                ar.append(item)
                tokens.add(token)
        self.lookup = lookup
        self.tokens = tokens

    def search(self, terms):
        if self.lookup is None:
            self.compute_lookup_table()
        tally = {}
        for i in self.items:
            tally[i] = 0

        lookup = self.lookup
        tokens = self.tokens

        for term in terms:
            sadf = process.extract(term, tokens)
            for token, val in sadf:
                for match in lookup[token]:
                    tally[match] += val
        return sorted(list(tally.items()), key=operator.itemgetter(1), reverse=True)


conn = sqlite3.connect(os.path.join(DB_FOLDER, 'gear.sqlite3'))
cur = conn.cursor()
gears = {_[0]:_[1:] for _ in cur.execute('SELECT * FROM enh_Gear')}
conn.close()

gear_tup = [(k,v[0]) for k,v in gears.items()]
gearzip = [x for x in zip(*gear_tup)]

matcher = FuzzyMatcher(items=gearzip[0], items_str=gearzip[1])
matcher.compute_lookup_table()


class ImageQueueThread(QtCore.QThread):
    DEATH = -42069
    sig_icon_ready = QtCore.pyqtSignal(str, object)

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
                    url, str_pth, twi = item

                    flag = True
                    try:
                        twi.column()
                    except RuntimeError:
                        flag = False

                    if flag:
                        dat = self.connection_pool.request('GET', url, preload_content=False)
                        with open(str_pth, 'wb') as f:
                            for chunk in dat.stream(512):
                                f.write(chunk)
                        self.sig_icon_ready.emit(str_pth, twi)
            finally:
                self.que.task_done()

    def pull_the_plug(self):
        self.live = False


def pix_overlay_enhance(pix: QPixmap, gear:Gear):
    enh_lvl_n = gear.enhance_lvl_to_number()
    if enh_lvl_n > 0:
        enhance_lvl = gear.enhance_lvl_from_number(enh_lvl_n - 1)
        enh_p = os.path.join(ENH_IMG_PATH, enhance_lvl + ".png")
        if os.path.isfile(enh_p):
            this_pix = QPixmap(QtCore.QSize(32, 32))
            this_pix.fill(QtCore.Qt.transparent)
            painter = QPainter(this_pix)

            painter.drawPixmap(0, 0, pix)
            painter.drawPixmap(0, 0, QPixmap(enh_p))
            pix = this_pix
    return pix


class Dlg_AddGear(QtWidgets.QDialog):
    sig_gear_chosen = QtCore.pyqtSignal(str,str,str,str, name='sig_gear_chosen')

    def __init__(self, frmMain):
        super(Dlg_AddGear, self).__init__(parent=frmMain)
        frmObj = Ui_dlgSearchGear()
        self .ui = frmObj
        frmObj.setupUi(self)
        self.frmMain = frmMain


        self.image_que = queue.Queue()


        self.image_threads = []

        for i in range(0, self.frmMain.pool_size):
            th = ImageQueueThread(self.frmMain.connection, self.image_que)
            th.sig_icon_ready.connect(self.icon_ready)
            self.image_threads.append(th)
            th.start()

        self.search_results = []

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
        name = frmObj.lstGear.item(row, 0).text()
        item_class = frmObj.lstGear.item(row, 1).text()
        item_grade = frmObj.lstGear.item(row, 2).text()
        item_id = frmObj.lstGear.item(row, 3).text()
        self.sig_gear_chosen.emit(name, item_class, item_grade, item_id)
        self.close()

    def closeEvent(self, a0) -> None:
        self.kill_pool()
        super(Dlg_AddGear, self).closeEvent(a0)

    def kill_pool(self):
        for th in self.image_threads:
            th.pull_the_plug()
        for i in range(0, len(self.image_threads)):
            self.image_que.put_nowait(ImageQueueThread.DEATH)

    def icon_ready(self, path, twi):
        this_icon = QIcon(path)
        try:
            twi.setIcon(this_icon)
        except RuntimeError:
            pass

    def spinResultsPerPage_valueChanged(self):
        self.update_spins()
        self.update_table()

    def cmdSearch_clicked(self):
        frmObj = self.ui
        search_text = frmObj.txtSearch.text().split(' ')
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
            itm_id = result[0]
            this_gear = gears[itm_id]
            name_item = QtWidgets.QTableWidgetItem(str(this_gear[0]))
            res_class = this_gear[3]
            if res_class == 0:
                res_class_str = 'Weapons'
            elif res_class == 1:
                res_class_str = 'Armor'
            elif res_class == 2:
                res_class_str = 'Accessories'
            else:
                res_class_str = 'Error'
            res_grade = this_gear[1]
            if res_grade == 0:
                res_grade_str = 'White'
            elif res_grade == 1:
                res_grade_str = 'Green'
            elif res_grade == 2:
                res_grade_str = 'Blue'
            elif res_grade == 3:
                res_grade_str = 'Yellow'
            elif res_grade == 4:
                res_grade_str = 'Orange'
            else:
                res_grade_str = 'Error'



            name_p_str = f'{itm_id:08}'

            img_file_name = os.path.join(IMG_TMP, name_p_str+'.png')

            if os.path.isfile(img_file_name):
                self.icon_ready(img_file_name, name_item)
            else:
                self.image_que.put((this_gear[2], img_file_name, name_item))
                #dat = self.connection.urlopen('GET', )
                #with open(img_file_name, 'wb') as f:
                #    f.write(dat.data)



            class_item = QtWidgets.QTableWidgetItem(res_class_str)
            grade_item = QtWidgets.QTableWidgetItem(res_grade_str)
            id_item = QtWidgets.QTableWidgetItem(name_p_str)
            lstGear.setItem(i, 0, name_item)
            lstGear.setItem(i, 1, class_item)
            lstGear.setItem(i, 2, grade_item)
            lstGear.setItem(i, 3, id_item)
        lstGear.resizeColumnToContents(1)
