#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import numpy, json
from typing import List, Set, Union, Tuple

from .Core.Settings import EnhanceSettings
from .Core.Gear import Gear
from .Core.ItemStore import ItemStoreException, ItemStore

from .EnhanceModelSettings import EnhanceModelSettings
from .fsl import FailStackList
from .common import DEFAULT_SETTINGS_PATH, GearItemStore
from .utilities import fmt_traceback


class Invalid_FS_Parameters(Exception):
    pass


class SettingsException(Exception):
    def __init__(self, msg, embedded):
        super(SettingsException, self).__init__(msg)
        self.embedded: Exception = embedded

    def __str__(self):
        this_str = super(SettingsException, self).__str__()
        print(self.embedded)
        tb = self.embedded.__traceback__
        if tb is not None:
            this_str += '\r\n' + fmt_traceback(tb)
        return this_str


class Solution(object):
    def __init__(self, gear, cost, is_cron=False):
        self.gear:Gear = gear
        self.cost = cost
        self.is_cron = is_cron


class StrategySolution(object):
    # TODO: Optimize this object with caching (lazy sorts)
    def __init__(self, settings: EnhanceModelSettings, enh_gear:List[Gear], cron_gear: List[Gear], fs_items:List[Gear], balance_vec, balance_vec_fs):
        self.enh_gear = enh_gear + cron_gear
        self.cron_start = len(enh_gear)
        self.fs_items = fs_items.copy()

        # Sort maps needed to reference the gear table
        sort_map_balance_vec = numpy.argsort(balance_vec, axis=0)
        sort_map_balance_vec_fs = numpy.argsort(balance_vec_fs, axis=0)
        self.sort_map_balance_vec = sort_map_balance_vec
        self.sort_map_balance_vec_fs = sort_map_balance_vec_fs

        self.balance_vec_unsort = balance_vec
        self.balance_vec_fs_unsort = balance_vec_fs

        self.balance_vec = numpy.take_along_axis(balance_vec, sort_map_balance_vec, axis=0)
        self.balance_vec_fs = numpy.take_along_axis(balance_vec_fs, sort_map_balance_vec_fs, axis=0)

        self.settings = settings

        self.enh_me = set(settings[settings.P_ENHANCE_ME])
        self.mod_enhance_me = []
        for gear in enh_gear:
                self.mod_enhance_me.append(gear)

    def is_fake(self, enh_gear):
        return enh_gear not in self.enh_me

    def iter_best_solutions(self, start_fs=None):
        if start_fs is None:
            start_fs = 0
        best_balance_vec_idx = self.sort_map_balance_vec[0]
        best_fs_vec_idx = self.sort_map_balance_vec_fs[0]
        enh_gear = self.enh_gear
        fs_items = self.fs_items
        balance_vec = self.balance_vec[0]
        balance_vec_fs = self.balance_vec_fs[0]
        for i in range(start_fs, len(best_balance_vec_idx)):
            idx_enh_gear = best_balance_vec_idx[i]
            idx_fs_gear = best_fs_vec_idx[i]
            this_enh_gear = enh_gear[idx_enh_gear]
            fs_gear = fs_items[idx_fs_gear]
            is_cron = idx_enh_gear >= self.cron_start
            yield fs_gear, balance_vec_fs[i], this_enh_gear, balance_vec[i], is_cron

    def it_sort_enh_fs_lvl(self, fs_lvl):
        balance_vec = self.balance_vec
        sorted_args = self.sort_map_balance_vec.T[fs_lvl]

        best_idx = sorted_args[0]
        best_gear = self.enh_gear[best_idx]
        best_cost = balance_vec[0][fs_lvl]

        best_sol = Solution(best_gear, best_cost, is_cron=best_idx>=self.cron_start)

        for i in range(0, len(sorted_args)):
            this_gear_idx = sorted_args[i]
            is_cron = this_gear_idx >= self.cron_start
            gear = self.enh_gear[this_gear_idx]
            gear_cost = balance_vec[i][fs_lvl]
            yield Solution(gear, gear_cost, is_cron=is_cron), best_sol

    def it_sort_fs_fs_lvl(self, fs_lvl):
        balance_vec_fs = self.balance_vec_fs
        sorted_args = self.sort_map_balance_vec_fs.T[fs_lvl]

        best_idx = sorted_args[0]
        best_gear = self.fs_items[best_idx]
        best_cost = balance_vec_fs[0][fs_lvl]

        best_sol = Solution(best_gear, best_cost)

        for i in range(0, len(sorted_args)):
            this_gear_idx = sorted_args[i]
            gear = self.fs_items[this_gear_idx]
            gear_cost = balance_vec_fs[i][fs_lvl]
            yield Solution(gear, gear_cost), best_sol

    def get_best_fs_solution(self, fs_lvl):
        best_idx = self.sort_map_balance_vec_fs[0][fs_lvl]
        return Solution(self.fs_items[best_idx], self.balance_vec_fs[0][fs_lvl])

    def get_best_enh_solution(self, fs_lvl):
        best_idx = self.sort_map_balance_vec[0][fs_lvl]
        return Solution(self.enh_gear[best_idx], self.balance_vec[0][fs_lvl], is_cron=best_idx>=self.cron_start)

    def get_solution_gear(self, fs_lvl, gear: Gear):
        index = self.enh_gear.index(gear)
        bvt_l = self.balance_vec_unsort.T[fs_lvl]
        return bvt_l[index]

    def get_loss_prevs(self, fs):
        balance_vec_unsort = self.balance_vec_unsort
        sort_map_balance_vec_T = self.sort_map_balance_vec.T
        enh_gear = self.enh_gear

        sols = []

        for i, g_idx in enumerate(sort_map_balance_vec_T[fs]):
            cost = balance_vec_unsort[g_idx][fs]
            this_gear = enh_gear[g_idx]
            if cost <= 0 and not self.is_fake(this_gear):
                sols.append(Solution(this_gear, cost, is_cron=g_idx >= self.cron_start))

        return sols

    def eval_fs_attempt(self, start_fs, saves=False, collapse=False, loss_prev=False) -> Tuple[Union[List[Solution], None], Union[Solution,None]]:
        balance_vec_unsort = self.balance_vec_unsort
        best_balance_vec = self.balance_vec[0]
        sort_map_balance_vec_T = self.sort_map_balance_vec.T
        best_sort_map_balance_vec = self.sort_map_balance_vec[0]
        settings = self.settings
        if start_fs < settings[settings.P_QUEST_FS_INC]:
            start_fs = settings[settings.P_QUEST_FS_INC]
        enh_gear = self.enh_gear
        fsl_l:List[FailStackList] = settings[settings.P_GENOME_FS]
        num_fs = settings[settings.P_NUM_FS]

        def loop_life_nom(_fs):
            if _fs > num_fs:
                return False
            return best_balance_vec[_fs] > 0 or (not saves and self.is_fake(enh_gear[best_sort_map_balance_vec[_fs]]))

        def loop_life_loss_prv(_fs):
            if _fs > num_fs:
                return False
            for i, g_idx in enumerate(sort_map_balance_vec_T[_fs]):
                cost = balance_vec_unsort[g_idx][_fs]
                if cost <= 0 and not self.is_fake(enh_gear[g_idx]):
                    return False
            return True

        if loss_prev:
            ll = loop_life_loss_prv
        else:
            ll = loop_life_nom

        sol_total_cost = []
        sols_l = []
        sol_end_fs = []
        for fsl in fsl_l:
            track_fs = start_fs
            sols = []
            total_cost = 0
            incl = True
            while incl and ll(track_fs):
                if track_fs < len(fsl.gear_list):
                    gear = fsl.gear_list[track_fs]
                    if gear is None:  # this is a free fs
                        track_fs += 1
                    else:
                        cost = fsl.fs_cost[track_fs]
                        total_cost += cost
                        sols.append(Solution(gear, cost))
                        track_fs += gear.fs_gain()
                else:
                    incl = False
            if incl:
                sol_total_cost.append(total_cost)
                sols_l.append(sols)
                sol_end_fs.append(track_fs)

        ret_fs_sols = None
        sol_total_cost = numpy.array(sol_total_cost)
        min_sol = numpy.argmin(sol_total_cost)
        end_fs = sol_end_fs[min_sol]
        if len(sols_l) > 0 and len(sols_l[0]) > 0:
            ret_fs_sols = sols_l[min_sol]
            if collapse:
                new_ret_sols = []
                this_gear = ret_fs_sols[0].gear
                counter = 0
                cost_counter = 0
                for sol in ret_fs_sols:
                    if sol.gear == this_gear:
                        counter += 1
                        cost_counter += sol.cost
                    else:
                        new_ret_sols.append((counter, Solution(this_gear, cost_counter)))
                        this_gear = sol.gear
                        counter = 1
                        cost_counter = sol.cost
                if counter > 0:
                    new_ret_sols.append((counter, Solution(this_gear, cost_counter)))
                ret_fs_sols = new_ret_sols

        ret_sol_enh = None
        try:
            gear_dx = best_sort_map_balance_vec[end_fs]
            ret_sol_enh = Solution(enh_gear[gear_dx], best_balance_vec[end_fs], is_cron=gear_dx >= self.cron_start)
        except IndexError:
            pass
        return ret_fs_sols, ret_sol_enh

    def __len__(self):
        return len(self.balance_vec.T)


