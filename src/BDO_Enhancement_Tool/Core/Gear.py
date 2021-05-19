# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import json
import os
import sqlite3
import sys
import numpy

from BDO_Enhancement_Tool.utilities import check_pop, relative_path_convert
from .Item import Item
from .CronStones import CRON_MANAGER
from .ItemStore import ItemStore
from .Settings import EnhanceSettings

TXT_PATH_DATA = relative_path_convert('Data', fp=__file__)

FS_GAIN_PRI = 2
FS_GAIN_DUO = 3
FS_GAIN_TRI = 4
FS_GAIN_TET = 5
FS_GAIN_PEN = 6
FS_GAINS = [FS_GAIN_PRI,
            FS_GAIN_DUO,
            FS_GAIN_TRI,
            FS_GAIN_TET,
            FS_GAIN_PEN]

def generate_gear_obj(settings, gear_type, base_item_cost=None, enhance_lvl=None, name=None, sale_balance=None, id=None):
    if gear_type is None:
        gear_type = list(gear_types.items())[0][1]
    if base_item_cost is None:
        # This must have a value or some numerical members may be None
        base_item_cost = 0
    if name is None:
        name = ''
    gear = gear_type.instantiable(settings, base_item_cost=base_item_cost, enhance_lvl=enhance_lvl, gear_type=gear_type,
                     name=name, sale_balance=sale_balance, item_id=id)
    return gear


class ge_gen(list):
    def __init__(self, downcap=0.7, uniform=None):
        super(ge_gen, self).__init__([])
        self.down_cap = downcap
        self.uniform = uniform  # This forces the matrix to be square and not jagged

    def append(self, object):
        super(ge_gen, self).append(object)

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            start = idx.start
            stop = idx.stop
            step = idx.step
            if start is None:
                start = 0
            if stop is None:
                stop = super(ge_gen, self).__len__()
            if step is None:
                step = 1

            if stop < super(ge_gen, self).__len__():
                return super(ge_gen, self).__getitem__(idx)
            else:
                return [self.__getitem__(i) for i in range(start, stop, step)]

        try:
            return super(ge_gen, self).__getitem__(idx)
        except IndexError:
            # Use super here to avoid recursive stack overflow and throw exception in the event of an empty list
            zero_val = super(ge_gen, self).__getitem__(0)
            tent_val = self.__getitem__(idx-1)
            #tent_val2 = self.__getitem__(idx - 2)
            if tent_val >= self.down_cap:
                tent_val += (zero_val * 0.02)  #(9/350)  # 0.02
                #tent_val += zero_val * (9/350)
            else:
                tent_val += zero_val * 0.1
            if tent_val > 0.9:
                tent_val = 0.9
            # append should work here because of recursion
            self.append(tent_val)
            if self.uniform is not None:
                for u in self.uniform:
                    foo = u[idx]
            return tent_val


class gg_atmpt_cnt(list):
    def __init__(self, p_vals: ge_gen, fs_gain=1):
        super(gg_atmpt_cnt, self).__init__([])
        self.p_vals = p_vals  # Probability value vector
        self.fs_gain = fs_gain

    def append(self, object):
        raise ValueError('Cannot append')

    def __getitem__(self, idx):
        if not idx == 0:
            foo = self[idx-1]
        if isinstance(idx, slice):
            start = idx.start
            stop = idx.stop
            step = idx.step
            if start is None:
                start = 0
            if stop is None:
                stop = super(gg_atmpt_cnt, self).__len__()
            if step is None:
                step = 1

            if stop < super(gg_atmpt_cnt, self).__len__():
                return super(gg_atmpt_cnt, self).__getitem__(idx)
            else:
                return [self.__getitem__(i) for i in range(start, stop, step)]

        try:
            return super(gg_atmpt_cnt, self).__getitem__(idx)
        except IndexError:
            fs_gain = self.fs_gain
            p_vals = self.p_vals
            p_add = 0.0
            pre_add = 0.0
            s_idx = idx
            num_fail = 0
            while p_add < 1.0:
                pre_add = p_add
                p_add += p_vals[s_idx]
                s_idx += fs_gain
                num_fail += 1
            remainder_fraction = ((1.0 - pre_add) / p_vals[s_idx])
            _val = (num_fail-1) + remainder_fraction

            super(gg_atmpt_cnt, self).append(_val)
            return _val


