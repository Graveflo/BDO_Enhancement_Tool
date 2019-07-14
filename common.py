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

binVf = numpy.vectorize(lambda x,y: binom_cdf(1,x,y))

DEFAULT_SETTINGS_PATH = relative_path_covnert('settings.json')

BLACK_STONE_WEAPON_COST = 225000
BLACK_STONE_ARMOR_COST = 220000

CONC_WEAPON_COST = 2590000
CONC_ARMOR_COST = 1470000

MEMORY_FRAG_COST = 1740000

CRON_STONE_COST = 2000000

CLEANSE_COST = 100000

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

TXT_PATH_DATA = relative_path_covnert('DATA')


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
        map = self.map
        new_map = []
        for i in range(0,len(map)):
            new_map.append(ge_gen())
        #new_map = [ge_gen()] * len(map)
        for i,itm in enumerate(map):
            for val in itm:
                new_map[i].append(val)
        self.map = new_map

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


class Gear(object):
    def __init__(self, item_cost=None, enhance_lvl=None, gear_type=None, name=None, num_fs=None, sale_balance=None):
        if sale_balance is None:
            sale_balance = 0
        self.cost = item_cost
        self.enhance_lvl = enhance_lvl
        self.gear_type = gear_type
        self.fs_cost = []
        self.cost_vec = []
        self.tap_risk = []
        #self.cum_fs_cost = []
        self.fs_vec = None
        self.repair_cost = None
        self.name = name
        self.sale_balance = sale_balance
        self.num_fs = num_fs


    def set_sale_balance(self, intbal):
        self.sale_balance = float(intbal)

    def prep_calc(self):
        gear_type = self.gear_type
        enhance_lvl = self.enhance_lvl
        self.fs_vec = gear_type.map[gear_type.lvl_map[enhance_lvl]]

    def set_enhance_lvl(self, enhance_lvl):
        self.enhance_lvl = enhance_lvl
        gear_type = self.gear_type
        if gear_type is not None:
            self.fs_vec = gear_type.map[gear_type.lvl_map[enhance_lvl]]
            self.fs_vec[self.num_fs]

    def set_gear_type(self, gear_type):
        self.gear_type = gear_type
        enhance_lvl = self.enhance_lvl
        if enhance_lvl is not None:
            # Just manually catch this exception
            self.fs_vec = gear_type.map[gear_type.lvl_map[enhance_lvl]]

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
            'cost': self.cost,
            'enhance_lvl': self.enhance_lvl,
            'gear_type': self.gear_type.name,
            'name': self.name,
            'sale_balance': self.sale_balance
        }

    def __setstate__(self, json_obj):
        # Do not call __init__ as it wil erase other class members from inherited classes
        self.fs_cost = []
        self.cost_vec = []
        self.tap_risk = []
        self.fs_vec = None
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
        self.cost = cost

    def to_json(self):
        return json.dumps(self.__getstate__(), indent=4)

    def calc_FS_fail(self):
        raise NotImplementedError()

    def fs_gain(self):
        raise NotImplementedError()

    def from_json(self, json_str):
        self.__setstate__(json.loads(json_str))

    def fail_FS_accum(self):
        return 1

    def upgrade(self):
        this_dx = self.get_enhance_lvl_idx()
        new_idx = self.gear_type.idx_lvl_map[this_dx + 1]
        self.set_enhance_lvl(new_idx)

    def downgrade(self):
        this_dx = self.get_enhance_lvl_idx()
        new_idx = self.gear_type.idx_lvl_map[this_dx - 1]
        self.set_enhance_lvl(new_idx)


