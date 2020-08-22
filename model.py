#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧
"""
import numpy, json
from . import common
from .old_settings import converters
import shutil
from typing import List

Gear = common.Gear
Classic_Gear = common.Classic_Gear
Smashable = common.Smashable
gear_types = common.gear_types
EnhanceSettings = common.EnhanceSettings
ItemStore = common.ItemStore
generate_gear_obj = common.generate_gear_obj

class Invalid_FS_Parameters(Exception):
    pass


def genload_gear(gear_state, settings):
    gtype = gear_types[gear_state['gear_type']]
    gear = generate_gear_obj(settings, gear_type=gtype)
    gear.__setstate__(gear_state)
    return gear


class EnhanceModelSettings(common.EnhanceSettings):
    P_FAIL_STACKERS = 'fail_stackers'
    P_ENHANCE_ME = 'enhance_me'
    P_FS_EXCEPTIONS = 'fs_exceptions'
    P_R_FAIL_STACKERS = 'r_fail_stackers'
    P_R_ENHANCE_ME = 'r_enhance_me'
    P_FAIL_STACKERS_COUNT = 'fail_stackers_count'
    P_ALTS = 'alts'
    P_VALKS = 'valks'
    P_NADERR_BAND = 'naderrs_band'
    P_QUEST_FS_INC = 'quest_fs_inc'
    #P_COST_FUNC = 'cost_func'
    P_VERSION = '_version'

    def init_settings(self, sets=None):
        super(EnhanceModelSettings, self).init_settings({
            self.P_FAIL_STACKERS: [],  # Target fail stacking gear object list
            self.P_ENHANCE_ME: [],  # Target enhance gear object list
            self.P_FS_EXCEPTIONS: {},  # Dictionary of fs indexes that have a custom override {int: Gear}
            self.P_R_FAIL_STACKERS: [],  # Target fail stacking gear objects that are removed from processing
            self.P_R_ENHANCE_ME: [],  # Target enhance gear objects that are removed from processing
            self.P_FAIL_STACKERS_COUNT: {},  # Number of fail stacking items available for a gear object
            self.P_ALTS: [],  # Information for each alt character
            self.P_VALKS: {},  # Valks saved failstacks,
            self.P_NADERR_BAND: [],
            self.P_QUEST_FS_INC: 0,  # Free FS increase from quests
            #self.P_COST_FUNC: 'Thorough (Slow)',
            self.P_VERSION: Enhance_model.VERSION
        })

    def __getstate__(self):
        super_state = {}
        super_state.update(super(EnhanceModelSettings, self).__getstate__())
        fail_stackers = self[self.P_FAIL_STACKERS]
        super_state.update({
            self.P_FAIL_STACKERS: [g.__getstate__() for g in fail_stackers],
            self.P_ENHANCE_ME: [g.__getstate__() for g in self[self.P_ENHANCE_ME]],
            self.P_FS_EXCEPTIONS: {k:fail_stackers.index(v) for k,v in self[self.P_FS_EXCEPTIONS].items()},
            self.P_R_FAIL_STACKERS: [g.__getstate__() for g in self[self.P_R_FAIL_STACKERS]],
            self.P_R_ENHANCE_ME: [g.__getstate__() for g in self[self.P_R_ENHANCE_ME]],
            self.P_FAIL_STACKERS_COUNT: {fail_stackers.index(k):v for k,v in self[self.P_FAIL_STACKERS_COUNT].items()},
            self.P_ALTS: self[self.P_ALTS],
            self.P_VALKS: self[self.P_VALKS],
            self.P_QUEST_FS_INC: self[self.P_QUEST_FS_INC],
            self.P_VERSION: Enhance_model.VERSION
        })
        return super_state

    def __setstate__(self, state):
        P_VERSION = state.pop(self.P_VERSION)
        if P_VERSION not in self.versions():
            try:
                if self.f_path is not None:
                    fp = self.f_path + "_backup"+P_VERSION
                    shutil.copyfile(self.f_path, fp)
                converter = converters[P_VERSION]
                state = converter(state)
            except KeyError:
                raise IOError('Settings file version is not understood.')
        P_FAIL_STACKERS = state.pop(self.P_FAIL_STACKERS)
        P_FAIL_STACKERS = [genload_gear(g, self) for g in P_FAIL_STACKERS]
        P_ENHANCE_ME = state.pop(self.P_ENHANCE_ME)
        P_ENHANCE_ME = [genload_gear(g, self) for g in P_ENHANCE_ME]
        P_R_FAIL_STACKERS = state.pop(self.P_R_FAIL_STACKERS)
        P_R_FAIL_STACKERS = [genload_gear(g, self) for g in P_R_FAIL_STACKERS]
        P_R_ENHANCE_ME = state.pop(self.P_R_ENHANCE_ME)
        P_R_ENHANCE_ME = [genload_gear(g, self) for g in P_R_ENHANCE_ME]

        #for i in P_ENHANCE_ME:
        #    print "{} is a ({}) {}".format(i.name, i.gear_type.name, type(i))

        P_FS_EXCEPTIONS = state.pop(self.P_FS_EXCEPTIONS)
        P_FAIL_STACKERS_COUNT = state.pop(self.P_FAIL_STACKERS_COUNT)
        valks = state.pop(self.P_VALKS)
        new_valks = {int(k): v for k,v in valks.items()}
        state[self.P_VALKS] = new_valks
        super(EnhanceModelSettings, self).__setstate__(state)  # load settings base settings first
        update_r = {
            self.P_FAIL_STACKERS: P_FAIL_STACKERS,
            self.P_ENHANCE_ME: P_ENHANCE_ME,
            self.P_R_FAIL_STACKERS: P_R_FAIL_STACKERS,
            self.P_R_ENHANCE_ME: P_R_ENHANCE_ME,
            self.P_FS_EXCEPTIONS: {int(k):P_FAIL_STACKERS[int(v)] for k,v in P_FS_EXCEPTIONS.items()},
            self.P_FAIL_STACKERS_COUNT: {P_FAIL_STACKERS[int(k)]:int(v) for k,v in P_FAIL_STACKERS_COUNT.items()}
        }
        self.update(update_r)

    def versions(self):
        return [
            Enhance_model.VERSION
        ]


class Enhance_model(object):
    VERSION = "0.0.1.4"
    """
    Do not catch exceptions here unless they are a disambiguation.
    """
    def __init__(self):
        self.settings = EnhanceModelSettings()

        #self.equipment_costs = []  # Cost of equipment
        #self.r_equipment_costs = []  # Cost of removed equipment
        self.optimal_fs_items = []  # Fail stack items chosen as optimal at each fails tack index
        self.fs_cost = []  # Cost of each fail stack
        self.fs_probs = []  # Probability of gaining fail stack
        self.cum_fs_probs = []  # Cumulative chance of gaining fail stack
        self.cum_fs_cost = []  # Cumulative cost of gaining a fail stack
        self.custom_input_fs = {}

        self.fs_needs_update = True
        self.gear_cost_needs_update = True
        self.auto_save = True

        self.dragon_scale_30 = False
        self.dragon_scale_350 = False
        self.cost_funcs = {
            'Estimate (Fast)': 0,
            '2-Point Average (Moderate)': 1,
            'Average (Moderate)': 1,
            'Thorough (Slow)': 2
        }

    def edit_fs_exception(self, fs_index, fs_item):
        """
        Adds an exception to the automatically generated fail stack cost list.
        :param fs_index: This is the index that corresponds to a fail stack count
        :param fs_item: This is the gear object that will be forced at the fs_index
        :return: None
        """
        self.settings[[EnhanceModelSettings.P_FS_EXCEPTIONS, fs_index]] = fs_item
        self.invalidate_failstack_list()
        #self.fs_exceptions[fs_index] = fs_item

    def add_fs_item(self, this_gear):
        fail_stackers = self.settings[EnhanceModelSettings.P_FAIL_STACKERS]
        fail_stackers.append(this_gear)
        self.settings.changes_made = True
        self.invalidate_failstack_list()
        self.save()

    def update_costs(self, gear_list: List[Gear]):
        settings = self.settings
        item_store: ItemStore = settings[settings.P_ITEM_STORE]
        for gear in gear_list:
            item_store.check_in_gear(gear)
            gear.set_base_item_cost(item_store.get_cost(gear, grade=0))

    def add_equipment_item(self, this_gear):
        enhance_me = self.settings[EnhanceModelSettings.P_ENHANCE_ME]
        enhance_me.append(this_gear)
        self.settings.changes_made = True
        self.invalidate_enahce_list()
        self.save()

    def clean_min_fs(self):
        settings = self.settings
        alts = settings[settings.P_ALTS]
        naderr = settings[settings.P_NADERR_BAND]

        min_fs = self.get_min_fs()

        for i,n in enumerate(naderr):
            if n < min_fs:
                naderr[i] = min_fs

        for i, pack in enumerate(alts):
            pic_path, name, fs = pack
            if fs < min_fs:
                alts[i][2] = min_fs

    def set_cost_bs_a(self, cost_bs_a):
        self.settings[[EnhanceSettings.P_ITEM_STORE, ItemStore.P_BLACK_STONE_ARMOR]] = float(cost_bs_a)
        self.invalidate_enahce_list()
        self.invalidate_all_gear_cost()

    def set_cost_bs_w(self, cost_bs_w):
        self.settings[[EnhanceSettings.P_ITEM_STORE, ItemStore.P_BLACK_STONE_WEAPON]] = float(cost_bs_w)
        self.invalidate_enahce_list()
        self.invalidate_all_gear_cost()

    def set_cost_conc_a(self, cost_conc_a):
        self.settings[[EnhanceSettings.P_ITEM_STORE, ItemStore.P_CONC_ARMOR]] = float(cost_conc_a)
        self.invalidate_enahce_list()
        self.invalidate_all_gear_cost()

    def set_cost_conc_w(self, cost_conc_w):
        self.settings[[EnhanceSettings.P_ITEM_STORE, ItemStore.P_CONC_WEAPON]] = float(cost_conc_w)
        self.invalidate_enahce_list()
        self.invalidate_all_gear_cost()

    def set_cost_hard(self, cost_conc_a):
        self.settings[[EnhanceSettings.P_ITEM_STORE, ItemStore.P_HARD_BLACK]] = float(cost_conc_a)
        self.invalidate_enahce_list()
        self.invalidate_all_gear_cost()

    def set_cost_sharp(self, cost_conc_w):
        self.settings[[EnhanceSettings.P_ITEM_STORE, ItemStore.P_SHARP_BLACK]] = float(cost_conc_w)
        self.invalidate_enahce_list()
        self.invalidate_all_gear_cost()

    def set_cost_meme(self, cost_meme):
        self.settings[[EnhanceSettings.P_ITEM_STORE, ItemStore.P_MEMORY_FRAG]] = float(cost_meme)
        self.invalidate_enahce_list()
        self.invalidate_all_gear_cost()

    def set_cost_cron(self, cost_cron):
        self.settings[EnhanceSettings.P_CRON_STONE_COST] = float(cost_cron)
        #self.cost_cron = float(cost_cron)

    def set_cost_cleanse(self, cost_cleanse):
        self.settings[EnhanceSettings.P_CLEANSE_COST] = float(cost_cleanse)
        #self.cost_cleanse = float(cost_cleanse)

    def set_market_tax(self, mtax):
        self.settings[EnhanceSettings.P_MARKET_TAX] = float(mtax)
        self.settings.recalc_tax()

    #def set_cost_func(self, str_cost_f):
    #    self.settings[EnhanceModelSettings.P_COST_FUNC] = str_cost_f

    def quest_fs_inc_changed(self, fs):
        self.settings[EnhanceModelSettings.P_QUEST_FS_INC] = int(fs)

    def get_min_fs(self):
        return self.settings[EnhanceModelSettings.P_QUEST_FS_INC]

    def value_pack_changed(self, val):
        self.settings[EnhanceSettings.P_VALUE_PACK] = val
        self.settings.recalc_tax()

    def merch_ring_changed(self, val):
        self.settings[EnhanceSettings.P_MERCH_RING] = val
        self.settings.recalc_tax()

    def using_merch_ring(self, val):
        self.settings[EnhanceSettings.P_MERCH_RING_ACTIVE] = val
        self.settings.recalc_tax()

    def using_value_pack(self, val):
        self.settings[EnhanceSettings.P_VALUE_PACK_ACTIVE] = val
        self.settings.recalc_tax()

    def set_cost_dragonscale(self, cost_dscale):
        self.settings[[EnhanceSettings.P_ITEM_STORE, ItemStore.P_DRAGON_SCALE]] = float(cost_dscale)

    def invalidate_enahce_list(self):
        self.gear_cost_needs_update = True
        self.save()

    def invalidate_all_gear_cost(self):
        settings = self.settings
        enhance_me = settings[EnhanceModelSettings.P_ENHANCE_ME]
        r_enhance_me = settings[EnhanceModelSettings.P_R_ENHANCE_ME]

        for x in enhance_me + r_enhance_me:
            x.costs_need_update = True

    def invalidate_failstack_list(self):
        self.fs_needs_update = True
        self.optimal_fs_items = []
        self.fs_cost = []
        self.cum_fs_cost = []
        self.cum_fs_probs = []
        self.fs_probs = []
        self.invalidate_enahce_list()

    def edit_fs_item(self, old_gear, gear_obj):
        fail_stackers = self.settings[EnhanceModelSettings.P_FAIL_STACKERS]
        r_fail_stackers = self.settings[EnhanceModelSettings.P_R_FAIL_STACKERS]
        if old_gear in fail_stackers:
            fail_stackers.remove(old_gear)
            fail_stackers.append(gear_obj)
            self.settings.changes_made = True
        elif old_gear in r_fail_stackers:
            r_fail_stackers.remove(old_gear)
            r_fail_stackers.append(gear_obj)
            self.settings.changes_made = True
        self.save()

    def swap_gear(self, old_gear: common.Gear, gear_obj: common.Gear):
        self.edit_fs_item(old_gear, gear_obj)
        self.edit_enhance_item(old_gear, gear_obj)

    def edit_enhance_item(self, old_gear, gear_obj):
        enhance_me = self.settings[EnhanceModelSettings.P_ENHANCE_ME]
        r_enhance_me = self.settings[EnhanceModelSettings.P_R_ENHANCE_ME]
        if old_gear in enhance_me:
            enhance_me.remove(old_gear)
            enhance_me.append(gear_obj)
            self.settings.changes_made = True
        elif old_gear in r_enhance_me:
            r_enhance_me.remove(old_gear)
            r_enhance_me.append(gear_obj)
            self.settings.changes_made = True
        self.save()
        #self.enhance_me.append(gear_obj)

    def get_max_fs(self):
        return self.settings[EnhanceSettings.P_NUM_FS]

    def calcFS(self):
        settings = self.settings
        num_fs = self.get_max_fs()
        fail_stackers = settings[EnhanceModelSettings.P_FAIL_STACKERS]
        fs_exceptions = settings[EnhanceModelSettings.P_FS_EXCEPTIONS]
        fs_items = []
        fs_cost = []
        cum_fs_cost = []
        cum_fs_probs = []
        fs_probs = []


        list(map(lambda x: x.prep_lvl_calc(), fail_stackers))


        if len(fail_stackers) < 1:
            raise Invalid_FS_Parameters('Must have at least one item on fail stacking list.')

        last_rate = 0
        cum_probability = 1
        fs_num = num_fs+1
        min_fs = self.get_min_fs()

        for i in range(0, min_fs):
            fs_probs.append(1.0)
            cum_fs_probs.append(1.0)
            fs_items.append(None)
            fs_cost.append(0)
            cum_fs_cost.append(0)


        for i in range(min_fs, fs_num):
            if i in fs_exceptions:
                this_fs_item: Gear = fs_exceptions[i]
                this_fs_cost = this_fs_item.simulate_FS(i, last_rate)
            else:
                trys = [x.simulate_FS(i, last_rate) for x in fail_stackers]
                this_fs_idx = int(numpy.argmin(trys))
                this_fs_cost = trys[this_fs_idx]
                this_fs_item: Gear = fail_stackers[this_fs_idx]
                if i == 19:
                    dsc = settings[settings.P_ITEM_STORE].get_cost(ItemStore.P_DRAGON_SCALE)
                    cost = dsc * 30
                    if cost < last_rate:
                        last_rate = 0
                        this_fs_cost = cost
                        self.dragon_scale_30 = True
                    else:
                        self.dragon_scale_30 = False
                    this_fs_cost = min(this_fs_cost, cost)
                elif i == 39:
                    dsc = settings[settings.P_ITEM_STORE].get_cost(ItemStore.P_DRAGON_SCALE)
                    cost = dsc * 350
                    if cost < last_rate:
                        last_rate = 0
                        this_fs_cost = cost
                        self.dragon_scale_350 = True
                    else:
                        self.dragon_scale_350 = False
            this_cum_cost = last_rate + this_fs_cost
            this_prob = 1.0 - this_fs_item.gear_type.map[this_fs_item.get_enhance_lvl_idx()][i]
            if this_fs_item.fs_gain() > 1:
                cum_probability *= this_prob ** (1/this_fs_item.fs_gain())
            else:
                cum_probability *= this_prob
            fs_probs.append(this_prob)
            cum_fs_probs.append(cum_probability)
            fs_items.append(this_fs_item)
            fs_cost.append(this_fs_cost)
            cum_fs_cost.append(this_cum_cost)
            last_rate = this_cum_cost

        #fsa = [x for x in fail_stackers if isinstance(x, Classic_Gear)]
        #list(map(lambda x: x.simulate_Enhance_sale(cum_fs_cost), fsa))

        self.optimal_fs_items = fs_items
        self.fs_cost = fs_cost
        self.cum_fs_cost = cum_fs_cost
        self.cum_fs_probs = cum_fs_probs
        self.fs_probs = fs_probs
        self.fs_needs_update = False

    def calc_equip_costs(self, gear=None):
        settings = self.settings
        enhance_me = settings[EnhanceModelSettings.P_ENHANCE_ME]
        if gear is None:
            euip = enhance_me + settings[EnhanceModelSettings.P_R_ENHANCE_ME]
        else:
            euip = gear

        fail_stackers = settings[EnhanceModelSettings.P_FAIL_STACKERS]
        num_fs = settings[EnhanceSettings.P_NUM_FS]

        if len(euip) < 1:
            raise ValueError('No enhancement items to calculate.')

        # ~ DEAD CODE FOR CHANGING ENHANCE COST FUNCTION ~
        #try:
        #    meth = self.cost_funcs[settings[settings.P_COST_FUNC]]
        #    fnc = lambda x: x.set_enhance_cost_func(meth)
        #    [x.set_enhance_cost_func(meth) for x in euip]
        #except KeyError:
        #    pass

        gts = [x.gear_type for x in euip]
        gts = set(gts)

        # Need to fill the gap between the fail stack calculated at num_fs and the potential for gear to roll past it
        for gt in gts:
            for glmap in gt.p_num_f_map:
                foo = glmap[num_fs]

        if self.fs_needs_update:
            self.calcFS()

        cum_fs = self.cum_fs_cost
        # The map object has the highest stack needed for the overflow since it will be pushed up by the resolving of p_num_f_map
        this_max_fs = len(gts.pop().map[0]) + 1
        cum_fs_s = numpy.zeros(this_max_fs)
        cum_fs_s[1:num_fs + 2] = cum_fs
        last_rate = cum_fs[-1]
        for i in range(num_fs + 2, this_max_fs):
            last_rate += min([x.simulate_FS(i, last_rate) for x in fail_stackers])
            cum_fs_s[i] = last_rate
        # this_fs_idx = int(numpy.argmin(trys))

        eq_c = [x.enhance_cost(cum_fs_s) for x in euip]
        #if gear is None:  # This means that all hear was updated
        need_update = False
        for gear in enhance_me:
            need_update |= len(gear.cost_vec) < 1
            if need_update is True:
                break
        self.gear_cost_needs_update = need_update
        if len(eq_c) > 0:
            return eq_c
        else:
            raise Invalid_FS_Parameters('There is no equipment selected for enhancement.')

    def calcEnhances(self, enhance_me=None, fail_stackers=None, count_fs=False, count_fs_fs=True, devaule_fs=False, regress=False):
        if self.fs_needs_update:
            self.calcFS()

        settings = self.settings
        if enhance_me is None:
            enhance_me = settings[EnhanceModelSettings.P_ENHANCE_ME]
        if fail_stackers is None:
            fail_stackers = settings[EnhanceModelSettings.P_FAIL_STACKERS]

        if self.gear_cost_needs_update:
            self.calc_equip_costs(gear=enhance_me)

        if len(enhance_me) < 1:
            raise ValueError('No enhance items')
            return
        if len(fail_stackers) < 1:
            raise ValueError('No fail stacking items')
            return

        num_fs = settings[EnhanceSettings.P_NUM_FS]
        cum_fs_cost = self.cum_fs_cost
        cum_fs_cost = numpy.roll(cum_fs_cost, 1)
        cum_fs_cost[0] = 0
        fs_cost = self.fs_cost

        min_fs = self.get_min_fs()

        new_fs_cost = fs_cost[:]

        fs_len = num_fs+1


        # This is a bit hacky and confusing but we need a cost estimate on potential fs gain vs recovery loss on items that have no success gain
        # For fail-stacking items there should not be a total cost gained from success. It only gains value from fail stacks.
        #zero_out = lambda x: x.enhance_lvl_cost(cum_fs_cost,  total_cost=numpy.array([[0]*fs_len]*len(x.gear_type.map)), count_fs=count_fs)

        balance_vec_fser = [x.fs_lvl_cost(cum_fs_cost, count_fs=count_fs_fs) for x in fail_stackers]
        balance_vec_enh = [x.enhance_lvl_cost(cum_fs_cost, count_fs=count_fs) for x in enhance_me]

        balance_vec_fser = numpy.array(balance_vec_fser)
        balance_vec_enh = numpy.array(balance_vec_enh)

        min_gear_map = [numpy.argmin(x) for x in balance_vec_enh.T]

        def check_out_gains(balance_vec, gains_lookup_vec, gear_list, fs_cost):
            """
            This method adds the value of increasing gains on gear that is ahead in the strategy fs list.
            For example:
            When attempting TRI on a weapon, if the user fails enhancement they will gain 3 fail stacks and these fail
            stacks have a value that is the increased chance of success with the 3 fail stacks. The actual cost is
            calculated by looking at what price of gear is up for enhancement 3 fail stacks higher then the qgear in
            question.
            If the gear ahead happens to be more expensive once the enhancement fails that gain becomes a cost.
            :param balance_vec:
            :param gains_lookup_vec:
            :param gear_list:
            :param fs_cost:
            :return:
            """
            #gearz = map(lambda x: gear_list[x], min_gear_map)
            # indexed by enhance_me returns the number of fail stacks gained by a failure
            gainz = [x.fs_gain() for x in gear_list]
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
            chances = numpy.array([x.gear_type.map[x.get_enhance_lvl_idx()][:num_fs+1] for x in gear_list]).T

            # The very last item has to be a self pointer only
            # Not double counting fs cost bc this is a copy
            this_bal_vec = numpy.copy(balance_vec)
            # cycle through all fsil stack levels
            for i in range(min_fs, fs_len):
                lookup_idx = i
                #this_gear = gearz[lookup_idx]

                cost_emmend = numpy.zeros(len(balance_vec))
                # cycle through all types of gear packaged by the number of fail stacks they will gain. Since it will be
                # the same gain value
                for num_fs_gain, gear_idx_list in fs_dict.items():
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
                    go:Gear = enhance_me[min_gear_map[i]]
                    co = go.get_cost_obj()[go.enhance_lvl_to_number()]
                    r_gear_cost_current_fs = co[lookup_idx]
                    r_gear_cost_ahead_fs = co[fs_pointer_idx]

                    if balance_vec is balance_vec_enh:
                        self_reduction = r_gear_cost_ahead_fs - r_gear_cost_current_fs

                    else:
                        self_reduction = 0
                    self_reduction = r_gear_cost_ahead_fs - r_gear_cost_current_fs

                    gear_pointed_cost = gear_cost_ahead_fs - gear_cost_current_fs
                    if devaule_fs:
                        projected_gain = gear_pointed_cost
                        projected_gain = max(gear_pointed_cost, gain_cost)
                    else:
                        #projected_gain = max(gain_cost, min(0,self_reduction))
                        #projected_gain = min(0  , self_reduction)
                        #projected_gain = 0
                        projected_gain = gain_cost
                        #print(
                        #    'FS: {} | Gear {} | Cost: {} | Gain: {}'.format(i, go.get_full_name(),
                        #                                         self_reduction, projected_gain))
                    # All gear at this FS level and gain level have the same cost diff
                    cost_emmend[gear_idx_list] = projected_gain
                    #print cost_emmend

                fail_rate = 1 - chances[lookup_idx]

                this_bal_vec.T[lookup_idx] += numpy.multiply(fail_rate, cost_emmend)

                if balance_vec is balance_vec_enh:  # only update minimums when we are looking at the enhancement gear
                    new_min_idx = numpy.argmin(this_bal_vec.T[lookup_idx])
                    min_gear_map[lookup_idx] = new_min_idx
            return this_bal_vec

        enh_vec_ammend = check_out_gains(balance_vec_enh, balance_vec_enh, enhance_me, new_fs_cost)
        fs_vec_ammend = check_out_gains(balance_vec_fser, balance_vec_enh, fail_stackers, new_fs_cost)

        if devaule_fs and regress:
            raise NotImplementedError('This doesnt really work')
            max_iter = 100
            counter = 0
            changes = True
            while changes and counter<max_iter:
                min_gear_map_prev = min_gear_map[:]
                enh_vec_ammend = check_out_gains(balance_vec_enh, balance_vec_enh, enhance_me, new_fs_cost)
                fs_vec_ammend = check_out_gains(balance_vec_fser, balance_vec_enh, fail_stackers, new_fs_cost)

                changes = not min_gear_map == min_gear_map_prev
                counter += 1

        balance_vec_enh = enh_vec_ammend
        balance_vec_fser = fs_vec_ammend

        return balance_vec_fser, balance_vec_enh

    def calcEnhances_backup(self, count_fs=False, count_fs_fs=True, devaule_fs=False, regress=False):
        if self.fs_needs_update:
            self.calcFS()
        if self.gear_cost_needs_update:
            self.calc_equip_costs()
        settings = self.settings
        enhance_me = settings[EnhanceModelSettings.P_ENHANCE_ME]
        num_fs = settings[EnhanceSettings.P_NUM_FS]
        fail_stackers = settings[EnhanceModelSettings.P_FAIL_STACKERS]
        cum_fs_cost = self.cum_fs_cost
        fs_cost = self.fs_cost
        enhance_me = enhance_me

        new_fs_cost = fs_cost[:]

        fs_len = num_fs+1


        # This is a bit hacky and confusing but we need a cost estimate on potential fs gain vs recovery loss on items that have no success gain
        # For fail-stacking items there should not be a total cost gained from success. It only gains value from fail stacks.
        #zero_out = lambda x: x.enhance_lvl_cost(cum_fs_cost,  total_cost=numpy.array([[0]*fs_len]*len(x.gear_type.map)), count_fs=count_fs)

        balance_vec_fser = [x.fs_lvl_cost(cum_fs_cost, count_fs=count_fs_fs) for x in fail_stackers]
        balance_vec_enh = [x.enhance_lvl_cost(cum_fs_cost, count_fs=count_fs) for x in enhance_me]

        balance_vec_fser = numpy.array(balance_vec_fser)
        balance_vec_enh = numpy.array(balance_vec_enh)

        min_gear_map = [numpy.argmin(x) for x in balance_vec_enh.T]

        def check_out_gains(balance_vec, gains_lookup_vec, gear_list, fs_cost):
            """
            This method adds the value of increasing gains on gear that is ahead in the strategy fs list.
            For example:
            When attempting TRI on a weapon, if the user fails enhancement they will gain 3 fail stacks and these fail
            stacks have a value that is the increased chance of success with the 3 fail stacks. The actual cost is
            calculated by looking at what price of gear is up for enhancement 3 fail stacks higher then the qgear in
            question.
            If the gear ahead happens to be more expensive once the enhancement fails that gain becomes a cost.
            :param balance_vec:
            :param gains_lookup_vec:
            :param gear_list:
            :param fs_cost:
            :return:
            """
            #gearz = map(lambda x: gear_list[x], min_gear_map)
            # indexed by enhance_me returns the number of fail stacks gained by a failure
            gainz = [x.fs_gain() for x in gear_list]
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
            chances = numpy.array([x.gear_type.map[x.get_enhance_lvl_idx()][:num_fs+1] for x in gear_list]).T

            # The very last item has to be a self pointer only
            this_bal_vec = numpy.copy(balance_vec)
            # cycle through all fsil stack levels
            for i in range(1, fs_len+1):
                lookup_idx = fs_len - i
                #this_gear = gearz[lookup_idx]

                cost_emmend = numpy.zeros(len(balance_vec))
                # cycle through all types of gear packaged by the number of fail stacks they will gain. Since it will be
                # the same gain value
                for num_fs_gain, gear_idx_list in fs_dict.items():
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
                    if devaule_fs:

                        #projected_gain = max(gear_pointed_cost, gain_cost)
                        projected_gain = gear_pointed_cost

                        #projected_gain = gear_pointed_cost
                        #gear_fs_cost = gear_pointed_cost
                        #new_fs_cost[i-1] = gear_fs_cost

                        #new_fs_cost[i - 1] = -projected_gain
                    else:
                        projected_gain = gain_cost
                    #projected_gain = gain_cost
                    # All gear at this FS level and gain level have the same cost diff
                    cost_emmend[gear_idx_list] = projected_gain
                    #print cost_emmend

                fail_rate = 1 - chances[lookup_idx]

                this_bal_vec.T[lookup_idx] += numpy.multiply(fail_rate, cost_emmend)

                if balance_vec is balance_vec_enh:  # only update minimums when we are looking at the enhancement gear
                    new_min_idx = numpy.argmin(this_bal_vec.T[lookup_idx])
                    min_gear_map[lookup_idx] = new_min_idx
            return this_bal_vec
                #gearz[lookup_idx] = gear_list[new_min_idx]

        #changed = [False]*fs_len
        #vals = [None]*fs_len
        enh_vec_ammend = check_out_gains(balance_vec_enh, balance_vec_enh, enhance_me, new_fs_cost)
        fs_vec_ammend = check_out_gains(balance_vec_fser, balance_vec_enh, fail_stackers, new_fs_cost)

        if devaule_fs and regress:
            max_iter = 100
            counter = 0
            changes = True
            while changes and counter<max_iter:
                min_gear_map_prev = min_gear_map[:]
                enh_vec_ammend = check_out_gains(balance_vec_enh, balance_vec_enh, enhance_me, new_fs_cost)
                fs_vec_ammend = check_out_gains(balance_vec_fser, balance_vec_enh, fail_stackers, new_fs_cost)

                changes = not min_gear_map == min_gear_map_prev
                counter += 1

        balance_vec_enh = enh_vec_ammend
        balance_vec_fser = fs_vec_ammend
        #for i, val in enumerate(changed):
        #    print 'FS: {}\t| B: {}\t| C: {}'.format(i, val, vals[i])

        #self.fs_cost = new_fs_cost
        return balance_vec_fser, balance_vec_enh

    def save_to_file(self, txt_path=None):
        if txt_path is None:
            # Force a write
            txt_path = self.settings.f_path
            if txt_path is None:
                txt_path = common.DEFAULT_SETTINGS_PATH
        self.settings.save(file_path=txt_path)

    def save(self):
        if not self.settings.f_path is None:
            self.settings.save()

    def load_from_file(self, txt_path):
        #TODO: add error checking here so setings files dont get overwritten
        self.settings.load(txt_path)
        settings = self.settings
        max_fs = settings[settings.P_NUM_FS]
        min_fs = settings[settings.P_QUEST_FS_INC]
        for i, pack in enumerate(settings[settings.P_ALTS]):
            alt_pic, alt_name, alt_fs = pack
            if alt_fs > max_fs:
                max_fs = alt_fs
                settings[settings.P_NUM_FS] = max_fs
            if alt_fs < min_fs:
                pack[2] = min_fs
                settings.invalidate()
        for i in settings[settings.P_VALKS]:
            if i > max_fs:
                max_fs = i
                settings[settings.P_NUM_FS] = max_fs

    def to_json(self):
        return json.dumps(self.settings.__getstate__(), indent=4)

    def from_json(self, json_str):
        self.settings.__setstate__(json.loads(json_str))
        self.clean_min_fs()
