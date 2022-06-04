#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑  ❧
"""
import sys, os, time
from PyQt6.QtWidgets import QApplication, QStyleFactory, QSplashScreen
from .common import USER_DATA_PATH, relative_path_convert

from .qt_UI_Common import pix, BS_CHEER
from .DlgAddGear import imgs
from .FrmMain import Frm_Main
from .utilities import Tee, getStackTrace
from .Qt_common import get_dark_palette, check_win_icon

MAXIMUM_LOGFILE_SIZE = 500 * 1024


def launch(RELEASE_VER):
    frmmain = None
    log_path = os.path.join(USER_DATA_PATH, 'LOG.log')
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
    tee = Tee(log_path, 'a')
    print('Starting: ' + str(time.time()))
    try:
        sys.stdout = tee
        # --reduced-referrer-granularity --disable-site-isolation-trials --disable-features=NetworkService,NetworkServiceInProcess
        # os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--remote-debugging-port=4867 --reduced-referrer-granularity=1'
        app = QApplication(sys.argv)
        splash = QSplashScreen(pix[BS_CHEER])
        splash.show()
        app.processEvents()
        #app
        # Basic app theme here
        app.setStyle(QStyleFactory.create('Fusion'))
        app.setPalette(get_dark_palette())

        # Initialize main window
        frmmain = Frm_Main(app, RELEASE_VER)
        check_win_icon('RAM.EnhOpt.Grave.1', app, frmmain,
                                 relative_path_convert("favicon.ico"))
        #frmmain.load_file(common.DEFAULT_SETTINGS_PATH)

        frmmain.show()
        splash.finish(frmmain)
        app.setQuitOnLastWindowClosed(False)
        status_code = app.exec()
        imgs.kill_pool()
        sys.exit(status_code)
    except Exception as e:
        exec_info = sys.exc_info()[0]
        if not exec_info is SystemExit:
            print("Traceback: ", exec_info)
            print(getStackTrace())
        print(e)
    except:
        exec_info = sys.exc_info()[0]
        if not exec_info is SystemExit:
            print("Unexpected error: ", exec_info)
            print(getStackTrace())
    finally:
        if frmmain is not None:
            frmmain.shut_down()
        tee.flush()
        tee.file.close()

if __name__ == "__main__":
    launch()
