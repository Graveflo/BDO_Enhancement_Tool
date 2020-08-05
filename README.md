# BDO Enhancement Optimizer
I've throw together this fail stack calculator so that I could try out 
the new enhancement chance numbers that were released. I also wanted to 
get a more objective way to decide how to fail stack and enhance when 
considering multiple different pieces of gear at different enhancement levels.

It still needs more testing and the code  could be commented better, but I am posting 
the code so it isn't necessary to wait on me and you can alter it as you please.

<p align="center">
  <img src="Images/Equipment.png">
</p>
<p align="center">
  <img src="Images/compact_overlay.png">
</p>

## GUI User guide
### 1.) Go to the "Monnies/ MP" tab on the left side of the program.

2.) Chose if you want to sign into the online Central Market or manually enter prices
* To sign into the Central Market click "Tools" -> "Sign into MP" on the main menu. Once you sign in a green message
should show on the main window status bar. You can close the Central Market sign in window or keep it up.

3.) If you have done the Bartali quest line or have free permanent fail stacks, set the "Quest FS Increase" field 
to your minimum fail stack.

4.) Make sure "Value Pack Active?" is checked if you will be using a Value Pack when interacting with the central market.

### 5.) Go to the "FS Gear" tab on the left side of the program.

6.) This is the gear you will be using to build fail stacks and not yet attempting an enhancement.
There should be a list of default gear if you just installed the program.

7.) To add gear press "Add Item." You can click on the magnifying glass icon in the "Name" column of the table to bring up a search window. Type in the gear you are
looking for and find it on the list. Double click it to register the gear with a picture, name, type and central market
functionality. Un-checking gear will keep it out of the algorithm later.

8.) If you signed into the online central market press "MP: Update all" to automatically update the gear costs from the central market.

9.) "Sale Success", "Sale Fail" and "Procurement Cost" should be zero unless you are fail stacking on the gear by buying it on the central 
market and selling it. In this case do not include tax here. Tax is automatically calculated from the settings in the previous section.

### 10.) OPTIONAL: Go to the "FS Cost" tab on the left side of the program.

11.) Click refresh to generate a list of what to fail stack on. The numbers here should be fairly self explanatory

### 12.) Go to the "Equipment" tab on the left side of the program.

13.) To add gear press "Add Item." You can click on the magnifying glass icon in the "Name" column of the table to bring up a search window. Type in the gear you are
looking for and find it on the list. Double click it to register the gear with a picture, name, type and central market
functionality. Un-checking gear will keep it out of the algorithm later.

14.) Add gear here that you are working on enhancing. Once you add a piece of gear you can expand the item
too see future enhancements for that item. All of the checked levels of enhancement will be considered by the algorithm
but it is important to distinguish the current level of the gear. This is used to calculate when to save a fail stack and 
when to attempt an enhancement
* Note that in the "Strategy" tab, only items that are on this list are considered by the algorithm, so this can lead to decisions that would otherwise be odd
like attempting an enhancement on a low fail stack or greatly overstacking for an item. If you are only going to attempt enhancements on the gear in this list
and you either know when to stop, or you have future enhancements checked under your current gear you should be good to go.

15.) Once you have all your gear set up, click "MP: Update Base Cost" if you are signed into the market place or manually enter the cost
of a base item for each of the gear.

16.) OPTIONAL: Press "Calculate Costs" to calculate: the fail stack to start enhancing the gear, the total cost, 
the total cost of repair materials + upfront costs, the average number of fails before success, starting probability and
if you should use memory fragments.

17.) The cost, and optimal failstack numbers where minimize the total cost of the enhancement. Later in the
program this is referred to as a "Loss prevention" calculation.


### 18.) Go to the "Strategy" tab on the left side of the program.

19.) Press "Calculate"


## Future Plans
* graphs
* Export to Excel
* Make UI more betterer in some places

## How run code
If you are unsure how to set up the environment see the \"Dependencies\" section below.
Make sure the directory that houses the code is in python path variable and run:
```
python.exe -m BDO_Enhancement_Tool
```

This will spawn the window and create a log file in the same directory as \"common.py\"

Start by making sure the prices are correct in the \"Monnies \\ MP\" tab. Make sure to click the "Manage Saved Fail Stacks"
 to input your Advice of Valks items and "Manage Alts/Toons" to register your alts and fail stacks stored on them.

Next enter your fail stacking gear \(reblath, rosar, etc.\) in the \"FS Gear\" section. Click the magnifying glass icon
to search through a database of items.

**Gear is entered at the TARGET level of enhancement. For example a +14 Reblath Helmet is entered at Level 15**

By the above you see that the highest level for all is PEN. This means that entering in PEN is a TET item because PEN is the target enhancement level. This makes less sense for fail stacking items, but for now this is how we enter gear.

