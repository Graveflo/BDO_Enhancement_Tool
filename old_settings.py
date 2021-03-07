#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
from .common import ItemStore, EnhanceSettings
from .utilities import Settings, chain_iter
from time import time
from .common import ItemStoreItem, ItemStore

MEMORY_FRAG_COST = 1740000
P_CRON_STONE_COST = 2000000
P_CLEANSE_COST = 100000


def convert_0002(state_obj):
    P_NUM_FS = 'num_fs'
    P_CRON_STONE_COST = 'cost_cron'
    P_CLEANSE_COST = 'cost_cleanse'
    P_FAIL_STACKERS = 'fail_stackers'
    P_COST_CONC_W = 'cost_conc_w'
    P_COST_BS_W = 'cost_bs_w'
    P_R_ENHANCE_ME = 'r_enhance_me'
    P_FS_EXCEPTIONS = 'fs_exceptions'
    P_COST_CONC_A = 'cost_conc_a'
    P_R_FAIL_STACKERS = 'r_fail_stackers'
    P_COST_BS_A = 'cost_bs_a'
    P_ENHANCE_ME= 'enhance_me'
    P_FS_COUNTS = 'fail_stackers_count'
    P_COST_MEME = 'cost_meme'

    item_shop = {'items':{
        ItemStore.P_MEMORY_FRAG: state_obj.pop(P_COST_MEME),
        ItemStore.P_CONC_WEAPON: state_obj.pop(P_COST_CONC_W),
        ItemStore.P_CONC_ARMOR: state_obj.pop(P_COST_CONC_A),
        ItemStore.P_BLACK_STONE_WEAPON: state_obj.pop(P_COST_BS_W),
        ItemStore.P_BLACK_STONE_ARMOR: state_obj.pop(P_COST_BS_A)
    }
    }

    state_obj[EnhanceSettings.P_ITEM_STORE] = item_shop

    return state_obj

def convert_0010(state_obj):
    P_NUM_FS = 'num_fs'
    P_CRON_STONE_COST = 'cost_cron'
    P_CLEANSE_COST = 'cost_cleanse'
    P_FAIL_STACKERS = 'fail_stackers'
    P_COST_CONC_W = 'cost_conc_w'
    P_COST_BS_W = 'cost_bs_w'
    P_R_ENHANCE_ME = 'r_enhance_me'
    P_FS_EXCEPTIONS = 'fs_exceptions'
    P_COST_CONC_A = 'cost_conc_a'
    P_R_FAIL_STACKERS = 'r_fail_stackers'
    P_COST_BS_A = 'cost_bs_a'
    P_ENHANCE_ME= 'enhance_me'
    P_FS_COUNTS = 'fail_stackers_count'
    P_COST_MEME = 'cost_meme'


    P_fail_stackers = state_obj[P_FAIL_STACKERS]
    P_r_fail_stackers = state_obj[P_R_FAIL_STACKERS]
    P_enhanceme = state_obj[P_ENHANCE_ME]
    P_r_enhanceme = state_obj[P_R_ENHANCE_ME]


    for gear_obj in chain_iter(P_fail_stackers, P_r_fail_stackers, P_enhanceme, P_r_enhanceme):
        cost = gear_obj.pop('cost')
        gear_obj['base_item_cost'] = cost

    return state_obj


def convert_0011(state_obj):
    item_store = state_obj['item_store']
    items = item_store['items']

    P_BLACK_STONE_ARMOR = items['BLACK_STONE_ARMOR']
    P_BLACK_STONE_WEAPON = items['BLACK_STONE_WEAPON']
    P_CONC_ARMOR = items['CONC_ARMOR']
    P_CONC_WEAPON = items['CONC_WEAPON']
    P_MEMORY_FRAG = items['MEMORY_FRAG']
    P_DRAGON_SCALE = items['DRAGON_SCALE']

    hour_from_now = time() + 3600

    state_obj[EnhanceSettings.P_ITEM_STORE] = {'items':{
        ItemStore.P_BLACK_STONE_ARMOR: ItemStoreItem('BLACK_STONE_ARMOR', [P_BLACK_STONE_ARMOR], expires=hour_from_now).get_state_json(),
        ItemStore.P_BLACK_STONE_WEAPON: ItemStoreItem('BLACK_STONE_WEAPON', [P_BLACK_STONE_WEAPON], expires=hour_from_now).get_state_json(),
        ItemStore.P_CONC_ARMOR: ItemStoreItem('CONC_ARMOR', [P_CONC_ARMOR], expires=hour_from_now).get_state_json(),
        ItemStore.P_CONC_WEAPON: ItemStoreItem('CONC_WEAPON', [P_CONC_WEAPON], expires=hour_from_now).get_state_json(),
        ItemStore.P_MEMORY_FRAG: ItemStoreItem('MEMORY_FRAG', [P_MEMORY_FRAG], expires=hour_from_now).get_state_json(),
        ItemStore.P_DRAGON_SCALE: ItemStoreItem('DRAGON_SCALE', [P_DRAGON_SCALE], expires=hour_from_now).get_state_json()
    }
    }

    return state_obj


