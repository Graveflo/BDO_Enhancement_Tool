#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import numpy, json
from . import common
from .old_settings import converters
import shutil
from random import randint, random, choice
from math import ceil
from typing import List, Dict
from multiprocessing import Process, Value
from multiprocessing import Lock as MLock
from multiprocessing import Queue as MQueue
from multiprocessing import Pipe as MPipe
from multiprocessing.connection import Connection as MConnection
from queue import Queue, Empty

Gear = common.Gear
Classic_Gear = common.Classic_Gear
Smashable = common.Smashable
gear_types = common.gear_types
EnhanceSettings = common.EnhanceSettings
ItemStore = common.ItemStore
generate_gear_obj = common.generate_gear_obj


class Invalid_FS_Parameters(Exception):
    pass


def genload_gear(gear_state, settings):
    gtype = gear_types[gear_state['gear_type']]
    gear = generate_gear_obj(settings, gear_type=gtype)
    gear.set_state_json(gear_state)
    return gear


class SettingsException(Exception):
    def __init__(self, msg, embedded):
        super(SettingsException, self).__init__(msg)
        self.embedded = embedded


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
            self.P_GENOME_FS: (0, 22, 2, 4, 8),
            self.P_QUEST_FS_INC: 0,  # Free FS increase from quests
            #self.P_COST_FUNC: 'Thorough (Slow)',
            self.P_VERSION: Enhance_model.VERSION
        })

    def get_state_json(self):
        super_state = {}
        super_state.update(super(EnhanceModelSettings, self).get_state_json())
        fail_stackers = self[self.P_FAIL_STACKERS]
        super_state.update({
            self.P_FAIL_STACKERS: [g.get_state_json() for g in fail_stackers],
            self.P_FAIL_STACKER_SECONDARY: [g.get_state_json() for g in self[self.P_FAIL_STACKER_SECONDARY]],
            self.P_ENH_FOR_PROFIT: [g.get_state_json() for g in self[self.P_ENH_FOR_PROFIT]],
            self.P_ENHANCE_ME: [g.get_state_json() for g in self[self.P_ENHANCE_ME]],
            self.P_FS_EXCEPTIONS: {k:fail_stackers.index(v) for k,v in self[self.P_FS_EXCEPTIONS].items()},
            self.P_R_FAIL_STACKERS: [g.get_state_json() for g in self[self.P_R_FAIL_STACKERS]],
            self.P_R_FOR_PROFIT: [g.get_state_json() for g in self[self.P_R_FOR_PROFIT]],
            self.P_R_STACKER_SECONDARY: [g.get_state_json() for g in self[self.P_R_STACKER_SECONDARY]],
            self.P_R_ENHANCE_ME: [g.get_state_json() for g in self[self.P_R_ENHANCE_ME]],
            self.P_FAIL_STACKERS_COUNT: {fail_stackers.index(k):v for k,v in self[self.P_FAIL_STACKERS_COUNT].items()},
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
        P_FAIL_STACKERS = [genload_gear(g, self) for g in P_FAIL_STACKERS]
        P_FAIL_STACKER_SECONDARY = state.pop(self.P_FAIL_STACKER_SECONDARY)
        P_FAIL_STACKER_SECONDARY = [genload_gear(g, self) for g in P_FAIL_STACKER_SECONDARY]

        P_ENH_FOR_PROFIT = state.pop(self.P_ENH_FOR_PROFIT)
        P_ENH_FOR_PROFIT = [genload_gear(g, self) for g in P_ENH_FOR_PROFIT]

        P_R_STACKER_SECONDARY = state.pop(self.P_R_STACKER_SECONDARY)
        P_R_STACKER_SECONDARY = [genload_gear(g, self) for g in P_R_STACKER_SECONDARY]

        P_R_FOR_PROFIT = state.pop(self.P_R_FOR_PROFIT)
        P_R_FOR_PROFIT = [genload_gear(g, self) for g in P_R_FOR_PROFIT]

        P_ENHANCE_ME = state.pop(self.P_ENHANCE_ME)
        P_ENHANCE_ME = [genload_gear(g, self) for g in P_ENHANCE_ME]
        P_R_FAIL_STACKERS = state.pop(self.P_R_FAIL_STACKERS)
        P_R_FAIL_STACKERS = [genload_gear(g, self) for g in P_R_FAIL_STACKERS]
        P_R_ENHANCE_ME = state.pop(self.P_R_ENHANCE_ME)
        P_R_ENHANCE_ME = [genload_gear(g, self) for g in P_R_ENHANCE_ME]

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
        self.gear_list:List[Gear] = optimal_primary_list
        self.fs_cost:List = optimal_cost
        self.fs_cum_cost:List = cum_cost

        self.starting_pos = None
        self.secondary_gear:Gear = secondary
        self.secondary_map = []
        self.hopeful_nums = []
        self.remake_strat = []

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

    def evaluate_map(self):
        if self.starting_pos is None:
            raise Exception()
        starting_pos = self.starting_pos
        settings = self.settings
        num_fs = settings[settings.P_NUM_FS] + 1
        s_g = self.secondary_gear

        s_g_bt = s_g.get_backtrack_start()
        start_g_lvl_idx = s_g_bt - 1
        self.hopeful_nums = []

        fs_cum_cost = self.fs_cum_cost
        fs_cost = self.fs_cost
        gear_list = self.gear_list

        reserve = 0
        reserve_accum = 0
        #reserve_buff = 0
        prev_cost_per_succ = 0
        fs_lvl = starting_pos

        # the first prev_cost_per_succ is missing the failstack price

        for lvl_off, num_bmp in enumerate(self.secondary_map):
            s_g = s_g.duplicate() # This can be optimized
            s_g.set_enhance_lvl(s_g.gear_type.idx_lvl_map[start_g_lvl_idx + lvl_off])
            fs_gain = s_g.fs_gain()
            #build_fs_cost = fs_cum_cost[fs_lvl - 1]  # Rebuilding the stack is baked in
            waste_fails = 1.0
            #avg_cost_acum = 0
            start_fs_lvl = fs_lvl
            start_reserve = reserve
            #relief_suc_accum = 0

            for i in range(0, num_bmp):
                suc_rate = s_g.lvl_success_rate[fs_lvl]


                this_cum_cost = fs_cum_cost[fs_lvl - 1]
                this_cost = s_g.simulate_FS(fs_lvl, this_cum_cost)
                fail_rate = 1 - suc_rate
                waste_fails *= fail_rate

                num_attempts =  1 / fail_rate
                multi = min(num_attempts, reserve)
                multi = max(0, multi)
                this_cost += (num_attempts-multi) * prev_cost_per_succ
                reserve -= num_attempts

                #avg_cost_acum += (this_cost / num_attempts)
                #relief_suc_accum += suc_rate
                cost_f = this_cost / fs_gain

                succ_times = suc_rate * num_attempts
                reserve += succ_times * reserve  # Don't add back the reserve it takes to get here
                if reserve_accum == 0:
                    reserve_accum = succ_times
                else:
                    reserve_accum += succ_times + (succ_times * reserve_accum) # Succeeding makes you go through all previous attempts also
                for j in range(0, fs_gain):
                    offset = fs_lvl + j
                    if offset >= num_fs:
                        return
                    gear_list[offset] = s_g
                    fs_cost[offset] = cost_f
                    fs_cum_cost[offset] = self.fs_cum_cost[offset-1] + cost_f

                fs_lvl += fs_gain

            reserve = reserve_accum

            self.hopeful_nums.append(reserve)

            accum_chance = 0
            t_fs_lvl = start_fs_lvl
            this_reserve = start_reserve
            cum_cost = self.fs_cum_cost[fs_lvl - 1]
            counter = 0
            count_chance_discard = 0
            count_cost_discard = cum_cost
            while accum_chance < 1:
                suc_rate = s_g.lvl_success_rate[t_fs_lvl]
                fail_rate = 1 - suc_rate
                this_cost = s_g.simulate_FS(fs_lvl, 0) * fail_rate

                multi = min(1, this_reserve)
                multi = max(0, multi)
                this_cost += (1 - multi) * prev_cost_per_succ
                cum_cost += this_cost
                this_reserve -= 1

                if counter < num_bmp:
                    count_chance_discard += suc_rate
                    count_cost_discard += this_cost

                accum_chance += suc_rate
                counter += 1

            prev_cost_p_suc_taptap = cum_cost
            prev_cost_p_suc_discard = count_cost_discard / count_chance_discard

            if prev_cost_p_suc_taptap < prev_cost_p_suc_discard:
                prev_cost_per_succ = prev_cost_p_suc_taptap
                self.remake_strat.append(self.REMAKE_OVERSTACK)
            else:
                prev_cost_per_succ = prev_cost_p_suc_discard
                self.remake_strat.append(self.REMAKE_DISCARD_STACK)

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

    def __getstate__(self):
        json_obj = self.get_state_json()
        json_obj['fs_cost'] = self.fs_cost
        return json_obj

    def __setstate__(self, state):
        base_gear = state['base_gear']
        secondary = state['secondary']
        starting_pos = state['starting_pos']
        fs_cost = state['fs_cost']
        secondary_map = state['secondary_map']
        hopeful_nums = state['hopeful_nums']
        remake_strat = state['remake_strat']
        self.starting_pos = starting_pos
        self.secondary_gear = secondary

        gear_list = []
        for i in range(0, starting_pos):
            gear_list.append(base_gear)
        s_g_bt = secondary.get_backtrack_start()
        start_g_lvl_idx = s_g_bt - 1
        gear_type = secondary.gear_type
        for i,pn in enumerate(secondary):
            this_gear = secondary.duplicate()
            this_gear.set_enhance_lvl(gear_type.idx_lvl_map[start_g_lvl_idx + i])
            for _ in range(starting_pos, starting_pos+pn):
                gear_list.append(this_gear)
            starting_pos += pn

        self.gear_list = gear_list
        self.fs_cost = fs_cost
        self.secondary_map = secondary_map
        self.hopeful_nums = hopeful_nums
        self.remake_strat = remake_strat

    def get_gnome(self):
        return (self.starting_pos, *self.secondary_map)

    def set_gnome(self, gnome):
        self.starting_pos = gnome[0]
        self.secondary_map = gnome[1:]


def evolve_p_s(num_proc, settings:EnhanceModelSettings, optimal_cost, cum_cost):
    cons = []
    returnq = MQueue()
    new_set = EnhanceModelSettings()
    new_set.set_state_json(settings.get_state_json())

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
    for i in range(num_proc):
        cons.append(MPipe(False))
    procs = []
    for i in range(num_proc):
        procs.append(Process(target=evolve_multi_process_landing, args=(cons[i-1][0], cons[i][1], returnq, new_set.get_state_json(), new_primaries, optimal_cost, cum_cost)))
    return returnq, procs


def evolve_multi_process_landing(in_con:MConnection, out_con: MConnection, returnq: MQueue, settings:EnhanceModelSettings,
           optimal_primary_list: List[Gear], optimal_cost, cum_cost):
    nset = settings
    settings = EnhanceModelSettings()
    settings.set_state_json(nset)
    evolve(in_con, out_con, returnq, settings,optimal_primary_list, optimal_cost, cum_cost)


def evolve(in_con:MConnection, out_con: MConnection, returnq: MQueue, settings:EnhanceModelSettings,
           optimal_primary_list: List[Gear], optimal_cost, cum_cost, secondaries=None):


    if secondaries is None:
        secondaries = settings[settings.P_FAIL_STACKER_SECONDARY]
    population_size = 200
    ultra_elitism = 0.4
    num_elites = 120
    brood_size = 200
    seent = set()
    this_seent = []
    trait_dominance = 0.2

    mutation_rate = 0.40
    max_mutation = 5
    best = cum_cost
    best_fsl = None
    lb = 0

    def check_2(x: FailStackList):
        # sig = (x.starting_pos, x.secondary_gear, *x.secondary_map[:-1])
        sig = (secondaries.index(x.secondary_gear), *x.get_gnome())
        if sig in seent:
            return False
        else:
            seent.add(sig)
            this_seent.append(sig)  # Send this signature to the other processes
            return True

    def check(x:FailStackList):
        return True

    population = []

    for _ in range(0, population_size):
        p = FailStackList(settings, choice(secondaries), optimal_primary_list.copy(), numpy.copy(optimal_cost), numpy.copy(cum_cost))
        p.generate_secondary_map(randint(10, 60))
        if check(p):
            population.append(p)

    def mutate(new_indiv):
        max_mutation = int(ceil(min(lb, 20) / 2))
        for i, v in enumerate(new_indiv.secondary_map[:-1]):
            if random() < mutation_rate:
                new_v = v + randint(-max_mutation, max_mutation)
                new_indiv.secondary_map[i] = max(1, new_v)
        if random() < mutation_rate:
            new_s = new_indiv.starting_pos + randint(-max_mutation, max_mutation)
            new_indiv.starting_pos = min(max(10, new_s), 60)
        if random() < mutation_rate:
            new_indiv.secondary_gear = choice(secondaries)
        new_indiv.secondary_map[-1] = 300

    def duplicate_fsl(dfsl:FailStackList):
        nfsl = FailStackList(settings, dfsl.secondary_gear, optimal_primary_list.copy(),
                             numpy.copy(optimal_cost), numpy.copy(cum_cost))
        nfsl.starting_pos = dfsl.starting_pos
        nfsl.secondary_map = dfsl.secondary_map.copy()
        return nfsl

    global evolve_lock
    best_fitness = 0
    while True:
        [p.evaluate_map() for p in population]
        pop_costs = best / numpy.array([f.fs_cum_cost for f in population])  # Bigger is better
        fitness = numpy.sum(pop_costs, axis=1)
        sort_order = numpy.argsort(fitness)
        for i in range(0, population_size // 2):
            bad_fsl = population[sort_order[-1]]
            check_2(bad_fsl)
        this_best_fitness = fitness[sort_order[-1]]
        if this_best_fitness > best_fitness:
            best_fitness = this_best_fitness
            best_fsl = population[sort_order[-1]]
            returnq.put((lb, secondaries.index(best_fsl.secondary_gear), best_fsl.get_gnome()), block=True)
            lb = 0
            #best = numpy.min([best, best_fsl.fs_cum_cost], axis=0)

        new_pop = []
        while in_con.poll():
            try:
                others_seent = in_con.recv()
            except EOFError:  # Pipe broken: terminate loop
                out_con.close()
                return
            for i in others_seent:
                seent.add(tuple(i))
                this_seent.append(i)

            #seent.update(this_seent)


        for i in range(0, brood_size):
            breeder1 = choice(sort_order[-num_elites:])
            breeder1 = population[breeder1]
            if random() < ultra_elitism:
                breeder2 = best_fsl
            else:
                breeder2 = choice(sort_order[-num_elites:])
                breeder2 = population[breeder2]
            offspring = FailStackList(settings, choice([breeder1.secondary_gear, breeder2.secondary_gear]), optimal_primary_list.copy(),
                                        numpy.copy(optimal_cost), numpy.copy(cum_cost))
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
        for i in range(len(new_pop), population_size):
            new_indiv = FailStackList(settings, choice(secondaries), optimal_primary_list.copy(), numpy.copy(optimal_cost), numpy.copy(cum_cost))
            new_indiv.generate_secondary_map(randint(10, 60))
            #mutate(new_indiv)
            if check(new_indiv):
                new_pop.append(new_indiv)
        population = new_pop

        if len(this_seent) > 0:
            out_con.send(this_seent)
            this_seent = []
        lb += 1


class Enhance_model(object):
    VERSION = "0.0.1.5"
    """
    Do not catch exceptions here unless they are a disambiguation.
    """
    def __init__(self):
        self.settings = EnhanceModelSettings()

        #self.equipment_costs = []  # Cost of equipment
        #self.r_equipment_costs = []  # Cost of removed equipment
        self.optimal_fs_items = []  # Fail stack items chosen as optimal at each fails tack index
        self.fs_cost = []  # Cost of each fail stack
        self.fs_probs = []  # Probability of gaining fail stack
        self.cum_fs_probs = []  # Cumulative chance of gaining fail stack
        self.cum_fs_cost = []  # Cumulative cost of gaining a fail stack
        self.custom_input_fs = {}

        self.fs_needs_update = True
        self.gear_cost_needs_update = True
        self.auto_save = True

        self.dragon_scale_30 = False
        self.dragon_scale_350 = False
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
        self.optimal_fs_items = []
        self.fs_cost = []
        self.cum_fs_cost = []
        self.cum_fs_probs = []
        self.fs_probs = []
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

    def swap_gear(self, old_gear: common.Gear, gear_obj: common.Gear):
        self.edit_fs_item(old_gear, gear_obj)
        self.edit_enhance_item(old_gear, gear_obj)

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
                    if cost < last_rate:
                        last_rate = 0
                        this_fs_cost = cost
                        self.dragon_scale_30 = True
                    else:
                        self.dragon_scale_30 = False
                    this_fs_cost = min(this_fs_cost, cost)
                elif i == 39:
                    dsc = settings[settings.P_ITEM_STORE].get_cost(ItemStore.P_DRAGON_SCALE)
                    cost = dsc * 350
                    if cost < last_rate:
                        last_rate = 0
                        this_fs_cost = cost
                        self.dragon_scale_350 = True
                    else:
                        self.dragon_scale_350 = False
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

        #fsa = [x for x in fail_stackers if isinstance(x, Classic_Gear)]
        #list(map(lambda x: x.simulate_Enhance_sale(cum_fs_cost), fsa))

        #fsl = evolve(settings, settings[settings.P_FAIL_STACKER_SECONDARY], fs_items, fs_cost, cum_fs_cost)

        #self.optimal_fs_items = fsl.gear_list
        #self.fs_cost = fsl.fs_cost
        #self.cum_fs_cost = fsl.fs_cum_cost
        self.optimal_fs_items = fs_items
        self.fs_cost = fs_cost
        self.cum_fs_cost = cum_fs_cost
        self.cum_fs_probs = cum_fs_probs
        self.fs_probs = fs_probs
        self.fs_needs_update = False

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

    def calcEnhances(self, enhance_me=None, fail_stackers=None, count_fs=False, count_fs_fs=True, devaule_fs=False, regress=False):
        if self.fs_needs_update:
            self.calcFS()

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

        num_fs = settings[EnhanceSettings.P_NUM_FS]
        cum_fs_cost = self.cum_fs_cost
        cum_fs_cost = numpy.roll(cum_fs_cost, 1)
        cum_fs_cost[0] = 0
        fs_cost = self.fs_cost

        min_fs = self.get_min_fs()

        new_fs_cost = fs_cost[:]

        fs_len = num_fs + 1


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
            # Not double counting fs cost bc this is a copy
            this_bal_vec = numpy.copy(balance_vec)
            # cycle through all fsil stack levels
            for i in range(min_fs, fs_len):
                lookup_idx = i
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
                    go:Gear = enhance_me[min_gear_map[i]]
                    co = go.get_cost_obj()[go.enhance_lvl_to_number()]
                    r_gear_cost_current_fs = co[lookup_idx]
                    r_gear_cost_ahead_fs = co[fs_pointer_idx]

                    if balance_vec is balance_vec_enh:
                        self_reduction = r_gear_cost_ahead_fs - r_gear_cost_current_fs

                    else:
                        self_reduction = 0
                    self_reduction = r_gear_cost_ahead_fs - r_gear_cost_current_fs

                    gear_pointed_cost = gear_cost_ahead_fs - gear_cost_current_fs
                    if devaule_fs:
                        projected_gain = gear_pointed_cost
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

        if devaule_fs and regress:
            raise NotImplementedError('This doesnt really work')
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

        return balance_vec_fser, balance_vec_enh

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

