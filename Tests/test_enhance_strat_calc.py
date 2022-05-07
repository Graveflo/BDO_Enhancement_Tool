#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑  ❧
"""
import numpy
import model
from datetime import datetime, timedelta

def run_test(count_fs=False, devaule_fs=True, count_overflow=True, regress=True, name='default', settings='settings.json'):
    mymodel = model.Enhance_model()

    mymodel.load_from_file(settings)

    mymodel.calcFS()
    fs = mymodel.cum_fs_cost
    mymodel.calc_equip_costs()

    fsers, enhc_me = mymodel.calcEnhances(count_fs=count_fs, devaule_fs=devaule_fs, regress=regress)
    #enhance_me = mymodel.enhance_me
    enhance_me = mymodel.settings[mymodel.settings.P_ENHANCE_ME]
    #fail_stackers = mymodel.fail_stackers
    fail_stackers = mymodel.settings[mymodel.settings.P_FAIL_STACKERS]

    enhc_me_mins = [numpy.argmin(x) for x in enhc_me.T]
    fsers_mins = [numpy.argmin(x) for x in fsers.T]


    enhance_order = [enhc_me[c][i] for i,c in enumerate(enhc_me_mins)]
    fser_order = [fsers[c][i] for i,c in enumerate(fsers_mins)]

    #enhance_me_costs = [[min(x) for x in this_gear.cost_vec] for this_gear in enhance_me ]
    #enhance_me_costs_lvl = [costs[enhance_me[i].get_enhance_lvl_idx()] for i,costs in enumerate(enhance_me_costs)]


    # only on enhancement success are the avgs saved

    print('count_fs: {} | devaule_fs: {} | count_overflow: {} | regress: {}'.format(count_fs, devaule_fs, count_overflow, regress))

    for i in range(0, len(fs)):
        if enhance_order[i] < fser_order[i]:
            enhance_me_idx = enhc_me_mins[i]
            this_gear = enhance_me[enhance_me_idx]
        else:
            fsers_idx = fsers_mins[i]
            this_gear = fail_stackers[fsers_idx]
        print('{} : {}'.format(i, this_gear.name))

    fs_strats = []

    def fs_cost_strat(fs_num):
        recu = True
        if fs_num >= len(fs):
            fs_num = len(fs) - 1
            recu = False
        balance = 0
        if enhance_order[fs_num] < fser_order[fs_num]:
            # enhance wins
            enhance_me_idx = enhc_me_mins[fs_num]
            this_gear = enhance_me[enhance_me_idx]
            gain_cost = this_gear.get_min_cost()[this_gear.get_enhance_lvl_idx()]
        else:
            # fs win
            fsers_idx = fsers_mins[fs_num]
            this_gear = fail_stackers[fsers_idx]
            gain_cost = 0
        lvl_idx = this_gear.get_enhance_lvl_idx()
        thi_chance = this_gear.gear_type.map[lvl_idx][fs_num]
        fs_gain = this_gear.fs_gain()
        balance += this_gear.calc_lvl_flat_cost()
        balance -= thi_chance * gain_cost
        ahead_cost = 0
        if recu:
            ahead_cost = fs_cost_strat(fs_num + fs_gain)
        balance += (1.0 - thi_chance) * (this_gear.calc_lvl_repair_cost() + ahead_cost)
        return balance

    for i in range(0, len(fs)):
        fs_strats.append(fs_cost_strat(i))

    return fs_strats


def run_test2(count_fs=False, devaule_fs=True, count_overflow=True, regress=True, name='default', settings='settings.json'):
    mymodel = model.Enhance_model()

    mymodel.load_from_file(settings)

    mymodel.calcFS()
    num_fs = mymodel.settings[mymodel.settings.P_NUM_FS]
    mymodel.calc_equip_costs()

    fsers, enhc_me = mymodel.calcEnhances(count_fs=count_fs, devaule_fs=devaule_fs, regress=regress)
    #enhance_me = mymodel.enhance_me
    enhance_me = mymodel.settings[mymodel.settings.P_ENHANCE_ME]
    #fail_stackers = mymodel.fail_stackers
    fail_stackers = mymodel.settings[mymodel.settings.P_FAIL_STACKERS]

    enhc_me_mins = [numpy.argmin(x) for x in enhc_me.T]
    fsers_mins = [numpy.argmin(x) for x in fsers.T]


    enhance_order = [enhc_me[c][i] for i,c in enumerate(enhc_me_mins)]
    fser_order = [fsers[c][i] for i,c in enumerate(fsers_mins)]

    #enhance_me_costs = [[min(x) for x in this_gear.cost_vec] for this_gear in enhance_me ]
    #enhance_me_costs_lvl = [costs[enhance_me[i].get_enhance_lvl_idx()] for i,costs in enumerate(enhance_me_costs)]


    # only on enhancement success are the avgs saved

    print('count_fs: {} | devaule_fs: {} | count_overflow: {} | regress: {}'.format(count_fs, devaule_fs, count_overflow, regress))

    for i in range(0, num_fs+1):
        if enhance_order[i] < fser_order[i]:
            enhance_me_idx = enhc_me_mins[i]
            this_gear = enhance_me[enhance_me_idx]
        else:
            fsers_idx = fsers_mins[i]
            this_gear = fail_stackers[fsers_idx]
        print('{} : {}'.format(i, this_gear.name))

    fs_strats = []

    def fs_cost_strat(fs_num):
        prev_fs_cost = 0
        balance = 0
        while fs_num < num_fs+1:
            if enhance_order[fs_num] < fser_order[fs_num]:
                # enhance wins
                enhance_me_idx = enhc_me_mins[fs_num]
                this_gear = enhance_me[enhance_me_idx]
                gain_cost = this_gear.get_min_cost()[this_gear.get_enhance_lvl_idx()]
            else:
                # fs win
                fsers_idx = fsers_mins[fs_num]
                this_gear = fail_stackers[fsers_idx]
                gain_cost = 0
            lvl_idx = this_gear.get_enhance_lvl_idx()
            thi_chance = this_gear.gear_type.map[lvl_idx][fs_num]
            fs_gain = this_gear.fs_gain()
            fs_num += fs_gain
            balance += this_gear.calc_lvl_flat_cost()
            balance -= thi_chance * gain_cost
            balance += prev_fs_cost
            prev_fs_cost += this_gear.calc_lvl_repair_cost() + this_gear.calc_lvl_flat_cost()
            balance += (1.0 - thi_chance) * this_gear.calc_lvl_repair_cost()
        return balance

    for i in range(0, num_fs+1):
        fs_strats.append(fs_cost_strat(i))

    return fs_strats


def run_ehaust_test(settings='settings_booger.json'):
    import itertools

    mymodel = model.Enhance_model()

    mymodel.load_from_file(settings)

    mymodel.calcFS()
    fs = mymodel.cum_fs_cost
    mymodel.calc_equip_costs()

    enhance_me = mymodel.settings[mymodel.settings.P_ENHANCE_ME]
    fail_stackers = mymodel.settings[mymodel.settings.P_FAIL_STACKERS]

    #enhance_me_costs = [[min(x) for x in this_gear.cost_vec] for this_gear in enhance_me ]
    #enhance_me_costs_lvl = [costs[enhance_me[i].get_enhance_lvl_idx()] for i,costs in enumerate(enhance_me_costs)]


    # only on enhancement success are the avgs saved
    pick_mask = [True] * len(fs)

    t_ = 20 * 60
    t_start = datetime.utcnow() - timedelta(hours=1)

    def clear_cost(x):
        x.cost_vec_min = numpy.zeros(len(x.gear_type.map))
        x.restore_cost_vec_min = numpy.zeros(len(x.gear_type.map))
    list(map(clear_cost, fail_stackers))
    alls = fail_stackers + enhance_me

    best = float('inf')
    best_map = None


    def fs_cost_strat(fs_num, gear_map):
        recu = True
        if fs_num >= len(fs):
            fs_num = len(fs) - 1
            recu = False
        balance = 0
        this_gear = gear_map[fs_num]
        lvl_idx = this_gear.get_enhance_lvl_idx()
        gain_cost = this_gear.get_min_cost()[lvl_idx]
        thi_chance = this_gear.gear_type.map[lvl_idx][fs_num]
        fs_gain = this_gear.fs_gain()
        balance += this_gear.calc_lvl_flat_cost()
        balance -= thi_chance * gain_cost
        ahead_cost = 0
        if recu:
            ahead_cost = fs_cost_strat(fs_num + fs_gain, gear_map)
        balance += (1.0 - thi_chance) * (this_gear.calc_lvl_repair_cost() + ahead_cost)
        return balance

    for comb in itertools.product(alls, repeat=len(fs)):
        cost_zero = fs_cost_strat(0, comb)
        if cost_zero < best:
            best = cost_zero
            best_map = comb
            if (datetime.utcnow() - t_start).total_seconds() >= t_:
                for i, g in enumerate(best_map):
                    print('FS: {}\t{}'.format(i, g.name))
                print(best)
            t_start = datetime.utcnow()

    return best, best_map




if __name__ == '__main__':
    matrix = []
    def add_test(count_fs=False, devaule_fs=True, count_overflow=True, regress=True, name='default'):
        ret = run_test2(count_fs=count_fs, devaule_fs=devaule_fs, count_overflow=count_overflow, regress=regress, name=name)
        ret.insert(0, name)
        matrix.append(ret)
    add_test(count_fs=False, devaule_fs=True, count_overflow=False, regress=False, name='REG_DEVAL')
    add_test(count_fs=False, devaule_fs=True, count_overflow=False, regress=True, name='REG_DEVAL_REGRESS')
    add_test(count_fs=False, devaule_fs=False, count_overflow=False, regress=False, name='BASE')
    #add_test(count_fs=False, devaule_fs=False, count_overflow=False, regress=True, name='REG_REGRESS')
    #import sys
    #sys.exit(0)
    import csv
    with open('strat_calcs.csv', 'wb') as f:
        writer = csv.writer(f)
        rows = list(zip(*matrix))
        writer.writerow(rows[0])
        for rew in rows[1:]:
            writer.writerow(rew)

if __name__ == '__main__ NOT':
    best, best_map = run_ehaust_test()
    for i,g in enumerate(best_map):
        print('FS: {}\t{}'.format(i, g.name))
    print(best)

