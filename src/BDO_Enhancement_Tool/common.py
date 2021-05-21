#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import os, numpy, shutil
def relative_path_convert(x):
    """
    Takes a valid path: either relative to CWD or an absolute path and convert it to a relative path for this file.
    The relative path assumes that simply joining the returned path with the path of this file shall result in a valid
    path pointing to the origonal valid file object (x).
    :param x: str: path to a valid file object
    :return: str: a path to the file object relative to this file
    """
    return os.path.abspath(os.path.join(os.path.split(__file__)[0], x))
from typing import Dict, List, Union
from .bdo_database.gear_database import GEAR_DB, CachedGearDataBase, GearData
from .Core.CronStones import initialize_cronstone_manager
DB_FOLDER = relative_path_convert('bdo_database')  # Could be error if this is a file for some reason
initialize_cronstone_manager(os.path.join(DB_FOLDER, GEAR_DB))  # initialize this database before everything loads
from .Core.Gear import gear_types, GearType, Gear
from .Core.ItemStore import ItemStore, ItemStoreException, STR_FMT_ITM_ID, ItemStoreItem, check_in_dict

IMG_TMP = os.path.join(DB_FOLDER, 'tmp_imgs')
ENH_IMG_PATH = relative_path_convert('images/gear_lvl')

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


factorials = [1]

def get_num_level_attempts(prob_fails):
    num_fails = 0
    for prob in prob_fails:
        this_num_attempts = 1 / prob
        num_succ = this_num_attempts - 1
        num_fails += (num_succ * num_fails) + this_num_attempts
    return num_fails

# def get_num_attempts_before_success(prob_success):
#     i = 0
#     suful = 0
#     for prob in prob_success:
#         suful += prob
#         i += 1
#         if suful >= 1:
#             break
#     return (1/suful) * i

def iter_float(fn):
    while fn > 0:
        tn = max(0, min(fn, 1))
        fn -= 1
        yield tn

def p_or(p1, p2):
    return 1 - ((1-p1) * (1-p2))

def approximate_succ_num(prob, times):
    if times > len(prob):
        return 0
    c = 1
    counter = 0
    while times > 0:
        counter += 1
        multi = max(0, times)
        multi = min(multi, 1)
        if multi >= 1:
            c *= prob[-counter]
        else:
            pn = 1/multi
            rot = prob[-counter] ** (multi)
            c *= rot
        times -= 1

    return c

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

def exp_integral(start, stop, p):
    ln_p =numpy.log(p)
    return ((p**stop) / ln_p) - ((p**start) / ln_p)

def loop_sum(p, x):
    odds = p**x
    for i in range(1, 2):
        odds = p_or(odds, odds * p**(x+i))
    return odds

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



