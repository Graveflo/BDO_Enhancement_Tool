#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
DEBUG_PRINT_FILE = False
import json, os, numpy, shutil
from . import utilities as utils
from typing import Dict, Tuple
import time
import sys


BASE_MARKET_TAX = 0.65

def relative_path_convert(x):
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


DB_FOLDER = relative_path_convert('bdo_database')  # Could be error if this is a file for some reason
IMG_TMP = os.path.join(DB_FOLDER, 'tmp_imgs')
ENH_IMG_PATH = relative_path_convert('images/gear_lvl')
GEAR_ID_FMT = '{:08}'

USER_DATA_PATH = os.path.join(os.environ['APPDATA'], 'GravefloEnhancementTool')
os.makedirs(USER_DATA_PATH, exist_ok=True)


if not os.path.isdir(IMG_TMP):
    if os.path.isfile(IMG_TMP):
        os.remove(IMG_TMP)
    else:
        os.makedirs(IMG_TMP, exist_ok=True)

DEFAULT_SETTINGS_PATH = os.path.join(USER_DATA_PATH, 'settings.json')
if not os.path.isfile(DEFAULT_SETTINGS_PATH):
    tmplto = relative_path_convert('settings.json')
    if os.path.isfile(tmplto):
        try:
            shutil.copy(tmplto, USER_DATA_PATH)
        except:
            pass


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

TXT_PATH_DATA = relative_path_convert('Data')
STR_FMT_ITM_ID = '{:08}'


