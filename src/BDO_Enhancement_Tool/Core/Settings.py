# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import BDO_Enhancement_Tool.utilities as utils
from .ItemStore import ItemStore

BASE_MARKET_TAX = 0.65


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
    P_TIME_PENALTY = 't_pen'
    P_TIME_CLEANSE = 't_cleanse'
    P_TIME_CLICK = 't_click'
    P_TIME_REPAIR = 't_repair'

    def __init__(self, settings_file_path=None, item_store=None):
        if item_store is None:
            item_store = ItemStore()
        self.tax = 0.65
        self.item_store: ItemStore = item_store
        super(EnhanceSettings, self).__init__(settings_file_path=settings_file_path)

    def init_settings(self, sets=None):
        this_vec = {
            EnhanceSettings.P_NUM_FS: 300,
            EnhanceSettings.P_CRON_STONE_COST: 2000000,
            EnhanceSettings.P_CLEANSE_COST: 100000,
            EnhanceSettings.P_ITEM_STORE: self.item_store,
            EnhanceSettings.P_MARKET_TAX: BASE_MARKET_TAX,
            EnhanceSettings.P_VALUE_PACK: 0.3,
            EnhanceSettings.P_VALUE_PACK_ACTIVE: True,
            EnhanceSettings.P_MERCH_RING: 0.05,
            EnhanceSettings.P_MERCH_RING_ACTIVE: False,
            EnhanceSettings.P_TIME_PENALTY: 0,
            EnhanceSettings.P_TIME_CLICK: 1,
            EnhanceSettings.P_TIME_CLEANSE: 30,
            EnhanceSettings.P_TIME_REPAIR: 1.5
        }
        if sets is not None:
            sets.update(this_vec)
            super(EnhanceSettings, self).init_settings(sets)
        else:
            super(EnhanceSettings, self).init_settings(this_vec)

    def get_state_json(self) -> dict:
        class_obj = {}
        class_obj.update(super(EnhanceSettings, self).get_state_json())
        class_obj[self.P_ITEM_STORE] = self[self.P_ITEM_STORE].get_state_json()
        return class_obj

    def set_state_json(self, state):
        if self.P_ITEM_STORE in state:
            item_store = self.item_store
            item_store.set_state_json(state[self.P_ITEM_STORE])
            state[self.P_ITEM_STORE] = item_store
        super(EnhanceSettings, self).set_state_json(state)
        self.recalc_tax()

    def __getstate__(self):
        return self.get_state_json()

    def __setstate__(self, state):
        self.set_state_json(state)

    def recalc_tax(self):
        BASE_TAX = self[EnhanceSettings.P_MARKET_TAX]
        tax = BASE_TAX

        if self[EnhanceSettings.P_VALUE_PACK_ACTIVE]: tax += BASE_TAX * self[EnhanceSettings.P_VALUE_PACK]
        if self[EnhanceSettings.P_MERCH_RING_ACTIVE]: tax += BASE_TAX * self[EnhanceSettings.P_MERCH_RING]
        self.tax = tax