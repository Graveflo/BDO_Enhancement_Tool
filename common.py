#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import json, os, numpy

relative_path_add = lambda str_path: sys.path.append(
    os.path.abspath(os.path.join(os.path.split(__file__)[0], str_path)))
import sys, os, numpy

import utilities as utils


def relative_path_covnert(x):
    """
    Takes a valid path: either relative to CWD or an absolute path and convert it to a relative path for this file.
    The relative path assumes that simply joining the returned path with the path of this file shall result in a valid
    path pointing to the origonal valid file object (x).
    :param x: str: path to a valid file object
    :return: str: a path to the file object relative to this file
    """
    return os.path.abspath(os.path.join(os.path.split(__file__)[0], x))


factorials = [1]

def factrl(n, ceil=500):
    if n < 0:
        raise ValueError('No factorial of negative numbers allowed.')
    if n > ceil:
        raise ValueError('Factorial is high. It might choke your PC. n={}'.format(n))
    lna = len(factorials)
    if lna > n:
        return factorials[n]
    else:
        for i in range(lna-1, n):
            factorials.append((i+1) * factorials[i])
        return factorials[-1]

def NchooseK(n, k):
    return factrl(n) / float(factrl(k) * factrl(n-k))

def binom_cdf_X_gte_x(oc, pool, prob):
    #prob = 1-prob
    cum_mas = 0
    for i in range(oc, pool+1):
        cum_mas += NchooseK(pool, i) * (prob**i) * ((1.0-prob)**(pool-i))
    return cum_mas

def spc_binom_cdf_X_gte_1(pool, prob):
    return 1-((1-prob)**pool)

binVf = numpy.vectorize(spc_binom_cdf_X_gte_1)


DEFAULT_SETTINGS_PATH = relative_path_covnert('settings.json')





FS_GAIN_PRI = 2
FS_GAIN_DUO = 3
FS_GAIN_TRI = 4
FS_GAIN_TET = 5
FS_GAIN_PEN = 6

FS_GAINS = [FS_GAIN_PRI,
            FS_GAIN_DUO,
            FS_GAIN_TRI,
            FS_GAIN_TET,
            FS_GAIN_PEN]

TXT_PATH_DATA = relative_path_covnert('Data')


class EnhanceSettings(utils.Settings):
    P_NUM_FS = 'num_fs'
    P_CRON_STONE_COST = 'cost_cron'
    P_CLEANSE_COST = 'cost_cleanse'
    P_ITEM_STORE = 'item_store'

    def init_settings(self, sets=None):
        this_vec = {
            EnhanceSettings.P_NUM_FS: 120,
            EnhanceSettings.P_CRON_STONE_COST: 2000000,
            EnhanceSettings.P_CLEANSE_COST: 100000,
            EnhanceSettings.P_ITEM_STORE: ItemStore()
        }
        if sets is not None:
            sets.update(this_vec)
            super(EnhanceSettings, self).init_settings(sets)
        else:
            super(EnhanceSettings, self).init_settings(this_vec)

    def __getstate__(self):
        class_obj = {}
        class_obj.update(super(EnhanceSettings, self).__getstate__())
        class_obj[self.P_ITEM_STORE] = self[self.P_ITEM_STORE].__getstate__()
        return class_obj

    def __setstate__(self, state):
        item_store = ItemStore()
        item_store.__setstate__(state[self.P_ITEM_STORE])
        state[self.P_ITEM_STORE] = item_store
        super(EnhanceSettings, self).__setstate__(state)


