#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import numpy
from random import uniform


factorials = [1]

def factrl(n):
    if n < 0:
        raise ValueError('No factorial of negative numbers allowed.')
    lna = len(factorials)
    if lna > n:
        return factorials[n-1]
    else:
        for i in range(lna-1, n):
            factorials.append((i+1) * factorials[i])
        return factorials[-1]

def NchooseK(n, k):
    return factrl(n) / float(factrl(k) * factrl(n-k))

def binom_cdf(oc, pool, prob):
    cum_mas = 0
    for i in range(0, oc+1):
        cum_mas += NchooseK(pool, i) * (prob**i) * ((1.0-prob)**(pool-i))
    return cum_mas


show_every = 100000
nump_trails = 1000000

chance = 0.06782
return_cost = 100000
fail_cost = 8000
const_rate = 140000

fail_chance = 1-chance
attempts = []


opportunity_cost = const_rate + (chance * return_cost) + (fail_chance * fail_cost)
adjusted = (1 / fail_chance) * opportunity_cost

avg_num_oppertunities = (1 / fail_chance)
prob_fail = binom_cdf(1, int(round(avg_num_oppertunities)), fail_chance)

int_binom_adj = (prob_fail * avg_num_oppertunities * opportunity_cost) + (chance * return_cost)

print("Opportunity cost: " + str(opportunity_cost))
print("Adjusted: " + str(adjusted))
print("Integer Binomial adjusted: " + str(int_binom_adj))

for i in range(0, nump_trails):
    this_attempt_cost = 0
    while uniform(0,1) < chance:
        this_attempt_cost += const_rate + return_cost
    this_attempt_cost += const_rate + fail_cost
    attempts.append(this_attempt_cost)
    if i % show_every == 0:
        print(numpy.mean(attempts))

print('Final:')
print(numpy.mean(attempts))
