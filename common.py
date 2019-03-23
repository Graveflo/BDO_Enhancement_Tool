#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import json, os, numpy

relative_path_add = lambda str_path: sys.path.append(
    os.path.abspath(os.path.join(os.path.split(__file__)[0], str_path)))
import sys, os, numpy

from QtCommon import Qt_common
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

DEFAULT_SETTINGS_PATH = relative_path_covnert('settings.json')
JSON_TYPE_KEY = 'TYPE'

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

class Gear_Type(object):
    def __init__(self, name=None):
        self.name = name
        self.lvl_map = {}
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
    def __init__(self, item_cost=None, enhance_lvl=None, gear_type=None, name=None):
        self.cost = item_cost
        self.enhance_lvl = enhance_lvl
        self.gear_type = gear_type
        self.fs_cost = []
        self.cost_vec = []
        #self.cum_fs_cost = []
        self.fs_vec = None
        self.repair_cost = None
        self.name = name
        self.sale_balance = 0

    def calc_repair_cost(self):
        pass

    def set_sale_balance(self, intbal):
        self.sale_balance = float(intbal)

    def prep_calc(self):
        #self.calc_FS_costs()
        self.calc_repair_cost()
        gear_type = self.gear_type
        enhance_lvl = self.enhance_lvl
        self.fs_vec = gear_type.map[gear_type.lvl_map[enhance_lvl]]

    def set_enhance_lvl(self, enhance_lvl):
        self.enhance_lvl = enhance_lvl
        gear_type = self.gear_type
        if gear_type is not None:
            self.fs_vec = gear_type.map[gear_type.lvl_map[enhance_lvl]]

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

    def to_json_obj(self):
        return {
            'cost': self.cost,
            'enhance_lvl': self.enhance_lvl,
            'gear_type': self.gear_type.name,
            'name': self.name,
            'sale_balance': self.sale_balance
        }

    def from_json_obj(self, json_obj):
        for key, val in json_obj.iteritems():
            if key == 'gear_type':
                self.gear_type = gear_types[val]
            elif key == JSON_TYPE_KEY:
                pass
            else:
                self.__dict__[key] = val

    def simulate_FS(self, fs_count, last_cost):
        raise NotImplementedError()

    def get_enhance_lvl_idx(self):
        return self.gear_type.lvl_map[self.enhance_lvl]

    def set_cost(self, cost):
        self.cost = cost

    def to_json(self):
        return json.dumps(self.to_json_obj(), indent=4)

    def calc_FS_fail(self):
        raise NotImplementedError()

    def from_json(self, json_str):
        self.from_json_obj(json.loads(json_str))

    def fail_FS_accum(self):
        return 1