class ItemStore(object):
    """
    This may later be re-vamped to get items from database
    """
    P_BLACK_STONE_ARMOR = 'BLACK_STONE_ARMOR'
    P_BLACK_STONE_WEAPON = 'BLACK_STONE_WEAPON'
    P_CONC_ARMOR = 'CONC_ARMOR'
    P_CONC_WEAPON = 'CONC_WEAPON'
    P_MEMORY_FRAG = 'MEMORY_FRAG'

    def __init__(self):
        self.store_items = {
            ItemStore.P_BLACK_STONE_ARMOR: 220000,
            ItemStore.P_BLACK_STONE_WEAPON: 225000,
            ItemStore.P_CONC_ARMOR: 1470000,
            ItemStore.P_CONC_WEAPON: 2590000,
            ItemStore.P_MEMORY_FRAG: 1740000
        }

    def __getitem__(self, item):
        return self.store_items[item]

    def __setitem__(self, key, value):
        self.store_items[key] = value

    def iteritems(self):
        return self.store_items.iteritems()

    def get_cost(self, item):
        return self.__getitem__(item)

    def __getstate__(self):
        return {
            'items': self.store_items
        }

    def __setstate__(self, state):
        self.store_items = state['items']


class ge_gen(list):
    def __getitem__(self, idx):
        try:
            return super(ge_gen, self).__getitem__(idx)
        except IndexError:
            # Use super here to avoid recursive stack overflow and throw exception in the event of an empty list
            zero_val = super(ge_gen, self).__getitem__(0)
            tent_val = self.__getitem__(idx-1)
            if tent_val > 0.7:
                tent_val += zero_val * 0.02
            else:
                tent_val += zero_val * 0.1
            if tent_val > 0.9:
                tent_val = 0.9
            # append should work here because of recursion
            self.append(tent_val)
            return tent_val


class Gear_Type(object):
    def __init__(self, name=None):
        self.name = name
        self.lvl_map = {}
        self.idx_lvl_map = {}
        self.map = []
        self.instantiable = None

    def __str__(self):
        return json.dumps({
            'name' : self.name,
            'lvl_map': self.lvl_map,
            'map': self.map,
        }, indent=4)

    def load_txt(self, txt):
        load_d = json.loads(txt)
        for key, val in load_d.iteritems():
            self.__dict__[key] = val
        for key,val in self.lvl_map.iteritems():
            self.idx_lvl_map[val] = key
        if len(self.lvl_map) == 5:
            self.instantiable = Smashable
        else:
            self.instantiable = Classic_Gear
        map = self.map
        new_map = []
        for i in range(0,len(map)):
            new_map.append(ge_gen())
        #new_map = [ge_gen()] * len(map)
        for i,itm in enumerate(map):
            for val in itm:
                new_map[i].append(val)
        self.map = new_map

def enumerate_smashables(gl):
    if gl == 'PEN':
        return 5
    elif gl == 'TET':
        return 4
    elif gl == 'TRI':
        return 3
    elif gl == 'DUO':
        return 2
    elif gl == 'PRI':
        return 1
    else:
        raise Exception('wat')

def enumerate_gt_lvl(gl):
    try:
        int_enhance = int(gl)
        return int_enhance
    except ValueError:
        if gl == 'PEN':
            return 20
        elif gl == 'TET':
            return 19
        elif gl == 'TRI':
            return 18
        elif gl == 'DUO':
            return 17
        elif gl == 'PRI':
            return 16
        else:
            raise Exception('wat')

def enumerate_gt(g1):
    txt_c = g1.lower()
    if txt_c.find('white') > -1:
        return 0
    elif txt_c.find('green') > -1:
        return 1
    elif txt_c.find('blue') > -1:
        return 2
    elif txt_c.find('yellow') > -1 or txt_c.find('boss') > -1:
        return 3
    else:
        return -1

def gt_lvl_compare(gl1, gl2):
    return enumerate_gt_lvl(gl1) - enumerate_gt_lvl(gl2)

def dec_enhance_lvl(enhance):
    try:
        int_enhance = int(enhance)
        return str(int_enhance-1)
    except ValueError:
        if enhance == 'PEN':
            return 'TET'
        elif enhance == 'TET':
            return 'TRI'
        elif enhance == 'TRI':
            return 'DUO'
        elif enhance == 'DUO':
            return 'PRI'
        elif enhance == 'PRI':
            return '15'
        else:
            raise Exception('wat')