class GearType(object):
    def __init__(self, name=None):
        self.name = name
        self.lvl_map = {}
        self.idx_lvl_map = {}
        self.map = []
        self.instantiable = None
        self.p_num_atmpt_map = []
        self.fs_gain = None
        self.downcap = None
        self.module = None
        self.type = None
        self.bt_start = None
        self.mat_cost = None
        self.repair_dura = None

    def __str__(self):
        return json.dumps({
            'name' : self.name,
            'lvl_map': self.lvl_map,
            'map': self.map,
        }, indent=4)

    def load_txt(self, txt):
        load_d = json.loads(txt)
        self.set_state_json(load_d)

    def set_state_json(self, load_d):
        for key, val in load_d.items():
            self.__dict__[key] = val
        self.module = self.module.replace('{KP}', __package__)
        idx_lvl_map = {}
        lvl_map = self.lvl_map
        for key,val in lvl_map.items():
            idx_lvl_map[val] = key
        self.idx_lvl_map = idx_lvl_map


        has_downcap = 'downcap' in load_d
        has_bt_start = 'bt_start' in load_d
        has_mat_cost = 'mat_cost' in load_d
        has_repair_dura = 'repair_dura' in load_d

        map = self.map
        new_map = []
        new_p_num_atmpt_map = []
        mat_cost = []

        if self.downcap is None:
            self.downcap = [0.7] * len(self.map)

        if self.fs_gain is None:
            self.fs_gain = [1] * len(self.map)

        if self.module is None or self.type is None:
            if len(self.lvl_map) == 5:
                self.instantiable = Smashable
            else:
                self.instantiable = Classic_Gear
        else:
            self.instantiable = sys.modules[self.module].__dict__[self.type]

        if self.instantiable is Smashable:
            if not has_downcap:
                self.downcap[lvl_map['DUO']] = 0.5
                self.downcap[lvl_map['TRI']] = 0.4
                self.downcap[lvl_map['TET']] = 0.3
                self.downcap[lvl_map['PEN']] = 0.2
            if not has_bt_start:
                self.bt_start = 1
        elif self.instantiable is Classic_Gear:
            if not has_bt_start:
                self.bt_start = self.lvl_map['TRI']
            if not has_mat_cost:
                is_weapon = self.name.lower().find('weapon') > -1
                if self.name.find('Blackstar') > -1:
                    bs_cost = [ItemStore.P_CONC_WEAPON]
                    hard = ItemStore.P_HARD_BLACK
                    sharp = ItemStore.P_SHARP_BLACK
                    conc_cost = [hard, sharp]
                elif is_weapon:
                    bs_cost = [ItemStore.P_BLACK_STONE_WEAPON]
                    conc_cost = [ItemStore.P_CONC_WEAPON]
                else:
                    bs_cost = [ItemStore.P_BLACK_STONE_ARMOR]
                    conc_cost = [ItemStore.P_CONC_ARMOR]
                for _ in range(0, self.lvl_map['PRI']):
                    mat_cost.append(bs_cost)
                for _ in range(self.lvl_map['PRI'], len(self.map)):
                    mat_cost.append(conc_cost)
                self.mat_cost = mat_cost
            if not has_repair_dura:
                if self.name.lower().find('(dura)') > -1:
                    self.repair_dura = 4
                else:
                    if self.name.lower().find('blackstar') > -1:
                        self.repair_dura = 10
                    else:
                        self.repair_dura = 5

        for i in range(0, len(map)):
            gg = ge_gen(downcap=self.downcap[i], uniform=new_map)
            new_map.append(gg)
            new_p_num_atmpt_map.append(gg_atmpt_cnt(gg, fs_gain=self.fs_gain[i]))

        #new_map = [ge_gen()] * len(map)
        for i, itm in enumerate(map):
            for val in itm:
                new_map[i].append(val)
        self.map = new_map
        self.p_num_atmpt_map = new_p_num_atmpt_map

    def get_fs_gain(self, lvl_idx):
        return self.fs_gain[lvl_idx]

    def bin_mp(self, idx):
        if idx < 0:
            return 0
        if self.name.find('Weapons') > -1:
            if self.name.find('Green') > -1:
                if idx < 4:
                    idx = 1
                elif idx < 6:
                    idx = 2
                elif idx < 9:
                    idx = 3
                else:
                    idx = idx - 5
            else:
                if idx < 4:
                    idx = 1
                elif idx < 6:
                    idx = 2
                else:
                    idx = idx - 3
        elif self.name.find('Armor') > -1:
            if self.name.find('Green') > -1:
                if idx < 5:
                    idx = 1
                elif idx < 8:
                    idx = 2
                elif idx < 11:
                    idx = 3
                else:
                    idx = idx - 7
            else:
                if idx < 5:
                    idx = 1
                elif idx < 8:
                    idx = 2
                else:
                    idx = idx - 5
        return idx

    def enumerate_gt_lvl(self, gl):
        min_idx = self.idx_lvl_map[0]
        this_idx = self.lvl_map[gl]
        try:
            lvl_num = int(min_idx) - 1
            return lvl_num + this_idx
        except ValueError:
            return this_idx

    def gt_lvl_compare(self, gl1, gl2):
        return self.enumerate_gt_lvl(gl1) - self.enumerate_gt_lvl(gl2)

    def get_mat_costs(self, item_store: ItemStore):
        black_stone_costs = []
        mat_costs = self.mat_cost
        for mat_l in mat_costs:  # Each struct is one enhancement level
            cost = 0
            for mato in mat_l:  # Each list is a list of item ids in the item store
                if isinstance(mato, list):  # List item may be a multiplier tuple
                    num, mat = mato
                else:
                    num = 1
                    mat = mato
                cost += num * item_store.get_cost(mat)
            black_stone_costs.append(cost)
        return black_stone_costs

    def get_state_json(self):
        down_caps = []
        map = []

        for ggen in self.map:
            map.append([ggen[0]])
            down_caps.append(ggen.down_cap)
        return {
            'name': self.name,
            'lvl_map': self.lvl_map,
            'map': map,
            'downcap': down_caps,
            'fs_gain': self.fs_gain,
            'bt_start': self.bt_start,
            'mat_cost': self.mat_cost,
            'repair_dura': self.repair_dura,
            'module': self.instantiable.__module__,
            'type': self.instantiable.__name__
        }

    def __getstate__(self):
        return self.get_state_json()

    def __setstate__(self, state):
        self.set_state_json(state)


