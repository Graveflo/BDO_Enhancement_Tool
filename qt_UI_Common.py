# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import os

from PyQt5.QtGui import QIcon
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

def get_chk_icon():
    return QIcon(STR_CHECK_PIC)

def get_arrow_icon():
    return QIcon(STR_NEXT_PIC)