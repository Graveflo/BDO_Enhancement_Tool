# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import numpy
from .common import Gear, EnhanceSettings, ItemStore, Smashable, Classic_Gear


# TODO: smashables buy in value for PRI is not correct currently (needs * 2)

class GearNotProfitableException(Exception):
    pass


class GearManager(object):
    def __init__(self, gear:Gear):
        self.gear = gear
        settings = gear.settings
        self.settings:EnhanceSettings = settings
        self.item_store:ItemStore = settings[settings.P_ITEM_STORE]
        self.gross_margin_vec = None
        self.cum_cost_vec = None
        self.margin_matrix = None
        self.margin_mins = None
        if issubclass(self.gear.gear_type.instantiable, Classic_Gear):
            self.pure_buy_in_cost = self.item_store.get_cost(gear, 0)
        else:
            self.pure_buy_in_cost = 0

    def calc_gross_margins(self):
        gear = self.gear
        item_store = self.item_store
        settings = self.settings
        tax = settings.tax
        cum_enh_cost = 0
        end_cost_gross = []
        cum_enh_vals = []
        for i in range(0, len(gear.cost_vec_min)):
            cum_enh_cost += gear.cost_vec_min[i]
            cum_enh_vals.append(cum_enh_cost)
            goal_mp_cost = item_store.get_cost(gear, i + 1) * tax
            end_cost_gross.append(cum_enh_cost - goal_mp_cost)
        self.gross_margin_vec = numpy.array(end_cost_gross)
        self.cum_cost_vec = numpy.array(cum_enh_vals)
        return cum_enh_vals, end_cost_gross

    def find_best_margin(self):
        gross_margin_vec = self.gross_margin_vec
        cum_cost_vec = self.cum_cost_vec
        item_store = self.item_store
        gear = self.gear
        margin_matrix = []
        for i,cost in enumerate(cum_cost_vec):
            # subtract the costs of enhancing this level and substitute buying it
            buy_in_cost = item_store.get_cost(gear, i+1)
            this_gross = numpy.copy(gross_margin_vec)
            this_gross[i:] -= cost
            these_margins = this_gross + buy_in_cost
            margin_matrix.append(these_margins)
        margin_matrix = numpy.array(margin_matrix)
        self.margin_matrix = margin_matrix
        matrix_argmins = numpy.argmin(self.margin_matrix, axis=1)
        mins = margin_matrix[numpy.arange(len(margin_matrix)), matrix_argmins]
        self.margin_mins = mins
        start = numpy.argmin(mins)
        stop = matrix_argmins[start]
        if start == stop or margin_matrix[start][stop] > 0:
            raise GearNotProfitableException('Gear has no profitable margins')
        return start, stop

    def get_margin(self, start, stop):
        if start > -1:
            return self.margin_matrix[start][stop]
        else:
            return self.pure_buy_in_cost + self.gross_margin_vec[stop]

    def find_best_margin_for_start(self, start):
        margin_matrix = self.margin_matrix
        return numpy.argmin(margin_matrix[start])

    def find_margin_idx_for_pure(self):
        return numpy.argmin(self.pure_buy_in_cost + self.gross_margin_vec)

    def find_best_margin_for_end(self, end):
        margin_matrix = self.margin_matrix
        margin_matrix = margin_matrix[:,:end]
        matrix_argmins = numpy.argmin(self.margin_matrix, axis=1)
        mins = margin_matrix[numpy.arange(len(margin_matrix)), matrix_argmins]
        self.margin_mins = mins
        start = numpy.argmin(mins)
        return start
