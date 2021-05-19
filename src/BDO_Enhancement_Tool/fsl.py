# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
from math import ceil
from random import randint
from typing import Union, List
import numpy

from .Core.Gear import Gear
from .Core.ItemStore import ItemStoreException, ItemStore
from .common import get_num_level_attempts, loop_sum


#from .EnhanceModelSettings import EnhanceModelSettings


class FailStackList(object):
    REMAKE_DISCARD_STACK = 'discard'
    REMAKE_OVERSTACK = 'overstack'

    def __init__(self, settings, secondary:Union[Gear,None], optimal_primary_list: Union[List[Gear],None], optimal_cost, cum_cost, num_fs=None):
        self.settings = settings
        self.gear_list = None
        self.fs_cost = None
        self.fs_cum_cost = None

        self.needs_update = True

        if num_fs is None:
            num_fs = settings[settings.P_NUM_FS]
        self.num_fs = num_fs

        #self.invalidated = True
        self.set_gear_list(optimal_primary_list)
        self.set_fs_cost(optimal_cost)
        self.set_fs_cum_cost(cum_cost)

        self.starting_pos = None
        self.secondary_gear: Gear = secondary
        self.secondary_map = []

        self.gearz: List[Gear] = []  # List of gear set to the correct enhancement level
        self.fs_gain: List[int] = []  # List of FS gain for each gear
        self.num_levels: Union[None, int] = None  # Number of gear levels in this map
        self.num_attempts: List[float] = []  # of attempts before failing through per level
        self.num_attempts_b4_suc: List[float] = [] # Number of attempts before a success is expected
        self.avg_cost = []
        self.probs_list: List[numpy.ndarray] = []  # List of probabilities for each level of gear and fs level used
        self.prob_all_fails: List[float] = []  # Probability of stacking though a level in one go
        self.expected_num_succ: List[float] = []
        self.num_sweeps_succ: List[float] = []  # Expected number of sweeps through level before one success is expected
        self.num_fails_total: List[float] = []  # Number of fails per level counting stack pops

    def set_primary_data(self, optimal_primary_list: List[Gear], optimal_cost, cum_cost):
        self.set_fs_cost(optimal_cost)
        self.set_fs_cum_cost(cum_cost)
        self.set_gear_list(optimal_primary_list)  # order matters with above

    def set_gear_list(self, optimal_primary_list: List[Gear]):
        if optimal_primary_list is not None:
            self.needs_update = True
            if self.num_fs < len(optimal_primary_list) - 1:
                optimal_primary_list = optimal_primary_list[:self.num_fs+1]
            self.gear_list = optimal_primary_list.copy()

    def set_fs_cost(self, optimal_cost):
        if optimal_cost is not None:
            self.needs_update = True
            if len(optimal_cost) <= self.num_fs:
                self.num_fs = len(optimal_cost) - 1
            self.fs_cost = numpy.copy(optimal_cost[:self.num_fs+1])

    def set_fs_cum_cost(self, cum_cost):
        if cum_cost is not None:
            self.needs_update = True
            if len(cum_cost) <= self.num_fs:
                self.num_fs = len(cum_cost) - 1
            self.fs_cum_cost = numpy.copy(cum_cost[:self.num_fs+1])

    def generate_secondary_map(self, starting_pos):
        settings = self.settings
        num_fs = self.num_fs + 1
        s_g = self.secondary_gear
        s_g_bt = s_g.get_backtrack_start()
        gear_type = s_g.gear_type
        len_map = len(gear_type.map)
        max_idx = len_map - 1
        start_g_lvl_idx = s_g_bt - 1
        secondary_map = [1] * (len_map-start_g_lvl_idx)
        self.secondary_map = secondary_map
        self.starting_pos = starting_pos
        this_pos = starting_pos
        this_gl_idx = start_g_lvl_idx
        while this_pos < num_fs:
            fs_left = num_fs - this_pos
            start_g_lvl = gear_type.idx_lvl_map[this_gl_idx]
            s_g.set_enhance_lvl(start_g_lvl)

            fs_gain = s_g.fs_gain()
            max_gs_lvl = ceil(fs_left / fs_gain)

            if this_gl_idx >= max_idx:
                this_num = max_gs_lvl
            else:
                this_num = randint(1, max_gs_lvl)

            actual_fs_gain = this_num * fs_gain
            secondary_map[this_gl_idx-start_g_lvl_idx] = this_num
            this_pos += actual_fs_gain
            this_gl_idx += 1

    def has_ran(self):
        return not self.needs_update

    def evaluate_stats(self):
        num_fs = self.num_fs
        secondary_gear = self.secondary_gear
        starting_pos = self.starting_pos
        gear_type = secondary_gear.gear_type
        s_g_bt = secondary_gear.get_backtrack_start()
        start_g_lvl_idx = s_g_bt - 1

        gearz = []
        fs_gain_l = []
        probs_list = []
        num_attempt_l = []
        prob_all_fails = []
        num_sweeps_before_success = []

        max_len_sm = len(gear_type.map) - start_g_lvl_idx
        num_attempts_maps = []
        # rolls the secondary map to the right
        offset = len(self.secondary_map) - max_len_sm
        self.secondary_map = list(self.secondary_map[offset:])
        fs_lvl = starting_pos
        for lvl_off, num_bmp in enumerate(self.secondary_map):
            s_g = secondary_gear.duplicate()
            gearz.append(s_g)
            idx = start_g_lvl_idx + lvl_off
            s_g.set_enhance_lvl(s_g.gear_type.idx_lvl_map[idx])
            fs_gain = s_g.fs_gain()
            fs_gain_l.append(fs_gain)
            end_fsl = fs_lvl+(num_bmp*fs_gain)
            if end_fsl > num_fs:
                end_fsl = num_fs
            probs = numpy.array(s_g.lvl_success_rate[fs_lvl:end_fsl:fs_gain])
            num_attempts_maps.append(gear_type.p_num_atmpt_map[idx][fs_lvl])
            #expected_num_succ.append(numpy.sum(probs))
            #prob_all_succ.append(numpy.prod(probs))
            #attempt_before_suc_l.append(get_num_attempts_before_success(probs))
            p_all_fs = numpy.prod(1-probs)
            prob_all_fails.append(p_all_fs)
            p_at_least_one_success = 1 - p_all_fs
            num_sweeps_before_success.append(1/p_at_least_one_success)
            num_attempt_l.append(get_num_level_attempts(1 - probs))
            probs_list.append(probs)
            if end_fsl == num_fs:
                self.secondary_map[lvl_off] = max(0, ceil((num_fs-fs_lvl) / fs_gain))
                break
            fs_lvl = end_fsl
        self.secondary_map = numpy.array(self.secondary_map)
        prob_all_fails = numpy.array(prob_all_fails)
        self.num_levels = len(probs_list)
        self.num_attempts = numpy.array(num_attempt_l)
        self.num_attempts_b4_suc = numpy.array(num_attempts_maps)
        self.gearz = gearz
        self.fs_gain = fs_gain_l
        self.probs_list = probs_list
        self.prob_all_fails = prob_all_fails
        self.expected_num_succ = (1/prob_all_fails) - 1
        self.num_sweeps_succ = num_sweeps_before_success
        self.num_fails_total = self.num_attempts - self.expected_num_succ

    def evaluate_map(self, varbose=False):
        if self.starting_pos is None:
            raise Exception()
        if self.has_ran():
            raise Exception('Can not evaluate map twice without resetting primary data')
        starting_pos = self.starting_pos
        settings = self.settings
        num_fs = self.num_fs + 1
        s_g = self.secondary_gear


        gear_type = s_g.gear_type
        self.num_attempts = []
        self.num_attempts_b4_suc = []
        self.avg_cost = []

        self.evaluate_stats()
        secondary_map = self.secondary_map
        num_success_total = self.expected_num_succ
        attempt_before_suc_l = self.num_attempts_b4_suc
        num_levels = self.num_levels
        num_attempt_l = self.num_attempts
        gearz = self.gearz
        fs_gain_l = self.fs_gain
        prob_all_fails = self.prob_all_fails

        sim = WeakFslSimulator(self)
        sim.evaluate_reserves()
        reserves = sim.reserves
        from_below = numpy.roll(num_success_total, 1)
        from_below[0] = 0
        balance = (numpy.array(reserves[:num_levels]) + from_below + (from_below * num_success_total))
        m_succ = numpy.copy(attempt_before_suc_l)
        m_succ[-1] = 0
        balance -= numpy.amax([m_succ, num_attempt_l], axis=0)

        reserves[-1] = 0
        sim.pri_draft = 1
        sim.evaluate_reserves()

        pens = reserves[-1]
        pri_cost = self.get_pri_cost()
        pen_cost = self.get_pen_cost()
        pen_gains = pen_cost * pens
        pri_cost = sim.pri_draft * pri_cost
        pripen_cost = pri_cost - pen_gains

        fs_cum_cost = self.fs_cum_cost
        fs_cost = self.fs_cost
        gear_list = self.gear_list

        prev_cost_per_succ = 0
        prev_cost_per_succ_just_f = 0
        fs_lvl = starting_pos

        for lvl_off, num_bmp in enumerate(self.secondary_map):
            s_g = gearz[lvl_off]
            fs_gain = fs_gain_l[lvl_off]
            start_fs_lvl = fs_lvl
            cum_attempts = 0
            this_p_all_fails = 1
            cum_success_p = 0
            this_p_all_fails = 1

            for i in range(0, num_bmp):
                suc_rate = s_g.lvl_success_rate[fs_lvl]

                this_cum_cost = fs_cum_cost[fs_lvl - 1]
                fail_rate = 1 - suc_rate
                this_cost = s_g.simulate_FS(fs_lvl, this_cum_cost) * fail_rate

                num_attempts = 1 / fail_rate

                succ_times = num_attempts - 1
                cum_attempts += num_attempts
                this_p_all_fails *= succ_times
                cum_success_p += suc_rate
                this_p_all_fails *= fail_rate

                if balance[lvl_off] < 0 and lvl_off > 0:
                    p_at_least_one_success = 1 - prob_all_fails[lvl_off - 1]
                    odds_free = loop_sum(p_at_least_one_success, (i+1) * (1-this_p_all_fails))  # since stack resets on success, can just multiply with itself n times
                    #odds_free = p_or(odds_free, odds_free * (1-this_p_all_fails))
                    #odds_free = exp_integral(i + 1, i + 20, p_at_least_one_success)
                    #odds_free = loop_sum(p_at_least_one_success, i+1)
                    if lvl_off < len(secondary_map) - 1 and False:
                        # * (1-this_p_all_fails)
                        odds_free = max(odds_free, loop_sum(p_at_least_one_success, i+2) * (1-this_p_all_fails))
                    this_cost += (1 - odds_free) * prev_cost_per_succ
                    this_cost *= num_attempts
                    if i > 0:
                        this_cost -= (1 - odds_free) * (prev_cost_per_succ - prev_cost_per_succ_just_f)
                else:
                    this_cost *= num_attempts
                cost_f = this_cost / fs_gain
                for j in range(0, fs_gain):
                    offset = fs_lvl + j
                    if offset >= num_fs-1:
                        if offset == num_fs-1:
                            gear_list[offset] = s_g
                            fs_cost[offset] = cost_f
                            fs_cum_cost[offset] = self.fs_cum_cost[offset - 1] + cost_f
                        self.factor_pripen(pripen_cost, num_fs - starting_pos)
                        self.needs_update = False
                        return
                    gear_list[offset] = s_g
                    fs_cost[offset] = cost_f
                    fs_cum_cost[offset] = self.fs_cum_cost[offset-1] + cost_f

                fs_lvl += fs_gain

            accum_chance = 0
            t_fs_lvl = start_fs_lvl
            cum_cost = self.fs_cum_cost[t_fs_lvl - 1]
            i = 0
            count_chance_discard = 0
            count_cost_discard = cum_cost
            count_cost_discard_just_f = cum_cost
            count_cost_overstack_just_f = cum_cost
            this_p_all_fails = 1
            looking_for_suc = True
            while looking_for_suc:
                suc_rate = s_g.lvl_success_rate[t_fs_lvl]
                fail_rate = 1 - suc_rate
                # succeeding pays no cost - count material costs
                this_cost = s_g.simulate_FS(t_fs_lvl, 0) * fail_rate
                this_cost_just_f = this_cost
                this_p_all_fails *= fail_rate

                if balance[lvl_off] < 0 < lvl_off:
                    p_at_least_one_success = 1 - prob_all_fails[lvl_off - 1]
                    odds_free = loop_sum(p_at_least_one_success, i + 1)
                    if i > 0:
                        this_cost += (1 - odds_free) * prev_cost_per_succ_just_f
                        this_cost_just_f += (1 - loop_sum(p_at_least_one_success, i)) * prev_cost_per_succ_just_f
                    else:
                        this_cost += (1 - odds_free) * prev_cost_per_succ

                cum_cost += this_cost
                count_cost_overstack_just_f += this_cost_just_f
                t_fs_lvl += fs_gain

                if i < num_bmp:
                    count_chance_discard += suc_rate
                    count_cost_discard += this_cost
                    count_cost_discard_just_f += this_cost_just_f
                accum_chance += suc_rate
                i += 1
                looking_for_suc = accum_chance < 1

            prev_cost_p_suc_taptap = cum_cost
            prev_cost_per_succ = prev_cost_p_suc_taptap
            prev_cost_per_succ_just_f = count_cost_overstack_just_f
            self.avg_cost.append(prev_cost_per_succ)
        self.factor_pripen(pripen_cost, num_fs - starting_pos)
        self.needs_update = False

    def get_pri_cost(self):
        settings = self.settings
        itms:ItemStore = settings[settings.P_ITEM_STORE]
        sg:Gear = self.secondary_gear
        pc = sg.pri_cost
        gt = sg.gear_type
        try:
            pri_dx = gt.bin_mp(gt.bt_start-1)
            str_item_id = itms.check_out_item(sg)
            prices = itms[str_item_id]
            return min(pc, prices[pri_dx])
        except (KeyError, ItemStoreException, TypeError):
            return pc

    def get_pen_cost(self):
        settings = self.settings
        itms:ItemStore = settings[settings.P_ITEM_STORE]
        sg:Gear = self.secondary_gear
        gt = sg.gear_type
        try:
            pen_dx = gt.bin_mp(len(gt.map)-1)
            str_item_id = itms.check_out_item(sg)
            prices = itms[str_item_id]
            return prices[pen_dx]
        except (KeyError, ItemStoreException, TypeError):
            return 0

    def factor_pripen(self, cost, depth):
        settings = self.settings
        num_fs = self.num_fs
        aum = numpy.sum(self.fs_cum_cost[num_fs-depth:num_fs])
        for i in range(0, depth):
            this_cost = self.fs_cum_cost[num_fs-i]
            rat = this_cost / aum
            self.fs_cum_cost[num_fs-i] += cost * rat

    def get_cost(self, stack_n):
        pass

    def get_item(self, stank_n):
        pass

    def get_state_json_ext(self):
        return {
            'base_gear': self.gear_list[0].get_state_json(),
            'secondary': self.secondary_gear.get_state_json(),
            'starting_pos': self.starting_pos,
            'gear_list': [x.enhance_lvl for x in self.gear_list],
            'fs_cost': [x for x in self.fs_cost],
            'secondary_map': self.secondary_map
        }

    def get_state_json(self):
        return {
            'genome': self.get_gnome(),
            'gear_id': id(self.secondary_gear),
            'num_fs': self.num_fs
        }

    def set_state_json(self, state):
        settings = self.settings
        genome = state.pop('genome')
        gear_id = state.pop('gear_id')
        num_fs = state.pop('num_fs')
        gear_reg = settings.gear_reg
        if gear_id in gear_reg:
            sec_gear = gear_reg[gear_id]
        else:
            sec_gear = None
        self.set_gnome(genome)
        self.secondary_gear = sec_gear
        self.num_fs = num_fs

    def get_gnome(self):
        return (self.starting_pos, *map(int, self.secondary_map[:-1]))

    def set_gnome(self, gnome):
        self.starting_pos = gnome[0]
        self.secondary_map = (*gnome[1:], 100000)
        self.needs_update = True

    def validate(self):
        #if self.fs_cost is None or self.gear_list is None or self.fs_cum_cost is None:
        #    return False
        if self.starting_pos is None:
            return False
        if not isinstance(self.secondary_gear, Gear):
            return False

        #s_g = self.secondary_gear
        #s_g_bt = s_g.get_backtrack_start()
        #gear_type = s_g.gear_type
        #len_map = len(gear_type.map)
        #start_g_lvl_idx = s_g_bt - 1
        #secondary_map_len = len_map - start_g_lvl_idx
        #return len(self.secondary_map) >= secondary_map_len-1

        return len(self.secondary_map) > 1


