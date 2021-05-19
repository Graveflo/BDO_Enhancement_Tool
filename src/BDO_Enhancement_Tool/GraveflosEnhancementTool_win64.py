#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
from BDO_Enhancement_Tool import start_ui
from BDO_Enhancement_Tool.__main__ import RELEASE_VER
import multiprocessing

if __name__ == '__main__':
    multiprocessing.freeze_support()
    start_ui.launch(RELEASE_VER)