class Enhance_model(object):
    def __init__(self, file=None, settings=None):
        if settings is None:
            settings = EnhanceModelSettings(item_store=GearItemStore())
        self.settings: EnhanceModelSettings = settings
        if file is not None:
            self.load_from_file(file)

        #self.equipment_costs = []  # Cost of equipment
        #self.r_equipment_costs = []  # Cost of removed equipment
        self.optimal_fs_items = []  # Fail stack items chosen as optimal at each fails tack index
        self.fs_cost = []  # Cost of each fail stack
        self.fs_probs = []  # Probability of gaining fail stack
        self.cum_fs_probs = []  # Cumulative chance of gaining fail stack
        self.cum_fs_cost = []  # Cumulative cost of gaining a fail stack
        self.primary_fs_gear = []
        self.primary_fs_cost = []
        self.primary_cum_fs_cost = []

        self.custom_input_fs = {}

        self.for_profit_fs = False

        self.fs_needs_update = True
        self.fs_secondary_needs_update = True
        self.gear_cost_needs_update = True
        self.auto_save = True

        self.dragon_scale_30 = False
        self.dragon_scale_30_v = None
        self.dragon_scale_350 = False
        self.dragon_scale_350_v = None
        self.cost_funcs = {
            'Estimate (Fast)': 0,
            '2-Point Average (Moderate)': 1,
            'Average (Moderate)': 1,
            'Thorough (Slow)': 2
        }

    def add_fs_item(self, this_gear):
        fail_stackers = self.settings[EnhanceModelSettings.P_FAIL_STACKERS]
        fail_stackers.append(this_gear)
        self.update_costs([this_gear])
        self.settings.changes_made = True
        self.invalidate_failstack_list()
        self.save()

    def add_fs_secondary_item(self, this_gear:Gear):
        fail_stackers = self.settings[EnhanceModelSettings.P_FAIL_STACKER_SECONDARY]
        fail_stackers.append(this_gear)
        self.update_costs([this_gear])
        self.settings.changes_made = True
        self.invalidate_secondary_fs()
        self.save()

    def add_equipment_item(self, this_gear):
        enhance_me = self.settings[EnhanceModelSettings.P_ENHANCE_ME]
        enhance_me.append(this_gear)
        self.update_costs([this_gear])
        self.settings.changes_made = True
        self.invalidate_enahce_list()
        self.save()

    def add_for_profit_item(self, this_gear):
        for_profit = self.settings[EnhanceModelSettings.P_ENH_FOR_PROFIT]
        for_profit.append(this_gear)
        self.update_costs([this_gear])
        self.settings.changes_made = True
        self.invalidate_enahce_list()
        self.save()

    def edit_fs_item(self, old_gear, gear_obj):
        if old_gear == gear_obj:
            return
        fail_stackers = self.settings[EnhanceModelSettings.P_FAIL_STACKERS]
        r_fail_stackers = self.settings[EnhanceModelSettings.P_R_FAIL_STACKERS]
        if old_gear in fail_stackers:
            fail_stackers.remove(old_gear)
            self.add_fs_item(gear_obj)
        elif old_gear in r_fail_stackers:
            r_fail_stackers.remove(old_gear)
            r_fail_stackers.append(gear_obj)
            self.settings.changes_made = True
            self.save()

    def edit_fs_secondary_item(self, old_gear, gear_obj):
        if old_gear == gear_obj:
            return
        fail_stackers = self.settings[EnhanceModelSettings.P_FAIL_STACKER_SECONDARY]
        r_fail_stackers = self.settings[EnhanceModelSettings.P_R_STACKER_SECONDARY]
        if old_gear in fail_stackers:
            fail_stackers.remove(old_gear)
            self.add_fs_secondary_item(gear_obj)
        elif old_gear in r_fail_stackers:
            r_fail_stackers.remove(old_gear)
            r_fail_stackers.append(gear_obj)
            self.settings.changes_made = True
            self.save()

    def edit_enhance_item(self, old_gear, gear_obj):
        if old_gear == gear_obj:
            return
        enhance_me = self.settings[EnhanceModelSettings.P_ENHANCE_ME]
        r_enhance_me = self.settings[EnhanceModelSettings.P_R_ENHANCE_ME]
        if old_gear in enhance_me:
            enhance_me.remove(old_gear)
            self.add_equipment_item(gear_obj)
        elif old_gear in r_enhance_me:
            r_enhance_me.remove(old_gear)
            r_enhance_me.append(gear_obj)
            self.settings.changes_made = True
            self.save()

    def edit_for_profit_item(self, old_gear, gear_obj):
        if old_gear == gear_obj:
            return
        for_profit = self.settings[EnhanceModelSettings.P_ENH_FOR_PROFIT]
        r_for_profit = self.settings[EnhanceModelSettings.P_R_FOR_PROFIT]
        if old_gear in for_profit:
            for_profit.remove(old_gear)
            self.add_for_profit_item(gear_obj)
        elif old_gear in r_for_profit:
            r_for_profit.remove(old_gear)
            r_for_profit.append(gear_obj)
            self.settings.changes_made = True
            self.save()

    def swap_gear(self, old_gear: Gear, gear_obj: Gear):
        self.edit_fs_item(old_gear, gear_obj)
        self.edit_enhance_item(old_gear, gear_obj)
        self.edit_fs_secondary_item(old_gear, gear_obj)
        self.edit_for_profit_item(old_gear, gear_obj)

    def include_fs_item(self, gear:Gear):
        settings = self.settings
        r_fail_stackers = settings[settings.P_R_FAIL_STACKERS]
        fail_stackers = settings[settings.P_FAIL_STACKERS]

        if gear in r_fail_stackers:
            r_fail_stackers.remove(gear)

        fail_stackers.append(gear)
        self.invalidate_failstack_list()

    def exclude_fs_item(self, gear:Gear):
        settings = self.settings
        r_fail_stackers = settings[settings.P_R_FAIL_STACKERS]
        fail_stackers = settings[settings.P_FAIL_STACKERS]
        if gear in fail_stackers:
            fail_stackers.remove(gear)

        r_fail_stackers.append(gear)
        if gear in self.optimal_fs_items:
            self.invalidate_failstack_list()

    def include_fs_secondary_item(self, gear:Gear):
        settings = self.settings
        r_fail_stackers = settings[settings.P_R_STACKER_SECONDARY]
        fail_stackers = settings[settings.P_FAIL_STACKER_SECONDARY]

        if gear in r_fail_stackers:
            r_fail_stackers.remove(gear)

        fail_stackers.append(gear)

    def exclude_fs_secondary_item(self, gear:Gear):
        settings = self.settings
        r_fail_stackers = settings[settings.P_R_STACKER_SECONDARY]
        fail_stackers = settings[settings.P_FAIL_STACKER_SECONDARY]
        fsl_l:Set[FailStackList] = settings[settings.P_GENOME_FS]
        if gear in fail_stackers:
            fail_stackers.remove(gear)
        r_fail_stackers.append(gear)

        rems = []
        for fsl in fsl_l:
            if gear is fsl.secondary_gear:
                rems.append(fsl)
        if len(rems) > 0:
            for i in rems:
                fsl_l.remove(i)
            self.calcFS()

    def include_enhance_me(self, gear:Gear):
        settings = self.settings
        r_fail_stackers = settings[settings.P_R_ENHANCE_ME]
        fail_stackers = settings[settings.P_ENHANCE_ME]

        if gear in r_fail_stackers:
            r_fail_stackers.remove(gear)

        fail_stackers.append(gear)

    def exclude_enhance_me(self, gear:Gear):
        settings = self.settings
        r_fail_stackers = settings[settings.P_R_ENHANCE_ME]
        fail_stackers = settings[settings.P_ENHANCE_ME]

        if gear in fail_stackers:
            fail_stackers.remove(gear)

        r_fail_stackers.append(gear)

    def update_costs(self, gear_list: List[Gear]):
        settings = self.settings
        item_store = settings.item_store
        for gear in gear_list:
            if gear.item_id is None:
                continue
            item_store.check_in_gear(gear)
            if gear in item_store:
                try:
                    gear.set_base_item_cost(item_store.get_cost(gear, grade=-1))
                except ItemStoreException:
                    pass

    def clean_min_fs(self):
        settings = self.settings
        alts = settings[settings.P_ALTS]
        naderr = settings[settings.P_NADERR_BAND]

        min_fs = self.get_min_fs()

        for i,n in enumerate(naderr):
            if n < min_fs:
                naderr[i] = min_fs

        for i, pack in enumerate(alts):
            pic_path, name, fs = pack
            if fs < min_fs:
                alts[i][2] = min_fs

    def set_fsl(self, fsl: FailStackList):
        if not isinstance(fsl, FailStackList):
            raise ValueError('Must be a fail stacking list object')
        settings = self.settings
        fsl_l = settings[settings.P_GENOME_FS]
        lp = len(fsl_l)
        fsl_l.add(fsl)
        if len(fsl_l) > lp:
            self.invalidate_secondary_fs()
            return True
        else:
            return False

    def remove_fsl(self, fsl):
        settings = self.settings
        fsl_l = settings[settings.P_GENOME_FS]
        try:
            fsl_l.remove(fsl)
            self.invalidate_failstack_list()
            return True
        except KeyError:
            return False

    def set_time_penalty(self, time_p):
        self.settings[self.settings.P_TIME_PENALTY] = float(time_p)
        self.invalidate_failstack_list()
        self.invalidate_all_gear_cost()

    def set_cost_mopm(self, cost_mopm):
        self.settings[[EnhanceSettings.P_ITEM_STORE, ItemStore.P_MASS_OF_PURE_MAGIC]] = float(cost_mopm)
        self.invalidate_enahce_list()
        self.invalidate_all_gear_cost()

    def set_cost_bs_a(self, cost_bs_a):
        self.settings[[EnhanceSettings.P_ITEM_STORE, ItemStore.P_BLACK_STONE_ARMOR]] = float(cost_bs_a)
        self.invalidate_enahce_list()
        self.invalidate_all_gear_cost()

    def set_cost_bs_w(self, cost_bs_w):
        self.settings[[EnhanceSettings.P_ITEM_STORE, ItemStore.P_BLACK_STONE_WEAPON]] = float(cost_bs_w)
        self.invalidate_enahce_list()
        self.invalidate_all_gear_cost()

    def set_cost_conc_a(self, cost_conc_a):
        self.settings[[EnhanceSettings.P_ITEM_STORE, ItemStore.P_CONC_ARMOR]] = float(cost_conc_a)
        self.invalidate_enahce_list()
        self.invalidate_all_gear_cost()

    def set_cost_conc_w(self, cost_conc_w):
        self.settings[[EnhanceSettings.P_ITEM_STORE, ItemStore.P_CONC_WEAPON]] = float(cost_conc_w)
        self.invalidate_enahce_list()
        self.invalidate_all_gear_cost()

    def set_cost_hard(self, cost_conc_a):
        self.settings[[EnhanceSettings.P_ITEM_STORE, ItemStore.P_HARD_BLACK]] = float(cost_conc_a)
        self.invalidate_enahce_list()
        self.invalidate_all_gear_cost()

    def set_cost_sharp(self, cost_conc_w):
        self.settings[[EnhanceSettings.P_ITEM_STORE, ItemStore.P_SHARP_BLACK]] = float(cost_conc_w)
        self.invalidate_enahce_list()
        self.invalidate_all_gear_cost()

    def set_cost_meme(self, cost_meme):
        self.settings[[EnhanceSettings.P_ITEM_STORE, ItemStore.P_MEMORY_FRAG]] = float(cost_meme)
        self.invalidate_enahce_list()
        self.invalidate_all_gear_cost()

    def set_cost_caph(self, cost_caph):
        self.settings[[EnhanceSettings.P_ITEM_STORE, ItemStore.P_CAPH_STONE]] = float(cost_caph)
        self.invalidate_enahce_list()
        self.invalidate_all_gear_cost()

    def set_cost_cron(self, cost_cron):
        self.settings[EnhanceSettings.P_CRON_STONE_COST] = float(cost_cron)
        self.invalidate_enahce_list()
        self.invalidate_all_gear_cost()
        #self.cost_cron = float(cost_cron)

    def set_cost_cleanse(self, cost_cleanse):
        self.settings[EnhanceSettings.P_CLEANSE_COST] = float(cost_cleanse)
        #self.cost_cleanse = float(cost_cleanse)

    def set_market_tax(self, mtax):
        self.settings[EnhanceSettings.P_MARKET_TAX] = float(mtax)
        self.settings.recalc_tax()

    def quest_fs_inc_changed(self, fs):
        self.settings[EnhanceModelSettings.P_QUEST_FS_INC] = int(fs)

    def get_min_fs(self):
        return self.settings[EnhanceModelSettings.P_QUEST_FS_INC]

    def value_pack_changed(self, val):
        self.settings[EnhanceSettings.P_VALUE_PACK] = val
        self.settings.recalc_tax()

    def merch_ring_changed(self, val):
        self.settings[EnhanceSettings.P_MERCH_RING] = val
        self.settings.recalc_tax()

    def using_merch_ring(self, val):
        self.settings[EnhanceSettings.P_MERCH_RING_ACTIVE] = val
        self.settings.recalc_tax()

    def using_value_pack(self, val):
        self.settings[EnhanceSettings.P_VALUE_PACK_ACTIVE] = val
        self.settings.recalc_tax()

    def set_cost_dragonscale(self, cost_dscale):
        self.settings[[EnhanceSettings.P_ITEM_STORE, ItemStore.P_DRAGON_SCALE]] = float(cost_dscale)

    def invalidate_enahce_list(self):
        self.gear_cost_needs_update = True
        self.save()

    def invalidate_all_gear_cost(self):
        settings = self.settings
        enhance_me = settings[EnhanceModelSettings.P_ENHANCE_ME]
        r_enhance_me = settings[EnhanceModelSettings.P_R_ENHANCE_ME]

        for x in enhance_me + r_enhance_me:
            x.costs_need_update = True

    def invalidate_failstack_list(self):
        self.fs_needs_update = True
        self.fs_secondary_needs_update = True
        self.optimal_fs_items = []
        self.fs_cost = []
        self.cum_fs_cost = []
        self.cum_fs_probs = []
        self.fs_probs = []

        self.primary_fs_gear = []
        self.primary_fs_cost = []
        self.primary_cum_fs_cost = []
        self.invalidate_enahce_list()

    def invalidate_secondary_fs(self):
        self.fs_secondary_needs_update = True
        self.invalidate_enahce_list()

    def get_max_fs(self):
        return self.settings[EnhanceSettings.P_NUM_FS]

    def check_calc_fs(self):
        if self.fs_needs_update:
            self.calcFS()
        elif self.fs_secondary_needs_update:
            self.calc_fs_secondary()

    def calcFS(self):
        settings = self.settings
        num_fs = self.get_max_fs()
        fail_stackers = settings[EnhanceModelSettings.P_FAIL_STACKERS]
        fs_second:List[Gear] = settings[EnhanceModelSettings.P_FAIL_STACKER_SECONDARY]
        fs_items = []
        fs_cost = []
        cum_fs_cost = []
        cum_fs_probs = []
        fs_probs = []


        list(map(lambda x: x.prep_lvl_calc(), fail_stackers))


        if len(fail_stackers) < 1:
            raise Invalid_FS_Parameters('Must have at least one item on fail stacking list.')

        last_rate = 0
        cum_probability = 1
        fs_num = num_fs+1
        min_fs = self.get_min_fs()

        for i in range(0, min_fs):
            fs_probs.append(1.0)
            cum_fs_probs.append(1.0)
            fs_items.append(None)
            fs_cost.append(0)
            cum_fs_cost.append(0)


        for i in range(min_fs, fs_num):
            trys = [x.simulate_FS(i, last_rate) for x in fail_stackers]
            this_fs_idx = int(numpy.argmin(trys))
            this_fs_cost = trys[this_fs_idx]
            this_fs_item: Gear = fail_stackers[this_fs_idx]
            if i == 19:
                dsc = settings[settings.P_ITEM_STORE].get_cost(ItemStore.P_DRAGON_SCALE)
                cost = dsc * 30
                if cost < last_rate+this_fs_cost:
                    last_rate = 0
                    this_fs_cost = cost
                    self.dragon_scale_30 = True
                    self.dragon_scale_30 = this_fs_cost
                else:
                    self.dragon_scale_30 = False
                    self.dragon_scale_30 = None
                this_fs_cost = min(this_fs_cost, cost)
            elif i == 39:
                dsc = settings[settings.P_ITEM_STORE].get_cost(ItemStore.P_DRAGON_SCALE)
                cost = dsc * 350
                if cost < last_rate+this_fs_cost:
                    last_rate = 0
                    this_fs_cost = cost
                    self.dragon_scale_350 = True
                    self.dragon_scale_350_v = this_fs_cost
                else:
                        self.dragon_scale_350 = False
                        self.dragon_scale_350_v = None
            this_cum_cost = last_rate + this_fs_cost
            this_prob = 1.0 - this_fs_item.gear_type.map[this_fs_item.get_enhance_lvl_idx()][i]
            if this_fs_item.fs_gain() > 1:
                cum_probability *= this_prob ** (1/this_fs_item.fs_gain())
            else:
                cum_probability *= this_prob
            fs_probs.append(this_prob)
            cum_fs_probs.append(cum_probability)
            fs_items.append(this_fs_item)
            fs_cost.append(this_fs_cost)
            cum_fs_cost.append(this_cum_cost)
            last_rate = this_cum_cost

        fs_cost = numpy.array(fs_cost)
        cum_fs_cost = numpy.array(cum_fs_cost)
        fs_cost.setflags(write=False)
        cum_fs_cost.setflags(write=False)
        self.primary_fs_gear = fs_items.copy()
        self.primary_fs_cost = fs_cost
        self.primary_cum_fs_cost = cum_fs_cost
        self.optimal_fs_items = fs_items
        self.fs_cost = numpy.copy(fs_cost)
        self.cum_fs_cost = numpy.copy(cum_fs_cost)
        self.cum_fs_probs = cum_fs_probs
        self.fs_probs = fs_probs
        self.fs_needs_update = False

        # Set the self-enahnce pri cost for secondary gear
        if len(fs_second) > 0:
            sfs_cost = self.calc_equip_cost_u(fs_second, cum_fs_cost)
            for i,sfsg in enumerate(fs_second):
                csv = sfs_cost[i]
                bts = sfsg.gear_type.bt_start
                cum_cost = 0
                # bts is index of cost succeeding on DUO
                for i in range(0, bts-1):  # PRI is at bts-1
                    cum_cost += min(csv[i])
                sfsg.pri_cost = cum_cost
            self.calc_fs_secondary()

    def calc_fs_secondary(self):
        self.fs_needs_update = False
        settings = self.settings
        fsl_l = settings[settings.P_GENOME_FS]
        for fsl in fsl_l:
            fsl.set_primary_data(self.primary_fs_gear, self.primary_fs_cost, self.primary_cum_fs_cost)
            if fsl.validate():
                fsl.evaluate_map()
                mintrix = numpy.argmin([self.cum_fs_cost[:fsl.num_fs+1], fsl.fs_cum_cost], axis=0)
                for i, p in enumerate(mintrix):
                    if p == 1:
                        self.optimal_fs_items[i] = fsl.gear_list[i]
                        self.fs_cost[i] = fsl.fs_cost[i]
                        self.cum_fs_cost[i] = fsl.fs_cum_cost[i]

    def calc_equip_cost_u(self, gears, cum_fs):
        settings = self.settings
        fail_stackers = settings[EnhanceModelSettings.P_FAIL_STACKERS]
        num_fs = settings[EnhanceSettings.P_NUM_FS]

        if len(gears) < 1:
            raise ValueError('No enhancement items to calculate.')

        gts = [x.gear_type for x in gears]
        gts = set(gts)

        # Need to fill the gap between the fail stack calculated at num_fs and the potential for gear to roll past it
        for gt in gts:
            for glmap in gt.p_num_atmpt_map:
                foo = glmap[num_fs]

        # The map object has the highest stack needed for the overflow since it will be pushed up by the resolving of p_num_f_map
        this_max_fs = len(gts.pop().map[0]) + 1
        cum_fs_s = numpy.zeros(this_max_fs)
        cum_fs_s[1:num_fs + 2] = cum_fs
        last_rate = cum_fs[-1]
        for i in range(num_fs + 2, this_max_fs):
            last_rate += min([x.simulate_FS(i, last_rate) for x in fail_stackers])
            cum_fs_s[i] = last_rate

        eq_c = [x.enhance_cost(cum_fs_s) for x in gears]
        if len(eq_c) > 0:
            return eq_c
        else:
            raise Invalid_FS_Parameters('There is no equipment selected to calculate.')

    def calc_equip_costs(self, gear=None):
        settings = self.settings
        enhance_me = settings[EnhanceModelSettings.P_ENHANCE_ME]
        if gear is None:
            euip = enhance_me + settings[EnhanceModelSettings.P_R_ENHANCE_ME]
        else:
            euip = gear

        if self.fs_needs_update:
            self.calcFS()
        elif self.fs_secondary_needs_update:
            self.calc_fs_secondary()

        eq_c = self.calc_equip_cost_u(euip, self.cum_fs_cost)
        # if gear is None:  # This means that all hear was updated
        need_update = False
        for gear in enhance_me:
            need_update |= len(gear.cost_vec) < 1
            if need_update is True:
                break
        self.gear_cost_needs_update = need_update
        return eq_c

    def calcEnhances(self, enhance_me=None, fail_stackers=None, count_fs=False, count_fs_fs=True, devaule_fs=True, regress=False):
        if self.fs_needs_update:
            self.calcFS()
        elif self.fs_secondary_needs_update:
            self.calc_fs_secondary()

        settings = self.settings
        if enhance_me is None:
            enhance_me = settings[EnhanceModelSettings.P_ENHANCE_ME]
        if fail_stackers is None:
            fail_stackers = settings[EnhanceModelSettings.P_FAIL_STACKERS]

        if self.gear_cost_needs_update:
            self.calc_equip_costs(gear=enhance_me)

        if len(enhance_me) < 1:
            raise ValueError('No enhance items')
            return
        if len(fail_stackers) < 1:
            raise ValueError('No fail stacking items')
            return

        #enhance_me = enhance_me.copy()

        num_fs = settings[EnhanceSettings.P_NUM_FS]
        cum_fs_cost = self.cum_fs_cost
        cum_fs_cost = numpy.roll(cum_fs_cost, 1)
        cum_fs_cost[0] = 0
        fs_cost = self.fs_cost

        min_fs = self.get_min_fs()

        new_fs_cost = numpy.copy(fs_cost)
        if self.dragon_scale_30:
            new_fs_cost[19] = self.dragon_scale_30_v
        if self.dragon_scale_350:
            new_fs_cost[39] = self.dragon_scale_350_v

        fs_len = num_fs + 1


        # This is a bit hacky and confusing but we need a cost estimate on potential fs gain vs recovery loss on items that have no success gain
        # For fail-stacking items there should not be a total cost gained from success. It only gains value from fail stacks.
        #zero_out = lambda x: x.enhance_lvl_cost(cum_fs_cost,  total_cost=numpy.array([[0]*fs_len]*len(x.gear_type.map)), count_fs=count_fs)

        balance_vec_fser = [x.fs_lvl_cost(cum_fs_cost, count_fs=count_fs_fs) for x in fail_stackers]
        balance_vec_enh = [x.enhance_lvl_cost(cum_fs_cost, count_fs=count_fs, use_crons=False) for x in enhance_me]
        cron_start = len(balance_vec_enh)
        balance_vec_cron = []
        balance_vec_adds = []

        for gear in enhance_me:
            gear:Gear
            if gear.get_enhance_lvl_idx() in gear.cron_stone_dict:
                balance_vec_cron.append(gear.enhance_lvl_cost(cum_fs_cost, count_fs=count_fs, use_crons=True))
                balance_vec_adds.append(gear)

        balance_vec_fser = numpy.array(balance_vec_fser)
        balance_vec_enh = numpy.array(balance_vec_enh + balance_vec_cron)

        min_gear_map = [numpy.argmin(x) for x in balance_vec_enh.T]

        def check_out_gains(balance_vec, gains_lookup_vec, gear_list, fs_cost):
            """
            This method adds the value of increasing gains on gear that is ahead in the strategy fs list.
            For example:
            When attempting TRI on a weapon, if the user fails enhancement they will gain 3 fail stacks and these fail
            stacks have a value that is the increased chance of success with the 3 fail stacks. The actual cost is
            calculated by looking at what price of gear is up for enhancement 3 fail stacks higher then the qgear in
            question.
            If the gear ahead happens to be more expensive once the enhancement fails that gain becomes a cost.
            :param balance_vec:
            :param gains_lookup_vec:
            :param gear_list:
            :param fs_cost:
            :return:
            """
            #gearz = map(lambda x: gear_list[x], min_gear_map)
            # indexed by enhance_me returns the number of fail stacks gained by a failure
            gainz = [x.fs_gain() for x in gear_list]
            # indexed by sort order, returns index of enhance_me
            arg_sorts = numpy.argsort(gainz)
            fs_dict = {}
            #idx_ = 0
            for idx_, gear_idx in enumerate(arg_sorts):
                # = arg_sorts[idx_]
                try:
                    fs_dict[gainz[gear_idx]].append(gear_idx)
                except KeyError:
                    fs_dict[gainz[gear_idx]] = [gear_idx]

            # indexed by fs, returns list indexed by enhance_me of success chance
            chances = numpy.array([x.gear_type.map[x.get_enhance_lvl_idx()][:num_fs+1] for x in gear_list]).T

            # The very last item has to be a self pointer only
            # Not double counting fs cost bc this is a copy
            this_bal_vec = numpy.copy(balance_vec)
            # cycle through all fsil stack levels
            for i in range(min_fs, fs_len):
                lookup_idx = i
                #this_gear = gearz[lookup_idx]

                cost_emmend = numpy.zeros(len(this_bal_vec))
                # cycle through all types of gear packaged by the number of fail stacks they will gain. Since it will be
                # the same gain value
                for num_fs_gain, gear_idx_list in fs_dict.items():
                    #for gidx in enhance_me_idx_list:
                    #    print 'GEAR: {}\t\t| GAIN: {}'.format(enhance_me[gidx].name, num_fs_gain)
                    # the fs position index that the gear will move the FS counter to upon failure
                    fs_pointer_idx = lookup_idx + num_fs_gain

                    try:
                        gear_map_pointer_idx = min_gear_map[fs_pointer_idx]
                    except IndexError:
                        fs_pointer_idx = len(min_gear_map) - 1
                        gear_map_pointer_idx = min_gear_map[fs_pointer_idx]
                    gain_vec = fs_cost[lookup_idx: fs_pointer_idx]  # The fs costs to be gained from failure
                    gain_cost = -numpy.sum(gain_vec)
                    #print 'FS: {} | Gear {} | Cost: {}'.format(fs_pointer_idx, enhance_me[gear_map_pointer_idx].name, balance_vec_enh[gear_map_pointer_idx][fs_pointer_idx])
                    gear_cost_current_fs = gains_lookup_vec[gear_map_pointer_idx][lookup_idx]
                    gear_cost_ahead_fs = gains_lookup_vec[gear_map_pointer_idx][fs_pointer_idx]

                    gear_pointed_cost = gear_cost_ahead_fs - gear_cost_current_fs
                    if devaule_fs:
                        projected_gain = max(gear_pointed_cost, gain_cost)
                    else:
                        #projected_gain = max(gain_cost, min(0,self_reduction))
                        #projected_gain = min(0  , self_reduction)
                        #projected_gain = 0
                        projected_gain = gain_cost
                        #print(
                        #    'FS: {} | Gear {} | Cost: {} | Gain: {}'.format(i, go.get_full_name(),
                        #                                         self_reduction, projected_gain))
                    # All gear at this FS level and gain level have the same cost diff
                    cost_emmend[gear_idx_list] = projected_gain
                    #print cost_emmend

                fail_rate = 1 - chances[lookup_idx]

                this_bal_vec.T[lookup_idx] += numpy.multiply(fail_rate, cost_emmend)

                if balance_vec is balance_vec_enh:  # only update minimums when we are looking at the enhancement gear
                    new_min_idx = numpy.argmin(this_bal_vec.T[lookup_idx])
                    min_gear_map[lookup_idx] = new_min_idx
            return this_bal_vec

        enh_vec_ammend = check_out_gains(balance_vec_enh[:cron_start], balance_vec_enh, enhance_me, new_fs_cost)
        fs_vec_ammend = check_out_gains(balance_vec_fser, balance_vec_enh, fail_stackers, new_fs_cost)

        balance_vec_fser = fs_vec_ammend
        balance_vec_enh[:cron_start] = enh_vec_ammend

        return StrategySolution(settings, enhance_me, balance_vec_adds, fail_stackers, balance_vec_enh, balance_vec_fser)

    def calcEnhances_backup(self, count_fs=False, count_fs_fs=True, devaule_fs=False, regress=False):
        if self.fs_needs_update:
            self.calcFS()
        if self.gear_cost_needs_update:
            self.calc_equip_costs()
        settings = self.settings
        enhance_me = settings[EnhanceModelSettings.P_ENHANCE_ME]
        num_fs = settings[EnhanceSettings.P_NUM_FS]
        fail_stackers = settings[EnhanceModelSettings.P_FAIL_STACKERS]
        cum_fs_cost = self.cum_fs_cost
        fs_cost = self.fs_cost
        enhance_me = enhance_me

        new_fs_cost = fs_cost[:]

        fs_len = num_fs+1


        # This is a bit hacky and confusing but we need a cost estimate on potential fs gain vs recovery loss on items that have no success gain
        # For fail-stacking items there should not be a total cost gained from success. It only gains value from fail stacks.
        #zero_out = lambda x: x.enhance_lvl_cost(cum_fs_cost,  total_cost=numpy.array([[0]*fs_len]*len(x.gear_type.map)), count_fs=count_fs)

        balance_vec_fser = [x.fs_lvl_cost(cum_fs_cost, count_fs=count_fs_fs) for x in fail_stackers]
        balance_vec_enh = [x.enhance_lvl_cost(cum_fs_cost, count_fs=count_fs) for x in enhance_me]

        balance_vec_fser = numpy.array(balance_vec_fser)
        balance_vec_enh = numpy.array(balance_vec_enh)

        min_gear_map = [numpy.argmin(x) for x in balance_vec_enh.T]

        def check_out_gains(balance_vec, gains_lookup_vec, gear_list, fs_cost):
            """
            This method adds the value of increasing gains on gear that is ahead in the strategy fs list.
            For example:
            When attempting TRI on a weapon, if the user fails enhancement they will gain 3 fail stacks and these fail
            stacks have a value that is the increased chance of success with the 3 fail stacks. The actual cost is
            calculated by looking at what price of gear is up for enhancement 3 fail stacks higher then the qgear in
            question.
            If the gear ahead happens to be more expensive once the enhancement fails that gain becomes a cost.
            :param balance_vec:
            :param gains_lookup_vec:
            :param gear_list:
            :param fs_cost:
            :return:
            """
            #gearz = map(lambda x: gear_list[x], min_gear_map)
            # indexed by enhance_me returns the number of fail stacks gained by a failure
            gainz = [x.fs_gain() for x in gear_list]
            # indexed by sort order, returns index of enhance_me
            arg_sorts = numpy.argsort(gainz)
            fs_dict = {}
            #idx_ = 0
            for idx_, gear_idx in enumerate(arg_sorts):
                # = arg_sorts[idx_]
                try:
                    fs_dict[gainz[gear_idx]].append(gear_idx)
                except KeyError:
                    fs_dict[gainz[gear_idx]] = [gear_idx]

            # indexed by fs, returns list indexed by enhance_me of success chance
            chances = numpy.array([x.gear_type.map[x.get_enhance_lvl_idx()][:num_fs+1] for x in gear_list]).T

            # The very last item has to be a self pointer only
            this_bal_vec = numpy.copy(balance_vec)
            # cycle through all fsil stack levels
            for i in range(1, fs_len+1):
                lookup_idx = fs_len - i
                #this_gear = gearz[lookup_idx]

                cost_emmend = numpy.zeros(len(balance_vec))
                # cycle through all types of gear packaged by the number of fail stacks they will gain. Since it will be
                # the same gain value
                for num_fs_gain, gear_idx_list in fs_dict.items():
                    #for gidx in enhance_me_idx_list:
                    #    print 'GEAR: {}\t\t| GAIN: {}'.format(enhance_me[gidx].name, num_fs_gain)
                    # the fs position index that the gear will move the FS counter to upon failure
                    fs_pointer_idx = lookup_idx + num_fs_gain

                    try:
                        gear_map_pointer_idx = min_gear_map[fs_pointer_idx]
                    except IndexError:
                        fs_pointer_idx = len(min_gear_map) - 1
                        gear_map_pointer_idx = min_gear_map[fs_pointer_idx]
                    gain_vec = fs_cost[lookup_idx: fs_pointer_idx]  # The fs costs to be gained from failure
                    gain_cost = -numpy.sum(gain_vec)
                    #print 'FS: {} | Gear {} | Cost: {}'.format(fs_pointer_idx, enhance_me[gear_map_pointer_idx].name, balance_vec_enh[gear_map_pointer_idx][fs_pointer_idx])
                    gear_cost_current_fs = gains_lookup_vec[gear_map_pointer_idx][lookup_idx]
                    gear_cost_ahead_fs = gains_lookup_vec[gear_map_pointer_idx][fs_pointer_idx]
                    gear_pointed_cost = gear_cost_ahead_fs - gear_cost_current_fs
                    if devaule_fs:

                        #projected_gain = max(gear_pointed_cost, gain_cost)
                        projected_gain = gear_pointed_cost

                        #projected_gain = gear_pointed_cost
                        #gear_fs_cost = gear_pointed_cost
                        #new_fs_cost[i-1] = gear_fs_cost

                        #new_fs_cost[i - 1] = -projected_gain
                    else:
                        projected_gain = gain_cost
                    #projected_gain = gain_cost
                    # All gear at this FS level and gain level have the same cost diff
                    cost_emmend[gear_idx_list] = projected_gain
                    #print cost_emmend

                fail_rate = 1 - chances[lookup_idx]

                this_bal_vec.T[lookup_idx] += numpy.multiply(fail_rate, cost_emmend)

                if balance_vec is balance_vec_enh:  # only update minimums when we are looking at the enhancement gear
                    new_min_idx = numpy.argmin(this_bal_vec.T[lookup_idx])
                    min_gear_map[lookup_idx] = new_min_idx
            return this_bal_vec
                #gearz[lookup_idx] = gear_list[new_min_idx]

        #changed = [False]*fs_len
        #vals = [None]*fs_len
        enh_vec_ammend = check_out_gains(balance_vec_enh, balance_vec_enh, enhance_me, new_fs_cost)
        fs_vec_ammend = check_out_gains(balance_vec_fser, balance_vec_enh, fail_stackers, new_fs_cost)

        if devaule_fs and regress:
            max_iter = 100
            counter = 0
            changes = True
            while changes and counter<max_iter:
                min_gear_map_prev = min_gear_map[:]
                enh_vec_ammend = check_out_gains(balance_vec_enh, balance_vec_enh, enhance_me, new_fs_cost)
                fs_vec_ammend = check_out_gains(balance_vec_fser, balance_vec_enh, fail_stackers, new_fs_cost)

                changes = not min_gear_map == min_gear_map_prev
                counter += 1

        balance_vec_enh = enh_vec_ammend
        balance_vec_fser = fs_vec_ammend
        #for i, val in enumerate(changed):
        #    print 'FS: {}\t| B: {}\t| C: {}'.format(i, val, vals[i])

        #self.fs_cost = new_fs_cost
        return balance_vec_fser, balance_vec_enh

    def item_store(self) -> GearItemStore:
        return self.settings[self.settings.P_ITEM_STORE]

    def save_to_file(self, txt_path=None):
        if txt_path is None:
            # Force a write
            txt_path = self.settings.f_path
            if txt_path is None:
                txt_path = DEFAULT_SETTINGS_PATH
        self.settings.save(file_path=txt_path)

    def save(self):
        if not self.settings.f_path is None:
            self.settings.save()

    def load_from_file(self, txt_path):
        #TODO: add error checking here so setings files dont get overwritten
        self.settings.load(txt_path)
        settings = self.settings
        max_fs = settings[settings.P_NUM_FS]
        min_fs = settings[settings.P_QUEST_FS_INC]
        for i, pack in enumerate(settings[settings.P_ALTS]):
            alt_pic, alt_name, alt_fs = pack
            if alt_fs > max_fs:
                max_fs = alt_fs
                settings[settings.P_NUM_FS] = max_fs
            if alt_fs < min_fs:
                pack[2] = min_fs
                settings.invalidate()
        for i in settings[settings.P_VALKS]:
            if i > max_fs:
                max_fs = i
                settings[settings.P_NUM_FS] = max_fs

    def to_json(self):
        return json.dumps(self.settings.get_state_json(), indent=4)

    def from_json(self, json_str):
        self.settings.set_state_json(json.loads(json_str))
        self.clean_min_fs()
