#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import numpy, json
import common

Classic_Gear = common.Classic_Gear
Smashable = common.Smashable
gear_types = common.gear_types

class Invalid_FS_Parameters(Exception):
    pass

class Enhance_model(object):
    VERSION = "0.0.0.1"
    """
    Do not catch exceptions here unless they are a disambiguation.
    """
    def __init__(self):
        self.cost_bs_a = common.BLACK_STONE_ARMOR_COST
        self.cost_bs_w = common.BLACK_STONE_WEAPON_COST
        self.cost_conc_a = common.CONC_ARMOR_COST
        self.cost_conc_w = common.CONC_WEAPON_COST
        self.cost_meme = common.MEMORY_FRAG_COST
        self.cost_cron = common.CRON_STONE_COST
        self.cost_cleanse = common.CLEANSE_COST

        self.current_path = None

        self.fail_stackers = []
        self.enhance_me = []
        self.r_fail_stackers = []
        self.r_enhance_me = []
        self.fail_stackers_counts = {}

        self.equipment_costs = []
        self.r_equipment_costs = []
        self.fs_items = []  # rename this
        self.fs_cost = []
        self.fs_probs = []
        self.cum_fs_probs = []
        self.cum_fs_cost = []
        self.fs_exceptions = {}

        self.fs_needs_update = True
        self.gear_cost_needs_update = True

    def add_fs_exception(self, fs_index, fs_item):
        """
        Adds an exception to the automatically generated fail stack cost list.
        :param fs_index: This is the index that corresponds to a fail stack count
        :param fs_item: This is the gear object that will be forced at the fs_index
        :return: None
        """
        self.fs_exceptions[fs_index] = fs_item

    def add_fs_item(self, this_gear):
        self.fail_stackers.append(this_gear)

    def add_equipment_item(self, this_gear):
        self.enhance_me.append(this_gear)

    def set_cost_bs_a(self, cost_bs_a):
        self.cost_bs_a = float(cost_bs_a)
        # update item values

    def set_cost_bs_w(self, cost_bs_w):
        self.cost_bs_w = float(cost_bs_w)
        # update item values

    def set_cost_conc_a(self, cost_conc_a):
        self.cost_conc_a = float(cost_conc_a)
        # update item values

    def set_cost_conc_w(self, cost_conc_w):
        self.cost_conc_w = float(cost_conc_w)
        # update item values

    def set_cost_meme(self, cost_meme):
        self.cost_meme = float(cost_meme)
        # update item values

    def set_cost_cron(self, cost_cron):
        self.cost_cron = float(cost_cron)
        # update item values

    def set_cost_cleanse(self, cost_cleanse):
        self.cost_cleanse = float(cost_cleanse)
        # update item values

    def invalidate_enahce_list(self):
        self.gear_cost_needs_update = True
        self.equipment_costs = []
        self.r_equipment_costs = []

    def invalidate_failstack_list(self):
        self.fs_needs_update = True
        self.fs_items = []
        self.fs_cost = []
        self.cum_fs_cost = []
        self.cum_fs_probs = []
        self.fs_probs = []

    def generate_gear_obj(self, item_cost=None, enhance_lvl=None, gear_type=None, name=None):
        str_gear_t = gear_type.name
        if str_gear_t.lower().find('accessor') > -1:
            gear = Smashable(item_cost=item_cost, enhance_lvl=enhance_lvl, gear_type=gear_type, name=name)
        else:
            gear = Classic_Gear(item_cost=item_cost, enhance_lvl=enhance_lvl, gear_type=gear_type, name=name,
                                mem_frag_cost=self.cost_meme)
            if str_gear_t.lower().find('weapon') > -1:
                gear.black_stone_cost = self.cost_bs_w
                gear.conc_black_stone_cost = self.cost_conc_w
            else:
                gear.black_stone_cost = self.cost_bs_a
                gear.conc_black_stone_cost = self.cost_conc_a
            if str_gear_t.lower().find('dura'):
                gear.fail_dura_cost = 4.0
            gear.mem_frag_cost = self.cost_meme
        return gear

    def edit_fs_item(self, old_gear, gear_obj):
        try:
            self.fail_stackers.remove(old_gear)
        except ValueError:
            pass
        self.fail_stackers.append(gear_obj)

    def edit_enhance_item(self, old_gear, gear_obj):
        try:
            self.enhance_me.remove(old_gear)
        except ValueError:
            pass
        self.enhance_me.append(gear_obj)

    def calcFS(self):
        fail_stackers = self.fail_stackers
        fs_exceptions = self.fs_exceptions
        fs_items = []
        fs_cost = []
        cum_fs_cost = []
        cum_fs_probs = []
        fs_probs = []

        map(lambda x: x.prep_calc(), fail_stackers)
        first_order = []
        second_order = []
        for item in fail_stackers:
            if item.fail_FS_accum() == 1:
                first_order.append(item)
            else:
                second_order.append(item)

        if len(first_order) < 1:
            raise Invalid_FS_Parameters('Must have at least one item below PRI on fail stacking list.')

        last_rate = 0
        cum_probability = 1
        for i in range(0, 121):
            if i in fs_exceptions:
                this_fs_item = fs_exceptions[i]
                this_fs_cost = this_fs_item.simulate_FS(i, last_rate)
            else:
                trys = map(lambda x: x.simulate_FS(i, last_rate), first_order)
                this_fs_idx = numpy.argmin(trys)
                this_fs_cost = trys[this_fs_idx]
                this_fs_item = first_order[this_fs_idx]
            this_cum_cost = last_rate + this_fs_cost
            this_prob = 1.0 - this_fs_item.gear_type.map[this_fs_item.get_enhance_lvl_idx()][i]
            cum_probability *= this_prob
            fs_probs.append(this_prob)
            cum_fs_probs.append(cum_probability)
            fs_items.append(this_fs_item)
            fs_cost.append(this_fs_cost)
            cum_fs_cost.append(this_cum_cost)
            last_rate = this_cum_cost

        last_rate = 0
        if len(second_order) > 0:
            for i in range(0, 121):
                this_fs_cost = fs_cost[i]
                if i not in fs_exceptions:
                    trys = map(lambda x: x.simulate_FS_complex(i, last_rate, cum_fs_cost), second_order)
                    this_fs_idx = numpy.argmin(trys)
                    this_fs_cost_cmp = trys[this_fs_idx]
                    this_fs_item = second_order[this_fs_idx]
                    if this_fs_cost_cmp < 0:
                        fs_items[i] = this_fs_item
                this_cum = last_rate + this_fs_cost
                last_rate = this_cum

        self.fs_items = fs_items
        self.fs_cost = fs_cost
        self.cum_fs_cost = cum_fs_cost
        self.cum_fs_probs = cum_fs_probs
        self.fs_probs = fs_probs
        self.fs_needs_update = False

    def calc_equip_costs(self):
        if self.fs_needs_update:
            self.calcFS()
        eq_c = map(lambda x: x.enhance_cost(self.cum_fs_cost), self.enhance_me)
        r_eq_c = map(lambda x: x.enhance_cost(self.cum_fs_cost), self.r_enhance_me)
        self.equipment_costs = eq_c
        self.r_equipment_costs = r_eq_c
        self.gear_cost_needs_update = False
        return eq_c

    def calcEnhances(self):
        if self.fs_needs_update:
            self.calcFS()
        if self.gear_cost_needs_update:
            self.calc_equip_costs()
        cum_fs_cost = self.cum_fs_cost
        fs_cost = self.fs_cost
        enhance_me = self.enhance_me

        zero_out = lambda x: x.enhance_lvl_cost(cum_fs_cost, fs_cost, total_cost=numpy.array([[0]*121]*len(x.gear_type.map)))
        balance_vec_fser = map(zero_out, self.fail_stackers)
        balance_vec_enh = map(lambda x: x.enhance_lvl_cost(cum_fs_cost, fs_cost), enhance_me)

        balance_vec_fser = numpy.array(balance_vec_fser)
        balance_vec_enh = numpy.array(balance_vec_enh)
        return balance_vec_fser, balance_vec_enh

    def to_json_obj(self):
        enhance_me = []
        fail_stackers = []
        r_fail_stackers = []
        r_enhance_me = []
        fs_exc = {}
        fail_stackers_count = {}
        for key, val in self.fs_exceptions.iteritems():
            fs_exc[key] = self.fail_stackers.index(val)
        for key, val in self.fail_stackers_counts.iteritems():
            try:
                fail_stackers_count[self.fail_stackers.index(key)] = val
            except ValueError:
                try:
                    fail_stackers_count[self.r_fail_stackers.index(key)] = [val]
                except ValueError:
                    print 'Fail stacking item has no target?'
        for enh in self.enhance_me:
            enhance_me.append(enh.to_json_obj())
        for fser in self.fail_stackers:
            fail_stackers.append(fser.to_json_obj())
        for enh in self.r_enhance_me:
            r_enhance_me.append(enh.to_json_obj())
        for fser in self.r_fail_stackers:
            r_fail_stackers.append(fser.to_json_obj())

        return {
            'cost_bs_a': self.cost_bs_a,
            'cost_bs_w': self.cost_bs_w,
            'cost_conc_a': self.cost_conc_a,
            'cost_conc_w': self.cost_conc_w,
            'cost_meme': self.cost_meme,
            'cost_cron': self.cost_cron,
            'cost_cleanse': self.cost_cleanse,
            'fail_stackers': fail_stackers,
            'enhance_me': enhance_me,
            'fs_exceptions': fs_exc,
            'r_fail_stackers': r_fail_stackers,
            'r_enhance_me': r_enhance_me,
            'fail_stackers_count': fail_stackers_count,
            '_version': Enhance_model.VERSION
        }

    def from_json_obj(self, json_obj):
        try:
            _fs_exceptions = json_obj['fs_exceptions']
        except KeyError:
            _fs_exceptions = {}
        try:
            _fail_stackers_count = json_obj['fail_stackers_count']
        except KeyError:
            _fail_stackers_count = {}
        for key, val in json_obj.iteritems():
            if key in ['fail_stackers', 'enhance_me', 'r_fail_stackers', 'r_enhance_me']:
                gear_list = []
                for gear in val:
                    gt = gear_types[gear['gear_type']]

                    dis_gear = self.generate_gear_obj(item_cost=0, enhance_lvl=gear['enhance_lvl'], gear_type=gt,
                                                      name='Default')
                    dis_gear.from_json_obj(gear)
                    gear_list.append(dis_gear)
                self.__dict__[key] = gear_list
            else:
                self.__dict__[key] = val
        fs_exceptions = {}
        fail_stackers = self.fail_stackers
        for key, val in _fs_exceptions.iteritems():
            fs_exceptions[int(key)] = fail_stackers[val]
        self.fs_exceptions = fs_exceptions

        fail_stackers_count = {}
        for key, val in _fail_stackers_count.iteritems():
            try:
                this_val = val[0]
                thisgear = self.r_fail_stackers[int(key)]
            except TypeError:
                this_val = val
                thisgear = self.fail_stackers[int(key)]
            fail_stackers_count[thisgear] = this_val
        self.fail_stackers_counts = fail_stackers_count

    def save_to_file(self, txt_path=None):
        if txt_path is None:
            txt_path = self.current_path
        else:
            self.current_path = txt_path
        json_obj = self.to_json()
        with open(txt_path, 'w') as f:
            f.write(json_obj)

    def load_from_file(self, txt_path):
        self.current_path = txt_path
        with open(txt_path, 'r') as f:
            self.from_json(f.read())

    def to_json(self):
        return json.dumps(self.to_json_obj(), indent=4)

    def from_json(self, json_str):
        self.from_json_obj(json.loads(json_str))