class WeakFslSimulator(object):
    def __init__(self, fsl: FailStackList):
        self.fsl:FailStackList = fsl
        self.pri_draft = 1
        self.reserves = [0] * (len(fsl.secondary_map) + 1)  # Must stay len(secondary_map) for pen/pri cost to work

    def evaluate_reserves(self):
        final_g_lvl_idx = self.fsl.num_levels - 1
        self.stack_thru_gear(1, final_g_lvl_idx)

    def stack_thru_gear(self, M, gear_idx):
        reserves = self.reserves
        fsl = self.fsl
        num_success_total = fsl.expected_num_succ
        num_fails_total = fsl.num_fails_total
        if gear_idx == 0:
            self.get_gear(num_success_total[0] * M, 0)  # Only successes change the reserves
        else:
            prev_gear_idx = gear_idx - 1
            next_gear = gear_idx + 1
            self.stack_thru_gear(M, prev_gear_idx)
            num_success = num_success_total[gear_idx] * M
            num_fails = num_fails_total[gear_idx] * M
            num_attempts = num_success + num_fails

            reserves[prev_gear_idx] += num_fails
            reserves[next_gear] += num_success

            self.stack_thru_gear(num_success, prev_gear_idx)
            void_attempt = num_attempts - reserves[gear_idx]
            if void_attempt > 0:
                self.get_gear(void_attempt, gear_idx)
                # reserves[gear_idx] = 0
            reserves[gear_idx] -= num_attempts

    def get_gear(self, M, gear_idx):
        reserves = self.reserves
        num_attempts_maps = self.fsl.num_attempts_b4_suc
        if gear_idx == 0:
            void_attempt = M - reserves[0]
            if void_attempt >= 0:
                self.pri_draft += void_attempt + 1
                reserves[0] = 1
            else:
                reserves[0] -= M
            reserves[1] += M
        else:
            prev_gear = gear_idx - 1
            if prev_gear <= 0:
                self.get_gear(M, 0)
                return

            atmpts_before_succ = num_attempts_maps[prev_gear] * M  # This is neither overstack nor discard (fix this)
            reserves[prev_gear - 1] += atmpts_before_succ - M
            # num_discard_stacks = num_sweeps_before_success[prev_gear]
            # stack_thru_gear(num_discard_stacks*M, prev_gear-1)
            self.stack_thru_gear(M, prev_gear - 1)  # Get the stacks
            void_attempt = atmpts_before_succ - reserves[prev_gear]

            if void_attempt > 0:  # Get the missing gear( if any )
                self.get_gear(void_attempt, prev_gear)
            reserves[prev_gear] -= atmpts_before_succ
            reserves[gear_idx] += M

