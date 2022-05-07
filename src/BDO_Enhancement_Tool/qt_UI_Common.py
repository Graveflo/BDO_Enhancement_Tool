# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑  ❧
"""
import os

from BDO_Enhancement_Tool.Core.ItemStore import STR_FMT_ITM_ID
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap, QColor

from .common import relative_path_convert

ITEM_PIC_DIR = relative_path_convert('Images/items/')
STR_PIC_BSA = os.path.join(ITEM_PIC_DIR, '00016002.png')
STR_PIC_BSW = os.path.join(ITEM_PIC_DIR, '00016001.png')
STR_PIC_CBSA = os.path.join(ITEM_PIC_DIR, '00016005.png')
STR_PIC_CBSW = os.path.join(ITEM_PIC_DIR, '00016004.png')
STR_PIC_HBCS = os.path.join(ITEM_PIC_DIR, '00004997.png')
STR_PIC_SBCS = os.path.join(ITEM_PIC_DIR, '00004998.png')
STR_PIC_CAPH = os.path.join(ITEM_PIC_DIR, '00721003.png')
STR_PIC_CRON = os.path.join(ITEM_PIC_DIR, '00016080.png')
STR_PIC_MEME = os.path.join(ITEM_PIC_DIR, '00044195.png')
STR_PIC_MOPM = os.path.join(ITEM_PIC_DIR, '00752023.png')
STR_PIC_PRIEST = os.path.join(ITEM_PIC_DIR, 'ic_00017.png')
STR_PIC_DRAGON_SCALE = os.path.join(ITEM_PIC_DIR, '00044364.png')
STR_PIC_VALUE_PACK = os.path.join(ITEM_PIC_DIR, '00017583.png')
STR_PIC_RICH_MERCH_RING = os.path.join(ITEM_PIC_DIR, '00012034.png')
STR_PIC_MARKET_TAX = os.path.join(ITEM_PIC_DIR, '00000005_special.png')
STR_PIC_BARTALI = os.path.join(ITEM_PIC_DIR, 'ic_00018.png')
STR_PIC_VALKS = os.path.join(ITEM_PIC_DIR, '00017800.png')
BS_CHEER = relative_path_convert('Images/B.S.Happy.png')
BS_AW_MAN = relative_path_convert('Images/B.S. Awh Man.png')
BS_FACE_PALM = relative_path_convert('Images/B.S. Face Palm.png')
BS_HMM = relative_path_convert('Images/B.S. Hmmmm.png')
BS = relative_path_convert('Images/B.S.png')
STR_NEXT_PIC = relative_path_convert('Images/next.png')
STR_CHECK_PIC = relative_path_convert('Images/tick.png')
STR_PLUS_PIC = relative_path_convert('Images/plus.svg')
STR_MINUS_PIC = relative_path_convert('Images/minus.svg')
STR_GOLD_PIC = relative_path_convert('Images/gold-ingots.svg')
STR_REFRESH_PIC = relative_path_convert('Images/refresh.svg')
STR_CALC_PIC = relative_path_convert('Images/calculator.svg')
STR_DIAL_PIC = relative_path_convert('Images/dial.svg')
STR_STOP_PIC = relative_path_convert('Images/no-stopping.svg')
STR_LENS_PATH  = relative_path_convert('Images/lens2.png')


COLOR_CUSTOM_PRICE =  QColor(Qt.GlobalColor.red).lighter()

class PictureStorage(object):
    def __init__(self):
        self.pixmap_cache = {}
        self.icon_cache = {}

    def __getitem__(self, item):
        if type(item) == int:
            item = os.path.join(ITEM_PIC_DIR, '{}.png'.format(STR_FMT_ITM_ID).format(item))
        if item in self.pixmap_cache:
            return QPixmap(self.pixmap_cache[item])
        else:
            ret = QPixmap(item)
            self.pixmap_cache[item] = ret
            return ret

    def get_icon(self, item):
        if item in self.icon_cache:
            return QIcon(self.icon_cache[item])
        else:
            pixmap = self[item]
            ret = QIcon(pixmap)
            self.icon_cache[item] = ret
            return ret

pix = PictureStorage()


