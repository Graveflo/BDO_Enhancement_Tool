# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
from PyQt5.QtWidgets import QTreeWidget


class TableEquipment(QTreeWidget):
    def __init__(self, *args, **kwargs):
        super(TableEquipment, self).__init__(*args, **kwargs)

    def cmdEquipRemove_clicked(self):
        tmodel = self.model
        tsettings = tmodel.settings
        tw = frmObj.table_Equip

        effect_list = [i for i in tw.selectedItems()]


        enhance_me = tsettings[tsettings.P_ENHANCE_ME]
        r_enhance_me = tsettings[tsettings.P_R_ENHANCE_ME]

        for i in effect_list:
            thic = tw.itemWidget(i, 0).gear
            try:
                enhance_me.remove(thic)
                #tmodel.invalidate_enahce_list()
            except ValueError:
                pass
            try:
                r_enhance_me.remove(thic)
            except ValueError:
                pass
            p = i.parent()
            if p is None:
                tw.takeTopLevelItem(tw.indexOfTopLevelItem(i))
            #else:
            #    p.removeChild(i)
            #tw.takeTopLevelItem()
        tsettings.changes_made = True

    def cmdEquipAdd_clicked(self, bool_):
        model = self.model

        gear_type = list(gear_types.items())[0][1]
        enhance_lvl = list(gear_type.lvl_map.keys())[0]

        this_gear = generate_gear_obj(model.settings, base_item_cost=0, enhance_lvl=enhance_lvl, gear_type=gear_type)

        self.table_Eq_add_gear( this_gear)
        model.add_equipment_item(this_gear)

    def cmdEquipCost_clicked(self):
        model = self.model
        frmObj = self.ui
        tw = frmObj.table_Equip

        try:
            model.calc_equip_costs(gear=self.invalidated_gear)
            self.invalidated_gear = set()
        except ValueError as f:
            self.show_warning_msg(str(f))
            return

        tw.setSortingEnabled(False)

        def populate_row(this_head, this_gear:Gear, eh_idx):

            cost_vec_l = this_gear.cost_vec[eh_idx]
            restore_cost_vec_min = this_gear.restore_cost_vec_min[eh_idx]
            idx_ = numpy.argmin(this_gear.cost_vec[eh_idx])
            #twi = numeric_twi(str(idx_))
            #twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
            #tw.setItem(i, 4, twi)
            this_head.setText(4, str(this_gear.get_enhance_lvl_idx() in this_gear.cron_use))
            this_head.setText(5, str(idx_))
            #twi = self.monnies_twi_factory(cost_vec_l[idx_])
            #twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
            #tw.setItem(i, 5, twi)
            this_head.setText(6, MONNIES_FORMAT.format(round(cost_vec_l[idx_])))
            this_head.setText(7, MONNIES_FORMAT.format(round(restore_cost_vec_min)))

            this_fail_map = numpy.array(this_gear.gear_type.map)[eh_idx]
            avg_num_fails = numpy.divide(numpy.ones(this_fail_map.shape), this_fail_map)[idx_] - 1
            avg_num_fails = this_gear.gear_type.p_num_atmpt_map[eh_idx][idx_] - 1
            #twi = numeric_twi()
            #twi.__dict__['__lt__'] = types.MethodType(numeric_less_than, twi)
            #tw.setItem(i, 6, twi)
            #this_head.setText(6, STR_TWO_DEC_FORMAT.format(avg_num_fails[idx_]))
            this_head.setText(8, STR_TWO_DEC_FORMAT.format(avg_num_fails))
            #twi = numeric_twi()
            #tw.setItem(i, 7, twi)
            this_head.setText(9, STR_PERCENT_FORMAT.format(this_fail_map[idx_] * 100.0))
            try:

                this_head.setText(9, str(this_gear.using_memfrags))
            except AttributeError:
                pass

        for i in range(0, tw.topLevelItemCount()):
            this_head = tw.topLevelItem(i)
            gear_widget = tw.itemWidget(this_head, 0)
            this_gear = gear_widget.gear
            eh_idx = this_gear.get_enhance_lvl_idx()
            populate_row(this_head, this_gear, eh_idx)
            for j in range(0, this_head.childCount()):
                this_child = this_head.child(j)
                child_gear_widget = tw.itemWidget(this_child, 0)
                child_gear = child_gear_widget.gear
                eh_idx = child_gear.get_enhance_lvl_idx()
                populate_row(this_child, this_gear, eh_idx)



        tw.setSortingEnabled(True)

    def cmdEnhanceMeMP_callback(self, thread:QThread, ret):
        if isinstance(ret, Exception):
            print(ret)
            self.show_critical_error('Error contacting central market')
        else:
            with QBlockSig(table_Equip):
                self.invalidate_equipment()
            frmObj.statusbar.showMessage('Enhancement gear prices updated')
        thread.wait(2000)
        if thread.isRunning():
            thread.terminate()
        self.mp_threads.remove(thread)

    def cmdEnhanceMeMP_clicked(self):
        settings = self.model.settings
        thread = MPThread(self.model.update_costs, settings[settings.P_ENHANCE_ME] + settings[settings.P_R_ENHANCE_ME])
        self.mp_threads.append(thread)
        thread.sig_done.connect(cmdEnhanceMeMP_callback)
        thread.start()