def generate_gear_obj(settings, base_item_cost=None, enhance_lvl=None, gear_type=None, name=None, sale_balance=None):
    if gear_type is None:
        gear_type = gear_types.items()[0][1]
    str_gear_t = gear_type.name
    gear = gear_type.instantiable(settings, base_item_cost=base_item_cost, enhance_lvl=enhance_lvl, gear_type=gear_type,
                     name=name, sale_balance=sale_balance)
    if str_gear_t.lower().find('dura'):
        gear.fail_dura_cost = 4.0
    return gear

class Gear(object):
    def __init__(self, settings, base_item_cost=None, enhance_lvl=None, gear_type=None, name=None, sale_balance=None,
                 fail_sale_balance=0):
        if sale_balance is None:
            sale_balance = 0
        self.settings = settings
        self.base_item_cost = base_item_cost  # Cost of procuring the equipment
        self.enhance_lvl = enhance_lvl
        self.gear_type = gear_type
        #self.fs_cost = []
        self.cost_vec = []  # Vectors of cost for each enhancement level and each fail stack level
        #self.tap_risk = []
        #self.cum_fs_cost = []
        self.lvl_success_rate = None  # Probabilities of success for the current level of enhancement
        self.repair_cost = None  # Cached repair cost for a normal fail, not a fail specific to enhancement level
        self.name = name
        self.sale_balance = sale_balance
        self.fail_sale_balance = fail_sale_balance

    def set_sale_balance(self, intbal):
        self.sale_balance = float(intbal)

    def prep_lvl_calc(self):
        gear_type = self.gear_type
        enhance_lvl = self.enhance_lvl
        self.lvl_success_rate = gear_type.map[gear_type.lvl_map[enhance_lvl]]

    def set_enhance_lvl(self, enhance_lvl):
        self.enhance_lvl = enhance_lvl
        gear_type = self.gear_type
        if gear_type is not None:
            self.lvl_success_rate = gear_type.map[gear_type.lvl_map[enhance_lvl]]
        #    self.fs_vec[self.num_fs]

    def set_gear_type(self, gear_type):
        self.gear_type = gear_type
        enhance_lvl = self.enhance_lvl
        if enhance_lvl is not None:
            # Just manually catch this exception
            self.lvl_success_rate = gear_type.map[gear_type.lvl_map[enhance_lvl]]

    def set_gear_params(self, gear_type, enhance_lvl):
        self.gear_type = gear_type
        self.set_enhance_lvl(enhance_lvl)

    #def __cmp__(self, other):
    #    other_lvl = other.enhance_lvl
    #    return gt_lvl_compare(self.enhance_lvl, other_lvl)

    def enhance_cost(self, cum_fs):
        """
        Enhance cost per level at each probability accounting for the cost of fail stacks absorbed upon success.

        Note:
        Although this function seems to be a super set of enhance_lvl_cost, this function is more expensive than
        enhance_lvl_cost and for this reason sometimes it is not used.
        :param cum_fs:
        :return:
        """
        raise NotImplementedError()

    def enhance_lvl_cost(self, cum_fs, fs_cost, total_cost=None, lvl=None):
        """
        Enhance cost at each probability accounting for the fail stacks absorbed upon success, the value gained from the
        successful enhancement upon success (in fail stack units) and the cost of the fail stacks gained upon failure
        :param cum_fs:
        :param fs_cost:
        :param total_cost:
        :param lvl:
        :return:
        """
        raise NotImplementedError()

    def __getstate__(self):
        return {
            'base_item_cost': self.base_item_cost,
            'enhance_lvl': self.enhance_lvl,
            'gear_type': self.gear_type.name,
            'name': self.name,
            'sale_balance': self.sale_balance,
            'fail_sale_balance': self.fail_sale_balance
        }

    def __setstate__(self, json_obj):
        # Do not call __init__ as it wil erase other class members from inherited classes
        self.fs_cost = []
        self.cost_vec = []
        #self.tap_risk = []
        self.lvl_success_rate = None
        self.repair_cost = None
        for key, val in json_obj.iteritems():
            if key == 'gear_type':
                self.gear_type = gear_types[val]
            else:
                self.__dict__[key] = val

    def simulate_FS(self, fs_count, last_cost):
        raise NotImplementedError()

    def get_enhance_lvl_idx(self):
        return self.gear_type.lvl_map[self.enhance_lvl]

    def set_cost(self, cost):
        self.base_item_cost = cost

    def to_json(self):
        return json.dumps(self.__getstate__(), indent=4)

    def calc_FS_enh_success(self):
        raise NotImplementedError()

    def fs_gain(self):
        raise NotImplementedError()

    def from_json(self, json_str):
        self.__setstate__(json.loads(json_str))

    def fail_FS_accum(self):
        return 1

    #def calc_repair_cost(self):
    #    raise NotImplementedError()

    def calc_lvl_repair_cost(self):
        raise NotImplementedError()

    def calc_lvl_flat_cost(self):
        raise NotImplementedError()

    def upgrade(self):
        this_dx = self.get_enhance_lvl_idx()
        new_idx = self.gear_type.idx_lvl_map[this_dx + 1]
        self.set_enhance_lvl(new_idx)

    def downgrade(self):
        this_dx = self.get_enhance_lvl_idx()
        new_idx = self.gear_type.idx_lvl_map[this_dx - 1]
        self.set_enhance_lvl(new_idx)


