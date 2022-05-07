# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑  ❧
"""
from math import ceil
from multiprocessing import Queue as MQueue, Pipe as MPipe, Process
from multiprocessing.connection import Connection as MConnection
from random import choice, randint, random
from typing import List

import numpy
from BDO_Enhancement_Tool.Core.Gear import Gear
from BDO_Enhancement_Tool.EnhanceModelSettings import EnhanceModelSettings
from BDO_Enhancement_Tool.common import GearItemStore
from BDO_Enhancement_Tool.fsl import FailStackList


class EvolveSettings(object):
    def __init__(self):
        self.num_procs = 4
        self.num_fs = 300
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


def evolve_p_s(settings: EnhanceModelSettings, optimal_cost, cum_cost, ev_set:EvolveSettings, secondaries=None):
    cons = []
    returnq = MQueue()
    new_set = EnhanceModelSettings(item_store=GearItemStore())
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


def evolve_multi_process_landing(in_con:MConnection, out_con: MConnection, returnq: MQueue, settings: EnhanceModelSettings,
                                 optimal_primary_list: List[Gear], optimal_cost, cum_cost, ev_set:EvolveSettings):
    nset = settings
    settings = EnhanceModelSettings(item_store=GearItemStore())
    settings.set_state_json(nset)
    evolve(in_con, out_con, returnq, settings,optimal_primary_list, optimal_cost, cum_cost, ev_set=ev_set)


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


def evolve(in_con:MConnection, out_con: MConnection, returnq: MQueue, settings: EnhanceModelSettings,
           optimal_primary_list: List[Gear], optimal_cost, cum_cost, secondaries=None, ev_set:EvolveSettings=None):
    if ev_set is None:
        ev_set = EvolveSettings()

    if secondaries is None:
        secondaries = settings[settings.P_FAIL_STACKER_SECONDARY]
    num_fs = ev_set.num_fs
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

    def check_pruned(x: FailStackList):
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
        retlist = [
            FailStackList(settings, choice(secondaries), optimal_primary_list, optimal_cost, cum_cost, num_fs=num_fs) for _ in range(0, size_)]
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
            new_indiv.starting_pos = min(max(5, new_s), 60)
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
                                      optimal_cost, cum_cost, num_fs=num_fs)
            offspring.secondary_map = breeder1.secondary_map.copy()  # this gets overwritten anyway
            for i in range(min(len(breeder1.secondary_map), len(breeder2.secondary_map))):
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


bil = 1000000000.0