#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import numpy, json
from .common import binom_cdf_X_gte_x, Gear, Classic_Gear, Smashable, gear_types, EnhanceSettings, ItemStore, generate_gear_obj, approximate_succ_num

from .utilities import fmt_traceback, UniqueList

from . import common
from .old_settings import converters
import shutil
from random import randint, random, choice
from math import ceil, floor
from typing import List, Dict
from poisson_binomial import PoissonBinomial
from multiprocessing import Process, Value
from multiprocessing import Lock as MLock
from multiprocessing import Queue as MQueue
from multiprocessing import Pipe as MPipe
from multiprocessing.connection import Connection as MConnection
from queue import Queue, Empty



class Invalid_FS_Parameters(Exception):
    pass


def genload_gear(gear_state, settings):
    gtype = gear_types[gear_state['gear_type']]
    gear = generate_gear_obj(settings, gear_type=gtype)
    gear.set_state_json(gear_state)
    return gear


class EvolveSettings(object):
    def __init__(self):
        self.num_procs = 4
        self.pop_size = 300
        self.num_elites = 120
        self.brood_size = 200
        self.ultra_elite = 0.2
        self.mutation_rate = 0.4
        self.extinction_epoch = 2000
        self.trait_dom = 0.2
        self.max_mutation = 10
        self.penalize_supremacy = True
        self.oppressive_mode = False
        self.fitness_function = 'avg'


class SettingsException(Exception):
    def __init__(self, msg, embedded):
        super(SettingsException, self).__init__(msg)
        self.embedded:Exception = embedded

    def __str__(self):
        this_str = super(SettingsException, self).__str__()
        tb = self.embedded.__traceback__
        if tb is not None:
            this_str += '\r\n' + fmt_traceback(tb)
        return this_str