<b>Automatic:</b> After FS gear is entered, switch to the \"FS Cost\" tab and hit \"Refresh\". This should create a list of fail stacks. You can override an item on this list by selecting the row and clicking \"Change Item\".

Next enter your gear in the \"Equipment\" section and click \"Calculate Cost\" to get info on your gear relative to your fail stacking items.
 Click the magnifying glass icon
to search through a database of items.

Lastly, on the \"Strategy\" tab click \"Calculate\" to get a list of fail stacks and items. Click on items in the list to get a break down of cost and risk for each item.

You can click the "Open Guide Overlay" button at the bottom of the strategy tab to open a smaller window with decision for
you to choose from. Each decision path automatically updates the program. If you switch on "Always on top" mode from the
View main menu and put BDO in windowed or full screen window mode you can use this tool while you are enhancing. 


## Dependencies
This project depends on several libraries and some libraries of 
my own. For this project to work the utilities and QtCommon module 
collection must be present. These are small versions of larger modules 
that I copied and cleaned for convenience.

See [requirements.txt](https://github.com/ILikesCaviar/BDO_Enhancement_Tool/blob/master/requirements.txt) for details:

* fuzzywuzzy==0.18.0
* numpy==1.19.0
* PyQt5==5.15.0
* PyQt5-sip==12.8.0
* python-Levenshtein==0.12.0
* urllib3==1.25.9


### Standard
* sys
* io
* types
* traceback
* operator 

### Versions
It is recommended to install Anaconda python distribution 2.7 for this 
project because that is how it was developed.

See: [Downloads | Anaconda](https://www.anaconda.com/download/)
```
> python --version
Python 3.7.6
> python -m conda --version
conda 4.8.3
```

## Methods
To be clear, I am not great at statistics so I highly encourage anyone 
who know what they are doing to critique the methods I am using to 
calculate. I detail the math here in the hopes that someone may destroy 
it \:\)

### Establishing Fail Stack Cost
The cost of a fail is an important factor in the calculation because it 
establishes a curve of value that equipment and opportunity cost rely on.

The essence of a fail stack cost at any level of fail stacks is the 
opportunity cost of acquiring another fail stack and the value of the 
current fail stack.

The opportunity cost pseudo code:
```
op_cost = black_stone_cost + (suc_rate * (last_cost + return_cost)) + (fail_rate * repair_cost)
```
Here, there is:
* black_stone_cost : Cost of black stone in one enhance attempt
* suc_rate : Probability of success enhancement
* last_cost : If this cost function of a fail stack \(F\) at position x then this is F\(x - 1\)
* return_cost : Cost to return the gear to how it was before the success. This is either cleanse cost or the cost of materials in the case of accessories (rely on cost class member in this case)
* reapir_cost : This is the cost to restore the gear after a fail
* See common.py -> simulate_FS

Since the opportunity cost is just the cost for the opportunity to 
gain a fail stack, we calculate the average amount of opportunities 
incurred before a fail is achieved. Now and hereafter the number of 
fails is calculated as the average number of fails:
```
avg_num_fails = 1.0 / suc_rate
```

Since for fail stacking we are counting the number of successes before a
failure we have:
```
avg_num_success = 1.0 / fail_rate
```

* See: https://math.stackexchange.com/questions/102673/what-is-the-expected-number-of-trials-until-x-successes

So the function \(F\) defined as, cost of gaining a fail stack, at fail 
stack position x :
```
F(x) = avg_num_success * op_cost
F(x) = avg_num_success * (black_stone_cost + (suc_rate * (F(x-1) + return_cost)) + (fail_rate * repair_cost))
```


### Calculating Enhancement Cost

The next step is to use the global fail stack cost curve to find the 
number of fail stacks for each gear such that the cost of enhancing at 
that number of fail stacks is minimized. Fail stacks get expensive 
quickly, almost needlessly so, an attempt at mitigating this issue is 
addressed next.

The method for calculating the price uses the same concept from before 
where an average number opportunities is calculated and then used with 
probabilities to compute an overall cost. The difference here is an 
a number of fails is calculated and the remainder is used as a number of 
successes. These are not integer values. The basic pseudo code for the 
enhancement cost of a piece of equipment at a particular fail stack:

```
avg_num_attempts = 1.0 / suc_rate
avg_num_fails = avg_num_attempts - 1

fails_cost = avg_num_fails * repair_cost
total_cost = fails_cost + cum_fs_cost + (black_stone_cost * avg_num_attempts)
```

Here we have:
* avg_num_attempts : The average number of attempts for one success
* avg_num_fails : The average number of attempts BEFORE one success
* fails_cost : The cost of failure
* cum_fs_cost : Cumulative cost of fail stacking to position x
* total_cost : The cost of the average number of fails and the one success

Notice here that the price of the fail stack is included in the success rate.
This may be obvious, but it is there so the max fail stack isn't chosen every time.
Here we have cumulative fail stack cost compared to repair cost.

What about gear that drops an enhancement level upon failure:

```
backtrack_start = lvl_map['TRI']

for i in range(0, 3):
    this_pos = backtrack_start + i
    prev_cost = min(total_cost[this_pos - 1])
    new_avg_attempts = 1.0 / suc_rate[this_pos - 1]
    new_num_fails = new_avg_attempts - 1
    new_fail_cost = repair_cost + prev_cost 
    total_cost[this_pos] = (new_num_fails * new_fail_cost) + (black_stone_costs[this_pos] * new_avg_attempts) + cum_fs_cost
```

This is just a loop starting at \"TRI\" which is \"DUO\" -> \"TRI\" that
factors in the previous gear cost upon failure. The cost formula is the 
came as above

Here we have:
* backtrack_start: An integer index where we start adding the previous cost
* this_pos: Position in the list of enhancement levels counter
* prev_cost: Cost of enhancing one level below
* new_avg_attempts: The average number of attempts for one success
* new_num_fails: The average number of attempts BEFORE one success
* cum_fs_cost: Cumulative cost of fail stacking to position x

Notice that this method needs to be different for accessories and the like.

### Calculating Enhancement Strategy
This needs an update. The previous explination does not represent the code anymore.

### Calculating Enhancement Probability

A quick note on the \"Strategy\" tab in the bottom right list of enhancing gear there is a probability on the far end
of the list. This probability is the chance of at least one success in n trials, where n is the average number or
trails to success. This probability helps determine a reasonable amount of fail stacks because it gives the confidence that
attempting the average number of trials will result in success.
* See [this article](https://en.m.wikipedia.org/wiki/Binomial_distribution) on the binomial distribution

## Files
Below are file definitions or descriptions of some of the files that this project uses.


### \*.log Files
Log files simply contain debug information that the program has output. 
Typically this file should not be altered by the user. These files 
should not be copied from one machine to another or it could make 
debugging the application harder. There is no maximum file size for 
these so if they get to big they can be deleted. That should not be a 
problem though

### settings.json
As the name would suggest this file is a JSON string that contains the 
programs settings. They can be safely edited with a text editor; be careful.
 If you really screwed up the settings file it can just be deleted. 
 The next time the program runs it will simply create a new settings 
 file with default values. The settings file is auto saved when the program 
 exits unless it crashes. This can be revised later. The settings file can be 
 found in the user %APPDATA% path under a folder named after this program. A command line 
 parameter should be used to supply the default loaded settings file in 
 the future. Below are a description of the fields:

Parameter | Default Value | Description
--- | --- | ---
fail_stackers | [] | List of gear objects on the fail stacking list
enhance_me | [] | List of gear objects on the enhancement list
r_fail_stackers | [] | List of gear objects removed from the fail stacking list
r_enhance_me | [] | List of gear objects removed from the enhancement list
fail_stackers_count | {} | Dictionary of indexes pointing to fail stacking items that specifies their count. If the value is encapsulated in a list it is in the removed list.
fs_exceptions | {} | Dictionary of fail stack indexes that corrispond to indexes of fail stack gear items
cost_conc_w | 2590000 | Cost of Conc stone (Weapon) (silver)
cost_conc_a | 1470000 | Cost of Conc stone (Armor) (silver)
cost_bs_w | 225000 | Cost of Black Stone stone (Weapon) (silver)
cost_bs_a | 220000 | Cost of Black Stone stone (Armor) (silver)
cost_cron | 2000000 | Cost of cron stone (silver)
cost_cleanse | 100000 |  Cost to clease gear from +15 to +14
cost_meme | 1740000 |  Cost of Memory Fragment
alts | \[\[\]\] | List of lists of size 3 \[img path, name, fail stack level \]
valks | \[\] | List of Valks enhance items (values)
quest_fs_inc | 0 | Bonus fail stacks from quests like the Bartali Adventure log
central_market_tax_rate | 0.65 | Tax rate on central market. This should probably not be changed
value_pack_p | 0.3 | Percentage of after tax value a Value Pack adds to sale balance
is_value_pack | True | Is a Value Pack active
merch_ring | 0.05 | Percentage of after tax value a Rich Merchant Ring adds to sale balance
is_merch_ring | False | Is a Rich Merchant Ring active
_version | None | Version information for change tracking

#### Gear Object
The gear object is a json string object that is encapsulated in the settings file.

Parameter | Description
--- | ---
name | A name for the piece of gear. 
cost | Cost of the base item, or cost of resetting an item after a fail attempt.
fail_dura_cost | For repairable items this is the amount of durability lost in failure.
enhance_lvl | String that denotes the level of enhancement, like \"PRI\"
gear_type | Corresponds to a file in the Data folder that describes it's enhancement levels and probabilities.
sale_balance | A balance that is added to the value of an item when fail stacking on enhancement success. For example sale price of TET minus price of DUO if purchased at DUO.
