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
    VERSION = "0.0.0.2"
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

        self.num_fs = 120

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
        self.invalidate_failstack_list()

    def add_equipment_item(self, this_gear):
        self.enhance_me.append(this_gear)
        self.invalidate_enahce_list()

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
        self.invalidate_enahce_list()

    def generate_gear_obj(self, item_cost=None, enhance_lvl=None, gear_type=None, name=None, sale_balance=None):
        str_gear_t = gear_type.name
        if str_gear_t.lower().find('accessor') > -1:
            gear = Smashable(item_cost=item_cost, enhance_lvl=enhance_lvl, gear_type=gear_type, name=name,
                             num_fs=self.num_fs, sale_balance=sale_balance)
        else:
            gear = Classic_Gear(item_cost=item_cost, enhance_lvl=enhance_lvl, gear_type=gear_type, name=name,
                                mem_frag_cost=self.cost_meme, num_fs=self.num_fs, sale_balance=sale_balance)
            if str_gear_t.lower().find('weapon') > -1:
                gear.black_stone_cost = self.cost_bs_w
                gear.conc_black_stone_cost = self.cost_conc_w
            else:
                gear.black_stone_cost = self.cost_bs_a
                gear.conc_black_stone_cost = self.cost_conc_a
            if str_gear_t.lower().find('dura'):
                gear.fail_dura_cost = 4.0
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
        fs_num = self.num_fs+1
        for i in range(0, fs_num):
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
            for i in range(0, fs_num):
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
        if len(eq_c) > 0:
            r_eq_c = map(lambda x: x.enhance_cost(self.cum_fs_cost), self.r_enhance_me)
            self.equipment_costs = eq_c
            self.r_equipment_costs = r_eq_c
            self.gear_cost_needs_update = False
            return eq_c
        else:
            raise Invalid_FS_Parameters('There is no equipment selected for enhancement.')

    def calcEnhances(self, count_fs=False):
        if self.fs_needs_update:
            self.calcFS()
        if self.gear_cost_needs_update:
            self.calc_equip_costs()
        cum_fs_cost = self.cum_fs_cost
        fs_cost = self.fs_cost
        enhance_me = self.enhance_me

        fs_len = self.num_fs+1


        # This is a bit hacky and confusing but we need a cost estimate on potential fs gain vs recovery loss on items that have no success gain
        # For fail-stacking items there should not be a total cost gained from success. It only gains value from fail stacks.
        zero_out = lambda x: x.enhance_lvl_cost(cum_fs_cost, fs_cost, total_cost=numpy.array([[0]*fs_len]*len(x.gear_type.map)))
        balance_vec_fser = map(zero_out, self.fail_stackers)
        balance_vec_enh = map(lambda x: x.enhance_lvl_cost(cum_fs_cost, fs_cost, count_fs=count_fs), enhance_me)

        balance_vec_fser = numpy.array(balance_vec_fser)
        balance_vec_enh = numpy.array(balance_vec_enh)

        #import numpy
        #print len(balance_vec_enh.T)


        def check_out_gains(balance_vec, gains_lookup_vec, gear_list):
            # Indexed by fs level contains the index of enhance_me for the minimal gear for that fail stack
            min_gear_map = map(lambda x: numpy.argmin(x), balance_vec.T)
            gearz = map(lambda x: gear_list[x], min_gear_map)
            # indexed by enhance_me returns the number of fail stacks gained by a failure
            gainz = map(lambda x: x.fs_gain(), gear_list)
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
            chances = numpy.array(map(lambda x: x.gear_type.map[x.get_enhance_lvl_idx()], gear_list)).T

            # The very last item has to be a self pointer only
            for i in range(1, fs_len+1):
                lookup_idx = fs_len - i
                #this_gear = gearz[lookup_idx]

                cost_emmend = numpy.zeros(len(balance_vec))
                for num_fs_gain, gear_idx_list in fs_dict.iteritems():
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
                    projected_gain = max(gear_pointed_cost, gain_cost)
                    #projected_gain = gain_cost
                    # All gear at this FS level and gain level have the same cost diff
                    cost_emmend[gear_idx_list] = projected_gain
                    #print cost_emmend

                fail_rate = 1 - chances[lookup_idx]

                balance_vec.T[lookup_idx] += numpy.multiply(fail_rate, cost_emmend)
                new_min_idx = numpy.argmin(balance_vec.T[lookup_idx])
                min_gear_map[lookup_idx] = new_min_idx
                gearz[lookup_idx] = gear_list[new_min_idx]

        check_out_gains(balance_vec_enh, balance_vec_enh, enhance_me)
        check_out_gains(balance_vec_fser, balance_vec_enh, self.fail_stackers)




        #zer = numpy.zeros(len(fs_cost)+1)
        #zer[1:] = fs_cost
        #print zer



        #print names

        return balance_vec_fser, balance_vec_enh

    def __getstate__(self):
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
            enhance_me.append(enh.__getstate__())
        for fser in self.fail_stackers:
            fail_stackers.append(fser.__getstate__())
        for enh in self.r_enhance_me:
            r_enhance_me.append(enh.__getstate__())
        for fser in self.r_fail_stackers:
            r_fail_stackers.append(fser.__getstate__())

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
            '_version': Enhance_model.VERSION,
            'num_fs':self.num_fs
        }

    def __setstate__(self, json_obj):
        try:
            _fs_exceptions = json_obj['fs_exceptions']
        except KeyError:
            _fs_exceptions = {}
        try:
            _fail_stackers_count = json_obj['fail_stackers_count']
        except KeyError:
            _fail_stackers_count = {}
        delay_round = {}
        for key, val in json_obj.iteritems():
            if key in ['fail_stackers', 'enhance_me', 'r_fail_stackers', 'r_enhance_me']:
                delay_round[key] = val
            else:
                self.__dict__[key] = val
        # want to make the sure memory fragment, black stone and other costs are loaded
        for key, val in delay_round.iteritems():
            gear_list = []
            for gear in val:
                gt = gear_types[gear['gear_type']]

                dis_gear = self.generate_gear_obj(item_cost=0, enhance_lvl=gear['enhance_lvl'], gear_type=gt,
                                                  name='Default')
                dis_gear.__setstate__(gear)
                gear_list.append(dis_gear)
            self.__dict__[key] = gear_list
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
        return json.dumps(self.__getstate__(), indent=4)

    def from_json(self, json_str):
        self.__setstate__(json.loads(json_str))