class EnhanceModelSettings(common.EnhanceSettings):
    P_FAIL_STACKERS = 'fail_stackers'
    P_FAIL_STACKER_SECONDARY = 'fail_stackers_2'
    P_ENH_FOR_PROFIT = 'for_profit_gear'
    P_ENHANCE_ME = 'enhance_me'
    P_FS_EXCEPTIONS = 'fs_exceptions'
    P_R_FAIL_STACKERS = 'r_fail_stackers'
    P_R_ENHANCE_ME = 'r_enhance_me'
    P_R_STACKER_SECONDARY = 'r_fail_stackers_2'
    P_R_FOR_PROFIT = 'r_for_profit_gear'
    P_FAIL_STACKERS_COUNT = 'fail_stackers_count'
    P_ALTS = 'alts'
    P_VALKS = 'valks'
    P_NADERR_BAND = 'naderrs_band'
    P_QUEST_FS_INC = 'quest_fs_inc'
    P_GENOME_FS = 'fs_genome'
    P_VERSION = '_version'


    def init_settings(self, sets=None):
        fsl = FailStackList(self, None, None, None, None)
        fsl.set_gnome((0, 22, 2, 4, 8))
        super(EnhanceModelSettings, self).init_settings({
            self.P_FAIL_STACKERS: [],  # Target fail stacking gear object list
            self.P_FAIL_STACKER_SECONDARY: [],
            self.P_ENH_FOR_PROFIT: [],
            self.P_ENHANCE_ME: [],  # Target enhance gear object list
            self.P_FS_EXCEPTIONS: {},  # Dictionary of fs indexes that have a custom override {int: Gear}
            self.P_R_FAIL_STACKERS: [],  # Target fail stacking gear objects that are removed from processing
            self.P_R_ENHANCE_ME: [],  # Target enhance gear objects that are removed from processing
            self.P_R_STACKER_SECONDARY: [],
            self.P_R_FOR_PROFIT: [],
            self.P_FAIL_STACKERS_COUNT: {},  # Number of fail stacking items available for a gear object
            self.P_ALTS: [],  # Information for each alt character
            self.P_VALKS: {},  # Valks saved failstacks
            self.P_NADERR_BAND: [],
            self.P_GENOME_FS: fsl,
            self.P_QUEST_FS_INC: 0,  # Free FS increase from quests
            #self.P_COST_FUNC: 'Thorough (Slow)',
            self.P_VERSION: Enhance_model.VERSION
        })

    def get_state_json(self):
        super_state = {}
        super_state.update(super(EnhanceModelSettings, self).get_state_json())
        fail_stackers = self[self.P_FAIL_STACKERS]
        fs_secondary = self[self.P_FAIL_STACKER_SECONDARY]
        fsl:FailStackList = self[self.P_GENOME_FS]
        secondary_gear = fsl.secondary_gear
        fsl_sec_gidx = 0
        try:
            fsl_sec_gidx = fs_secondary.index(secondary_gear)
        except ValueError:
            pass

        super_state.update({
            self.P_FAIL_STACKERS: [g.get_state_json() for g in fail_stackers],
            self.P_FAIL_STACKER_SECONDARY: [g.get_state_json() for g in fs_secondary],
            self.P_ENH_FOR_PROFIT: [g.get_state_json() for g in self[self.P_ENH_FOR_PROFIT]],
            self.P_ENHANCE_ME: [g.get_state_json() for g in self[self.P_ENHANCE_ME]],
            self.P_FS_EXCEPTIONS: {k:fail_stackers.index(v) for k,v in self[self.P_FS_EXCEPTIONS].items()},
            self.P_R_FAIL_STACKERS: [g.get_state_json() for g in self[self.P_R_FAIL_STACKERS]],
            self.P_R_FOR_PROFIT: [g.get_state_json() for g in self[self.P_R_FOR_PROFIT]],
            self.P_R_STACKER_SECONDARY: [g.get_state_json() for g in self[self.P_R_STACKER_SECONDARY]],
            self.P_R_ENHANCE_ME: [g.get_state_json() for g in self[self.P_R_ENHANCE_ME]],
            self.P_FAIL_STACKERS_COUNT: {fail_stackers.index(k):v for k,v in self[self.P_FAIL_STACKERS_COUNT].items()},
            self.P_GENOME_FS: (fsl_sec_gidx, *fsl.get_gnome()),
            self.P_ALTS: self[self.P_ALTS],
            self.P_VALKS: self[self.P_VALKS],
            self.P_QUEST_FS_INC: self[self.P_QUEST_FS_INC],
            self.P_VERSION: Enhance_model.VERSION
        })
        return super_state

    def set_state_json(self, state):
        P_VERSION = state.pop(self.P_VERSION)
        if P_VERSION not in self.versions():
            try:
                if self.f_path is not None:
                    fp = self.f_path + "_backup"+P_VERSION
                    shutil.copyfile(self.f_path, fp)
                converter = converters[P_VERSION]
                state = converter(state)
            except KeyError:
                raise IOError('Settings file version is not understood.')
        P_FAIL_STACKERS = state.pop(self.P_FAIL_STACKERS)
        P_FAIL_STACKERS = UniqueList(iterable=[genload_gear(g, self) for g in P_FAIL_STACKERS])
        P_FAIL_STACKER_SECONDARY = state.pop(self.P_FAIL_STACKER_SECONDARY)
        P_FAIL_STACKER_SECONDARY = UniqueList(iterable=[genload_gear(g, self) for g in P_FAIL_STACKER_SECONDARY])

        P_ENH_FOR_PROFIT = state.pop(self.P_ENH_FOR_PROFIT)
        P_ENH_FOR_PROFIT = UniqueList(iterable=[genload_gear(g, self) for g in P_ENH_FOR_PROFIT])

        P_R_STACKER_SECONDARY = state.pop(self.P_R_STACKER_SECONDARY)
        P_R_STACKER_SECONDARY = UniqueList(iterable=[genload_gear(g, self) for g in P_R_STACKER_SECONDARY])

        P_R_FOR_PROFIT = state.pop(self.P_R_FOR_PROFIT)
        P_R_FOR_PROFIT = UniqueList(iterable=[genload_gear(g, self) for g in P_R_FOR_PROFIT])

        P_ENHANCE_ME = state.pop(self.P_ENHANCE_ME)
        P_ENHANCE_ME = UniqueList(iterable=[genload_gear(g, self) for g in P_ENHANCE_ME])
        P_R_FAIL_STACKERS = state.pop(self.P_R_FAIL_STACKERS)
        P_R_FAIL_STACKERS = UniqueList(iterable=[genload_gear(g, self) for g in P_R_FAIL_STACKERS])
        P_R_ENHANCE_ME = state.pop(self.P_R_ENHANCE_ME)
        P_R_ENHANCE_ME = UniqueList(iterable=[genload_gear(g, self) for g in P_R_ENHANCE_ME])

        P_GENOME_FS = state.pop(self.P_GENOME_FS)
        fsl_sec_gidx = P_GENOME_FS[0]
        genome = P_GENOME_FS[1:]
        fsl_sec_gear = None
        try:
            fsl_sec_gear = P_FAIL_STACKER_SECONDARY[fsl_sec_gidx]
        except IndexError:
            pass
        fsl = FailStackList(self, fsl_sec_gear, None, None, None)
        fsl.set_gnome(genome)

        #for i in P_ENHANCE_ME:
        #    print "{} is a ({}) {}".format(i.name, i.gear_type.name, type(i))

        P_FS_EXCEPTIONS = state.pop(self.P_FS_EXCEPTIONS)
        P_FAIL_STACKERS_COUNT = state.pop(self.P_FAIL_STACKERS_COUNT)
        valks = state.pop(self.P_VALKS)
        new_valks = {int(k): v for k,v in valks.items()}
        state[self.P_VALKS] = new_valks
        super(EnhanceModelSettings, self).set_state_json(state)  # load settings base settings first
        update_r = {
            self.P_FAIL_STACKERS: P_FAIL_STACKERS,
            self.P_FAIL_STACKER_SECONDARY: P_FAIL_STACKER_SECONDARY,
            self.P_ENH_FOR_PROFIT: P_ENH_FOR_PROFIT,
            self.P_ENHANCE_ME: P_ENHANCE_ME,
            self.P_R_FAIL_STACKERS: P_R_FAIL_STACKERS,
            self.P_R_STACKER_SECONDARY: P_R_STACKER_SECONDARY,
            self.P_R_FOR_PROFIT: P_R_FOR_PROFIT,
            self.P_R_ENHANCE_ME: P_R_ENHANCE_ME,
            self.P_GENOME_FS: fsl,
            self.P_FS_EXCEPTIONS: {int(k):P_FAIL_STACKERS[int(v)] for k,v in P_FS_EXCEPTIONS.items()},
            self.P_FAIL_STACKERS_COUNT: {P_FAIL_STACKERS[int(k)]:int(v) for k,v in P_FAIL_STACKERS_COUNT.items()}
        }
        self.update(update_r)

    def __getstate__(self):
        return self.get_state_json()

    def __setstate__(self, state):
        self.set_state_json(state)

    def versions(self):
        return [
            Enhance_model.VERSION
        ]