class Classic_Gear(Gear):

    def __init__(self, item_cost=None, enhance_lvl=None, gear_type=None, name=None, fail_dura_cost=5.0,
                 black_stone_cost=None, conc_black_stone_cost=None, mem_frag_cost=None, num_fs=None, sale_balance=None):
        super(Classic_Gear, self).__init__(item_cost, enhance_lvl, gear_type, name=name, num_fs=num_fs,
                                           sale_balance=sale_balance)
        self.black_stone_cost = black_stone_cost
        self.conc_black_stone_cost = conc_black_stone_cost
        self.fail_dura_cost = fail_dura_cost
        self.using_memfrags = False
        self.mem_frag_cost = mem_frag_cost
        self.repair_cost = None

    def set_cost(self, cost):
        super(Classic_Gear, self).set_cost(cost)
        self.calc_repair_cost()

    def prep_calc(self):
        #self.calc_FS_costs()
        self.calc_repair_cost()
        super(Classic_Gear, self).prep_calc()

    def calc_repair_cost(self):
        fail_dura_cost = self.fail_dura_cost

        tentative_cost = self.cost * (fail_dura_cost / 10.00)
        memfrag_cost = self.mem_frag_cost * fail_dura_cost
        if memfrag_cost < tentative_cost:
            self.using_memfrags = True
            self.repair_cost = memfrag_cost
            return memfrag_cost
        else:
            self.using_memfrags = False
            self.repair_cost = tentative_cost
            return tentative_cost

    def fs_gain(self):
        lvl = self.enhance_lvl
        this_lvl = self.gear_type.lvl_map[lvl]
        backtrack_start = this_lvl - self.gear_type.lvl_map['15']
        if backtrack_start > 0:
            return backtrack_start + 1
        else:
            return 1

    def enhance_lvl_cost(self, cum_fs, fs_cost, total_cost=None, lvl=None):
        self.prep_calc()
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



        fs_meaning = numpy.array([x for x in [i**2/float(121**2) for i in range(0, 121)].__reversed__()])


        fail_rate = numpy.ones(success_rates.shape) - success_rates


        next_fs_cost = numpy.copy(fs_cost)

        conc_start = self.gear_type.lvl_map['PRI']
        if this_lvl < conc_start:
            black_stone_cost = self.black_stone_cost
        else:
            black_stone_cost = self.conc_black_stone_cost

        fail_repiar_cost_nom = self.calc_repair_cost()
        backtrack_start = this_lvl - self.gear_type.lvl_map['PRI']
        if this_lvl >= backtrack_start:
            fail_repiar_cost_nom *= 2

        # To balance the loss of failstack expense the success should account for the level increase in terms of fail stack cost
        success_balance = cum_fs - this_total_cost

        success_cost = success_rates * success_balance

        fail_stack_gains = next_fs_cost

        backtrack_start = this_lvl - self.gear_type.lvl_map['PRI']
        shifty = next_fs_cost
        for j in range(0, backtrack_start + 1):
            shifty = numpy.roll(shifty, -1)
            shifty[-1] = next_fs_cost[-1]
            fail_stack_gains += shifty

        fail_balance = fail_repiar_cost_nom - fail_stack_gains

        backtrack_start = self.gear_type.lvl_map['TRI']
        if this_lvl >= backtrack_start:
            fail_balance += min(total_cost[this_lvl-1])

        fail_cost = fail_rate * fail_balance
        tap_total_cost = success_cost + fail_cost + black_stone_cost

        return tap_total_cost

    def enhance_cost(self, cum_fs):
        cum_fs = numpy.roll(cum_fs, 1)
        cum_fs[0] = 0
        num_fs = self.num_fs
        for glmap in self.gear_type.map:
            glmap[num_fs]
        this_fail_map = numpy.array(self.gear_type.map)

        avg_num_attempts = numpy.divide(numpy.ones(this_fail_map.shape), this_fail_map)
        avg_num_fails = avg_num_attempts - 1

        cum_fs_tile = numpy.tile(cum_fs, (len(this_fail_map), 1))

        conc_start = self.gear_type.lvl_map['PRI']
        fail_repair_cost_nom = numpy.tile(self.calc_repair_cost(), len(avg_num_fails))

        black_stone_costs = numpy.array([self.black_stone_cost] * len(this_fail_map))
        for i in range(conc_start, len(this_fail_map)):
            black_stone_costs[i] = self.conc_black_stone_cost
            # Using concentrated black stones reduces twice the max durability upon failure
            fail_repair_cost_nom[i] *= 2


        # avg_num_fails is distinct from avg_num_attempts
        fails_cost = avg_num_fails * fail_repair_cost_nom[:, numpy.newaxis]
        total_cost = fails_cost + cum_fs_tile + (black_stone_costs[:, numpy.newaxis] * avg_num_attempts)

        restore_cost = numpy.subtract(numpy.ones(this_fail_map.shape), this_fail_map)
        restore_cost *= black_stone_costs[:, numpy.newaxis] + fail_repair_cost_nom[:, numpy.newaxis]
        #print black_stone_costs[:, numpy.newaxis] + fail_repair_cost_nom[:, numpy.newaxis]

        backtrack_start = self.gear_type.lvl_map['TRI']

        for i in range(0, 3):
            this_pos = backtrack_start + i
            prev_cost_idx = numpy.argmin(total_cost[this_pos - 1])
            prev_cost = total_cost[this_pos-1][prev_cost_idx]
            #new_fail_map = numpy.array(self.gear_type.map[this_pos])
            #new_avg_attempts = numpy.divide(numpy.ones(len(new_fail_map)), new_fail_map)
            new_avg_attempts = avg_num_attempts[this_pos]
            new_num_fails = new_avg_attempts - 1
            new_fail_cost = fail_repair_cost_nom[this_pos] + prev_cost

            total_cost[this_pos] = (new_num_fails * new_fail_cost) + (black_stone_costs[this_pos] * new_avg_attempts) + cum_fs

            # This is unused testing:
            # This is just the cost of repairing at the minimum total cost level of fail stacks
            prev_r_cost = restore_cost[this_pos-1][prev_cost_idx]
            new_r_fail_cost = fail_repair_cost_nom[this_pos] + prev_r_cost
            restore_cost[this_pos] = (new_num_fails * new_r_fail_cost) + black_stone_costs[this_pos]

        self.tap_risk = restore_cost
        #print restore_cost

        self.cost_vec = numpy.array(total_cost)
        self.cost_vec.flags.writeable = False

        return total_cost

    def calc_FS_fail(self):
        if self.enhance_lvl == '15':
            return CLEANSE_COST
        else:
            return -self.sale_balance

    def simulate_FS_complex(self, fs_count, last_cost, cum_fs):
        fs_vec = self.fs_vec
        repair_cost = self.repair_cost
        if repair_cost is None:
            self.calc_repair_cost()
            repair_cost = self.repair_cost
        enhance_lvl = self.enhance_lvl
        fs_gain = self.fail_FS_accum()
        cum_fs = numpy.roll(cum_fs, 1)
        cum_fs[0] = 0

        fs_upt = fs_count + fs_gain
        if len(cum_fs) <= fs_upt:
            fs_upt = len(cum_fs) - 1
        cum_fail_gain = cum_fs[fs_upt] - cum_fs[min(fs_count+1,len(cum_fs)-1)]

        try:
            int(enhance_lvl)
            black_stone_cost = self.black_stone_cost
        except ValueError:
            black_stone_cost = self.conc_black_stone_cost

        suc_rate = fs_vec[fs_count]
        fail_rate = 1.0 - suc_rate
        # print fail_rate
        fail_cost = repair_cost - cum_fail_gain
        success_cost = last_cost + self.calc_FS_fail()
        oppertunity_cost = black_stone_cost + (suc_rate * success_cost) + (fail_rate * fail_cost)
        avg_num_oppertunities = numpy.divide(1.0, fail_rate)
        return avg_num_oppertunities * oppertunity_cost

    def simulate_FS(self, fs_count, last_cost):
        fs_vec = self.fs_vec
        repair_cost = self.repair_cost
        if repair_cost is None:
            self.calc_repair_cost()
            repair_cost = self.repair_cost
        enhance_lvl = self.enhance_lvl
        try:
            int(enhance_lvl)
            black_stone_cost = self.black_stone_cost
        except ValueError:
            black_stone_cost = self.conc_black_stone_cost

        suc_rate = fs_vec[fs_count]
        fail_rate = 1.0 - suc_rate
        # print fail_rate
        fail_cost = repair_cost
        success_cost = last_cost + self.calc_FS_fail()

        oppertunity_cost = black_stone_cost + (suc_rate * success_cost) + (fail_rate * fail_cost)
        avg_num_oppertunities = numpy.divide(1.0, fail_rate)
        return avg_num_oppertunities * oppertunity_cost

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

    def __init__(self, item_cost=None, enhance_lvl=None, gear_type=None, name=None, num_fs=None, sale_balance=None):
        super(Smashable, self).__init__(item_cost, enhance_lvl, gear_type, name=name, num_fs=num_fs,
                                        sale_balance=sale_balance)

    def calc_FS_fail(self):
        # When an enhancement succeeded with the goal of selling the product the net gain is the sale balance minus
        # the bas material needed to perform the enhancement
        return -(self.sale_balance - self.cost)

    def prep_calc(self):
        #self.calc_FS_costs()
        self.enhance_cost()
        super(Smashable, self).prep_calc()

    def enhance_lvl_cost(self, cum_fs, fs_cost, total_cost=None, lvl=None):
        if lvl is None:
            lvl = self.enhance_lvl
        if total_cost is None:
            total_cost = self.cost_vec
        this_lvl = self.gear_type.lvl_map[lvl]
        this_total_cost = min(total_cost[this_lvl])
        success_rates = numpy.array(self.gear_type.map[this_lvl])

        fail_rates = numpy.ones(success_rates.shape) - success_rates

        #next_fs_cost = numpy.roll(fs_cost, -1)
        #next_fs_cost[-1] = fs_cost[-1]
        cum_fs = numpy.roll(cum_fs, 1)
        cum_fs[0] = 0

        success_balance = cum_fs - this_total_cost

        success_cost = success_rates * success_balance
        fail_balance = numpy.subtract(this_total_cost, fs_cost)


        backtrack_start = self.gear_type.lvl_map['DUO']
        if this_lvl >= backtrack_start:
            fail_balance += total_cost[this_lvl-1][:]

        fail_cost = fail_rates * fail_balance
        tap_total_cost = success_cost + fail_cost

        return tap_total_cost

    def enhance_cost(self, cum_fs):
        # Roll fail stack costs so that an attempt at 0 fail stacks costs no money
        cum_fs = numpy.roll(cum_fs, 1)
        cum_fs[0] = 0
        num_fs = self.num_fs
        for glmap in self.gear_type.map:
            # loads the cache from the generator
            glmap[num_fs]
        this_fail_map = numpy.array(self.gear_type.map)
        num_enhance_lvls = len(this_fail_map)

        this_num_fails = numpy.divide(numpy.ones(this_fail_map.shape), this_fail_map) - 1
        cum_fs_tile = numpy.tile(cum_fs, (num_enhance_lvls, 1))

        PRI_repair_cost = self.cost * 2  # two of a kind needed for a PRI accessory
        fails_cost = this_num_fails * PRI_repair_cost

        # The material cost is added to the cost of a fail stack
        total_cost = fails_cost + cum_fs_tile

        for i in range(1, num_enhance_lvls):
            prev_cost = numpy.min(total_cost[i - 1])
            this_level_num_fails = this_num_fails[i]
            new_fail_cost = self.cost + prev_cost
            total_cost[i] = (this_level_num_fails * new_fail_cost) + cum_fs

        self.cost_vec = total_cost
        return total_cost

    def simulate_FS(self, fs_count, last_cost):
        fs_vec = self.fs_vec
        fail_loss = numpy.min(self.cost_vec[self.enhance_lvl])

        suc_rate = fs_vec[fs_count]
        fail_rate = 1.0 - suc_rate
        fail_cost = fail_loss
        success_cost = last_cost + self.calc_FS_fail()
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

