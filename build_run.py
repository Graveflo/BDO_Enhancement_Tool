#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import sys, os
from .common import relative_path_convert
from .utilities import FileSearcher
from PyQt5.uic.pyuic import Driver, Version
import optparse

#python_dir = os.path.dirname(sys.executable)
#pyuic5 = os.path.join(python_dir, r'pkgs\pyqt-5.9.2-py38ha925a31_4\Library\bin\pyuic5.bat')

# Convert UI files to python files
def convert_ui_files(path):
    parser = optparse.OptionParser(usage="pyuic5 [options] <ui-file>",
            version=Version)
    parser.add_option("-p", "--preview", dest="preview", action="store_true",
            default=False,
            help="show a preview of the UI instead of generating code")
    parser.add_option("-o", "--output", dest="output", default="-",
            metavar="FILE",
            help="write generated code to FILE instead of stdout")
    parser.add_option("-x", "--execute", dest="execute", action="store_true",
            default=False,
            help="generate extra code to test and display the class")
    parser.add_option("-d", "--debug", dest="debug", action="store_true",
            default=False, help="show debug output")
    parser.add_option("-i", "--indent", dest="indent", action="store",
            type="int", default=4, metavar="N",
            help="set indent width to N spaces, tab if N is 0 [default: 4]")

    g = optparse.OptionGroup(parser, title="Code generation options")
    g.add_option("--import-from", dest="import_from", metavar="PACKAGE",
            help="generate imports of pyrcc5 generated modules in the style 'from PACKAGE import ...'")
    g.add_option("--from-imports", dest="from_imports", action="store_true",
            default=False, help="the equivalent of '--import-from=.'")
    g.add_option("--resource-suffix", dest="resource_suffix", action="store",
            type="string", default="_rc", metavar="SUFFIX",
            help="append SUFFIX to the basename of resource files [default: _rc]")
    parser.add_option_group(g)

    fs = FileSearcher(path, confirmation_function=lambda x: x.endswith('.ui'))
    for file_ in fs.NonRecursive():
        file_name = os.path.basename(file_)
        file_name = file_name[:file_name.rfind('.')]

        args, opts = parser.parse_args(args=['-o', os.path.join(os.path.dirname(file_), file_name+'.py')])

        #print(args)
        #continue

        d = Driver(args, os.path.join(path, file_))
        d.invoke()
        print('{} -> {}'.format(file_, file_name + '.py'))

if __name__ == '__main__':
    convert_ui_files(relative_path_convert('Forms'))
    convert_ui_files(relative_path_convert('QtCommon/forms'))
    from .start_ui import launch
    launch()