class FailStackList(object):
    REMAKE_DISCARD_STACK = 'discard'
    REMAKE_OVERSTACK = 'overstack'

    def __init__(self, settings, secondary:Gear, optimal_primary_list: List[Gear], optimal_cost, cum_cost):
        self.settings:EnhanceModelSettings = settings
        self.gear_list = None
        self.fs_cost = None
        self.fs_cum_cost = None

        self.fl_safety = True
        self.fl_cost = True
        self.fl_cum_cost = True

        #self.invalidated = True
        self.set_gear_list(optimal_primary_list)
        self.set_fs_cost(optimal_cost)
        self.set_fs_cum_cost(cum_cost)

        self.starting_pos = None
        self.secondary_gear:Gear = secondary
        self.secondary_map = []
        self.hopeful_nums = []
        self.remake_strat = []
        self.avg_cost = []

    def set_primary_data(self, optimal_primary_list: List[Gear], optimal_cost, cum_cost):
        self.set_gear_list(optimal_primary_list)
        self.set_fs_cost(optimal_cost)
        self.set_fs_cum_cost(cum_cost)

    def set_gear_list(self, optimal_primary_list: List[Gear]):
        if optimal_primary_list is not None:
            self.fl_safety = True
            self.gear_list = optimal_primary_list.copy()

    def set_fs_cost(self, optimal_cost):
        if optimal_cost is not None:
            self.fl_cost = True
            self.fs_cost = numpy.copy(optimal_cost)

    def set_fs_cum_cost(self, cum_cost):
        if cum_cost is not None:
            self.fl_cum_cost = True
            self.fs_cum_cost = numpy.copy(cum_cost)

    def generate_secondary_map(self, starting_pos):
        settings = self.settings
        num_fs = settings[settings.P_NUM_FS] + 1
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
        return not (self.fl_cost and self.fl_cum_cost and self.fl_safety)

    def evaluate_map(self):
        if self.starting_pos is None:
            raise Exception()
        if self.has_ran():
            raise Exception('Can not evaluate map twice without resetting primary data')
        self.fl_cost = False
        self.fl_cum_cost = False
        self.fl_safety = False
        starting_pos = self.starting_pos
        settings = self.settings
        num_fs = settings[settings.P_NUM_FS] + 1
        s_g = self.secondary_gear

        s_g_bt = s_g.get_backtrack_start()
        start_g_lvl_idx = s_g_bt - 1
        self.hopeful_nums = []
        self.avg_cost = []
        self.remake_strat = []

        self.secondary_map = list(self.secondary_map)

        fs_lvl = starting_pos
        gearz = []
        fs_gain_l = []
        probs_list = []
        empty_probs = []
        num_attempt_l = []
        prob_all_succ = []
        prob_all_fails = []
        attempt_num = 0
        for lvl_off, num_bmp in enumerate(self.secondary_map):
            s_g = s_g.duplicate()
            gearz.append(s_g)
            s_g.set_enhance_lvl(s_g.gear_type.idx_lvl_map[start_g_lvl_idx + lvl_off])
            fs_gain = s_g.fs_gain()
            fs_gain_l.append(fs_gain)
            end_fsl = fs_lvl+(num_bmp*fs_gain)
            if end_fsl > num_fs:
                end_fsl = num_fs
                self.secondary_map[lvl_off] = max(0, ceil((num_fs-fs_lvl) / fs_gain))
            #print('{} {} {}'.format(fs_lvl, end_fsl, fs_gain))

            probs = numpy.array(s_g.lvl_success_rate[fs_lvl:end_fsl:fs_gain])
            prob_all_succ.append(numpy.prod(probs))
            prob_all_fails.append(numpy.prod(1-probs))
            attempt_num = numpy.sum(1/(1-probs))
            num_attempt_l.append(attempt_num)
            probs_list.append(probs)
            fs_lvl = end_fsl
        secondary_map = numpy.array(self.secondary_map)
        prob_all_succ = numpy.array(prob_all_succ)
        prob_all_fails = numpy.array(prob_all_fails)
        num_attempt_l = numpy.array(num_attempt_l)
        num_success_total = num_attempt_l - secondary_map
        return_rate = secondary_map / num_attempt_l

        from_below = numpy.roll(num_success_total, 1)
        from_below[0] = 0

        positive_pressure = numpy.zeros(len(num_attempt_l))
        negative_pressure = numpy.zeros(len(num_attempt_l))
        #positive_pressure += from_below
        #positive_pressure[:-1] += num_success_total[:-1] / return_rate[1:]  # pressure from above

        negative_pressure[1:] += num_attempt_l[1:]
        balance = numpy.copy(from_below)
        #balance[:-1] = numpy.array([max(1,x) for x in balance[:-1]])   # at least one fail from above
        balance[1:] -= (num_attempt_l[1:])

        fs_cum_cost = self.fs_cum_cost
        fs_cost = self.fs_cost
        gear_list = self.gear_list

        reserve = 0
        #reserve_accum = 0
        #reserve_buff = 0
        prev_cost_per_succ = 0
        prev_cost_per_succ_just_f = 0
        fs_lvl = starting_pos
        waste_fails = 0

        cost_p_succ_l = []
        prev_free_odds = 1

        # the first prev_cost_per_succ is missing the failstack price

        for lvl_off, num_bmp in enumerate(self.secondary_map):
            s_g = gearz[lvl_off]
            fs_gain = fs_gain_l[lvl_off]
            #build_fs_cost = fs_cum_cost[fs_lvl - 1]  # Rebuilding the stack is baked in
            prev_waste_fails = waste_fails
            waste_fails = 1.0
            #accum_succ = 0
            #avg_cost_acum = 0
            start_fs_lvl = fs_lvl
            start_reserve = reserve
            dg_reserve_chance = 1
            if lvl_off < len(self.secondary_map) - 1:
                probs = probs_list[lvl_off+1]
                #reserve += numpy.sum(1-probs)
                dg_reserve_chance = numpy.prod(probs)
            #relief_suc_accum = 0
            cum_attempts = 0
            cum_success = 1
            probs = 0
            p_no_success = 1

            prob_rets = {}
            probs_l = []
            if lvl_off > 0:
                probs_l.extend(probs_list[lvl_off - 1])
            #if lvl_off < len(secondary_map) - 1:
            #    probs_l.extend(probs_list[lvl_off + 1])
            if len(probs_l) > 0:
                pb = PoissonBinomial(probs_l)  # x_or_more
                prob_rets[lvl_off] = pb
            final_idx = len(secondary_map) - 1
            orginal_last_prob_list = probs_list[final_idx-1]
            invert_last_prob_list = 1 - orginal_last_prob_list
            psb = [x for x in orginal_last_prob_list]
            # This just increases the granualrity. The real odds of success (in terms of items produced) compounds
            psb.extend(orginal_last_prob_list)
            #psb.extend(numpy.power(orginal_last_prob_list, 2))
            #psb.extend(numpy.power(orginal_last_prob_list, 3))
            #psb.extend(numpy.power(orginal_last_prob_list, 4))
            #psb.extend(numpy.power(orginal_last_prob_list, 5))
            #psb.extend(numpy.power(orginal_last_prob_list, 6))
            final_pb = PoissonBinomial(psb)

            for i in range(0, num_bmp):
                suc_rate = s_g.lvl_success_rate[fs_lvl]


                this_cum_cost = fs_cum_cost[fs_lvl - 1]
                fail_rate = 1 - suc_rate
                this_cost = s_g.simulate_FS(fs_lvl, this_cum_cost) * fail_rate

                waste_fails *= fail_rate

                num_attempts =  1 / fail_rate
                p_no_success *= fail_rate**num_attempts

                succ_times = num_attempts - 1
                cum_attempts += num_attempts
                cum_success *= succ_times

                if balance[lvl_off] < 0 and lvl_off > 0:
                    p_all_fails = prob_all_fails[lvl_off - 1]
                    odds_free = (1-p_all_fails)**(i+1)
                    this_cost += (1 - odds_free) * prev_free_odds * prev_cost_per_succ
                    this_cost *= num_attempts
                    this_cost -= (1 - odds_free) * (1-prev_free_odds) * (prev_cost_per_succ - self.avg_cost[lvl_off - 1])
                    prev_free_odds = prev_free_odds * fail_rate
                    #if i > 0:
                    #    this_cost -= (1 - odds_free) * (prev_cost_per_succ - self.avg_cost[lvl_off-1])
                else:
                    this_cost *= num_attempts


                reserve -= num_attempts
                cost_f = this_cost / fs_gain


                reserve += succ_times * reserve  # Don't add back the reserve it takes to get here
                #reserve_accum += succ_times + (succ_times * reserve_accum) # Succeeding makes you go through all previous attempts also
                for j in range(0, fs_gain):
                    offset = fs_lvl + j
                    if offset >= num_fs:
                        return
                    gear_list[offset] = s_g
                    fs_cost[offset] = cost_f
                    fs_cum_cost[offset] = self.fs_cum_cost[offset-1] + cost_f

                fs_lvl += fs_gain

            reserve = (1 / waste_fails) - 1


            self.hopeful_nums.append(reserve)

            accum_chance = 0
            t_fs_lvl = start_fs_lvl
            this_reserve = start_reserve
            cum_cost = self.fs_cum_cost[t_fs_lvl - 1]
            counter = 0
            count_chance_discard = 0
            count_cost_discard = cum_cost

            count_chance_discard_just_f = 0
            count_cost_discard_just_f = cum_cost
            #cum_attempts = 0
            #cum_success = 1
            #num_attempts = 0
            prev_free_odds = 1
            probs = 0
            while accum_chance < 1:
                suc_rate = s_g.lvl_success_rate[t_fs_lvl]
                fail_rate = 1 - suc_rate
                # succeeding pays no cost - count material costs
                this_cost = s_g.simulate_FS(t_fs_lvl, 0) * fail_rate

                odds_free = (1 - prob_all_fails[lvl_off - 1]) ** (counter+1)
                if counter > 0:
                    if lvl_off > 0:
                        this_cost += (prev_cost_per_succ-self.avg_cost[lvl_off-1])
                else:
                    this_cost += prev_cost_per_succ
                #prev_free_odds = prev_free_odds * fail_rate

                #if counter <= 0 and lvl_off > 0:
                #    this_cost -= (1-odds_free) * self.avg_cost[-1]

                cum_cost += this_cost
                this_reserve -= 1
                t_fs_lvl += fs_gain

                if counter < num_bmp:
                    count_chance_discard += suc_rate
                    count_cost_discard += this_cost
                accum_chance += suc_rate
                counter += 1

            prev_cost_p_suc_taptap = cum_cost
            prev_cost_p_suc_discard = count_cost_discard / count_chance_discard

            #if prev_cost_p_suc_taptap < prev_cost_p_suc_discard:
            if False:
                prev_cost_per_succ = prev_cost_p_suc_taptap
                self.remake_strat.append(self.REMAKE_OVERSTACK)
            else:
                #print('LVL {}: {}'.format(lvl_off, prev_cost_p_suc_discard))
                prev_cost_per_succ = prev_cost_p_suc_discard
                prev_cost_per_succ_just_f = count_chance_discard_just_f
                cost_p_succ_l.append(prev_cost_per_succ)
                self.remake_strat.append(self.REMAKE_DISCARD_STACK)
            self.avg_cost.append(prev_cost_per_succ)

            reserve_accum = 0

    def get_cost(self, stack_n):
        pass

    def get_item(self, stank_n):
        pass

    def get_state_json(self):
        return {
            'base_gear': self.gear_list[0].get_state_json(),
            'secondary': self.secondary_gear.get_state_json(),
            'starting_pos': self.starting_pos,
            'gear_list': [x.enhance_lvl for x in self.gear_list],
            'fs_cost': [x for x in self.fs_cost],
            'secondary_map': self.secondary_map,
            'hopeful_nums': self.hopeful_nums,
            'remake_strat': self.remake_strat
        }

    def get_gnome(self):
        return (self.starting_pos, *self.secondary_map[:-1])

    def set_gnome(self, gnome):
        self.starting_pos = gnome[0]
        self.secondary_map = (*gnome[1:], 100000)

    def validate(self):
        #if self.fs_cost is None or self.gear_list is None or self.fs_cum_cost is None:
        #    return False
        if self.starting_pos is None:
            return False
        if not isinstance(self.secondary_gear, Gear):
            return False
        s_g = self.secondary_gear
        s_g_bt = s_g.get_backtrack_start()
        gear_type = s_g.gear_type
        len_map = len(gear_type.map)
        start_g_lvl_idx = s_g_bt - 1
        secondary_map_len = len_map - start_g_lvl_idx
        return len(self.secondary_map) >= secondary_map_len-1


