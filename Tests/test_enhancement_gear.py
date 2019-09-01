#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import numpy, csv, common, sys
from random import uniform

FAIL_STACK_FILE = 'fs_list.csv'
fs_list = []
with open(FAIL_STACK_FILE, 'rb') as f:
    reader = csv.reader(f)
    reader.next()
    for line in reader:
        fs_list.append([line[0], float(line[1]), float(line[2]), float(line[3]), float(line[4])])

cum_fs = [fs[2] for fs in fs_list]
# Fail stack costs start at one fail stack simulations start at 0
cum_fs.insert(0, 0)

BOSS_GEAR = common.gear_types['Boss Armor']

MEM_FRAG_COST = 1440000.0
CONC_COST = 1650000.0
BLACK_STONE_COST = 204000.0

nump_trails = 100000

if True:
    trail_at ='DUO'
    indx_trail = BOSS_GEAR.lvl_map[trail_at]
    avg_cost_per_fs = []
    print trail_at
    for fs, chance in enumerate(BOSS_GEAR.map[indx_trail]):
        attempts = []
        stack_cost = cum_fs[fs]
        for _ in xrange(0, nump_trails):
            this_attempt_cost = 0
            while uniform(0,1) > chance:
                this_attempt_cost += (MEM_FRAG_COST * 10) + CONC_COST
            this_attempt_cost += CONC_COST + stack_cost
            attempts.append(this_attempt_cost)
        this_avg_cost = numpy.mean(attempts)
        avg_cost_per_fs.append(this_avg_cost)
        #print "FS: " + str(fs) + ": " + str(this_avg_cost)

    print 'Optimal FS: ' + str(numpy.argmin(avg_cost_per_fs))
    PRI_MIN = numpy.min(avg_cost_per_fs)
    print 'Optimal Cost: ' + str(PRI_MIN)

    import matplotlib.pyplot as plt
    plt.plot(avg_cost_per_fs)
    plt.show()
else:
    PRI_MIN = 32575765.5847754

trail_at = 'TRI'
indx_trail = BOSS_GEAR.lvl_map[trail_at]
avg_cost_per_fs = []
print trail_at
for fs, chance in enumerate(BOSS_GEAR.map[indx_trail]):
    attempts = []
    stack_cost = cum_fs[fs]
    for _ in xrange(0, nump_trails):
        this_attempt_cost = 0
        while uniform(0,1) > chance:
            this_attempt_cost += (MEM_FRAG_COST * 10) + CONC_COST + PRI_MIN
        this_attempt_cost += CONC_COST + stack_cost
        attempts.append(this_attempt_cost)
    this_avg_cost = numpy.mean(attempts)
    avg_cost_per_fs.append(this_avg_cost)
    #print "FS: " + str(fs) + ": " + str(this_avg_cost)

print 'Optimal FS: ' + str(numpy.argmin(avg_cost_per_fs))
print 'Optimal Cost: ' + str(numpy.min(avg_cost_per_fs))

import matplotlib.pyplot as plt
plt.plot(avg_cost_per_fs)
plt.show()


