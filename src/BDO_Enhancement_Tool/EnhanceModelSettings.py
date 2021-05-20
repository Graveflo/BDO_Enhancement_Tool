# - * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import shutil
from typing import Set

from .common import GearItemStore

from .Core.Settings import EnhanceSettings
from .Core.Gear import Gear, generate_gear_obj, gear_types
from .fsl import FailStackList
from .old_settings import ConversionManager, ConversionError
from .utilities import UniqueList


class EnhanceModelSettings(EnhanceSettings):
    VERSION = '0.0.1.9'

    P_FAIL_STACKERS = 'fail_stackers'
    P_FAIL_STACKER_SECONDARY = 'fail_stackers_2'
    P_ENH_FOR_PROFIT = 'for_profit_gear'
    P_ENHANCE_ME = 'enhance_me'
    P_R_FAIL_STACKERS = 'r_fail_stackers'
    P_R_ENHANCE_ME = 'r_enhance_me'
    P_R_STACKER_SECONDARY = 'r_fail_stackers_2'
    P_R_FOR_PROFIT = 'r_for_profit_gear'
    P_ALTS = 'alts'
    P_VALKS = 'valks'
    P_NADERR_BAND = 'naderrs_band'
    P_QUEST_FS_INC = 'quest_fs_inc'
    P_GENOME_FS = 'fs_genome'
    P_VERSION = '_version'
    P_MP_DOMAIN = 'mp_domain'

    def __init__(self, *args, item_store:GearItemStore, **kwargs):
        super(EnhanceModelSettings, self).__init__(*args, item_store=item_store, **kwargs)
        self.gear_reg = {}
        self.item_store = item_store

    def init_settings(self, sets=None):
        fsl = FailStackList(self, None, None, None, None, num_fs=300)
        fsl.set_gnome((0, 22, 2, 4, 8))
        this_sets = {
            self.P_FAIL_STACKERS: [],  # Target fail stacking gear object list
            self.P_FAIL_STACKER_SECONDARY: [],
            self.P_ENH_FOR_PROFIT: [],
            self.P_ENHANCE_ME: [],  # Target enhance gear object list
            self.P_R_FAIL_STACKERS: [],  # Target fail stacking gear objects that are removed from processing
            self.P_R_ENHANCE_ME: [],  # Target enhance gear objects that are removed from processing
            self.P_R_STACKER_SECONDARY: [],
            self.P_R_FOR_PROFIT: [],
            self.P_ALTS: [],  # Information for each alt character
            self.P_VALKS: {},  # Valks saved failstacks
            self.P_NADERR_BAND: [],
            self.P_GENOME_FS: UniqueList(iterable=[fsl]),
            self.P_QUEST_FS_INC: 0,  # Free FS increase from quests
            self.P_MP_DOMAIN: 'na-trade.naeu.playblackdesert.com',
            self.P_VERSION: self.VERSION
        }
        if sets is not None:
            this_sets.update(sets)
        super(EnhanceModelSettings, self).init_settings(sets=this_sets)

    def get_state_json(self):
        super_state = {}

        super_state.update(super(EnhanceModelSettings, self).get_state_json())

        fail_stackers = self[self.P_FAIL_STACKERS]
        fs_secondary = self[self.P_FAIL_STACKER_SECONDARY]
        fsl_p:Set[FailStackList] = self[self.P_GENOME_FS]

        super_state.update({
            self.P_FAIL_STACKERS: [wrap_gear_spec(g) for g in fail_stackers],
            self.P_FAIL_STACKER_SECONDARY: [wrap_gear_spec(g) for g in fs_secondary],
            self.P_ENH_FOR_PROFIT: [wrap_gear_spec(g) for g in self[self.P_ENH_FOR_PROFIT]],
            self.P_ENHANCE_ME: [wrap_gear_spec(g) for g in self[self.P_ENHANCE_ME]],
            self.P_R_FAIL_STACKERS: [wrap_gear_spec(g) for g in self[self.P_R_FAIL_STACKERS]],
            self.P_R_FOR_PROFIT: [wrap_gear_spec(g) for g in self[self.P_R_FOR_PROFIT]],
            self.P_R_STACKER_SECONDARY: [wrap_gear_spec(g) for g in self[self.P_R_STACKER_SECONDARY]],
            self.P_R_ENHANCE_ME: [wrap_gear_spec(g) for g in self[self.P_R_ENHANCE_ME]],
            self.P_GENOME_FS: [x.get_state_json() for x in fsl_p],
            self.P_ALTS: self[self.P_ALTS],
            self.P_VALKS: self[self.P_VALKS],
            self.P_QUEST_FS_INC: self[self.P_QUEST_FS_INC],
            self.P_VERSION: self.VERSION
        })
        item_store = super_state[self.P_ITEM_STORE]
        customs = item_store['custom_prices']
        gear_customs = {}
        gear_entries = [k for k in customs.keys() if isinstance(k, Gear)]
        for ge in gear_entries:
            vm = customs.pop(ge)
            gear_customs[id(ge)] = vm
        super_state['gear_customs'] = gear_customs
        return super_state

    def unwrap_gear_list(self, gl):
        gear_reg = self.gear_reg
        gearz = []
        for gs in gl:
            this_gear = genload_gear(gs, self)
            if 'id' in gs:
                gear_reg[gs['id']] = this_gear
            gearz.append(this_gear)
        return gearz

    def set_state_json(self, state):
        unwrap_gear_list = self.unwrap_gear_list

        P_VERSION = state.pop(self.P_VERSION)
        if not P_VERSION == self.VERSION:
            try:
                if self.f_path is not None:
                    fp = self.f_path + "_backup"+P_VERSION
                    shutil.copyfile(self.f_path, fp)
                converter = ConversionManager(state)
                state = converter.convert(P_VERSION, target_ver=self.VERSION)
                #converter = converters[P_VERSION]
                #state = converter(state)
            except ConversionError:
                raise IOError('Settings file version is not understood.')
        P_FAIL_STACKERS = state.pop(self.P_FAIL_STACKERS)
        P_FAIL_STACKERS = UniqueList(iterable=unwrap_gear_list(P_FAIL_STACKERS))
        P_FAIL_STACKER_SECONDARY = state.pop(self.P_FAIL_STACKER_SECONDARY)
        P_FAIL_STACKER_SECONDARY = UniqueList(iterable=unwrap_gear_list(P_FAIL_STACKER_SECONDARY))

        P_ENH_FOR_PROFIT = state.pop(self.P_ENH_FOR_PROFIT)
        P_ENH_FOR_PROFIT = UniqueList(iterable=unwrap_gear_list(P_ENH_FOR_PROFIT))

        P_R_STACKER_SECONDARY = state.pop(self.P_R_STACKER_SECONDARY)
        P_R_STACKER_SECONDARY = UniqueList(iterable=unwrap_gear_list(P_R_STACKER_SECONDARY))

        P_R_FOR_PROFIT = state.pop(self.P_R_FOR_PROFIT)
        P_R_FOR_PROFIT = UniqueList(iterable=unwrap_gear_list(P_R_FOR_PROFIT))

        P_ENHANCE_ME = state.pop(self.P_ENHANCE_ME)
        P_ENHANCE_ME = UniqueList(iterable=unwrap_gear_list(P_ENHANCE_ME))
        P_R_FAIL_STACKERS = state.pop(self.P_R_FAIL_STACKERS)
        P_R_FAIL_STACKERS = UniqueList(iterable=unwrap_gear_list(P_R_FAIL_STACKERS))
        P_R_ENHANCE_ME = state.pop(self.P_R_ENHANCE_ME)
        P_R_ENHANCE_ME = UniqueList(iterable=unwrap_gear_list(P_R_ENHANCE_ME))

        P_GENOME_FS = state.pop(self.P_GENOME_FS)

        valks = state.pop(self.P_VALKS)
        new_valks = {int(k): v for k,v in valks.items()}
        state[self.P_VALKS] = new_valks

        item_store = state[self.P_ITEM_STORE]
        customs = item_store['custom_prices']
        gear_customs = state.pop('gear_customs')

        for k, v in gear_customs.items():
            gid = int(k)
            if gid in self.gear_reg:
                customs[self.gear_reg[gid]] = {int(x):y for x,y in v.items()}

        super(EnhanceModelSettings, self).set_state_json(state)  # load settings base settings first
        update_r = {
            self.P_FAIL_STACKERS: P_FAIL_STACKERS,
            self.P_FAIL_STACKER_SECONDARY: P_FAIL_STACKER_SECONDARY,
            self.P_ENH_FOR_PROFIT: P_ENH_FOR_PROFIT,
            self.P_ENHANCE_ME: P_ENHANCE_ME,
            self.P_R_FAIL_STACKERS: P_R_FAIL_STACKERS,
            self.P_R_STACKER_SECONDARY: P_R_STACKER_SECONDARY,
            self.P_R_FOR_PROFIT: P_R_FOR_PROFIT,
            self.P_R_ENHANCE_ME: P_R_ENHANCE_ME
        }
        self.update(update_r)
        set_fsl = UniqueList()
        for genome in P_GENOME_FS:
            fsl = FailStackList(self, None, None, None, None)
            fsl.set_state_json(genome)
            set_fsl.add(fsl)
        self[self.P_GENOME_FS] = set_fsl

    def __getstate__(self):
        return self.get_state_json()

    def __setstate__(self, state):
        self.set_state_json(state)


def genload_gear(gear_state:dict, settings) -> Gear:
    gtype = gear_types[gear_state['gear_type']]
    gear = generate_gear_obj(settings, gear_type=gtype)
    gear.set_state_json(gear_state)
    return gear


def wrap_gear_spec(gear:Gear) -> dict:
    json_obj = gear.get_state_json()
    json_obj['id'] = id(gear)
    return json_obj