def evolve_p_s(settings:EnhanceModelSettings, optimal_cost, cum_cost, ev_set:EvolveSettings, secondaries=None):
    cons = []
    returnq = MQueue()
    new_set = EnhanceModelSettings()
    new_set.set_state_json(settings.get_state_json())
    if secondaries is not None:
        new_set[new_set.P_FAIL_STACKER_SECONDARY] = secondaries

    new_set[settings.P_R_FAIL_STACKERS] = []
    new_set[settings.P_FAIL_STACKERS] = []
    new_set[settings.P_R_STACKER_SECONDARY] = []
    new_set[settings.P_ENHANCE_ME] = []
    new_set[settings.P_R_ENHANCE_ME] = []
    new_set[settings.P_R_FOR_PROFIT] = []
    new_set[settings.P_R_FOR_PROFIT] = []
    new_set[settings.P_ALTS] = []
    new_set[settings.P_NADERR_BAND] = []
    new_set[settings.P_VALKS] = {}

    new_primaries = [None]*len(optimal_cost)
    num_proc = ev_set.num_procs
    for i in range(num_proc):
        cons.append(MPipe(False))
    procs = []
    for i in range(num_proc):
        procs.append(Process(target=evolve_multi_process_landing, args=(cons[i-1][0], cons[i][1], returnq, new_set.get_state_json(), new_primaries, optimal_cost, cum_cost, ev_set)))
    return returnq, procs