class Classic_Gear(Gear):
    TYPE_WEAPON = 0
    TYPE_ARMOR = 1

    def __init__(self, settings, base_item_cost=None, enhance_lvl=None, gear_type=None, name=None, fail_dura_cost=5.0,
                 sale_balance=None, fail_sale_balance=0):
        super(Classic_Gear, self).__init__(settings, base_item_cost=base_item_cost, enhance_lvl=enhance_lvl, gear_type=gear_type,
                                           name=name, sale_balance=sale_balance, fail_sale_balance=fail_sale_balance)
        self.fail_dura_cost = fail_dura_cost
        self.using_memfrags = False
        self.repair_cost = None

    def set_cost(self, cost):
        super(Classic_Gear, self).set_cost(cost)
        self.calc_repair_cost()

    def prep_lvl_calc(self):
        #self.calc_FS_costs()
        self.calc_repair_cost()
        super(Classic_Gear, self).prep_lvl_calc()

    def calc_repair_cost(self):
        fail_dura_cost = self.fail_dura_cost
        mem_frag_cost = self.settings[EnhanceSettings.P_ITEM_STORE].get_cost(ItemStore.P_MEMORY_FRAG)

        tentative_cost = self.base_item_cost * (fail_dura_cost / 10.00)
        memfrag_cost = mem_frag_cost * fail_dura_cost
        if memfrag_cost < tentative_cost:
            self.using_memfrags = True
            self.repair_cost = memfrag_cost
            return memfrag_cost
        else:
            self.using_memfrags = False
            self.repair_cost = tentative_cost
            return tentative_cost

    def gear_type_code(self):
        if self.gear_type.name.lower().find('weapon') > -1:
            return self.TYPE_WEAPON
        else:
            return self.TYPE_ARMOR

    def get_blackstone_costs(self):
        if self.gear_type_code() == self.TYPE_ARMOR:
            bs_cost = self.settings[EnhanceSettings.P_ITEM_STORE].get_cost(ItemStore.P_BLACK_STONE_ARMOR)
            conc_cost = self.settings[EnhanceSettings.P_ITEM_STORE].get_cost(ItemStore.P_CONC_ARMOR)
        else:
            bs_cost = self.settings[EnhanceSettings.P_ITEM_STORE].get_cost(ItemStore.P_BLACK_STONE_WEAPON)
            conc_cost = self.settings[EnhanceSettings.P_ITEM_STORE].get_cost(ItemStore.P_CONC_WEAPON)
        return bs_cost, conc_cost

    def calc_enhance_vectors(self):
        bs_cost, conc_cost = self.get_blackstone_costs()

        num_enhance_lvls = len(self.gear_type.map)
        conc_start = self.gear_type.lvl_map['PRI']
        fail_repair_cost_nom = numpy.tile(self.calc_repair_cost(), num_enhance_lvls)
        black_stone_costs = numpy.array([bs_cost] * num_enhance_lvls)
        for i in range(conc_start, num_enhance_lvls):
            black_stone_costs[i] = conc_cost
            # Using concentrated black stones reduces twice the max durability upon failure
            fail_repair_cost_nom[i] *= 2
        return black_stone_costs, fail_repair_cost_nom

    def calc_lvl_flat_cost(self):
        this_lvl = self.get_enhance_lvl_idx()
        conc_start = self.gear_type.lvl_map['PRI']
        bs_cost, conc_cost = self.get_blackstone_costs()

        if this_lvl < conc_start:
            return bs_cost
        else:
            return conc_cost

    def calc_lvl_repair_cost(self, lvl_costs=None):
        if lvl_costs is None:
            lvl_costs = [min(x) for x in self.cost_vec]
        fail_repiar_cost_nom = self.repair_cost
        this_lvl = self.get_enhance_lvl_idx()
        backtrack_start = this_lvl - self.gear_type.lvl_map['PRI']
        fail_balance = fail_repiar_cost_nom
        if this_lvl >= backtrack_start:
            try:
                fail_balance = fail_repiar_cost_nom * 2
            except TypeError:
                # fail repair cost has not been set and is None
                fail_repiar_cost_nom = self.calc_lvl_repair_cost()
                fail_balance = fail_repiar_cost_nom * 2
        backtrack_start = self.gear_type.lvl_map['TRI']
        if this_lvl >= backtrack_start:
            fail_balance += lvl_costs[this_lvl - 1]
        return fail_balance

    def fs_gain(self):
        lvl = self.enhance_lvl
        this_lvl = self.gear_type.lvl_map[lvl]
        backtrack_start = this_lvl - self.gear_type.lvl_map['15']
        if backtrack_start > 0:
            return backtrack_start + 1
        else:
            return 1

    def enhance_lvl_cost(self, cum_fs, fs_cost, total_cost=None, lvl=None, count_fs=True):
        self.prep_lvl_calc()  # This is for repair cost calculation
        if lvl is None:
            lvl = self.enhance_lvl
        if total_cost is None:
            total_cost = self.cost_vec

            #print len(self.tap_risk)
            #this_lvl = self.gear_type.lvl_map[lvl]
            #this_risk = self.tap_risk[this_lvl]
            #cont_risk = cum_fs - this_risk
            #print self.name
            idx_ = -1
            #for i in range(0, 121):
            #    if cont_risk[i] >= 0:
            #        idx_ = i
            #        break
            #print idx_
            #print cont_risk
        cum_fs = numpy.roll(cum_fs, 1)
        cum_fs[0] = 0
        this_lvl = self.gear_type.lvl_map[lvl]
        this_total_cost = min(total_cost[this_lvl])
        success_rates = numpy.array(self.gear_type.map[this_lvl])



        #fs_meaning = numpy.array([x for x in [i**2/float(121**2) for i in range(0, 121)].__reversed__()])


        fail_rate = numpy.ones(success_rates.shape) - success_rates


        #next_fs_cost = numpy.copy(fs_cost)

        #conc_start = self.gear_type.lvl_map['PRI']

        fail_repiar_cost_nom = self.calc_repair_cost()
        backtrack_start = this_lvl - self.gear_type.lvl_map['PRI']
        if this_lvl >= backtrack_start:
            fail_repiar_cost_nom *= 2

        # To balance the loss of failstack expense the success should account for the level increase in terms of fail stack cost
        if count_fs is False:
            cum_fs = numpy.zeros(len(cum_fs))
        # I think losing the fail stack value here is double counting since they have already been paid for. Risk comes from repair here
        success_balance = cum_fs - this_total_cost

        success_cost = success_rates * success_balance

        # fail_stack_gains = next_fs_cost
        #
        # # This is effectively how many bonus fail stacks this gear is away from PRI
        # backtrack_start = this_lvl - self.gear_type.lvl_map['PRI']
        # shifty = numpy.copy(next_fs_cost)
        # # The amount of fail stacks to sum is the same but their cost is different depending on their position
        # for j in range(0, backtrack_start + 1):
        #     # Rolls to the left so when added it should be f(x)+f(x+1)
        #     shifty = numpy.roll(shifty, -1)
        #     # This preserves max value
        #     shifty[-1] = next_fs_cost[-1]
        #     fail_stack_gains += shifty

        #fail_balance = fail_repiar_cost_nom - fail_stack_gains
        fail_balance = fail_repiar_cost_nom

        # Downgrade cost
        backtrack_start = self.gear_type.lvl_map['TRI']
        if this_lvl >= backtrack_start:
            fail_balance += min(total_cost[this_lvl-1])

        fail_cost = fail_rate * fail_balance
        tap_total_cost = success_cost + fail_cost + self.calc_lvl_flat_cost()

        return tap_total_cost

    def enhance_cost(self, cum_fs):
        cum_fs = numpy.roll(cum_fs, 1)
        cum_fs[0] = 0
        num_fs = self.settings[EnhanceSettings.P_NUM_FS]
        for glmap in self.gear_type.map:
            foo = glmap[num_fs]
        p_success = numpy.array(self.gear_type.map)
        p_fail = 1-p_success

        avg_num_attempts = numpy.divide(numpy.ones(p_success.shape), p_success)

        cum_fs_tile = numpy.tile(cum_fs, (len(p_success), 1))

        black_stone_costs, fail_repair_cost_nom = self.calc_enhance_vectors()

        # avg_num_fails is distinct from avg_num_attempts
        success_cost = cum_fs_tile
        fail_cost = fail_repair_cost_nom[:, numpy.newaxis]
        opportunity_cost = (p_fail * fail_cost) + (p_success*success_cost) + black_stone_costs[:, numpy.newaxis]
        total_cost = avg_num_attempts * opportunity_cost
        #total_cost = fails_cost + cum_fs_tile + (black_stone_costs[:, numpy.newaxis] * avg_num_attempts)

        #restore_cost = numpy.subtract(numpy.ones(this_fail_map.shape), this_fail_map)
        #restore_cost *= black_stone_costs[:, numpy.newaxis] + fail_repair_cost_nom[:, numpy.newaxis]
        #print black_stone_costs[:, numpy.newaxis] + fail_repair_cost_nom[:, numpy.newaxis]

        backtrack_start = self.gear_type.lvl_map['TRI']
        prev_cost = numpy.min(total_cost[backtrack_start-1])
        for i in range(0, 3):
            this_pos = backtrack_start + i
            new_avg_attempts = avg_num_attempts[this_pos]

            new_success_cost = cum_fs
            new_fail_cost = fail_repair_cost_nom[this_pos] + prev_cost
            new_opportunity_cost = (p_fail[this_pos] * new_fail_cost) + (p_success[this_pos] * new_success_cost) + black_stone_costs[this_pos]
            this_cost = new_avg_attempts * new_opportunity_cost
            total_cost[this_pos] = this_cost
            prev_cost = numpy.min(this_cost)

            #total_cost[this_pos] = (new_num_fails * new_fail_cost) + (black_stone_costs[this_pos] * new_avg_attempts) + cum_fs

            # This is unused testing:
            # This is just the cost of repairing at the minimum total cost level of fail stacks
            #prev_r_cost = restore_cost[this_pos-1][prev_cost_idx]
            #new_r_fail_cost = fail_repair_cost_nom[this_pos] + prev_r_cost
            #restore_cost[this_pos] = (new_num_fails * new_r_fail_cost) + black_stone_costs[this_pos]

        #self.tap_risk = restore_cost
        #print restore_cost

        self.cost_vec = numpy.array(total_cost)
        self.cost_vec.flags.writeable = False

        return total_cost

    def calc_FS_enh_success(self):
        if self.enhance_lvl == '15':
            return self.settings[EnhanceSettings.P_CLEANSE_COST]
        else:
            return -self.sale_balance


    def simulate_FS(self, fs_count, last_cost):
        fs_vec = self.lvl_success_rate
        repair_cost = self.repair_cost
        if repair_cost is None:
            self.calc_repair_cost()
            repair_cost = self.repair_cost
        #enhance_lvl = self.enhance_lvl
        flat_cost = self.calc_lvl_flat_cost()

        suc_rate = fs_vec[fs_count]
        fail_rate = 1.0 - suc_rate
        # print fail_rate
        fail_cost = repair_cost + max(0, self.fail_sale_balance)
        success_cost =  max(0, last_cost +self.calc_FS_enh_success())

        opportunity_cost = flat_cost + (suc_rate * success_cost) + (fail_rate * fail_cost)
        avg_num_opportunities = numpy.divide(1.0, fail_rate)
        return (avg_num_opportunities * opportunity_cost) / float(self.fs_gain())

    def fail_FS_accum(self):
        ehl = self.enhance_lvl
        if ehl == 'PRI':
            return FS_GAIN_PRI
        if ehl == 'DUO':
            return FS_GAIN_DUO
        if ehl == 'TRI':
            return FS_GAIN_TRI
        if ehl == 'TET':
            return FS_GAIN_TET
        if ehl == 'PEN':
            return FS_GAIN_PEN
        else:
            return 1

    def clone_down(self):
        pass

    def __getstate__(self):
        this_dict = super(Classic_Gear, self).__getstate__()
        this_dict['fail_dura_cost'] = self.fail_dura_cost
        return this_dict


