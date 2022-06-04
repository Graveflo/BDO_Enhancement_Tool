#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑  ❧
"""
import os
from .utilities import FileSearcher
from PyQt6.uic.compile_ui import compileUi

#python_dir = os.path.dirname(sys.executable)
#pyuic5 = os.path.join(python_dir, r'pkgs\pyqt-5.9.2-py38ha925a31_4\Library\bin\pyuic5.bat')


def convert_ui_files(path):
    fs = FileSearcher(path, confirmation_function=lambda x: x.endswith('.ui'))
    files = []
    for file_ in fs.NonRecursive():
        file_name = os.path.basename(file_)
        file_name = file_name[:file_name.rfind('.')]
        output_file = os.path.join(os.path.dirname(file_), file_name+'.py')
        with open(output_file, 'wt', encoding='utf-8') as pyfile:
            with open(file_, 'rt', encoding='utf-8') as uifile:
                compileUi(uifile, pyfile, False, 4)
        print('{} -> {}'.format(file_, file_name + '.py'))

    return files