def evolve_multi_process_landing(in_con:MConnection, out_con: MConnection, returnq: MQueue, settings:EnhanceModelSettings,
           optimal_primary_list: List[Gear], optimal_cost, cum_cost, ev_set:EvolveSettings):
    nset = settings
    settings = EnhanceModelSettings()
    settings.set_state_json(nset)
    evolve(in_con, out_con, returnq, settings,optimal_primary_list, optimal_cost, cum_cost, ev_set=ev_set)

bil = 1000000000.0

def fitness_func_highest(fs_cost, cost, fs_cum_cost, cum_cost):
    return -(fs_cost[-1]/bil)

def fitness_func_avg(fs_cost, cost, fs_cum_cost, cum_cost):
    return -(numpy.mean(fs_cost/bil))

def fitness_func_minscale(fs_cost, cost, fs_cum_cost, cum_cost):
    return numpy.sum(cost / fs_cost)

def fitness_cum_func_highest(fs_cost, cost, fs_cum_cost, cum_cost):
    return -(fs_cum_cost[-1]/bil)

def fitness_cum_func_avg(fs_cost, cost, fs_cum_cost, cum_cost):
    return -(numpy.mean(fs_cum_cost/bil))

def fitness_cum_func_minscale(fs_cost, cost, fs_cum_cost, cum_cost):
    return numpy.sum(cum_cost / fs_cum_cost)

fitness_func = fitness_func_avg
fitness_funcs = {
    'avg': fitness_func_avg,
    'minmax': fitness_func_highest,
    'minscale': fitness_func_minscale,
    'cum_avg': fitness_cum_func_avg,
    'cum_minmax': fitness_cum_func_highest,
    'cum_minscale': fitness_cum_func_minscale
}

