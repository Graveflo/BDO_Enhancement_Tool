#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import sys, os, time
from . import common
from PyQt5.QtWidgets import QApplication, QStyleFactory
from .FrmMain import Frm_Main


from .QtCommon import Qt_common
utils = common.utils
relative_path_covnert = common.relative_path_convert

get_dark_palette = Qt_common.get_dark_palette
setIcon = Qt_common.setIcon
MAXIMUM_LOGFILE_SIZE = 500 * 1024

RELEASE_VER = '0.3.0a5'



def launch():
    frmmain = None
    log_path = relative_path_covnert('LOG.log')
    if os.path.isfile(log_path):
        file_size = os.stat(log_path).st_size
        if file_size > MAXIMUM_LOGFILE_SIZE:
            with open(log_path, 'rb') as f:
                file_contents = f.read()
            file_contents = file_contents[file_size-MAXIMUM_LOGFILE_SIZE:]
            with open(log_path, 'wb') as f:
                f.write(file_contents)
    elif os.path.isdir(log_path):
        print('Log file cannot be a directory.')
        sys.exit(1)
    tee = utils.Tee(log_path, 'a')
    print('Starting: ' + str(time.time()))
    try:
        sys.stdout = tee
        app = QApplication(sys.argv)
        #app
        # Basic app theme here
        app.setStyle(QStyleFactory.create('Fusion'))
        app.setPalette(get_dark_palette())

        # Initialize main window
        frmmain = Frm_Main(app, RELEASE_VER)
        Qt_common.check_win_icon('RAM.EnhOpt.Grave.1', app, frmmain,
                                 relative_path_covnert("favicon.ico"))
        try:
            frmmain.load_file(common.DEFAULT_SETTINGS_PATH)
        except IOError:
            frmmain.show_warning_msg('Running for the first time? Could not load the settings file. One will be created.')
            frmmain.load_ui_common()
        frmmain.show()
        app.setQuitOnLastWindowClosed(False)
        status_code = app.exec_()
        sys.exit(status_code)
    except:
        exec_info = sys.exc_info()[0]
        if not exec_info is SystemExit:
            print("Unexpected error: ", exec_info)
            print(utils.getStackTrace())
    finally:
        tee.flush()
        tee.file.close()
        if frmmain is not None:
            dlg_login = frmmain.dlg_login
            if dlg_login.this_connection is not None:
                dlg_login.this_connection.close()

if __name__ == "__main__":
    launch()