class GearItemStore(ItemStore):
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
    P_CAPH_STONE = '00721003'
    P_MASS_OF_PURE_MAGIC = '00752023'

    def __init__(self, gear_db=None):
        if gear_db is None:
            gear_db = GearGTDataBase()
        self.gear_db = gear_db
        super(GearItemStore, self).__init__()
        self.custom_gear_prices = {}

    def override_gear_price(self, pricable: Union[Gear, int], grade: int, price: float):
        if isinstance(pricable, Gear):
            if grade == -1:
                pricable.base_item_cost = price
            bn_mp = pricable.gear_type.bin_mp(grade)
            item_id = super(GearItemStore, self).check_out_item(pricable.item_id)
            check_in_dict(self.custom_gear_prices, pricable, bn_mp, price)
            if (item_id is not None) and ((item_id not in self) or (self[item_id].prices is None)):
                super(GearItemStore, self).override_gear_price(item_id, bn_mp, price)
        else:  # gear parameter is an item id
            gd = self.gear_db.lookup_id(int(pricable))
            gt = gd.get_gear_type()
            bn_mp = gt.bin_mp(grade)
            str_item_id = super(GearItemStore, self).check_out_item(pricable)
            super(GearItemStore, self).override_gear_price(str_item_id, bn_mp, price)

    def price_is_overridden(self, pricable: Union[Gear, int], grade: int):
        if isinstance(pricable, Gear):
            bn_mp = pricable.gear_type.bin_mp(grade)
            item_id = super(GearItemStore, self).check_out_item(pricable.item_id)
            custom_gear_prices = self.custom_gear_prices
            return ((pricable in custom_gear_prices) and (grade in custom_gear_prices[pricable])) or \
                   super(GearItemStore, self).price_is_overridden(item_id, bn_mp)
        else:  # gear parameter is an item id
            gd = self.gear_db.lookup_id(int(pricable))
            gt = gd.get_gear_type()
            bn_mp = gt.bin_mp(grade)
            item_id = super(GearItemStore, self).check_out_item(pricable)
            return super(GearItemStore, self).price_is_overridden(item_id, bn_mp)

    def check_out_item(self, item):
        if isinstance(item, Gear):
            item_id = item.item_id
            return super(GearItemStore, self).check_out_item(item_id)
        else:
            return super(GearItemStore, self).check_out_item(item)

    def check_in_gear(self, gear):
        item_id = gear.item_id
        if item_id is None:
            return
        str_item_id = STR_FMT_ITM_ID.format(item_id)
        if str_item_id in self.store_items:
            self.store_items[str_item_id].name = gear.name
            return True
        else:
            self.store_items[str_item_id] = ItemStoreItem(gear.name, None, expires=-1)
            return False

    def get_cost(self, priceable, grade=None):
        is_gear = isinstance(priceable, Gear)
        if is_gear:
            if grade is None:  # the cost of a particular gear object is it's current enhance lvl price
                grade = priceable.get_enhance_lvl_idx()
            gt = priceable.gear_type
            item_id = priceable.item_id
            bn_mp = gt.bin_mp(grade)

            if priceable in self.custom_gear_prices:
                price_reg = self.custom_gear_prices[priceable]
                if bn_mp in price_reg:
                    return price_reg[bn_mp]
        else:
            item_id = priceable
            if item_id in self.gear_db:
                gd = self.gear_db.lookup_id(item_id)
                gt = gd.get_gear_type()
                if grade is None:
                    bn_mp = 0
                else:
                    bn_mp = gt.bin_mp(grade)
            else:
                bn_mp = grade

        try:
            return super(GearItemStore, self).get_cost(item_id, bn_mp=bn_mp)
        except ItemStoreException as e:
            if is_gear and bn_mp == 0:
                return priceable.base_item_cost
            else:
                raise e

    def get_state_json(self) -> dict:
        super_state = super(GearItemStore, self).get_state_json()
        super_state['custom_gear_prices'] = {id(k):v for k,v in self.custom_gear_prices.items()}
        return super_state

    def set_custom_gear_json(self, custom_gear_prices, gear_reg):
        customs = {}
        for k, v in custom_gear_prices.items():
            gid = int(k)
            if gid in gear_reg:
                customs[gear_reg[gid]] = {int(x): y for x, y in v.items()}
        self.custom_gear_prices = customs


class GtGearData(GearData):
    def get_gear_type(self) -> GearType:
        return gear_types[self.get_gt_str()]


class GearGTDataBase(CachedGearDataBase):
    def __init__(self, db_path=None):
        super(GearGTDataBase, self).__init__(db_path=db_path)
        self.id_cache: Dict[int, GtGearData] = {}

    def process_row(self, row) -> GtGearData:
        gd = GtGearData(*row)
        self.id_cache[gd.item_id] = gd
        return gd

    def  process_rows(self, rows) -> List[GtGearData]:
        return super(GearGTDataBase, self).process_rows(rows)

    def lookup_id(self, item_id) -> GtGearData:
        return super(GearGTDataBase, self).lookup_id(item_id)

    def __contains__(self, item):
        return int(item) in self.id_cache


GEAR_DB_MANAGER = GearGTDataBase()