class Smashable(Gear):

    def __init__(self, settings, base_item_cost=None, enhance_lvl=None, gear_type=None, name=None, sale_balance=None,
                 fail_sale_balance=None):
        if fail_sale_balance is None:
            # this is for PRI
            fail_sale_balance = base_item_cost
        super(Smashable, self).__init__(settings, base_item_cost=base_item_cost, enhance_lvl=enhance_lvl, gear_type=gear_type,
                                        name=name, sale_balance=sale_balance, fail_sale_balance=fail_sale_balance)

    def calc_FS_enh_success(self):
        # When an enhancement succeeded with the goal of selling the product the net gain is the sale balance minus
        # the bas material needed to perform the enhancement
        return -(self.sale_balance - self.base_item_cost)

    def calc_lvl_repair_cost(self):
        cost_vec = self.cost_vec
        lvl_indx = self.get_enhance_lvl_idx()
        if lvl_indx == 0:
            return self.base_item_cost
        else:
            try:
                return numpy.sum(cost_vec[lvl_indx-1])
            except IndexError:
                self.prep_lvl_calc()
                return numpy.sum(cost_vec[lvl_indx-1])

    def calc_lvl_flat_cost(self):
        return self.base_item_cost

    def enhance_lvl_cost(self, cum_fs, fs_cost, total_cost=None, lvl=None, count_fs=True):
        if lvl is None:
            lvl = self.enhance_lvl
        if total_cost is None:
            total_cost = self.cost_vec
        if count_fs is False:
            cum_fs = numpy.zeros(len(cum_fs))
        this_lvl = self.gear_type.lvl_map[lvl]
        this_total_cost = min(total_cost[this_lvl])

        success_rates = numpy.array(self.gear_type.map[this_lvl])

        fail_rates = numpy.ones(success_rates.shape) - success_rates

        #next_fs_cost = numpy.roll(fs_cost, -1)
        #next_fs_cost[-1] = fs_cost[-1]
        cum_fs = numpy.roll(cum_fs, 1)
        cum_fs[0] = 0

        success_balance = cum_fs - this_total_cost

        fail_balance = self.calc_lvl_repair_cost() + self.calc_lvl_flat_cost() - numpy.array(fs_cost)

        success_cost = success_rates * success_balance
        fail_cost = fail_rates * fail_balance
        tap_total_cost = success_cost + fail_cost

        return tap_total_cost

    def enhance_cost(self, cum_fs):
        # Roll fail stack costs so that an attempt at 0 fail stacks costs no money
        cum_fs = numpy.roll(cum_fs, 1)
        cum_fs[0] = 0
        num_fs = self.settings[EnhanceSettings.P_NUM_FS]
        for glmap in self.gear_type.map:
            # loads the cache from the generator
            foo = glmap[num_fs]
        fail_map = numpy.array(self.gear_type.map)
        num_enhance_lvls = len(fail_map)

        num_attempts = numpy.divide(numpy.ones(fail_map.shape), fail_map)
        cum_fs_tile = numpy.tile(cum_fs, (num_enhance_lvls, 1))

        fail_cost = self.base_item_cost * 2  # two of a kind needed for a PRI accessory
        # Success consumes a fail stack and
        success_cost = self.base_item_cost + cum_fs_tile
        opportunity_cost = (fail_map * success_cost) + ((1-fail_map)*fail_cost)
        total_cost = num_attempts * opportunity_cost

        for i in range(1, num_enhance_lvls):
            prev_cost = numpy.min(total_cost[i - 1])
            this_num_attempts = num_attempts[i]
            new_fail_cost = self.base_item_cost + prev_cost
            this_opportunity_cost = ((fail_map[i] * success_cost[i]) + [i]) + ((1-fail_map[i]) * new_fail_cost)
            total_cost[i] = this_num_attempts * this_opportunity_cost

        self.cost_vec = total_cost
        return total_cost

    def simulate_FS(self, fs_count, last_cost):
        fs_vec = self.lvl_success_rate
        enhance_lvl_idx = self.get_enhance_lvl_idx()
        #fail_loss = numpy.min(self.cost_vec[enhance_lvl_idx])
        fail_loss = self.base_item_cost + self.fail_sale_balance

        suc_rate = fs_vec[fs_count]
        fail_rate = 1.0 - suc_rate
        fail_cost = fail_loss + max(0, self.fail_sale_balance)
        success_cost = last_cost + max(0, self.calc_FS_enh_success())
        oppertunity_cost = (suc_rate * success_cost) + (fail_rate * fail_cost)
        avg_num_oppertunities = numpy.divide(1.0, fail_rate)
        # Cost of GAINING the fail stack, not just attempting it
        return avg_num_oppertunities * oppertunity_cost

    def fs_gain(self):
        return 1

    def clone_down(self):
        pass

    def __getstate__(self):
        this_dict = super(Smashable, self).__getstate__()
        return this_dict


files = os.listdir(TXT_PATH_DATA)
gear_types = {}

for feel in files:
    if feel.endswith('.json'):
        pash = os.path.join(TXT_PATH_DATA, feel)
        name = feel[:feel.find('.')]
        gt = Gear_Type(name=name)
        with open(pash, 'r') as f:
            gt.load_txt(f.read())
        gear_types[name] = gt