class Gear(Item):
    def __init__(self, settings, gear_type, base_item_cost=None, enhance_lvl=None, name=None, sale_balance=None,
                 target_lvls=None, item_id=None):
        if sale_balance is None:
            sale_balance = 0

        self.settings = settings
        self.base_item_cost = base_item_cost  # Cost of procuring the equipment
        self.enhance_lvl = enhance_lvl
        self.gear_type: GearType = gear_type
        #self.fs_cost = []
        self.backtrack_accumulator = False

        self.cron_stone_dict = {}
        self.cron_block = set()
        self.cron_use = set()
        self.cron_downg_chance = 0

        self.pri_cost = 0

        self.cost_vec = []  # Vectors of cost for each enhancement level and each fail stack level
        self.restore_cost_vec = []
        self.cost_vec_min = []  # Vectors of cost for each enhancement level and each fail stack level
        self.restore_cost_vec_min = []
        #self.tap_risk = []
        #self.cum_fs_cost = []
        self.lvl_success_rate = None  # Probabilities of success for the current level of enhancement
        self.repair_cost = None  # Cached repair cost for a normal fail, not a fail specific to enhancement level
        self.name = name
        self.sale_balance = sale_balance
        self.costs_need_update = True
        if target_lvls is None:
            target_lvls = self.guess_target_lvls(enhance_lvl)
        self.target_lvls = target_lvls
        super(Gear, self).__init__(item_id=item_id)

    def set_procurement_cost(self, intbal):
        self.procurement_cost = int(round(intbal))
        self.costs_need_update = True

    def set_enhance_lvl(self, enhance_lvl):
        self.enhance_lvl = enhance_lvl
        gear_type = self.gear_type
        # = self.settings[EnhanceSettings.P_NUM_FS]
        if gear_type is not None:
            self.lvl_success_rate = gear_type.map[gear_type.lvl_map[enhance_lvl]]
        self.costs_need_update = True
        #    self.fs_vec[self.num_fs]

    def set_gear_type(self, gear_type:GearType):
        self.gear_type = gear_type
        enhance_lvl = self.enhance_lvl
        #num_fs = self.settings[EnhanceSettings.P_NUM_FS]
        if enhance_lvl is not None:
            # Just manually catch this exception
            self.lvl_success_rate = gear_type.map[gear_type.lvl_map[enhance_lvl]]
        self.costs_need_update = True

    def set_gear_type_by_str(self, str_gear_type):
        self.set_gear_type(gear_types[str_gear_type])
        self.costs_need_update = True

    def set_base_item_cost(self, cost):
        self.base_item_cost = cost
        self.costs_need_update = True

    def set_item_id(self, item_id):
        super(Gear, self).set_item_id(item_id)
        try:
            crons = CRON_MANAGER.check_out_gear(self)
        except sqlite3.ProgrammingError:
            return
        if crons is None:
            return
        gear_type = self.gear_type
        min_lvl = gear_type.idx_lvl_map[0]
        max_lvl = gear_type.idx_lvl_map[len(gear_type.map)-1]
        min_lvl_idx = gear_type.enumerate_gt_lvl(min_lvl)
        max_lvl_idx = gear_type.enumerate_gt_lvl(max_lvl)
        for i in range(min_lvl_idx, max_lvl_idx+1):
            msg = str(i)
            if msg in crons:
                actual_idx = i
                lvl_idx = actual_idx-min_lvl_idx
                if lvl_idx not in self.cron_stone_dict:
                    #print('{} for {} {}'.format(crons[msg], self.gear_type.idx_lvl_map[lvl_idx] ,self.name))
                    self.cron_stone_dict[lvl_idx] = crons[msg]

    def set_gear_params(self, gear_type, enhance_lvl):
        self.set_gear_type(gear_type)
        #self.gear_type = gear_type
        self.set_enhance_lvl(enhance_lvl)

    def get_repair_cost(self):
        return self.repair_cost

    def get_enhance_lvl_idx(self, enhance_lvl=None):
        if enhance_lvl is None:
            enhance_lvl = self.enhance_lvl
        return self.gear_type.lvl_map[enhance_lvl]

    def get_full_name(self):
        enhance_lvl = self.enhance_lvl
        try:
            int(enhance_lvl)
            enhance_lvl = '+'+enhance_lvl
        except ValueError:
            pass
        ret = enhance_lvl + " " + self.name
        if self.get_enhance_lvl_idx() in self.cron_use:
            ret = "CRON: " + ret
        return ret

    def get_cost_obj(self):
        return self.cost_vec

    def get_min_cost(self):
        return self.cost_vec_min

    def get_backtrack_start(self):
        return self.gear_type.bt_start

    def guess_target_lvls(self, enhance_lvl=None, intersect=None, excludes=None):
        if enhance_lvl is None:
            enhance_lvl = self.enhance_lvl
        if enhance_lvl is None:
            this_idx = 0
        else:
            this_idx = self.get_enhance_lvl_idx(enhance_lvl)
        backtrack_start = self.get_backtrack_start()-1
        this_idx = min(this_idx+1, backtrack_start)
        idx_list = range(this_idx, len(self.gear_type.lvl_map))
        target_lvls = [self.gear_type.idx_lvl_map[x] for x in idx_list]
        if enhance_lvl in target_lvls:
            target_lvls.remove(enhance_lvl)

        if intersect is not None:
            target_lvls = [x for x in intersect if x in target_lvls]

        if excludes is not None:
            target_lvls = [x for x in target_lvls if x not in excludes]

        return target_lvls

    def enhance_lvl_to_number(self, enhance_lvl=None):
        if enhance_lvl is None:
            enhance_lvl = self.enhance_lvl
        return self.gear_type.lvl_map[enhance_lvl]

    def enhance_lvl_from_number(self, num):
        return self.gear_type.idx_lvl_map[num]

    def prep_lvl_calc(self):
        gear_type = self.gear_type
        enhance_lvl = self.enhance_lvl
        #num_fs = self.settings[EnhanceSettings.P_NUM_FS]
        self.lvl_success_rate = gear_type.map[gear_type.lvl_map[enhance_lvl]]

    def calc_lvl_repair_cost(self, lvl_costs=None, use_crons=False):
        raise NotImplementedError('Must implement calc_lvl_repair_cost')

    def calc_enhance_vectors(self):
        raise NotImplementedError('Must implement calc_enhance_vectors')

    def enhance_cost_simp(self, cum_fs, material_cost, fail_repair_cost_nom):
        settings = self.settings
        num_fs = settings[EnhanceSettings.P_NUM_FS]+1
        p_num_f_map = self.gear_type.p_num_atmpt_map
        _map = self.gear_type.map
        num_f_m = numpy.array(p_num_f_map) - 1

        num_enhance_lvls = len(_map)


        cum_fs_tile = numpy.tile(cum_fs, (num_enhance_lvls, 1))

        fail_cost = fail_repair_cost_nom[:, numpy.newaxis]
        opportunity_cost = fail_cost + material_cost[:, numpy.newaxis]
        opportunity_cost = (opportunity_cost * num_f_m) + material_cost[:, numpy.newaxis]


        restore_cost = opportunity_cost.T[:num_fs].T
        total_cost = restore_cost + cum_fs_tile
        min_cost_idxs = list(map(numpy.argmin, total_cost))
        restore_cost_min = [x[1][min_cost_idxs[x[0]]] for x in enumerate(restore_cost)]
        total_cost_min = [x[1][min_cost_idxs[x[0]]] for x in enumerate(total_cost)]
        return restore_cost, restore_cost_min, total_cost, total_cost_min

    def enhance_cost(self, cum_fs):
        if not self.costs_need_update:
            return self.cost_vec
        settings = self.settings
        num_fs = settings[EnhanceSettings.P_NUM_FS]+1
        p_num_f_map = self.gear_type.p_num_atmpt_map
        _map = self.gear_type.map
        cron_cost = self.settings[EnhanceSettings.P_CRON_STONE_COST]
        num_f_m = numpy.array(p_num_f_map) - 1  # avg_num_fails is distinct from avg_num_attempts
        btau = self.backtrack_accumulator

        num_enhance_lvls = len(_map)
        self.cron_use = set()

        #print('{} - {}'.format(self.get_full_name(), self.cron_block))
        cum_fs = cum_fs[:num_fs]
        cron_dc = self.cron_downg_chance
        material_cost, fail_repair_cost_nom = self.calc_enhance_vectors()

        restore_cost, restore_cost_min, total_cost, total_cost_min = self.enhance_cost_simp(cum_fs, material_cost, fail_repair_cost_nom)

        backtrack_start = self.gear_type.bt_start
        tc_min_accum = total_cost_min[backtrack_start - 1] # Smashables have to start from backtrack_start on dry fail
        rc_min_accum = restore_cost_min[backtrack_start - 1] # Smashables have to start from backtrack_start on dry fail
        for gear_lvl in range(backtrack_start, num_enhance_lvls):
            mm = _map[gear_lvl]
            sec = mm[:69:3]
            pt = numpy.sum(sec)
            new_fail_cost = fail_repair_cost_nom[gear_lvl] + material_cost[gear_lvl]
            if btau:
                new_fail_cost += tc_min_accum
            else:
                new_fail_cost += total_cost_min[gear_lvl - 1]
            enh_cost = (new_fail_cost * num_f_m[gear_lvl]) + material_cost[gear_lvl] # Material for 1 success

            this_cost = enh_cost + cum_fs
            this_idx = numpy.argmin(this_cost)

            # Check cron stone
            use_crons = False
            if gear_lvl in self.cron_stone_dict and gear_lvl not in self.cron_block:
                num_crons = self.cron_stone_dict[gear_lvl]
                probabilities = numpy.array(_map[gear_lvl][:num_fs])
                num_attempts = numpy.full(len(probabilities), 1) / probabilities
                sum_cron_cost = num_crons * cron_cost
                cron_fail_cost = (1 - probabilities) * (fail_repair_cost_nom[gear_lvl] + (cron_dc * total_cost_min[gear_lvl - 1]))
                cron_fail_cost_rest = (1 - probabilities) * (fail_repair_cost_nom[gear_lvl] + (cron_dc * restore_cost_min[gear_lvl - 1]))
                cron_attempt_cost = cron_fail_cost + sum_cron_cost + material_cost[gear_lvl]
                cron_attempt_cost_rest = cron_fail_cost_rest + sum_cron_cost + material_cost[gear_lvl]
                cron_enh_cost = num_attempts * cron_attempt_cost
                cron_enh_cost_rest = num_attempts * cron_attempt_cost_rest
                cron_enh_cost = cron_enh_cost + cum_fs
                min_cron_cost_idx = numpy.argmin(cron_enh_cost)
                use_crons = cron_enh_cost[min_cron_cost_idx] < this_cost[this_idx]
                if use_crons:
                    this_cost = cron_enh_cost
                    enh_cost_rest = cron_enh_cost_rest
                    this_idx = min_cron_cost_idx
                    self.cron_use.add(gear_lvl)
            total_cost[gear_lvl] = this_cost
            total_cost_min[gear_lvl] = this_cost[this_idx]
            tc_min_accum += this_cost[this_idx]

            # Update material-only costs
            if not use_crons:
                new_fail_cost_rest = fail_repair_cost_nom[gear_lvl] + material_cost[gear_lvl]
                if btau:
                    new_fail_cost_rest += rc_min_accum
                else:
                    new_fail_cost_rest += restore_cost_min[gear_lvl - 1]
                enh_cost_rest = (new_fail_cost_rest * num_f_m[gear_lvl]) + material_cost[gear_lvl] # Meterial for 1 success

            restore_cost[gear_lvl] = enh_cost_rest
            restore_cost_min[gear_lvl] = enh_cost_rest[this_idx]
            rc_min_accum += enh_cost_rest[this_idx]


        self.cost_vec = numpy.array(total_cost)
        self.restore_cost_vec = numpy.array(restore_cost)
        self.cost_vec_min = numpy.array(total_cost_min)
        self.restore_cost_vec_min = numpy.array(restore_cost_min)
        #self.restore_cost_vec.flags.writeable = False
        self.cost_vec.flags.writeable = False
        self.costs_need_update = False

        return total_cost

    #def calc_fs_success_time(self):
    #    pass

    def enhance_lvl_cost(self, cum_fs, total_cost=None, lvl=None, count_fs=False, use_crons=False):
        """
        Calculates the cost of attempting an enhancement at a given level.
        This is the potential gain if success weighed against the possible cost of failure. The cost of failure is the
        cost of returning to the item/player's state before the enhancement was attempted.
        """
        self.prep_lvl_calc()  # This is for repair cost calculation
        if lvl is None:
            lvl = self.enhance_lvl
        if total_cost is None:
            if count_fs:
                total_cost = self.cost_vec_min
            else:
                total_cost = self.restore_cost_vec_min
            #total_cost = self.get_min_cost()
        lvl_dx = self.get_enhance_lvl_idx(lvl)
        this_lvl = self.gear_type.lvl_map[lvl]
        cron_cost = self.settings[EnhanceSettings.P_CRON_STONE_COST]
        num_crons = 0
        if use_crons:
            if lvl_dx in self.cron_stone_dict:
                num_crons = self.cron_stone_dict[lvl_dx]
            else:
                raise Exception('Cannot cron with no cron values')
        num_fs = self.settings[EnhanceSettings.P_NUM_FS]

        if count_fs is False:
            cum_fs = numpy.zeros(len(cum_fs))
        this_total_cost = total_cost[this_lvl]
        success_rates = numpy.array(self.gear_type.map[this_lvl][:num_fs+1])

        fail_rate = numpy.ones(success_rates.shape) - success_rates
        success_balance = cum_fs - this_total_cost
        success_cost = success_rates * success_balance

        fail_balance = self.calc_lvl_repair_cost(lvl_costs=total_cost, use_crons=use_crons)

        fail_cost = fail_rate * fail_balance
        tap_total_cost = success_cost + fail_cost + self.calc_lvl_flat_cost()
        if use_crons:
            tap_total_cost += cron_cost * num_crons

        return tap_total_cost

    def fs_lvl_cost(self, cum_fs, lvl=None, count_fs=True):
        """
        Enhance cost at each probability accounting for the fail stacks absorbed upon success, the value gained from the
        successful enhancement upon success (in fail stack units) and the cost of the fail stacks gained upon failure
        :param cum_fs:
        :param fs_cost:
        :param total_cost:
        :param lvl:
        :return:
        """
        self.prep_lvl_calc()  # This is for repair cost calculation
        #self.calc_lvl_repair_cost()
        if lvl is None:
            lvl = self.enhance_lvl
        num_fs = self.settings[EnhanceSettings.P_NUM_FS]

        this_lvl = self.gear_type.lvl_map[lvl]
        success_rates = numpy.array(self.gear_type.map[this_lvl])[:num_fs+1]


        fail_rate = numpy.ones(success_rates.shape) - success_rates

        if count_fs is False:
            cum_fs = numpy.zeros(len(cum_fs))
        success_balance = cum_fs + self.calc_FS_enh_success()  # calc_FS_enh_success return negative when gain
        success_cost = success_rates * success_balance

        # Repair cost variable so that backtracking cost is not included
        fail_balance = self.repair_cost

        fail_cost = fail_rate * fail_balance
        tap_total_cost = success_cost + fail_cost + self.calc_lvl_flat_cost()

        return tap_total_cost

    def get_state_json(self):
        return {
            'base_item_cost': self.base_item_cost,
            'enhance_lvl': self.enhance_lvl,
            'gear_type': self.gear_type.name,
            'name': self.name,
            'sale_balance': self.sale_balance,
            'item_id': self.item_id,
            'target_lvls': self.target_lvls,
            'pri_cost': self.pri_cost
        }

    def set_state_json(self, json_obj):
        # Do not call __init__ as it wil erase other class members from inherited classes
        self.fs_cost = []
        self.cost_vec = []
        #self.tap_risk = []
        self.lvl_success_rate = None
        self.repair_cost = None
        gear_type_str = json_obj.pop('gear_type')
        item_id = check_pop(json_obj, 'item_id')
        self.__dict__.update(json_obj)
        self.set_gear_type(gear_types[gear_type_str])
        if item_id is not None:
            self.set_item_id(item_id)

    def simulate_FS(self, fs_count, last_cost):
        raise NotImplementedError()

    def to_json(self):
        return json.dumps(self.get_state_json(), indent=4)

    def calc_FS_enh_success(self, time_penalty=None, time=None):
        raise NotImplementedError()

    def calc_FS_enh_success_old(self):
        # When an enhancement succeeded with the goal of selling the product the net gain is the sale balance minus
        # the bas material needed to perform the enhancement
        tax = self.settings.tax
        return -((self.sale_balance*tax) - self.procurement_cost)

    def fs_gain(self):
        return self.gear_type.get_fs_gain(self.get_enhance_lvl_idx())

    def from_json(self, json_str):
        self.set_state_json(json.loads(json_str))

    def calc_lvl_flat_cost(self):
        raise NotImplementedError()

    def upgrade(self):
        this_dx = self.get_enhance_lvl_idx()
        new_idx = self.gear_type.idx_lvl_map[this_dx + 1]
        self.set_enhance_lvl(new_idx)

    def downgrade(self):
        this_dx = self.get_enhance_lvl_idx()
        new_idx = self.gear_type.idx_lvl_map[this_dx - 1]
        self.set_enhance_lvl(new_idx)

    def duplicate(self):
        retme: Gear = self.gear_type.instantiable(self.settings, self.gear_type)
        retme.set_state_json(self.get_state_json())
        return retme