def evolve(in_con:MConnection, out_con: MConnection, returnq: MQueue, settings:EnhanceModelSettings,
           optimal_primary_list: List[Gear], optimal_cost, cum_cost, secondaries=None, ev_set:EvolveSettings=None):
    if ev_set is None:
        ev_set = EvolveSettings()

    if secondaries is None:
        secondaries = settings[settings.P_FAIL_STACKER_SECONDARY]
    population_size = ev_set.pop_size
    ultra_elitism = ev_set.ultra_elite
    num_elites = ev_set.num_elites
    brood_size = ev_set.brood_size
    seent = set()
    this_seent = []
    trait_dominance = ev_set.trait_dom

    mutation_rate = ev_set.mutation_rate
    extinction_epoch = ev_set.extinction_epoch
    max_mutation = ev_set.max_mutation
    f_fitness = fitness_funcs[ev_set.fitness_function]
    oppressive_mode = ev_set.oppressive_mode
    oppress_suprem = ev_set.penalize_supremacy
    best = cum_cost
    best_fsl = None
    lb = 0

    def reg_prune(x: FailStackList):
        # sig = (x.starting_pos, x.secondary_gear, *x.secondary_map[:-1])
        sig = (secondaries.index(x.secondary_gear), *x.get_gnome())
        if sig in seent:
            return False
        else:
            seent.add(sig)
            this_seent.append(sig)  # Send this signature to the other processes
            return True

    def check_pruned(x:FailStackList):
        sig = (secondaries.index(x.secondary_gear), *x.get_gnome())
        return sig not in seent

    def accept_prune(x):
        return True

    check_2 = accept_prune
    check = accept_prune
    if oppress_suprem:
        check_2 = reg_prune
        check = check_pruned
    if oppressive_mode:
        check = reg_prune
        check_2 = reg_prune

    def get_randoms(size_):
        retlist = [FailStackList(settings, choice(secondaries), optimal_primary_list, optimal_cost, cum_cost) for _ in range(0, size_)]
        [p.generate_secondary_map(randint(10, 60)) for p in retlist]
        return retlist

    def mutate(new_indiv):
        this_max_mutation = int(ceil(min(lb / 4, max_mutation)))
        for i, v in enumerate(new_indiv.secondary_map[:-1]):
            if random() < mutation_rate:
                new_v = v + randint(-this_max_mutation, this_max_mutation)
                new_indiv.secondary_map[i] = max(1, new_v)
        if random() < mutation_rate:
            new_s = new_indiv.starting_pos + randint(-this_max_mutation, this_max_mutation)
            new_indiv.starting_pos = min(max(10, new_s), 60)
        if random() < mutation_rate:
            new_indiv.secondary_gear = choice(secondaries)
        new_indiv.secondary_map[-1] = 300

    best_fitness = fitness_func(optimal_cost, optimal_cost, cum_cost, cum_cost)
    this_brood_size = 0
    population = get_randoms(population_size)
    epoch_mode = False
    while True:
        if lb > extinction_epoch:
            seent = set()
            population = get_randoms(population_size)
            lb = 0
        [p.evaluate_map() for p in population]
        #pop_costs = best / numpy.array([f.fs_cum_cost for f in population])  # Bigger is better
        #fitness = numpy.sum(pop_costs, axis=1)
        pop_costs = numpy.array([f_fitness(f.fs_cost, optimal_cost, f.fs_cum_cost, cum_cost) for f in population])  # Bigger is better
        fitness = pop_costs
        sort_order = numpy.argsort(fitness, kind='mergesort')
        #for i in range(0, min(lb-15, brood_size)):
        #    bad_fsl = population[sort_order[i]]
        #    check_2(bad_fsl)
        if oppress_suprem:
            epoch_mode = lb > 5
            if epoch_mode:
                for i in population[:this_brood_size]:
                    check_2(i)
        brood_size = max(20, brood_size-lb)
        this_best_fitness = fitness[sort_order[-1]]
        if this_best_fitness > best_fitness:
            best_fitness = this_best_fitness
            best_fsl = population[sort_order[-1]]
            returnq.put((this_best_fitness, lb, (secondaries.index(best_fsl.secondary_gear), *best_fsl.get_gnome())), block=True)
            lb = 0
            #best = numpy.min([best, best_fsl.fs_cum_cost], axis=0)

        new_pop = []
        others_seent = []

        try:
            while in_con.poll():
                others_seent.extend(in_con.recv())
        except EOFError:  # Pipe broken: terminate loop
            out_con.close()
            return
        except BrokenPipeError:
            out_con.close()
            return
        for i in others_seent:
            this_len = len(seent)
            seent.add(tuple(i))
            if len(seent) > this_len:
                this_seent.append(i)

        for i in range(0, brood_size):
            breeder1 = choice(sort_order[-num_elites:])
            breeder1 = population[breeder1]
            if not epoch_mode and (best_fsl is not None) and (random() < ultra_elitism):
                breeder2 = best_fsl
            else:
                if random() > (lb * 0.1):
                    breeder2 = choice(sort_order[-num_elites:])
                    breeder2 = population[breeder2]
                else:
                    breeder2 = choice(sort_order)
                    breeder2 = population[breeder2]
            offspring = FailStackList(settings, choice([breeder1.secondary_gear, breeder2.secondary_gear]), optimal_primary_list,
                                        optimal_cost, cum_cost)
            offspring.secondary_map = breeder1.secondary_map.copy()  # this gets overwritten anyway
            for i, v in enumerate(offspring.secondary_map[:-1]):
                if random() < trait_dominance:
                    if random() < 0.5:
                        offspring.secondary_map[i] = breeder1.secondary_map[i]
                    else:
                        offspring.secondary_map[i] = breeder2.secondary_map[i]
                else:
                    offspring.secondary_map[i] = int(round((breeder1.secondary_map[i] + breeder2.secondary_map[i]) / 2.0))

            if random() < trait_dominance:
                if random() < 0.5:
                    offspring.starting_pos = breeder1.starting_pos
                else:
                    offspring.starting_pos = breeder2.starting_pos
            else:
                offspring.starting_pos = int(round((breeder1.starting_pos + breeder2.starting_pos) / 2.0))

            offspring.secondary_map[-1] = 300
            mutate(offspring)
            if check(offspring):
                new_pop.append(offspring)
        this_brood_size = len(new_pop)
        new_pop.extend(get_randoms(population_size-len(new_pop)))
        population = new_pop

        if len(this_seent) > 0:
            out_con.send(this_seent)
            this_seent = []
        lb += 1


class Solution(object):
    def __init__(self, gear, cost, is_cron=False):
        self.gear = gear
        self.cost = cost
        self.is_cron = is_cron


class StrategySolution(object):
    def __init__(self, settings:EnhanceModelSettings, enh_gear:List[Gear], cron_gear: List[Gear], fs_items:List[Gear], balance_vec, balance_vec_fs):
        self.enh_gear = enh_gear + cron_gear
        self.cron_start = len(enh_gear)
        self.fs_items = fs_items.copy()

        self.balance_vec = balance_vec
        self.balance_vec_fs = balance_vec_fs

        self.settings = settings

        self.enh_me = set(settings[settings.P_ENHANCE_ME])
        self.mod_enhance_me = []
        for gear in enh_gear:
                self.mod_enhance_me.append(gear)

    def is_fake(self, enh_gear):
        return enh_gear not in self.enh_me

    def iter_best_solutions(self):
        bvt = self.balance_vec.T
        fst = self.balance_vec_fs.T
        for i in range(0, len(bvt)):
            bvt_i = bvt[i]
            idx_enh_gear = numpy.argmin(bvt_i)
            enh_gear = self.enh_gear[idx_enh_gear]
            fst_i = fst[i]
            idx_fs_gear = numpy.argmin(fst[i])
            fs_gear = self.fs_items[idx_fs_gear]
            is_cron = idx_enh_gear >= self.cron_start
            yield fs_gear, fst_i[idx_fs_gear], enh_gear, bvt_i[idx_enh_gear], is_cron

    def it_sort_enh_fs_lvl(self, fs_lvl):
        bvt_l = self.balance_vec.T[fs_lvl]
        sorted_args = numpy.argsort(bvt_l)

        best_idx = sorted_args[0]
        best_gear = self.enh_gear[best_idx]
        best_cost = bvt_l[best_idx]

        best_sol = Solution(best_gear, best_cost, is_cron=best_idx>=self.cron_start)

        for i in range(0, len(sorted_args)):
            this_gear_idx = sorted_args[i]
            is_cron = this_gear_idx >= self.cron_start
            gear = self.enh_gear[this_gear_idx]
            gear_cost = bvt_l[this_gear_idx]
            yield Solution(gear, gear_cost, is_cron=is_cron), best_sol

    def it_sort_fs_fs_lvl(self, fs_lvl):
        bvt_l = self.balance_vec_fs.T[fs_lvl]
        sorted_args = numpy.argsort(bvt_l)

        best_idx = sorted_args[0]
        best_gear = self.fs_items[best_idx]
        best_cost = bvt_l[best_idx]

        best_sol = Solution(best_gear, best_cost)

        for i in range(0, len(sorted_args)):
            this_gear_idx = sorted_args[i]
            gear = self.fs_items[this_gear_idx]
            gear_cost = bvt_l[this_gear_idx]
            yield Solution(gear, gear_cost), best_sol

    def get_best_fs_solution(self, fs_lvl):
        fst_l = self.balance_vec_fs.T[fs_lvl]
        best_idx = int(numpy.argmin(fst_l))
        return Solution(self.fs_items[best_idx], fst_l[best_idx])

    def get_best_enh_solution(self, fs_lvl):
        bvt_l = self.balance_vec.T[fs_lvl]
        best_idx = int(numpy.argmin(bvt_l))
        this_gear = self.enh_gear[best_idx]
        return Solution(this_gear, bvt_l[best_idx], is_cron=best_idx>=self.cron_start)

    def get_solution_gear(self, fs_lvl, gear: Gear):
        index = self.enh_gear.index(gear)
        bvt_l = self.balance_vec.T[fs_lvl]
        return bvt_l[index]

    def __len__(self):
        return len(self.balance_vec.T)


