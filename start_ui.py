#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import sys
import common
from PyQt5.QtWidgets import QApplication, QStyleFactory
from PyQt5 import QtGui, QtCore
from FrmMain import Frm_Main


Qt_common = common.Qt_common
utils = common.utils
relative_path_covnert = common.relative_path_covnert

get_dark_palette = Qt_common.get_dark_palette
setIcon = Qt_common.setIcon


if __name__ == "__main__":
    tee = utils.Tee(relative_path_covnert('LOG.log'), 'a')
    try:
        sys.stdout = tee
        app = QApplication(sys.argv)
        #app
        # Basic app theme here
        app.setStyle(QStyleFactory.create('Fusion'))
        app.setPalette(get_dark_palette())

        # Initialize main window
        frmmain = Frm_Main(app)
        Qt_common.check_win_icon('RAM.EnhOpt.Grave.1', app, frmmain,
                                 relative_path_covnert("favicon.ico"))
        try:
            frmmain.load_file(common.DEFAULT_SETTINGS_PATH)
        except IOError:
            frmmain.show_warning_msg('Running for the first time? Could not load the settings file. One will be created.')
        frmmain.show()
        status_code = app.exec_()
        sys.exit(status_code)
    except Exception as e:
        print utils.getStackTrace()
        print str(e)
    except:
        exec_info = sys.exc_info()[0]
        if not exec_info is SystemExit:
            print "Unexpected error: ", exec_info
            print utils.getStackTrace()
        raise
    finally:
        tee.flush()
        tee.file.close()
