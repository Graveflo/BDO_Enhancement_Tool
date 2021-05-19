# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import time
from typing import Tuple, Union, Dict

STR_FMT_ITM_ID = '{:08}'

class ItemStoreException(Exception):
    pass


class ItemStoreItem(object):
    def __init__(self, name, prices, expires=None):
        self.name = name
        self.prices = prices
        self.expires = expires

    def __getitem__(self, item):
        try:
            return self.prices[item]
        except (IndexError, KeyError):
            raise ItemStoreException('Item not in item store')

    def __setitem__(self, key, value):
        self.prices[key] = value

    def get_state_json(self):
        return {
            'name': self.name,
            'prices': self.prices,
            'expires': self.expires
        }

    def set_state_json(self, state):
        self.name = state.pop('name')
        self.prices = state.pop('prices')
        self.expires = state.pop('expires')

    def __getstate__(self):
        return self.get_state_json()

    def __setstate__(self, state):
        self.set_state_json(state)


class BasePriceUpdator(object):
    def get_update(self, id: str) -> Tuple[float, Union[None, list]]:
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
    P_CAPH_STONE = '00721003'
    P_MASS_OF_PURE_MAGIC = '00752023'

    def __init__(self):
        self.price_updator = BasePriceUpdator()
        self.custom_prices = {}
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
            ItemStore.P_DRAGON_SCALE: ItemStoreItem('DRAGON_SCALE', [550000], expires=hour_from_now),
            ItemStore.P_CAPH_STONE: ItemStoreItem('Caphras Stone', [2500000], expires=hour_from_now),
            ItemStore.P_MASS_OF_PURE_MAGIC: ItemStoreItem('Mass of Pure Magic', [1000000], expires=float('inf'))
        }

    def clear(self):
        self.store_items = {}
        self.custom_prices = {}

    def check_out_item(self, item_id):
        if item_id is None:
            raise ItemStoreException('Item is none')
        if type(item_id) is int:
            item_id = STR_FMT_ITM_ID.format(item_id)
        return item_id

    def override_gear_price(self, gear, level, price):
        if gear in self.custom_prices:
            gm = self.custom_prices[gear]
        else:
            gm = {}
            self.custom_prices[gear] = gm
        gm[level] = price

    def __getitem__(self, item) -> ItemStoreItem:
        return self.store_items[self.check_out_item(item)]

    def __setitem__(self, key, value):
        if isinstance(key, list) or isinstance(key, tuple):  # Allows for settings type and level
            self.store_items[self.check_out_item(key[0])].prices[key[1]] = value
        else:
            if isinstance(value, list) or isinstance(value, tuple):  # Allows for setting whole or level costs
                self.store_items[self.check_out_item(key)].prices = value
            else:  # Some only have one level why put 0 all the time
                self.store_items[self.check_out_item(key)].prices[0] = value

    def __contains__(self, item_id):
        itm_id = self.check_out_item(item_id)
        if itm_id is None:
            return False
        return itm_id in self.store_items

    def iteritems(self):
        return iter(self.store_items.items())

    def get_prices(self, item_id):
        str_item_id = self.check_out_item(item_id)
        item = self.__getitem__(str_item_id)
        this_time = time.time()
        if this_time > item.expires:
            expires, prices = self.price_updator.get_update(str_item_id)
            item.expires = expires
            if prices is not None:
                item.prices = prices
        return item

    def get_cost(self, item_id, bn_mp=None):
        if bn_mp is None:  # those cost of just an item id is the base cost
            bn_mp = 0

        if item_id in self.custom_prices:
            price_reg = self.custom_prices[item_id]
            if bn_mp in price_reg:
                return price_reg[bn_mp]

        try:
            return self.get_prices(item_id)[bn_mp]
        except TypeError:
            raise ItemStoreException('Item is not on the market')

    def get_state_json(self) -> dict:
        items = {}
        for key, item in self.store_items.items():
            items[key] = item.get_state_json()
        return {
            'items': items,
            'custom_prices': self.custom_prices
        }

    def set_state_json(self, state):
        self.clear()
        for key, _st in state['items'].items():
            this_item = ItemStoreItem(None, None)
            this_item.set_state_json(_st)
            self.store_items[key] = this_item
        self.custom_prices = state.pop('custom_prices')

    def __getstate__(self):
        return self.get_state_json()

    def __setstate__(self, state):
        self.set_state_json(state)