def convert_0012(state_obj):
    P_VALKS = 'valks'
    valks = state_obj[P_VALKS]
    new_valk = {}


    for v in valks:
        if v in new_valk:
            new_valk[v] += 1
        else:
            new_valk[v] = 1
    state_obj[P_VALKS] = new_valk
    return state_obj


def convert_0013(state_obj):
    P_VALKS = 'valks'
    item_store = state_obj['item_store']
    items = item_store['items']

    new_store = ItemStore().get_state_json()
    for key, v in new_store['items'].items():
        if key in items:
            new_store[key] = items[key]

    state_obj['item_store'] = new_store
    return state_obj

def convert_0014(state_obj):
    fail_stackers = state_obj.pop('fail_stackers')
    r_fail_stackers = state_obj.pop('r_fail_stackers')

    fail_stackers_2 = []
    state_obj['fail_stackers_2'] = fail_stackers_2
    r_fail_stackers_2 = []
    state_obj['r_fail_stackers_2'] = r_fail_stackers_2
    for_profit_gear = []
    state_obj['for_profit_gear'] = for_profit_gear
    r_for_profit_gear = []
    state_obj['r_for_profit_gear'] = r_for_profit_gear

    new_fail_stackers = []
    new_r_fail_stackers = []
    state_obj['fail_stackers'] = new_fail_stackers
    state_obj['r_fail_stackers'] = new_r_fail_stackers
    for gear_obj in fail_stackers:
        if gear_obj['enhance_lvl'] == '15':
            new_fail_stackers.append(gear_obj)
        elif gear_obj['procurement_cost'] == 0 and gear_obj['sale_balance'] == 0 and gear_obj['fail_sale_balance'] == 0:
            fail_stackers_2.append(gear_obj)
        else:
            for_profit_gear.append(gear_obj)

    for gear_obj in r_fail_stackers:
        if gear_obj['enhance_lvl'] == '15':
            new_r_fail_stackers.append(gear_obj)
        elif gear_obj['procurement_cost'] == 0 and gear_obj['sale_balance'] == 0 and gear_obj['fail_sale_balance'] == 0:
            r_fail_stackers_2.append(gear_obj)
        else:
            r_for_profit_gear.append(gear_obj)
    state_obj['fs_genome'] = [0, 23, 6, 6, 13]
    return state_obj

def convert_0015(state_obj):
    P_GENOME_FS = state_obj.pop('fs_genome')
    fsl_sec_gidx = P_GENOME_FS[0]
    genome = P_GENOME_FS[1:]

    state_obj['fs_genome'] = [{
        'genome': genome,
        'gear_dx': fsl_sec_gidx,
        'num_fs': state_obj['num_fs']
    }]

    return state_obj


LATEST = convert_0015

pasts = [
    convert_0002,
    convert_0010,
    convert_0011,
    convert_0012,
    convert_0013,
    convert_0014,
    convert_0015
]

def run_conversion(bgn, x, target=None):
    if target is None:
        target = pasts[-1]
    for i in range(pasts.index(bgn), pasts.index(target)+1):
        x = pasts[i](x)
    return x


converters = {
    '0.0.0.2': lambda x: run_conversion(convert_0002, x), # convert_0013(convert_0012(convert_0011(convert_0010(convert_0002(x))))),
    '0.0.1.0': lambda x: run_conversion(convert_0010, x), # convert_0013(convert_0012(convert_0011(convert_0010(x)))),
    '0.0.1.1': lambda x: run_conversion(convert_0011, x), # convert_0013(convert_0012(convert_0011(x))),
    '0.0.1.2': lambda x: run_conversion(convert_0012, x), # convert_0013(convert_0012(x)),
    '0.0.1.3': lambda x: run_conversion(convert_0013, x), # convert_0013
    '0.0.1.4': lambda x: run_conversion(convert_0014, x),
    '0.0.1.5': lambda x: run_conversion(convert_0015, x)
}