class Classic_Gear(Gear):

    def __init__(self, item_cost=None, enhance_lvl=None, gear_type=None, name=None, fail_dura_cost=5.0,
                 black_stone_cost=None, conc_black_stone_cost=None, mem_frag_cost=None):
        super(Classic_Gear, self).__init__(item_cost, enhance_lvl, gear_type, name=name)
        self.black_stone_cost = black_stone_cost
        self.conc_black_stone_cost = conc_black_stone_cost
        self.fail_dura_cost = fail_dura_cost
        self.using_memfrags = False
        self.mem_frag_cost = mem_frag_cost
        self.repair_cost = None

    def set_cost(self, cost):
        super(Classic_Gear, self).set_cost(cost)
        self.calc_repair_cost()

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

    def enhance_lvl_cost(self, cum_fs, fs_cost, total_cost=None, lvl=None):
        self.prep_calc()
        if lvl is None:
            lvl = self.enhance_lvl
        if total_cost is None:
            total_cost = self.cost_vec
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
        this_fail_map = numpy.array(self.gear_type.map)

        avg_num_attempts = numpy.divide(numpy.ones(this_fail_map.shape), this_fail_map)
        avg_num_fails = avg_num_attempts - 1

        cum_fs_tile = numpy.tile(cum_fs, (len(this_fail_map), 1))

        conc_start = self.gear_type.lvl_map['PRI']
        black_stone_costs = numpy.array([self.black_stone_cost] * len(this_fail_map))
        for i in range(conc_start, len(this_fail_map)):
            black_stone_costs[i] = self.conc_black_stone_cost

        fail_repair_cost_nom = numpy.tile(self.calc_repair_cost(), len(avg_num_fails))
        fails_cost = avg_num_fails * fail_repair_cost_nom[:, numpy.newaxis]
        total_cost = fails_cost + cum_fs_tile + (black_stone_costs[:, numpy.newaxis] * avg_num_attempts)

        backtrack_start = self.gear_type.lvl_map['TRI']

        for i in range(0, 3):
            this_pos = backtrack_start + i
            prev_cost = numpy.min(total_cost[this_pos - 1])
            new_fail_map = numpy.array(self.gear_type.map[this_pos])
            new_avg_attempts = numpy.divide(numpy.ones(len(new_fail_map)), new_fail_map)
            new_num_fails = new_avg_attempts - 1
            new_fail_cost = self.calc_repair_cost() + prev_cost
            total_cost[this_pos] = (new_num_fails * new_fail_cost) + (black_stone_costs[this_pos] * new_avg_attempts) + cum_fs

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
        enhance_lvl = self.enhance_lvl
        fs_gain = self.fail_FS_accum()
        cum_fs = numpy.roll(cum_fs, 1)
        cum_fs[0] = 0

        fs_upt = fs_count + fs_gain
        if len(cum_fs) <= fs_upt:
            fs_upt = len(cum_fs) - 1
        cum_fail_gain = cum_fs[fs_upt] - cum_fs[min(fs_count+1,120)]

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

    def to_json_obj(self):
        this_dict = super(Classic_Gear, self).to_json_obj()
        this_dict['fail_dura_cost'] = self.fail_dura_cost
        return this_dict


class Smashable(Gear):

    def __init__(self, item_cost, enhance_lvl, gear_type, name=None):
        super(Smashable, self).__init__(item_cost, enhance_lvl, gear_type, name=name)

    def calc_repair_cost(self):
        return self.cost * 2

    def get_blackstone_cost(self):
        raise NotImplementedError()

    def calc_FS_fail(self):
        return -self.sale_balance

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
        cum_fs = numpy.roll(cum_fs, 1)
        cum_fs[0] = 0
        this_fail_map = numpy.array(self.gear_type.map)
        num_enhance_lvls = len(this_fail_map)

        this_num_fails = numpy.divide(numpy.ones(this_fail_map.shape), this_fail_map) - 1

        cum_fs_tile = numpy.tile(cum_fs, (num_enhance_lvls, 1))

        fail_reapit_cost_nom = self.calc_repair_cost()
        fails_cost = this_num_fails * fail_reapit_cost_nom

        total_cost = fails_cost + cum_fs_tile

        for i in range(1, num_enhance_lvls):
            prev_cost = numpy.min(total_cost[i - 1])
            new_fail_map = numpy.array(self.gear_type.map[i])
            new_num_fails = numpy.divide(numpy.ones(len(new_fail_map)), new_fail_map)
            new_fail_cost = self.calc_repair_cost() + prev_cost

            total_cost[i] = (new_num_fails * new_fail_cost) + cum_fs

        self.cost_vec = total_cost
        return total_cost

    def simulate_FS(self, fs_count, last_cost):
        fs_vec = self.fs_vec
        repair_cost = self.calc_repair_cost()

        suc_rate = fs_vec[fs_count]
        fail_rate = 1.0 - suc_rate
        fail_cost = repair_cost
        success_cost = last_cost + self.calc_FS_fail()
        oppertunity_cost = (suc_rate * success_cost) + (fail_rate * fail_cost)
        avg_num_oppertunities = numpy.divide(1.0, fail_rate)
        # Cost of GAINING the fail stack, not just attempting it
        return avg_num_oppertunities * oppertunity_cost

    def clone_down(self):
        pass

    def to_json_obj(self):
        this_dict = super(Smashable, self).to_json_obj()
        return this_dict