class EnhanceSettings(utils.Settings):
    P_NUM_FS = 'num_fs'
    P_CRON_STONE_COST = 'cost_cron'
    P_CLEANSE_COST = 'cost_cleanse'
    P_ITEM_STORE = 'item_store'
    P_MARKET_TAX = 'central_market_tax_rate'
    P_VALUE_PACK = 'value_pack_p'
    P_VALUE_PACK_ACTIVE = 'is_value_pack'
    P_MERCH_RING = 'merch_ring'
    P_MERCH_RING_ACTIVE = 'is_merch_ring'

    def __init__(self, settings_file_path=None):
        super(EnhanceSettings, self).__init__(settings_file_path=settings_file_path)
        self.tax = 0.65

    def init_settings(self, sets=None):
        this_vec = {
            EnhanceSettings.P_NUM_FS: 300,
            EnhanceSettings.P_CRON_STONE_COST: 2000000,
            EnhanceSettings.P_CLEANSE_COST: 100000,
            EnhanceSettings.P_ITEM_STORE: ItemStore(),
            EnhanceSettings.P_MARKET_TAX: BASE_MARKET_TAX,
            EnhanceSettings.P_VALUE_PACK: 0.3,
            EnhanceSettings.P_VALUE_PACK_ACTIVE: True,
            EnhanceSettings.P_MERCH_RING: 0.05,
            EnhanceSettings.P_MERCH_RING_ACTIVE: False
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
        self.recalc_tax()

    def recalc_tax(self):
        BASE_TAX = self[EnhanceSettings.P_MARKET_TAX]
        tax = BASE_TAX

        if self[EnhanceSettings.P_VALUE_PACK_ACTIVE]: tax += BASE_TAX * self[EnhanceSettings.P_VALUE_PACK]
        if self[EnhanceSettings.P_MERCH_RING_ACTIVE]: tax += BASE_TAX * self[EnhanceSettings.P_MERCH_RING]
        self.tax = tax


class ItemStoreItem(object):
    def __init__(self, name, prices, expires=None):
        self.name = name
        self.prices = prices
        self.expires = expires

    def __getitem__(self, item):
        return self.prices[item]

    def __setitem__(self, key, value):

        self.prices[key] = value

    def __getstate__(self):
        return {
            'name': self.name,
            'prices': self.prices,
            'expires': self.expires
        }

    def __setstate__(self, state):
        self.name = state.pop('name')
        self.prices = state.pop('prices')
        self.expires = state.pop('expires')


class BasePriceUpdator(object):
    def get_update(self, id: str) -> Tuple[float, list]:
        return -1.0, None


class ItemStore(object):
    """
    This may later be re-vamped to get items from database
    """
    P_BLACK_STONE_ARMOR = '00016002'
    P_BLACK_STONE_WEAPON = '00016001'
    P_CONC_ARMOR = '00016005'
    P_CONC_WEAPON = '00016004'
    P_HARD_BLACK = '00004997'
    P_SHARP_BLACK = '00004998'
    P_MEMORY_FRAG = '00044195'
    P_DRAGON_SCALE = '00044364'

    def __init__(self):
        self.price_updator = BasePriceUpdator()
        #hour_from_now = time.time() + 3600
        hour_from_now = -1  # always try to update if at default
        self.store_items: Dict[str, ItemStoreItem] = {
            ItemStore.P_BLACK_STONE_ARMOR: ItemStoreItem('BLACK_STONE_ARMOR', [220000], expires=hour_from_now),
            ItemStore.P_BLACK_STONE_WEAPON: ItemStoreItem('BLACK_STONE_WEAPON', [225000], expires=hour_from_now),
            ItemStore.P_CONC_ARMOR: ItemStoreItem('CONC_ARMOR', [1470000], expires=hour_from_now),
            ItemStore.P_CONC_WEAPON: ItemStoreItem('CONC_WEAPON', [2590000], expires=hour_from_now),
            ItemStore.P_HARD_BLACK: ItemStoreItem('Hard Black Crystal Shard', [1470000], expires=hour_from_now),
            ItemStore.P_SHARP_BLACK: ItemStoreItem('Sharp Black Crystal Shard', [2590000], expires=hour_from_now),
            ItemStore.P_MEMORY_FRAG: ItemStoreItem('MEMORY_FRAG', [1740000], expires=hour_from_now),
            ItemStore.P_DRAGON_SCALE: ItemStoreItem('DRAGON_SCALE', [550000], expires=hour_from_now)
        }

    def check_out_item(self, item):
        if isinstance(item, Gear):
            item = item.item_id
        if type(item) is int:
            item = STR_FMT_ITM_ID.format(item)
        return item

    def check_in_gear(self, gear):
        itm_id = self.check_out_item(gear.item_id)
        if itm_id in self.store_items:
            self.store_items[itm_id].name = gear.name
            return True
        else:
            num_lvls = len(gear.gear_type.map)
            self.store_items[itm_id] = ItemStoreItem(gear.name, None, expires=-1)
            return False

    def __getitem__(self, item) -> ItemStoreItem:
        return self.store_items[self.check_out_item(item)]

    def __setitem__(self, key, value):
        if isinstance(key, list) or isinstance(key, tuple):
            self.store_items[self.check_out_item(key[0])].prices[key[1]] = value
        else:
            if isinstance(value, list) or isinstance(value, tuple):
                self.store_items[self.check_out_item(key)].prices = value
            else:
                self.store_items[self.check_out_item(key)].prices[0] = value

    def iteritems(self):
        return iter(self.store_items.items())

    def get_cost(self, item_id, grade=None):
        if isinstance(item_id, Gear):
            if grade is None:
                grade = item_id.get_enhance_lvl_idx()
            grade = item_id.gear_type.bin_mp(grade)
        else:
            if grade is None:
                grade = 0

        str_item_id = self.check_out_item(item_id)
        item = self.__getitem__(str_item_id)
        this_time = time.time()
        if this_time > item.expires:
            expires, prices = self.price_updator.get_update(str_item_id)
            item.expires = expires
            if prices is not None:
                item.prices = prices
        try:
            return item[grade]
        except TypeError as e:
            if isinstance(item_id, Gear) and grade == 0:
                return item_id.base_item_cost
            raise e

    def __getstate__(self):
        items = {}
        for key, item in self.store_items.items():
            items[key] = item.__getstate__()
        return {
            'items': items
        }

    def __setstate__(self, state):
        for key, _st in state['items'].items():
            this_item = ItemStoreItem(None, None)
            this_item.__setstate__(_st)
            self.store_items[key] = this_item


class ge_gen(list):
    def __init__(self, downcap=0.7, uniform=None):
        super(ge_gen, self).__init__([])
        self.down_cap = downcap
        self.uniform=uniform

    def append(self, object):
        super(ge_gen, self).append(object)

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            start = idx.start
            stop = idx.stop
            step = idx.step
            if start is None:
                start = 0
            if stop is None:
                stop = super(ge_gen, self).__len__()
            if step is None:
                step = 1

            if stop < super(ge_gen, self).__len__():
                return super(ge_gen, self).__getitem__(idx)
            else:
                return [self.__getitem__(i) for i in range(start, stop, step)]

        try:
            return super(ge_gen, self).__getitem__(idx)
        except IndexError:
            # Use super here to avoid recursive stack overflow and throw exception in the event of an empty list
            zero_val = super(ge_gen, self).__getitem__(0)
            tent_val = self.__getitem__(idx-1)
            #tent_val2 = self.__getitem__(idx - 2)
            if tent_val >= self.down_cap:
                tent_val += (zero_val * 0.02)  #(9/350)  # 0.02
                #tent_val += zero_val * (9/350)
            else:
                tent_val += zero_val * 0.1
            if tent_val > 0.9:
                tent_val = 0.9
            # append should work here because of recursion
            self.append(tent_val)
            if self.uniform is not None:
                for u in self.uniform:
                    foo = u[idx]
            return tent_val


class gg_F_count(list):
    def __init__(self, p_vals: ge_gen, fs_gain=1):
        super(gg_F_count, self).__init__([])
        self.p_vals = p_vals
        self.fs_gain = fs_gain

    def append(self, object):
        raise ValueError('Cannot append')

    def __getitem__(self, idx):
        if not idx == 0:
            foo = self[idx-1]
        if isinstance(idx, slice):
            start = idx.start
            stop = idx.stop
            step = idx.step
            if start is None:
                start = 0
            if stop is None:
                stop = super(gg_F_count, self).__len__()
            if step is None:
                step = 1

            if stop < super(gg_F_count, self).__len__():
                return super(gg_F_count, self).__getitem__(idx)
            else:
                return [self.__getitem__(i) for i in range(start, stop, step)]

        try:
            return super(gg_F_count, self).__getitem__(idx)
        except IndexError:
            fs_gain = self.fs_gain
            p_vals = self.p_vals
            p_add = 0.0
            pre_add = 0.0
            s_idx = idx
            num_fail = 0
            while p_add < 1.0:
                pre_add = p_add
                p_add += p_vals[s_idx]
                s_idx += fs_gain
                num_fail += 1
            _val = (num_fail-1) + ((1.0 - pre_add) / p_vals[s_idx])


            super(gg_F_count, self).append(_val)
            return _val


class Gear_Type(object):
    def __init__(self, name=None):
        self.name = name
        self.lvl_map = {}
        self.idx_lvl_map = {}
        self.map = []
        self.instantiable = None
        self.p_num_f_map = []
        self.fs_gain = None
        self.downcap = None
        self.module = None
        self.type = None
        self.bt_start = None
        self.mat_cost = None
        self.repair_dura = None

    def __str__(self):
        return json.dumps({
            'name' : self.name,
            'lvl_map': self.lvl_map,
            'map': self.map,
        }, indent=4)

    def load_txt(self, txt):
        load_d = json.loads(txt)
        self.__setstate__(load_d)

    def __setstate__(self, load_d):
        for key, val in load_d.items():
            self.__dict__[key] = val
        idx_lvl_map = {}
        lvl_map = self.lvl_map
        for key,val in lvl_map.items():
            idx_lvl_map[val] = key
        self.idx_lvl_map = idx_lvl_map


        has_downcap = 'downcap' in load_d
        has_fs_gain = 'fs_gain' in load_d
        has_bt_start = 'bt_start' in load_d
        has_mat_cost = 'mat_cost' in load_d
        has_repair_dura = 'repair_dura' in load_d

        map = self.map
        new_map = []
        new_p_num_f_map = []
        mat_cost = []

        if self.downcap is None:
            self.downcap = [0.7] * len(self.map)

        if self.fs_gain is None:
            self.fs_gain = [1] * len(self.map)

        if self.module is None or self.type is None:
            if len(self.lvl_map) == 5:
                self.instantiable = Smashable
            else:
                self.instantiable = Classic_Gear
        else:
            self.instantiable = sys.modules[self.module].__dict__[self.type]

        if self.instantiable is Smashable:
            if not has_downcap:
                self.downcap[lvl_map['DUO']] = 0.5
                self.downcap[lvl_map['TRI']] = 0.4
                self.downcap[lvl_map['TET']] = 0.3
                self.downcap[lvl_map['PEN']] = 0.2
            if not has_bt_start:
                self.bt_start = 1
        elif self.instantiable is Classic_Gear:
            if not has_fs_gain:
                self.fs_gain = [self.calc_classic_fs_gain(x) for x in range(0, len(self.map))]
            if not has_bt_start:
                self.bt_start = self.lvl_map['TRI']
            if not has_mat_cost:
                is_weapon = self.name.lower().find('weapon') > -1
                if self.name.find('Blackstar') > -1:
                    bs_cost = [ItemStore.P_CONC_WEAPON]
                    hard = ItemStore.P_HARD_BLACK
                    sharp = ItemStore.P_SHARP_BLACK
                    conc_cost = [hard, sharp]
                elif is_weapon:
                    bs_cost = [ItemStore.P_BLACK_STONE_WEAPON]
                    conc_cost = [ItemStore.P_CONC_WEAPON]
                else:
                    bs_cost = [ItemStore.P_BLACK_STONE_ARMOR]
                    conc_cost = [ItemStore.P_CONC_ARMOR]
                for _ in range(0, self.lvl_map['PRI']):
                    mat_cost.append(bs_cost)
                for _ in range(self.lvl_map['PRI'], len(self.map)):
                    mat_cost.append(conc_cost)
                self.mat_cost = mat_cost
            if not has_repair_dura:
                if self.name.lower().find('(dura)') > -1:
                    self.repair_dura = 4
                else:
                    if self.name.lower().find('blackstar') > -1:
                        self.repair_dura = 10
                    else:
                        self.repair_dura = 5

        for i in range(0, len(map)):
            gg = ge_gen(downcap=self.downcap[i], uniform=new_map)
            new_map.append(gg)
            new_p_num_f_map.append(gg_F_count(gg, fs_gain=self.fs_gain[i]))

        #new_map = [ge_gen()] * len(map)
        for i,itm in enumerate(map):
            for val in itm:
                new_map[i].append(val)
        self.map = new_map
        self.p_num_f_map = new_p_num_f_map

    def calc_classic_fs_gain(self, lvl_idx):
        backtrack_start = lvl_idx - self.lvl_map['15']
        if backtrack_start > 0:
            return backtrack_start + 1
        else:
            return 1

    def bin_mp(self, idx):
        if self.name.find('Weapons') > -1:
            if self.name.find('Green') > -1:
                if idx == 0:
                    pass
                elif idx < 4:
                    idx = 1
                elif idx < 6:
                    idx = 2
                elif idx < 9:
                    idx = 3
                else:
                    idx = idx - 5
            else:
                if idx == 0:
                    pass
                elif idx < 4:
                    idx = 1
                elif idx < 6:
                    idx = 2
                else:
                    idx = idx - 3
        elif self.name.find('Armor') > -1:
            if self.name.find('Green') > -1:
                if idx == 0:
                    pass
                elif idx < 5:
                    idx = 1
                elif idx < 8:
                    idx = 2
                elif idx < 11:
                    idx = 3
                else:
                    idx = idx - 7
            else:
                if idx == 0:
                    pass
                elif idx < 5:
                    idx = 1
                elif idx < 8:
                    idx = 2
                else:
                    idx = idx - 5
        return idx

    def __getstate__(self):
        down_caps = []
        map = []

        for ggen in self.map:
            map.append([ggen[0]])
            down_caps.append(ggen.down_cap)
        return {
            'name': self.name,
            'lvl_map': self.lvl_map,
            'map': map,
            'downcap': down_caps,
            'fs_gain': self.fs_gain,
            'bt_start': self.bt_start,
            'mat_cost': self.mat_cost,
            'repair_dura': self.repair_dura,
            'module': self.instantiable.__module__,
            'type': self.instantiable.__name__
        }

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

def generate_gear_obj(settings, gear_type, base_item_cost=None, enhance_lvl=None, name=None, sale_balance=None, id=None):
    if gear_type is None:
        gear_type = list(gear_types.items())[0][1]
    if base_item_cost is None:
        # This must have a value or some numerical members may be None
        base_item_cost = 0
    if name is None:
        name = ''
    gear = gear_type.instantiable(settings, base_item_cost=base_item_cost, enhance_lvl=enhance_lvl, gear_type=gear_type,
                     name=name, sale_balance=sale_balance)
    gear.item_id = id
    return gear


class Gear(object):
    def __init__(self, settings, gear_type, base_item_cost=None, enhance_lvl=None, name=None, sale_balance=None,
                 fail_sale_balance=0, procurement_cost=0, target_lvls=None):
        if sale_balance is None:
            sale_balance = 0

        self.settings = settings
        self.base_item_cost = base_item_cost  # Cost of procuring the equipment
        self.enhance_lvl = enhance_lvl
        self.gear_type = gear_type
        #self.fs_cost = []
        self.cost_vec = []  # Vectors of cost for each enhancement level and each fail stack level
        self.restore_cost_vec = []
        self.cost_vec_min = []  # Vectors of cost for each enhancement level and each fail stack level
        self.restore_cost_vec_min = []
        #self.tap_risk = []
        #self.cum_fs_cost = []
        self.lvl_success_rate = None  # Probabilities of success for the current level of enhancement
        self.repair_cost = 0  # Cached repair cost for a normal fail, not a fail specific to enhancement level
        self.name = name
        self.sale_balance = sale_balance
        self.fail_sale_balance = fail_sale_balance
        self.procurement_cost = procurement_cost
        self.item_id = None
        self.costs_need_update = True
        if target_lvls is None:
            target_lvls = self.guess_target_lvls(enhance_lvl)
        self.target_lvls = target_lvls
        #self.enhance_cost = self.enhance_cost_thorough

    def set_enhance_cost_func(self, int_type):
        if int_type == 0:
            self.enhance_cost = self.enhance_cost_rough
        elif int_type == 1:
            self.enhance_cost = self.enhance_cost_avg
        elif int_type == 2:
            self.enhance_cost = self.enhance_cost_thorough

    def guess_target_lvls(self, enhance_lvl=None, intersect=None, excludes=None):
        if enhance_lvl is None:
            enhance_lvl = self.enhance_lvl
        if enhance_lvl is None:
            this_idx = 0
        else:
            this_idx = self.get_enhance_lvl_idx(enhance_lvl)
        backtrack_start = self.get_backtrack_start()-1
        this_idx = min(this_idx+1, backtrack_start)
        idx_list = range(this_idx, len(self.gear_type.lvl_map))
        target_lvls = [self.gear_type.idx_lvl_map[x] for x in idx_list]
        if enhance_lvl in target_lvls:
            target_lvls.remove(enhance_lvl)

        if intersect is not None:
            target_lvls = [x for x in intersect if x in target_lvls]

        if excludes is not None:
            target_lvls = [x for x in target_lvls if x not in excludes]

        return target_lvls

    def get_backtrack_start(self):
        return self.gear_type.lvl_map['TRI']

    def set_sale_balance(self, intbal):
        self.sale_balance = int(round(intbal))
        self.costs_need_update = True

    def set_fail_sale_balance(self, intbal):
        self.fail_sale_balance = int(round(intbal))
        self.costs_need_update = True

    def set_procurement_cost(self, intbal):
        self.procurement_cost = int(round(intbal))
        self.costs_need_update = True

    def enhance_lvl_to_number(self, enhance_lvl=None):
        if enhance_lvl is None:
            enhance_lvl = self.enhance_lvl
        return self.gear_type.lvl_map[enhance_lvl]

    def enhance_lvl_from_number(self, num):
        return self.gear_type.idx_lvl_map[num]

    def prep_lvl_calc(self):
        gear_type = self.gear_type
        enhance_lvl = self.enhance_lvl
        #num_fs = self.settings[EnhanceSettings.P_NUM_FS]
        self.lvl_success_rate = gear_type.map[gear_type.lvl_map[enhance_lvl]]

    def set_enhance_lvl(self, enhance_lvl):
        self.enhance_lvl = enhance_lvl
        gear_type = self.gear_type
        # = self.settings[EnhanceSettings.P_NUM_FS]
        if gear_type is not None:
            self.lvl_success_rate = gear_type.map[gear_type.lvl_map[enhance_lvl]]
        self.costs_need_update = True
        #    self.fs_vec[self.num_fs]

    def set_gear_type(self, gear_type):
        self.gear_type = gear_type
        enhance_lvl = self.enhance_lvl
        #num_fs = self.settings[EnhanceSettings.P_NUM_FS]
        if enhance_lvl is not None:
            # Just manually catch this exception
            self.lvl_success_rate = gear_type.map[gear_type.lvl_map[enhance_lvl]]
        self.costs_need_update = True

    def set_gear_type_by_str(self, str_gear_type):
        self.set_gear_type(gear_types[str_gear_type])
        self.costs_need_update = True

    def set_gear_params(self, gear_type, enhance_lvl):
        self.set_gear_type(gear_type)
        #self.gear_type = gear_type
        self.set_enhance_lvl(enhance_lvl)

    def calc_lvl_repair_cost(self, lvl_costs=None):
        raise NotImplementedError('Must implement calc_lvl_repair_cost')

    def calc_enhance_vectors(self):
        raise NotImplementedError('Must implement calc_enhance_vectors')

    def get_full_name(self):
        enhance_lvl = self.enhance_lvl
        try:
            int(enhance_lvl)
            enhance_lvl = '+'+enhance_lvl
        except ValueError:
            pass
        return enhance_lvl + " " + self.name

    def get_cost_obj(self):
        return self.cost_vec

    def get_min_cost(self):
        return self.cost_vec_min

    def enhance_cost_rough(self, cum_fs):
        num_fs = self.settings[EnhanceSettings.P_NUM_FS]
        for glmap in self.gear_type.p_num_f_map:
            foo = glmap[num_fs]
            #foo =
        num_fs = self.settings[EnhanceSettings.P_NUM_FS] + 1
        p_success = numpy.array(self.gear_type.map, copy=True)[:,:num_fs]
        num_f_map = numpy.array(self.gear_type.p_num_f_map, copy=True)[:, :num_fs]
        num_enhance_lvls = len(p_success)
        p_fail = 1-p_success

        avg_num_cron_attempts = numpy.divide(numpy.ones(p_success.shape), p_success)
        avg_num_attempts = num_f_map
        #avg_num_attempts = numpy.divide(numpy.ones(p_success.shape), p_success)

        cum_fs_tile = numpy.tile(cum_fs[:num_fs], (len(p_success), 1))

        material_cost, fail_repair_cost_nom = self.calc_enhance_vectors()

        # avg_num_fails is distinct from avg_num_attempts

        fail_cost = fail_repair_cost_nom[:, numpy.newaxis]
        opportunity_cost = (p_fail * fail_cost) + material_cost[:, numpy.newaxis]
        restore_cost = avg_num_attempts * opportunity_cost
        total_cost = restore_cost + cum_fs_tile
        min_cost_idxs = list(map(numpy.argmin, total_cost))
        restore_cost_min = [x[1][min_cost_idxs[x[0]]] for x in enumerate(restore_cost)]
        total_cost_min = [x[1][min_cost_idxs[x[0]]] for x in enumerate(total_cost)]

        backtrack_start = self.gear_type.bt_start

        for this_pos in range(backtrack_start, num_enhance_lvls):
            new_avg_attempts = avg_num_attempts[this_pos]

            new_fail_cost = fail_repair_cost_nom[this_pos] + total_cost_min[this_pos-1]
            new_opportunity_cost = (p_fail[this_pos] * new_fail_cost) + material_cost[this_pos]
            this_cost = (new_avg_attempts * new_opportunity_cost) + cum_fs[:num_fs]
            this_idx = numpy.argmin(this_cost)
            total_cost[this_pos] = this_cost
            total_cost_min[this_pos] = this_cost[this_idx]

            #prev_cost_idx = numpy.argmin(this_cost)

            new_fail_cost_rest = fail_repair_cost_nom[this_pos] + restore_cost_min[this_pos-1]
            new_opportunity_cost_rest = (p_fail[this_pos] * new_fail_cost_rest) + material_cost[this_pos]
            this_restore_min_cost = new_avg_attempts * new_opportunity_cost_rest
            restore_cost[this_pos] = this_restore_min_cost
            restore_cost_min[this_pos] = this_restore_min_cost[this_idx]


        self.cost_vec = numpy.array(total_cost)
        self.restore_cost_vec = numpy.array(restore_cost)
        self.cost_vec_min = numpy.array(total_cost_min)
        self.restore_cost_vec_min = numpy.array(restore_cost_min)
        self.restore_cost_vec.flags.writeable = False
        self.cost_vec.flags.writeable = False

        return total_cost

    def enhance_cost(self, cum_fs):
        if not self.costs_need_update:
            return
        settings = self.settings
        num_fs = settings[EnhanceSettings.P_NUM_FS]+1
        p_num_f_map = self.gear_type.p_num_f_map
        _map = self.gear_type.map

        num_f_m = numpy.array(p_num_f_map) - 1

        num_enhance_lvls = len(_map)


        cum_fs = cum_fs[:num_fs]
        cum_fs_tile = numpy.tile(cum_fs, (num_enhance_lvls, 1))

        material_cost, fail_repair_cost_nom = self.calc_enhance_vectors()

        # avg_num_fails is distinct from avg_num_attempts
        backtrack_start = self.gear_type.bt_start

        fail_cost = fail_repair_cost_nom[:, numpy.newaxis]
        opportunity_cost = fail_cost + material_cost[:, numpy.newaxis]
        opportunity_cost = (opportunity_cost * num_f_m) + material_cost[:, numpy.newaxis]


        restore_cost = opportunity_cost.T[:num_fs].T
        total_cost = restore_cost + cum_fs_tile
        min_cost_idxs = list(map(numpy.argmin, total_cost))
        restore_cost_min = [x[1][min_cost_idxs[x[0]]] for x in enumerate(restore_cost)]
        total_cost_min = [x[1][min_cost_idxs[x[0]]] for x in enumerate(total_cost)]

        for gear_lvl in range(backtrack_start, num_enhance_lvls):
            new_fail_cost = fail_repair_cost_nom[gear_lvl] + total_cost_min[gear_lvl-1]
            opportunity_cost[gear_lvl] = new_fail_cost + material_cost[gear_lvl]
            opportunity_cost[gear_lvl] = (opportunity_cost[gear_lvl] * num_f_m[gear_lvl]) + material_cost[gear_lvl] # Meterial for 1 success

            this_cost = opportunity_cost[gear_lvl] + cum_fs
            this_idx = numpy.argmin(this_cost)
            total_cost[gear_lvl] = this_cost
            total_cost_min[gear_lvl] = this_cost[this_idx]

            new_opportunity_cost_rest = fail_repair_cost_nom[gear_lvl] + restore_cost_min[gear_lvl - 1] + material_cost[gear_lvl]
            new_opportunity_cost_rest = (new_opportunity_cost_rest * num_f_m[gear_lvl]) + material_cost[gear_lvl] # Meterial for 1 success

            restore_cost[gear_lvl] = new_opportunity_cost_rest[this_idx]
            restore_cost_min[gear_lvl] = new_opportunity_cost_rest[this_idx]


        self.cost_vec = numpy.array(total_cost)
        #self.restore_cost_vec = numpy.array(restore_cost)
        self.cost_vec_min = numpy.array(total_cost_min)
        self.restore_cost_vec_min = numpy.array(restore_cost_min)
        #self.restore_cost_vec.flags.writeable = False
        self.cost_vec.flags.writeable = False
        self.costs_need_update = False

        return total_cost

    def enhance_cost_avg(self, cum_fs):
        if not self.costs_need_update:
            return
        settings = self.settings
        num_fs = settings[EnhanceSettings.P_NUM_FS]+1
        p_num_f_map = self.gear_type.p_num_f_map
        _map = self.gear_type.map

        #pos_f = numpy.array(p_num_f_map, dtype=numpy.int)



        p_success = numpy.array(_map, copy=True)
        #num_f_map = numpy.array(p_num_f_map, copy=True)
        num_enhance_lvls = len(_map)
        p_fail = 1-p_success


        cum_fs = cum_fs[:num_fs]
        cum_fs_tile = numpy.tile(cum_fs, (num_enhance_lvls, 1))

        material_cost, fail_repair_cost_nom = self.calc_enhance_vectors()

        # avg_num_fails is distinct from avg_num_attempts
        backtrack_start = self.gear_type.bt_start
        gain_l = numpy.array([x.fs_gain for x in p_num_f_map[:backtrack_start]])[:, numpy.newaxis]
        pos_f = numpy.array(p_num_f_map)[:,:num_fs]
        div = numpy.around(pos_f).astype(numpy.int)

        fail_cost = fail_repair_cost_nom[:, numpy.newaxis]
        opportunity_cost = (p_fail * fail_cost) + material_cost[:, numpy.newaxis]
        row_h = numpy.arange(backtrack_start)[:,None]
        index_p = numpy.tile(numpy.arange(num_fs), (backtrack_start,1)) + (div[:backtrack_start] * gain_l)
        op_cost_a = numpy.add(opportunity_cost[:backtrack_start][:,:num_fs], opportunity_cost[row_h, index_p]) / 2.0

        opportunity_cost[:backtrack_start][:,:num_fs] = op_cost_a * pos_f[:backtrack_start]

        restore_cost = opportunity_cost.T[:num_fs].T
        total_cost = restore_cost + cum_fs_tile
        min_cost_idxs = list(map(numpy.argmin, total_cost))
        restore_cost_min = [x[1][min_cost_idxs[x[0]]] for x in enumerate(restore_cost)]
        total_cost_min = [x[1][min_cost_idxs[x[0]]] for x in enumerate(total_cost)]

        for gear_lvl in range(backtrack_start, num_enhance_lvls):
            fs_gain = p_num_f_map[gear_lvl].fs_gain
            new_fail_cost = fail_repair_cost_nom[gear_lvl] + total_cost_min[gear_lvl-1]
            opportunity_cost[gear_lvl] = (p_fail[gear_lvl] * new_fail_cost) + material_cost[gear_lvl]

            row_h = numpy.full(num_fs, gear_lvl, dtype=numpy.int)
            index_p = numpy.arange(num_fs) + (div[gear_lvl] * fs_gain)
            op_cost_a = numpy.add(opportunity_cost[gear_lvl,: num_fs],
                                  opportunity_cost[row_h, index_p]) / 2.0
            opportunity_cost[gear_lvl,:num_fs] = op_cost_a * pos_f[gear_lvl]

            this_cost = opportunity_cost[gear_lvl][:num_fs] + cum_fs
            this_idx = numpy.argmin(this_cost)
            total_cost[gear_lvl] = this_cost
            total_cost_min[gear_lvl] = this_cost[this_idx]

            new_fail_cost_rest = fail_repair_cost_nom[gear_lvl] + restore_cost_min[gear_lvl - 1]
            new_opportunity_cost_rest = (p_fail[gear_lvl] * new_fail_cost_rest) + material_cost[gear_lvl]


            op_cost_a_r = numpy.add(new_opportunity_cost_rest[:num_fs],
                                  new_opportunity_cost_rest[index_p]) / 2.0
            new_opportunity_cost_rest[:num_fs] = op_cost_a_r * pos_f[gear_lvl]


            restore_cost[gear_lvl] = new_opportunity_cost_rest[this_idx]
            restore_cost_min[gear_lvl] = new_opportunity_cost_rest[this_idx]




        self.cost_vec = numpy.array(total_cost)
        #self.restore_cost_vec = numpy.array(restore_cost)
        self.cost_vec_min = numpy.array(total_cost_min)
        self.restore_cost_vec_min = numpy.array(restore_cost_min)
        #self.restore_cost_vec.flags.writeable = False
        self.cost_vec.flags.writeable = False
        self.costs_need_update = False

        return total_cost

    def enhance_cost_thorough(self, cum_fs):
        if not self.costs_need_update:
            return
        settings = self.settings
        num_fs = settings[EnhanceSettings.P_NUM_FS]+1
        p_num_f_map = self.gear_type.p_num_f_map
        _map = self.gear_type.map


        p_success = numpy.array(_map, copy=True)
        #num_f_map = numpy.array(p_num_f_map, copy=True)
        num_enhance_lvls = len(_map)
        p_fail = 1-p_success


        cum_fs = cum_fs[:num_fs]
        cum_fs_tile = numpy.tile(cum_fs, (num_enhance_lvls, 1))

        material_cost, fail_repair_cost_nom = self.calc_enhance_vectors()

        # avg_num_fails is distinct from avg_num_attempts
        backtrack_start = self.gear_type.bt_start

        fail_cost = fail_repair_cost_nom[:, numpy.newaxis]
        opportunity_cost = (p_fail * fail_cost) + material_cost[:, numpy.newaxis]

        for gear_lvl in range(0, backtrack_start):
            fs_gain = p_num_f_map[gear_lvl].fs_gain
            for fs_lvl in range(0, num_fs):
                num_fails = p_num_f_map[gear_lvl][fs_lvl]
                int_num_fails, rem = divmod(num_fails, 1)
                int_num_fails = int(int_num_fails)
                opportunity_cost[gear_lvl][fs_lvl] = numpy.sum(
                    opportunity_cost[gear_lvl][fs_lvl::fs_gain][:int_num_fails])
                opportunity_cost[gear_lvl][fs_lvl] += (opportunity_cost[gear_lvl][fs_lvl+(int_num_fails*fs_gain)] * rem)

        restore_cost = opportunity_cost.T[:num_fs].T
        total_cost = restore_cost + cum_fs_tile
        min_cost_idxs = list(map(numpy.argmin, total_cost))
        restore_cost_min = [x[1][min_cost_idxs[x[0]]] for x in enumerate(restore_cost)]
        total_cost_min = [x[1][min_cost_idxs[x[0]]] for x in enumerate(total_cost)]

        for gear_lvl in range(backtrack_start, num_enhance_lvls):
            fs_gain = p_num_f_map[gear_lvl].fs_gain
            new_fail_cost = fail_repair_cost_nom[gear_lvl] + total_cost_min[gear_lvl-1]
            opportunity_cost[gear_lvl] = (p_fail[gear_lvl] * new_fail_cost) + material_cost[gear_lvl]

            for fs_lvl in range(0, num_fs):
                num_fails = p_num_f_map[gear_lvl][fs_lvl]
                int_num_fails, rem = divmod(num_fails, 1)
                int_num_fails = int(int_num_fails)
                # Step by fs_gain and cut off after number of fails i reached
                opportunity_cost[gear_lvl][fs_lvl] = numpy.sum(opportunity_cost[gear_lvl][fs_lvl::fs_gain][:int_num_fails])
                opportunity_cost[gear_lvl][fs_lvl] += (opportunity_cost[gear_lvl][fs_lvl + (int_num_fails*fs_gain)] * rem)

            this_cost = opportunity_cost[gear_lvl][:num_fs] + cum_fs
            this_idx = numpy.argmin(this_cost)
            total_cost[gear_lvl] = this_cost
            total_cost_min[gear_lvl] = this_cost[this_idx]

            new_fail_cost_rest = fail_repair_cost_nom[gear_lvl] + restore_cost_min[gear_lvl - 1]
            new_opportunity_cost_rest = (p_fail[gear_lvl] * new_fail_cost_rest) + material_cost[gear_lvl]


            num_fails = p_num_f_map[gear_lvl][this_idx]
            int_num_fails, rem = divmod(num_fails, 1)
            int_num_fails = int(int_num_fails)
            new_opportunity_cost_rest[this_idx] = numpy.sum(new_opportunity_cost_rest[this_idx::fs_gain][:int_num_fails])
            new_opportunity_cost_rest[this_idx] += (new_opportunity_cost_rest[this_idx + (int_num_fails*fs_gain)] * rem)

            restore_cost[gear_lvl] = new_opportunity_cost_rest[this_idx]
            restore_cost_min[gear_lvl] = new_opportunity_cost_rest[this_idx]




        self.cost_vec = numpy.array(total_cost)
        #self.restore_cost_vec = numpy.array(restore_cost)
        self.cost_vec_min = numpy.array(total_cost_min)
        self.restore_cost_vec_min = numpy.array(restore_cost_min)
        #self.restore_cost_vec.flags.writeable = False
        self.cost_vec.flags.writeable = False
        self.costs_need_update = False

        return total_cost

    def enhance_lvl_cost(self, cum_fs, total_cost=None, lvl=None, count_fs=False):
        """
        Enhance cost at each probability accounting for the fail stacks absorbed upon success, the value gained from the
        successful enhancement upon success (in fail stack units) and the cost of the fail stacks gained upon failure
        :param cum_fs:
        :param fs_cost:
        :param total_cost:
        :param lvl:
        :return:
        """
        self.prep_lvl_calc()  # This is for repair cost calculation
        if lvl is None:
            lvl = self.enhance_lvl
        if total_cost is None:
            if count_fs:
                total_cost = self.cost_vec_min
            else:
                total_cost = self.restore_cost_vec_min
            #total_cost = self.get_min_cost()
        num_fs = self.settings[EnhanceSettings.P_NUM_FS]

        if count_fs is False:
            cum_fs = numpy.zeros(len(cum_fs))
        this_lvl = self.gear_type.lvl_map[lvl]
        this_total_cost = total_cost[this_lvl]
        success_rates = numpy.array(self.gear_type.map[this_lvl])[:num_fs+1]


        fail_rate = numpy.ones(success_rates.shape) - success_rates


        success_balance = cum_fs - this_total_cost
        success_cost = success_rates * success_balance


        fail_balance = self.calc_lvl_repair_cost(lvl_costs=total_cost)

        fail_cost = fail_rate * fail_balance
        tap_total_cost = success_cost + fail_cost + self.calc_lvl_flat_cost()

        return tap_total_cost

    def fs_lvl_cost(self, cum_fs, lvl=None, count_fs=True):
        """
        Enhance cost at each probability accounting for the fail stacks absorbed upon success, the value gained from the
        successful enhancement upon success (in fail stack units) and the cost of the fail stacks gained upon failure
        :param cum_fs:
        :param fs_cost:
        :param total_cost:
        :param lvl:
        :return:
        """
        self.prep_lvl_calc()  # This is for repair cost calculation
        #self.calc_lvl_repair_cost()
        if lvl is None:
            lvl = self.enhance_lvl
        num_fs = self.settings[EnhanceSettings.P_NUM_FS]

        this_lvl = self.gear_type.lvl_map[lvl]
        success_rates = numpy.array(self.gear_type.map[this_lvl])[:num_fs+1]


        fail_rate = numpy.ones(success_rates.shape) - success_rates

        if count_fs is False:
            cum_fs = numpy.zeros(len(cum_fs))
        success_balance = cum_fs + self.calc_FS_enh_success()  # calc_FS_enh_success return negative when gain
        success_cost = success_rates * success_balance

        tax = self.settings.tax

        # Repair cost variable so that backtracking cost is not included
        fail_balance = (self.procurement_cost - (self.fail_sale_balance*tax)) + self.repair_cost

        fail_cost = fail_rate * fail_balance
        tap_total_cost = success_cost + fail_cost + self.calc_lvl_flat_cost()

        return tap_total_cost

    def __getstate__(self):
        return {
            'base_item_cost': self.base_item_cost,
            'enhance_lvl': self.enhance_lvl,
            'gear_type': self.gear_type.name,
            'name': self.name,
            'sale_balance': self.sale_balance,
            'fail_sale_balance': self.fail_sale_balance,
            'procurement_cost': self.procurement_cost,
            'item_id': self.item_id,
            'target_lvls': self.target_lvls
        }

    def __setstate__(self, json_obj):
        # Do not call __init__ as it wil erase other class members from inherited classes
        self.fs_cost = []
        self.cost_vec = []
        #self.tap_risk = []
        self.lvl_success_rate = None
        self.repair_cost = None
        for key, val in json_obj.items():
            if key == 'gear_type':
                self.gear_type = gear_types[val]
            else:
                self.__dict__[key] = val

    def simulate_FS(self, fs_count, last_cost):
        raise NotImplementedError()

    def get_enhance_lvl_idx(self, enhance_lvl=None):
        if enhance_lvl is None:
            enhance_lvl = self.enhance_lvl
        return self.gear_type.lvl_map[enhance_lvl]

    def set_cost(self, cost):
        self.base_item_cost = cost
        self.costs_need_update = True

    def to_json(self):
        return json.dumps(self.__getstate__(), indent=4)

    def calc_FS_enh_success(self):
        # When an enhancement succeeded with the goal of selling the product the net gain is the sale balance minus
        # the bas material needed to perform the enhancement
        tax = self.settings.tax
        return -((self.sale_balance*tax) - self.procurement_cost)

    def fs_gain(self):
        raise NotImplementedError()

    def from_json(self, json_str):
        self.__setstate__(json.loads(json_str))

    def fail_FS_accum(self):
        return 1

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

    def duplicate(self):
        retme: Gear = self.gear_type.instantiable(self.settings, self.gear_type)
        retme.__setstate__(self.__getstate__())
        return retme


class Classic_Gear(Gear):

    def __init__(self, settings, gear_type, base_item_cost=None, enhance_lvl=None, name=None,
                 sale_balance=None, fail_sale_balance=0, procurement_cost=0):
        super(Classic_Gear, self).__init__(settings, gear_type, base_item_cost=base_item_cost, enhance_lvl=enhance_lvl,
                                           name=name, sale_balance=sale_balance, fail_sale_balance=fail_sale_balance,
                                           procurement_cost=procurement_cost)
        #self.fail_dura_cost = fail_dura_cost
        self.using_memfrags = False
        self.repair_cost = None  # This is the repair cost BEFORE multipliers like conc attempts

    def set_gear_type(self, gear_type):
        super(Classic_Gear, self).set_gear_type(gear_type)

    def set_cost(self, cost):
        super(Classic_Gear, self).set_cost(cost)
        self.calc_repair_cost()

    def prep_lvl_calc(self):
        #self.calc_FS_costs()
        self.calc_repair_cost()
        super(Classic_Gear, self).prep_lvl_calc()

    def get_durability_cost(self):
        return self.gear_type.repair_dura

    def calc_repair_cost(self):
        """
        This is not the level cost this is the basic repair cost
        :return:
        """
        fail_dura_cost = self.get_durability_cost()

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


    def backtrack_start(self):
        return self.gear_type.lvl_map['TRI']

    def calc_enhance_vectors(self):
        item_store = self.settings[EnhanceSettings.P_ITEM_STORE]


        num_enhance_lvls = len(self.gear_type.map)
        conc_start = self.gear_type.lvl_map['PRI']
        fail_repair_cost_nom = numpy.tile(self.calc_repair_cost(), num_enhance_lvls)
        black_stone_costs = []
        for i in range(0, num_enhance_lvls):
            mats = self.gear_type.mat_cost[i]

            cost = 0
            for mat in mats:
                cost += item_store.get_cost(mat)

            black_stone_costs.append(cost)
            if i >= conc_start:
                # Using concentrated black stones reduces twice the max durability upon failure
                fail_repair_cost_nom[i] *= 2
        return numpy.array(black_stone_costs), fail_repair_cost_nom

    def calc_lvl_flat_cost(self):
        item_store = self.settings[EnhanceSettings.P_ITEM_STORE]
        this_lvl = self.get_enhance_lvl_idx()
        mats = self.gear_type.mat_cost[this_lvl]

        cost = 0
        for mat in mats:
            cost += item_store.get_cost(mat)

        return cost

    def calc_lvl_repair_cost(self, lvl_costs=None):
        if lvl_costs is None:
            lvl_costs = self.get_min_cost()
        fail_repiar_cost_nom = self.repair_cost
        this_lvl = self.get_enhance_lvl_idx()
        conc_start = this_lvl - self.gear_type.lvl_map['PRI']
        fail_balance = fail_repiar_cost_nom
        if this_lvl >= conc_start:
            try:
                fail_balance = fail_repiar_cost_nom * 2
            except TypeError:
                # fail repair cost has not been set and is None
                fail_repiar_cost_nom = self.calc_lvl_repair_cost()
                fail_balance = fail_repiar_cost_nom * 2
        backtrack_start = self.backtrack_start()
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

    def calc_FS_enh_success(self):
        if self.enhance_lvl == '15':
            return self.settings[EnhanceSettings.P_CLEANSE_COST]
        else:
            return super(Classic_Gear, self).calc_FS_enh_success()

    def simulate_Enhance_sale(self, cum_fs):
        #num_fs = self.settings[EnhanceSettings.P_NUM_FS]
        #fs_vec = self.lvl_success_rate[:num_fs+1]
        repair_cost = self.repair_cost
        if repair_cost is None:
            self.calc_repair_cost()
            repair_cost = self.repair_cost
        num_fs = self.settings[EnhanceSettings.P_NUM_FS]
        #enhance_lvl = self.enhance_lvl
        cum_fs = numpy.roll(cum_fs, 1)
        cum_fs[0] = 0
        flat_cost = self.calc_lvl_flat_cost()

        success_rates = numpy.array(self.gear_type.map[self.get_enhance_lvl_idx()])[:num_fs+1]
        fail_rates = 1.0 - success_rates
        # print fail_rate
        #print '{}: {}, {}'.format(self.name, self.fail_sale_balance, self.sale_balance)

        # We do not want negative fail stack values
        fail_cost = repair_cost - (self.fail_sale_balance - self.procurement_cost)
        success_costs =  cum_fs + self.calc_FS_enh_success()
        success_opportunity = success_rates * success_costs
        fail_opportunity = fail_rates * fail_cost
        opportunity_cost = flat_cost + success_opportunity + fail_opportunity
        if DEBUG_PRINT_FILE:
            with open(self.name+".csv", 'wb') as f:
                import csv
                writer = csv.writer(f)
                writer.writerow(['Repair cost', 'flat cost', 'fail_cost', 'fail_sale_balance', 'procurement_cost', 'sale_balance', 'calc_FS_enh_success'])
                writer.writerow([repair_cost, flat_cost, fail_cost, self.fail_sale_balance, self.procurement_cost, self.sale_balance, self.calc_FS_enh_success()])
                writer.writerow(['FS Cost', 'Success Rate', 'Fail Rate', 'success cost', 'success_opportunity', 'fail_opportunity', 'opportunity_cost'])
                for i in range(0, len(success_rates)):
                    cum_f = cum_fs[i]
                    success_rate = success_rates[i]
                    fail_rate = fail_rates[i]
                    success_cost = success_costs[i]
                    success_opportunit = success_opportunity[i]
                    fail_oppertunit = fail_opportunity[i]
                    opportunity_cos = opportunity_cost[i]
                    writer.writerow([cum_f, success_rate, fail_rate, success_cost, success_opportunit, fail_oppertunit, opportunity_cos])
        avg_num_opportunities = numpy.divide(1.0, success_rates)
        #print '{}: {}'.format(self.name, self.fs_gain())
        return avg_num_opportunities * opportunity_cost

    def simulate_FS(self, fs_count, last_cost):
        self.prep_lvl_calc()  # This is for repair cost calculation
        #num_fs = self.settings[EnhanceSettings.P_NUM_FS]
        suc_rate = self.lvl_success_rate[fs_count]
        repair_cost = self.repair_cost
        if repair_cost is None:
            self.calc_repair_cost()
            repair_cost = self.repair_cost
        #enhance_lvl = self.enhance_lvl
        flat_cost = self.calc_lvl_flat_cost()


        fail_rate = 1.0 - suc_rate
        tax = self.settings.tax

        # Splitting flat_cost here since it will have a 1.0 ratio when multiplied by succ and fail rate and
        # it should be negated when the enh_success cost (gain) overrides it
        fail_cost = flat_cost + repair_cost + max(0, self.procurement_cost-(self.fail_sale_balance*tax))
        success_cost = max(0, flat_cost + last_cost + self.calc_FS_enh_success())

        opportunity_cost = (suc_rate * success_cost) + (fail_rate * fail_cost)
        avg_num_opportunities = numpy.divide(1.0, fail_rate)
        #print '{}: {}'.format(self.name, self.fs_gain())
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


class Smashable(Gear):
    def __init__(self, settings, gear_type, base_item_cost=None, enhance_lvl=None, name=None, sale_balance=None,
                 fail_sale_balance=None, procurement_cost=None):
        if fail_sale_balance is None:
            # this is for PRI
            fail_sale_balance = base_item_cost
        if procurement_cost is None:
            # this is for PRI
            procurement_cost = base_item_cost
        super(Smashable, self).__init__(settings, gear_type, base_item_cost=base_item_cost, enhance_lvl=enhance_lvl,
                                        name=name, sale_balance=sale_balance, fail_sale_balance=fail_sale_balance,
                                        procurement_cost=procurement_cost)
        self.repair_bt_start_idx = 1
        self.repair_cost = 0  # This is 0 because repair cost is only used for durability and this item does not lose dura

    def prep_lvl_calc(self):
        self.repair_cost = 0
        super(Smashable, self).prep_lvl_calc()

    def guess_target_lvls(self, enhance_lvl=None, intersect=None, excludes=None):
        if enhance_lvl is None:
            enhance_lvl = self.enhance_lvl

        # Keep order sorted
        target_lvls = [self.enhance_lvl_from_number(i) for i in range(len(self.gear_type.map))]

        if enhance_lvl in target_lvls:
            target_lvls.remove(enhance_lvl)

        if intersect is not None:
            target_lvls = [x for x in intersect if x in target_lvls]

        if excludes is not None:
            target_lvls = [x for x in target_lvls if x not in excludes]

        return target_lvls

    def calc_lvl_repair_cost(self, lvl_costs=None):
        if lvl_costs is None:
            lvl_costs = self.get_min_cost()

        lvl_indx = self.get_enhance_lvl_idx()
        if lvl_indx == 0:
            return 0  # Price of failure scales with number of times paynig material cost not repair cost
        else:
            try:
                return numpy.sum(lvl_costs[:lvl_indx])
            except IndexError:
                self.prep_lvl_calc()
                return numpy.sum(lvl_costs[:lvl_indx])

    def calc_enhance_vectors(self):
        enhance_lvls = len(self.gear_type.map)
        matreial_cost = numpy.ones(enhance_lvls) * self.base_item_cost
        matreial_cost[0] += self.base_item_cost
        repair_costs = numpy.zeros(enhance_lvls)  # This is item repair not back-tracking repair
        return matreial_cost, repair_costs

    def calc_lvl_flat_cost(self):
        if self.get_enhance_lvl_idx() == 0:
            return self.base_item_cost * 2
        else:
            return self.base_item_cost

    def simulate_FS(self, fs_count, last_cost):
        self.prep_lvl_calc()  # This is for repair cost calculation
        num_fs = self.settings[EnhanceSettings.P_NUM_FS]
        fs_vec = self.lvl_success_rate[:num_fs+1]
        enhance_lvl_idx = self.get_enhance_lvl_idx()
        #fail_loss = numpy.min(self.cost_vec[enhance_lvl_idx])
        #fail_loss = self.base_item_cost + self.fail_sale_balance

        suc_rate = fs_vec[fs_count]
        fail_rate = 1.0 - suc_rate
        tax = self.settings.tax
        fail_cost = max(0, self.procurement_cost-(self.fail_sale_balance*tax))
        success_cost = last_cost + max(0, self.calc_FS_enh_success())
        oppertunity_cost = (suc_rate * success_cost) + (fail_rate * fail_cost) + self.calc_lvl_flat_cost()
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
