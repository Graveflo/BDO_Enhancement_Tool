#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import sys, datetime
import numpy, os
import common
import model
from random import uniform

import pymongo
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
database = mongo_client["BDO_Enhancer_strat_test"]
db_trials = database['enhance_strat_trials']
db_info = database['enhance_strat_info']


trials_max_time = 5 * 60 * 60
num_logs = 8
trial_time = int(numpy.ceil(trials_max_time/float(num_logs)))

class AverageAccumulator(object):
    def __init__(self):
        self.avg = 0
        self.avgs = 0.0

    def accumulate(self, num):
        avg = self.avg
        avgs = self.avgs
        avg *= avgs
        avgs += 1
        avg /= avgs
        avg += num / avgs
        self.avg = avg
        self.avgs = avgs

    def clear(self):
        self.avgs = 0.0
        self.avg = 0


def run_test(count_fs=False, devaule_fs=True, count_overflow=True, regress=True, name='default', settings='settings_test1.json'):
    mymodel = model.Enhance_model()

    mymodel.load_from_file(settings)

    mymodel.calcFS()
    fs = mymodel.cum_fs_cost
    fs_cost = mymodel.fs_cost
    mymodel.calc_equip_costs()

    fsers, enhc_me = mymodel.calcEnhances(count_fs=count_fs, devaule_fs=devaule_fs, regress=regress)
    #enhance_me = mymodel.enhance_me
    enhance_me = mymodel.settings[mymodel.settings.P_ENHANCE_ME]
    #fail_stackers = mymodel.fail_stackers
    fail_stackers = mymodel.settings[mymodel.settings.P_FAIL_STACKERS]

    log_count = 0

    enhc_me_mins = [numpy.argmin(x) for x in enhc_me.T]
    fsers_mins = [numpy.argmin(x) for x in fsers.T]


    enhance_order = [enhc_me[c][i] for i,c in enumerate(enhc_me_mins)]
    fser_order = [fsers[c][i] for i,c in enumerate(fsers_mins)]

    enhance_me_costs = [[min(x) for x in this_gear.cost_vec] for this_gear in enhance_me ]
    enhance_me_costs_lvl = [costs[enhance_me[i].get_enhance_lvl_idx()] for i,costs in enumerate(enhance_me_costs)]


    gear_accumulators = []
    for gear in enhance_me:
        gear_accumulators.append(AverageAccumulator())

    #for i, gear in enumerate(enhance_me):
    #    print 'GEAR: {} | COST: {}'.format(gear.name, enhance_me_costs_lvl[i])

    #sys.exit(0)
    start_time = datetime.datetime.utcnow()
    info_key = db_info.insert({
        'count_fs': count_fs,
        'devaule_fs': devaule_fs,
        'count_overflow': count_overflow,
        'regress': regress,
        'name': name,
        'time_stamp': start_time,
        'settings': mymodel.settings.__getstate__(),
        'trial_time': trial_time,
        'trials_max_time':trials_max_time,
        'settings_fp': settings,
        'fs': fs
    })

    max_fs = len(fs) - 6
    misses = [0]*6

    # only on enhancement success are the avgs saved

    print('count_fs: {} | devaule_fs: {} | count_overflow: {} | regress: {}'.format(count_fs, devaule_fs, count_overflow, regress))

    def log_data():
        db_trials.insert({
            'test_name': name,
            'avg': avg.avg,
            'num_avg': avg.avgs,
            'misses': misses,
            'info_key': info_key,
            'gear_avg': [
                {
                    'avg': x.avg,
                    'num_avg': x.avgs,
                    'gear_name': enhance_me[i].name
                } for i, x in enumerate(gear_accumulators)]
        })

    balance = 0
    ac_fs = 0
    avg = AverageAccumulator()
    round_time = datetime.datetime.utcnow()
    try:
        while True:
            if enhance_order[ac_fs] < fser_order[ac_fs]:
                enhance_me_idx = enhc_me_mins[ac_fs]
                this_gear = enhance_me[enhance_me_idx]

                roll = uniform(0, 1)
                lvl_idx = this_gear.get_enhance_lvl_idx()
                thi_chance = this_gear.gear_type.map[lvl_idx][ac_fs]
                balance += this_gear.calc_lvl_flat_cost()
                if roll > thi_chance:
                    # fail
                    balance += this_gear.calc_lvl_repair_cost()
                    ac_fs += this_gear.fs_gain()
                else:
                    # success
                    balance -= enhance_me_costs_lvl[enhance_me_idx]
                    gear_accumulators[enhance_me_idx].accumulate(balance)
                    avg.accumulate(balance)
                    balance = 0
            else:
                this_gear = fail_stackers[fsers_mins[ac_fs]]
                # at position 0 we aquire the first fs cost
                balance += fs_cost[ac_fs]
                ac_fs += this_gear.fs_gain()
            if ac_fs >= max_fs:
                misses[ac_fs - max_fs] += 1
                if count_overflow:
                    avg.accumulate(balance)
                balance = 0
                ac_fs = 0
            if (datetime.datetime.utcnow() - round_time).total_seconds() > trial_time:
                round_time = datetime.datetime.utcnow()
                log_data()
                balance = 0
                avg.clear()
                list(map(lambda x: x.clear(), gear_accumulators))
                log_count += 1
                if log_count >= num_logs or (datetime.datetime.utcnow() - start_time).total_seconds() > trials_max_time:
                    break

    except KeyboardInterrupt:
        print('AVG: {} | NUM_AVG: {}'.format(avg.avg, avg.avgs))
        log_data()
        mongo_client.close()
        sys.exit(0)


if __name__ == '__main__':
    run_test(count_fs=False, devaule_fs=True, count_overflow=True, regress=False, name='REG_DEVAL_OVFL')
    run_test(count_fs=False, devaule_fs=True, count_overflow=False, regress=False, name='REG_DEVAL')
    run_test(count_fs=False, devaule_fs=True, count_overflow=True, regress=True, name='REG_DEVAL_OVFL_REGRESS')
    run_test(count_fs=False, devaule_fs=True, count_overflow=False, regress=True, name='REG_DEVAL_REGRESS')

    run_test(count_fs=False, devaule_fs=False, count_overflow=True, regress=False, name='OVFL')
    run_test(count_fs=False, devaule_fs=False, count_overflow=False, regress=False, name='BASE')
    run_test(count_fs=False, devaule_fs=False, count_overflow=True, regress=True, name='REG_OVFL_REGRESS')
    run_test(count_fs=False, devaule_fs=False, count_overflow=False, regress=True, name='REG_REGRESS')
    mongo_client.close()