class Classic_Gear(Gear):

    def __init__(self, settings, gear_type, **kwargs):
        super(Classic_Gear, self).__init__(settings, gear_type, **kwargs)
        #self.fail_dura_cost = fail_dura_cost
        self.using_memfrags = False

    def set_gear_type(self, gear_type):
        super(Classic_Gear, self).set_gear_type(gear_type)

    def set_base_item_cost(self, cost):
        super(Classic_Gear, self).set_base_item_cost(cost)
        self.calc_repair_cost()

    def prep_lvl_calc(self):
        #self.calc_FS_costs()
        self.calc_repair_cost()
        super(Classic_Gear, self).prep_lvl_calc()

    def get_durability_cost(self, enhance_idx=None):
        if enhance_idx is None:
            enhance_idx = self.get_enhance_lvl_idx()
        return self.gear_type.repair_dura[enhance_idx]

    def get_repair_cost(self):
        repair_cost = self.repair_cost
        if repair_cost is None:
            self.calc_repair_cost()
        return self.repair_cost

    def calc_repair_cost(self):
        """
        This is not the level cost this is the basic repair cost
        :return:
        """
        fail_dura_cost = self.get_durability_cost(enhance_idx=0)

        mem_frag_cost = self.settings[EnhanceSettings.P_ITEM_STORE].get_cost(ItemStore.P_MEMORY_FRAG)

        tentative_cost = self.base_item_cost * (fail_dura_cost / 10.0)
        memfrag_cost = mem_frag_cost * fail_dura_cost
        if memfrag_cost < tentative_cost:
            self.using_memfrags = True
            self.repair_cost = memfrag_cost
            return memfrag_cost
        else:
            self.using_memfrags = False
            self.repair_cost = tentative_cost
            return tentative_cost

    def calc_enhance_vectors(self):
        item_store = self.settings[EnhanceSettings.P_ITEM_STORE]


        fail_repair_cost = self.calc_repair_cost()
        fail_dura_cost = self.get_durability_cost(0)
        fail_repair_cost_m = numpy.array(self.gear_type.repair_dura) / fail_dura_cost
        fail_repair_cost_nom = fail_repair_cost_m * fail_repair_cost

        mat_costs = self.gear_type.get_mat_costs(item_store) #.mat_cost

        return numpy.array(mat_costs), fail_repair_cost_nom

    def calc_lvl_flat_cost(self):
        item_store = self.settings[EnhanceSettings.P_ITEM_STORE]
        this_lvl = self.get_enhance_lvl_idx()
        return self.gear_type.get_mat_costs(item_store)[this_lvl]

    def calc_lvl_repair_cost(self, lvl_costs=None, use_crons=False):
        if lvl_costs is None:
            lvl_costs = self.get_min_cost()
        fail_balance = self.repair_cost * (self.get_durability_cost() / self.get_durability_cost(0))

        if use_crons:
            return fail_balance

        backtrack_start = self.get_backtrack_start()
        this_lvl = self.get_enhance_lvl_idx()
        if this_lvl >= backtrack_start:
            fail_balance += lvl_costs[this_lvl - 1]
        return fail_balance

    def calc_FS_enh_success(self, time_penalty=None, time=30):
        if self.enhance_lvl == '15':
            cleanse_cost = self.settings[EnhanceSettings.P_CLEANSE_COST]
            cost = cleanse_cost
            if time_penalty is not None:
                cost += time * time_penalty
        else:
            cost = 0
        return cost

    def simulate_FS(self, fs_count, last_cost, pen_time=True):
        self.prep_lvl_calc()  # This is for repair cost calculation
        #num_fs = self.settings[EnhanceSettings.P_NUM_FS]
        suc_rate = self.lvl_success_rate[fs_count]
        dura_cost = self.get_durability_cost()
        repair_fraction = dura_cost / self.get_durability_cost(enhance_idx=0)
        repair_cost = self.get_repair_cost() * repair_fraction
        cleanse_t = None
        time_penalty = None
        repair_time = 0
        if pen_time:
            cleanse_t = self.settings[EnhanceSettings.P_TIME_CLEANSE]
            time_penalty = self.settings[EnhanceSettings.P_TIME_PENALTY]
            repair_time = self.settings[EnhanceSettings.P_TIME_REPAIR]
        penalty_p_s = time_penalty / 3600.0
        flat_cost = self.calc_lvl_flat_cost()


        fail_rate = 1.0 - suc_rate
        #tax = self.settings.tax

        # Splitting flat_cost here since it will have a 1.0 ratio when multiplied by succ and fail rate and
        # it should be negated when the enh_success cost (gain) overrides it
        fail_cost = flat_cost + repair_cost + (repair_time * dura_cost * penalty_p_s)
        success_cost = flat_cost + last_cost + self.calc_FS_enh_success(time_penalty=penalty_p_s, time=cleanse_t)

        opportunity_cost = (suc_rate * success_cost) + (fail_rate * fail_cost)
        avg_num_opportunities = numpy.divide(1.0, fail_rate)
        #print '{}: {}'.format(self.name, self.fs_gain())
        return avg_num_opportunities * opportunity_cost

    def clone_down(self):
        pass