class Enhance_model(object):
    VERSION = "0.0.1.5"
    """
    Do not catch exceptions here unless they are a disambiguation.
    """
    def __init__(self, file=None):
        self.settings = EnhanceModelSettings()
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

    def edit_fs_exception(self, fs_index, fs_item):
        """
        Adds an exception to the automatically generated fail stack cost list.
        :param fs_index: This is the index that corresponds to a fail stack count
        :param fs_item: This is the gear object that will be forced at the fs_index
        :return: None
        """
        self.settings[[EnhanceModelSettings.P_FS_EXCEPTIONS, fs_index]] = fs_item
        self.invalidate_failstack_list()
        #self.fs_exceptions[fs_index] = fs_item

    def add_fs_item(self, this_gear):
        fail_stackers = self.settings[EnhanceModelSettings.P_FAIL_STACKERS]
        fail_stackers.append(this_gear)
        self.settings.changes_made = True
        self.invalidate_failstack_list()
        self.save()

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
        fsl:FailStackList = settings[settings.P_GENOME_FS]
        if gear in fail_stackers:
            fail_stackers.remove(gear)

        r_fail_stackers.append(gear)
        if gear is fsl.secondary_gear:
            fsl.secondary_gear = None
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

    def add_fs_secondary_item(self, this_gear:Gear):
        fail_stackers = self.settings[EnhanceModelSettings.P_FAIL_STACKER_SECONDARY]
        fail_stackers.append(this_gear)
        self.settings.changes_made = True
        # TODO: This needs proper setting
        #self.invalidate_failstack_list()
        self.save()

    def update_costs(self, gear_list: List[Gear]):
        settings = self.settings
        item_store: ItemStore = settings[settings.P_ITEM_STORE]
        for gear in gear_list:
            item_store.check_in_gear(gear)
            gear.set_base_item_cost(item_store.get_cost(gear, grade=0))

    def add_equipment_item(self, this_gear):
        enhance_me = self.settings[EnhanceModelSettings.P_ENHANCE_ME]
        enhance_me.append(this_gear)
        self.settings.changes_made = True
        self.invalidate_enahce_list()
        self.save()

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

    def set_fsl(self, fsl:FailStackList):
        if not isinstance(fsl, FailStackList):
            raise ValueError('Must be a fail stacking list object')
        settings = self.settings
        settings[settings.P_GENOME_FS] = fsl
        self.invalidate_secondary_fs()

    def remove_fsl(self):
        settings = self.settings
        fsl:FailStackList = settings[settings.P_GENOME_FS]
        fsl.secondary_map = []
        fsl.secondary_gear = None
        self.invalidate_failstack_list()

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

    #def set_cost_func(self, str_cost_f):
    #    self.settings[EnhanceModelSettings.P_COST_FUNC] = str_cost_f

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

    def edit_fs_item(self, old_gear, gear_obj):
        fail_stackers = self.settings[EnhanceModelSettings.P_FAIL_STACKERS]
        r_fail_stackers = self.settings[EnhanceModelSettings.P_R_FAIL_STACKERS]
        if old_gear in fail_stackers:
            fail_stackers.remove(old_gear)
            fail_stackers.append(gear_obj)
            self.settings.changes_made = True
        elif old_gear in r_fail_stackers:
            r_fail_stackers.remove(old_gear)
            r_fail_stackers.append(gear_obj)
            self.settings.changes_made = True
        self.save()

    def edit_fs_secondary_item(self, old_gear, gear_obj):
        fail_stackers = self.settings[EnhanceModelSettings.P_FAIL_STACKER_SECONDARY]
        r_fail_stackers = self.settings[EnhanceModelSettings.P_R_STACKER_SECONDARY]
        if old_gear in fail_stackers:
            fail_stackers.remove(old_gear)
            fail_stackers.append(gear_obj)
            self.settings.changes_made = True
        elif old_gear in r_fail_stackers:
            r_fail_stackers.remove(old_gear)
            r_fail_stackers.append(gear_obj)
            self.settings.changes_made = True
        self.save()

    def swap_gear(self, old_gear: common.Gear, gear_obj: common.Gear):
        self.edit_fs_item(old_gear, gear_obj)
        self.edit_enhance_item(old_gear, gear_obj)
        self.edit_fs_secondary_item(old_gear, gear_obj)

    def edit_enhance_item(self, old_gear, gear_obj):
        enhance_me = self.settings[EnhanceModelSettings.P_ENHANCE_ME]
        r_enhance_me = self.settings[EnhanceModelSettings.P_R_ENHANCE_ME]
        if old_gear in enhance_me:
            enhance_me.remove(old_gear)
            enhance_me.append(gear_obj)
            self.settings.changes_made = True
        elif old_gear in r_enhance_me:
            r_enhance_me.remove(old_gear)
            r_enhance_me.append(gear_obj)
            self.settings.changes_made = True
        self.save()
        #self.enhance_me.append(gear_obj)

    def get_max_fs(self):
        return self.settings[EnhanceSettings.P_NUM_FS]

    def calcFS(self):
        settings = self.settings
        num_fs = self.get_max_fs()
        fail_stackers = settings[EnhanceModelSettings.P_FAIL_STACKERS]
        fs_exceptions = settings[EnhanceModelSettings.P_FS_EXCEPTIONS]
        fs_second = settings[EnhanceModelSettings.P_FAIL_STACKER_SECONDARY]
        fsl_genome = settings[settings.P_GENOME_FS]
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
            if i in fs_exceptions:
                this_fs_item: Gear = fs_exceptions[i]
                this_fs_cost = this_fs_item.simulate_FS(i, last_rate)
            else:
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
        fs_cost.setflags(write=False)
        cum_fs_cost = numpy.array(cum_fs_cost)
        cum_fs_cost.setflags(write=False)
        self.primary_fs_gear = fs_items
        self.primary_fs_cost = fs_cost
        self.primary_cum_fs_cost = cum_fs_cost
        self.optimal_fs_items = fs_items
        self.fs_cost = fs_cost
        self.cum_fs_cost = cum_fs_cost
        self.cum_fs_probs = cum_fs_probs
        self.fs_probs = fs_probs
        self.fs_needs_update = False
        self.calc_fs_secondary()

    def calc_fs_secondary(self):
        self.fs_needs_update = False
        settings = self.settings
        fsl = settings[settings.P_GENOME_FS]
        fsl.set_primary_data(self.primary_fs_gear, self.primary_fs_cost, self.primary_cum_fs_cost)
        if fsl.validate():
            fsl.evaluate_map()
            self.optimal_fs_items = fsl.gear_list
            self.fs_cost = fsl.fs_cost
            self.cum_fs_cost = fsl.fs_cum_cost

    def calc_equip_costs(self, gear=None):
        settings = self.settings
        enhance_me = settings[EnhanceModelSettings.P_ENHANCE_ME]
        if gear is None:
            euip = enhance_me + settings[EnhanceModelSettings.P_R_ENHANCE_ME]
        else:
            euip = gear

        fail_stackers = settings[EnhanceModelSettings.P_FAIL_STACKERS]
        num_fs = settings[EnhanceSettings.P_NUM_FS]

        if len(euip) < 1:
            raise ValueError('No enhancement items to calculate.')

        # ~ DEAD CODE FOR CHANGING ENHANCE COST FUNCTION ~
        #try:
        #    meth = self.cost_funcs[settings[settings.P_COST_FUNC]]
        #    fnc = lambda x: x.set_enhance_cost_func(meth)
        #    [x.set_enhance_cost_func(meth) for x in euip]
        #except KeyError:
        #    pass

        gts = [x.gear_type for x in euip]
        gts = set(gts)

        # Need to fill the gap between the fail stack calculated at num_fs and the potential for gear to roll past it
        for gt in gts:
            for glmap in gt.p_num_atmpt_map:
                foo = glmap[num_fs]

        if self.fs_needs_update:
            self.calcFS()
        elif self.fs_secondary_needs_update:
            self.calc_fs_secondary()

        cum_fs = self.cum_fs_cost
        # The map object has the highest stack needed for the overflow since it will be pushed up by the resolving of p_num_f_map
        this_max_fs = len(gts.pop().map[0]) + 1
        cum_fs_s = numpy.zeros(this_max_fs)
        cum_fs_s[1:num_fs + 2] = cum_fs
        last_rate = cum_fs[-1]
        for i in range(num_fs + 2, this_max_fs):
            last_rate += min([x.simulate_FS(i, last_rate) for x in fail_stackers])
            cum_fs_s[i] = last_rate
        # this_fs_idx = int(numpy.argmin(trys))

        eq_c = [x.enhance_cost(cum_fs_s) for x in euip]
        #if gear is None:  # This means that all hear was updated
        need_update = False
        for gear in enhance_me:
            need_update |= len(gear.cost_vec) < 1
            if need_update is True:
                break
        self.gear_cost_needs_update = need_update
        if len(eq_c) > 0:
            return eq_c
        else:
            raise Invalid_FS_Parameters('There is no equipment selected for enhancement.')

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
        balance_vec_enh = [x.enhance_lvl_cost(cum_fs_cost, count_fs=count_fs) for x in enhance_me]
        cron_start = len(balance_vec_enh)
        balance_vec_cron = []
        balance_vec_adds = []
        for gear in enhance_me:
            gear:Gear
            if gear.get_enhance_lvl_idx() in gear.cron_stone_dict:
                balance_vec_cron.append(gear.enhance_lvl_cost(cum_fs_cost, count_fs=count_fs, use_crons=True))
                balance_vec_adds.append(gear)
        full_enh_list = enhance_me+balance_vec_adds
        #balance_vec_enh.extend(balance_vec_cron)

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
            this_bal_vec = numpy.copy(balance_vec[:cron_start])
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

        enh_vec_ammend = check_out_gains(balance_vec_enh, balance_vec_enh, enhance_me, new_fs_cost)
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

    def save_to_file(self, txt_path=None):
        if txt_path is None:
            # Force a write
            txt_path = self.settings.f_path
            if txt_path is None:
                txt_path = common.DEFAULT_SETTINGS_PATH
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
