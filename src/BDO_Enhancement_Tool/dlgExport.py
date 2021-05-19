#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import os, csv
#from common import relative_path_covnert
from .Forms.dlg_Export import Ui_Dialog_Export
import PyQt5.QtWidgets as QtWidgets
from PyQt5.QtWidgets import QFileDialog
from . import Qt_common

dlg_format_list = Qt_common.dlg_format_list


class dlg_Export(QtWidgets.QDialog):
    def __init__(self, parent, model=None):
        super(dlg_Export, self).__init__(parent)
        if model is None:
            model = parent.model
        self.model = model
        self.main_window = parent
        frmObj = Ui_Dialog_Export()
        self.ui = frmObj
        frmObj.setupUi(self)

        frmObj.buttonBox.accepted.connect(self.buttonBox_accepted)

    def buttonBox_accepted(self):
        frmObj = self.ui
        curi = frmObj.tabWidget.currentIndex()
        if curi == 0:
            # CSV selected
            self.export_csv()
        elif curi == 1:
            # Excel selected
            pass
        else:
            # This should not happen
            pass

    def export_excel(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        format_list = [('Any', '*'), ('Excel File', 'xlsx')]
        fileName, _ = QFileDialog.getSaveFileName(self, "Saving", './', dlg_format_list(format_list),
                                                  options=options,
                                                  initialFilter=dlg_format_list([format_list[1]]))
        if fileName:
            pass

    def export_csv(self):
        frmObj = self.ui
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        fileName = QFileDialog.getExistingDirectory()
        if fileName:
            if frmObj.chk_fs.isChecked():
                self.save_fs_list_csv(fileName)

    def save_fs_list_csv(self, folder_output):
        model = self.model
        if model.fs_needs_update:
            self.main_window.cmdFSRefresh_clicked()
            if model.fs_needs_update:
                self.close()
        with open(os.path.join(folder_output, 'fs_list.csv'), 'wb') as f:
            csv_writer = csv.writer(f)
            fs_items = model.optimal_fs_items
            fs_cost = model.fs_cost
            cum_fs_cost = model.cum_fs_cost
            cum_fs_probs = model.cum_fs_probs
            fs_probs = model.fs_probs

            matrix = [
                ['FS', 'Name', 'Cost', 'Cumulative Cost', 'Probability', 'Cumulative Probability']
            ]

            for i, this_gear in enumerate(fs_items):
                matrix.append(
                    [str(i), this_gear.get_full_name(), fs_cost[i], cum_fs_cost[i], fs_probs[i], cum_fs_probs[i]]
                )

            for i in zip(matrix):
                csv_writer.writerow(*i)
