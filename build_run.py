#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import sys, os
from common import relative_path_convert
from utilities import FileSearcher
import subprocess

python_dir = os.path.dirname(sys.executable)
pyuic5 = os.path.join(python_dir, r'Library/bin/pyuic5.bat')

# Convert UI files to python files
def convert_ui_files(path):
    fs = FileSearcher(path, confirmation_function=lambda x: x.endswith('.ui'))
    for file_ in fs.NonRecursive():
        file_name = os.path.basename(file_)
        file_name = file_name[:file_name.rfind('.')]
        output = subprocess.check_output([pyuic5, file_, '-o', os.path.join(os.path.dirname(file_), file_name+'.py')])
        if output.find('Error') > -1:
            print output
        else:
            print '{} -> {}'.format(file_, file_name+'.py')

if __name__ == '__main__':
    convert_ui_files(relative_path_convert('Forms'))
    convert_ui_files(relative_path_convert('QtCommon/forms'))
    from start_ui import launch
    launch()