class Smashable(Gear):
    def __init__(self, settings, gear_type, **kwargs):
        super(Smashable, self).__init__(settings, gear_type, **kwargs)
        self.repair_bt_start_idx = 1
        self.repair_cost = 0  # This is 0 because repair cost is only used for durability and this item does not lose dura
        self.backtrack_accumulator = True
        self.cron_downg_chance = 0.4

    def prep_lvl_calc(self):
        self.repair_cost = 0
        super(Smashable, self).prep_lvl_calc()

    def guess_target_lvls(self, enhance_lvl=None, intersect=None, excludes=None):
        if enhance_lvl is None:
            enhance_lvl = self.enhance_lvl

        # Keep order sorted
        target_lvls = [self.enhance_lvl_from_number(i) for i in range(len(self.gear_type.map))]

        if enhance_lvl in target_lvls:
            target_lvls.remove(enhance_lvl)

        if intersect is not None:
            target_lvls = [x for x in intersect if x in target_lvls]

        if excludes is not None:
            target_lvls = [x for x in target_lvls if x not in excludes]

        return target_lvls

    def enhance_cost_simp(self, cum_fs, material_cost, fail_repair_cost_nom):
        settings = self.settings
        num_fs = settings[EnhanceSettings.P_NUM_FS]+1
        p_num_f_map = self.gear_type.p_num_atmpt_map
        _map = self.gear_type.map
        bts = self.gear_type.bt_start
        num_atmpt_m = numpy.array(p_num_f_map[:bts])
        num_f_m = num_atmpt_m - 1
        cron_cost = self.settings[EnhanceSettings.P_CRON_STONE_COST]

        num_enhance_lvls = len(_map)


        cum_fs = cum_fs[:num_fs]
        total_cost = numpy.tile(cum_fs, (num_enhance_lvls, 1))
        restore_cost = numpy.full(total_cost.shape, 0, dtype=numpy.float)
        total_cost_min = numpy.full(len(total_cost), 0, dtype=numpy.float)
        restore_cost_min = numpy.full(len(total_cost), 0, dtype=numpy.float)


        opportunity_cost = numpy.copy(material_cost[:bts, numpy.newaxis])
        opportunity_cost[0][0] = material_cost[0] * 2
        restore_cost[:bts] = opportunity_cost * num_atmpt_m
        total_cost[:bts] += restore_cost[:bts]

        for gear_lvl in range(0, bts):
            min_tc_idx = numpy.argmin(total_cost[gear_lvl])
            total_cost_min[gear_lvl] = total_cost[gear_lvl][min_tc_idx]
            restore_cost_min[gear_lvl] = restore_cost[gear_lvl][min_tc_idx]
            if gear_lvl in self.cron_stone_dict and gear_lvl not in self.cron_block:
                num_crons = self.cron_stone_dict[gear_lvl]
                this_cron_cost = num_crons * cron_cost
                fail_cost_cron = (1 - numpy.array(_map[gear_lvl][:num_fs])) * (self.cron_downg_chance * material_cost[gear_lvl])
                rest_cost_cron = num_atmpt_m[gear_lvl] * ((material_cost[gear_lvl] + this_cron_cost) + fail_cost_cron)
                rest_cost_cron += material_cost[gear_lvl]  # Acquire the initial smashable
                cost_cron = rest_cost_cron + cum_fs
                min_cron_idx = numpy.argmin(cost_cron)
                min_cost_cron = cost_cron[min_cron_idx]
                if min_cost_cron < total_cost_min[gear_lvl]:
                    self.cron_use.add(gear_lvl)
                    total_cost[gear_lvl] = cost_cron
                    total_cost_min[gear_lvl] = min_cost_cron
                    restore_cost[gear_lvl] = rest_cost_cron
                    restore_cost_min[gear_lvl] = rest_cost_cron[min_cron_idx]

        return restore_cost, restore_cost_min, total_cost, total_cost_min

    def calc_lvl_repair_cost(self, lvl_costs=None, use_crons=False):
        if lvl_costs is None:
            lvl_costs = self.get_min_cost()

        lvl_indx = self.get_enhance_lvl_idx()
        if lvl_indx == 0:
            if use_crons:
                return -((1-self.cron_downg_chance) * self.base_item_cost)
            else:
                return 0  # Price of failure scales with number of times paying material cost not repair cost
        else:
            if use_crons:
                return self.cron_downg_chance * lvl_costs[lvl_indx-1]
            else:
                return numpy.sum(lvl_costs[:lvl_indx])

    def calc_enhance_vectors(self):
        enhance_lvls = len(self.gear_type.map)
        matreial_cost = numpy.ones(enhance_lvls) * self.base_item_cost
        #matreial_cost[0] += self.base_item_cost
        repair_costs = numpy.zeros(enhance_lvls)  # This is item repair not back-tracking repair
        return matreial_cost, repair_costs

    def calc_lvl_flat_cost(self):
        if self.get_enhance_lvl_idx() == 0:
            return self.base_item_cost * 2
        else:
            return self.base_item_cost

    def simulate_FS(self, fs_count, last_cost):
        self.prep_lvl_calc()  # This is for repair cost calculation
        num_fs = self.settings[EnhanceSettings.P_NUM_FS]
        fs_vec = self.lvl_success_rate[:num_fs+1]
        suc_rate = fs_vec[fs_count]
        fail_rate = 1.0 - suc_rate
        success_cost = last_cost
        oppertunity_cost = (suc_rate * success_cost) + self.calc_lvl_flat_cost()
        avg_num_oppertunities = numpy.divide(1.0, fail_rate)
        return avg_num_oppertunities * oppertunity_cost

    def clone_down(self):
        pass

    def get_state_json(self):
        this_dict = super(Smashable, self).get_state_json()
        return this_dict



files = os.listdir(TXT_PATH_DATA)
gear_types = {}



for feel in files:
    if feel.endswith('.json'):
        pash = os.path.join(TXT_PATH_DATA, feel)
        name = feel[:feel.find('.')]
        gt = GearType(name=name)
        with open(pash, 'r') as f:
            gt_obj = json.loads(f.read())
            gt_obj['module'] = '{KP}.Gear'
            gt.set_state_json(gt_obj)
        with open(pash, 'w') as f:
            f.write(json.dumps(gt_obj, indent=4))
        gear_types[name] = gt