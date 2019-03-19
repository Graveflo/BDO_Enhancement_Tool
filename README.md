# BDO Enhancement Optimizer
I've throw together this fail stack calculator so that I could try out 
the new enhancement chance numbers that were released. I also wanted to 
get a more objective way to decide how to fail stack and enhance when 
considering multiple different pieces of gear at different enhancement levels.

I haven't spent too much time making or testing it. There are almost no comments in the 
code and there are probably spelling errors everywhere, but that is part 
of the reason I am posting up the code. So it isn't necessary to wait on me and you can alter it as you please.

<p align="center">
  <img src="Images/Equipment.png">
</p>

## Future Plans
* Tables for green items in regular mode
* Recognize when recalculations are needed
* \"Always on top\" option
* Upgrade or downgrade gear from the \"Strategy\" tab
* More graphs
* Export to Excel
* Pull from online central market when implemented by PA
* Automatically calculate procurement / sale price with tax
* Find Cron stone / force enhancement data tables


## Dependencies
This project depends on a many standard libraries and some libraries of 
my own. For this project to work the utilities and QtCommon module 
collection must be present. These are small versions of larger modules 
that I copied and cleaned for convenience.

Some of the more standard libraries used that are not made by me are:
* matplotlib (switching to pyqtgraph)
* numpy
* PyQt5
* scipy.stats

### Versions
It is recommended to install Anaconda python distribution 2.7 for this 
project because that is how it was developed.

See: [Downloads | Anaconda](https://www.anaconda.com/download/)
```
> python --version
Python 2.7.15 :: Anaconda, Inc.
```
```
> python -m conda --version
conda 4.5.12
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

* See: https://math.stackexchange.com/questions/102673/what-is-the-expected-number-of-trials-until-x-successes

So the function \(F\) defined as, cost of gaining a fail stack, at fail 
stack position x :
```
F(x) = avg_num_fails * avg_num_fails
F(x) = (1.0 / suc_rate) * (black_stone_cost + (suc_rate * (F(x-1) + return_cost)) + (fail_rate * repair_cost))
```

### Establishing the Fail Stack Gear List
A complication with [Establishing Fail Stack Cost](#establishing-fail-stack-cost) 
is that items giving multiple fail stacks with one failure. This is 
handled by a second over the fail stack list so the negative cost of 
gaining more fail stacks is factored in. These items do not affect the 
global fail stack cost list because they introduce discontinuities.
The calculation is the same except the term in the formula for failing 
is different:
```
(fail_rate * repair_cost) -> (fail_rate * (repair_cost - (F(x + GAIN) - F(x + 1))))
```

Here we just have a negative cost deducted from repair_cost. The cost 
subtracted is the cost of the fail stacks gained omitting the cost of 
one fail stack because no other item got the cost of one fail stack omitted.

Items that are cost effective here are displayed as optimal for the fail
 stack in question but the over all cost does NOT effect the global fail
  stack curve used to price items and fail stacks.
* See: common.py -> simulate_FS_complex

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
The enhancement cost calculation assumes that the user is smashing 
through trash items to get to a particular level of fail stacks and 
then attempting their enhancement. A more realistic model would be one 
where a user may attempt a win-win situation at relatively low fail 
stack levels on equipment they are trying to enhance, that if they 
would fail they are still gaining the value of building a fail stack 
for items that require more fail stacks to be efficient. The reason this 
is not considered in the previous section is because fail stack prices
increase exponentially. From my experience it is hard to determine when 
the potential value of gaining fail stacks outweighs the cost and hassle 
of repairing gear.

My solution to this was, first to leave the value of gaining
a fail stack out of the calculation for optimizing the range at which to 
enhance gear. Gear enhance range is about potential loss not potential gain.

Next, in this second calculation the opportunity cost considers 
the value gained upon failure in fail stack costs and the value of the
gear obtained by succeeding the enhancement as determined by the enhancement cost. 
Gaining the gear enhancement cost upon success is supposed to balance out the greed for 
exponential fail stacks as the gear cost is based on fail stack price, not to be confused 
with the gear cost \(cost of acquiring\)

This is not the be all and end all calculation for determining what to do. This 
is supposed to suggest a cost efficient method for the dual objective of fail 
stacking and enhancing. In the GUI the user is shown a cost based calculation 
and a cost optimality to show them how efficient an attempt is in cost, not value, 
as well as their chances of succeeding at the average number of fails. With this 
info a user may weigh the value of gaining fail stacks while also considering the 
efficiency of the potential cost. 

After the enhancement cost and fail stack costs have been calculated, here is 
the Enhancement Strategy value:

```
fail_rate = numpy.ones(success_rates.shape) - success_rates
success_balance = cum_fs_cost - this_total_cost
success_cost = success_rates * success_balance
fail_balance = repair_cost - fail_stack_gains

backtrack_start = lvl_map['TRI']
if this_lvl >= backtrack_start:
    fail_balance += min(total_cost[this_lvl-1])

fail_cost = fail_rate * fail_balance
tap_total_cost = success_cost + fail_cost + black_stone_cost
```

This is very similar to the above except upon failure the cost for the 
next n fail stacks is subtracted \(negative cost\) from the balance and 
when a success happens the gear enhancement cost is subtracted. This attempts
to balance the dual objective of enhancing the gear and gaining fail stacks.

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
 exits unless it crashes. This can be revised later. For now the path 
 is relative to the common import module and static. A command line 
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

#### Gear Object
The gear object is a json string object that is encapsulated in the settings file.

Parameter | Description
--- | ---
name | A name for the piece of gear. 
cost | Cost of the base item, or cost of resetting an item (like TRI price - DUO price if buying at DUO and selling at TRI)
fail_dura_cost | For repairable items this is the amount of durability lost in failure.
enhance_lvl | String that denotes the level of enhancement, like \"PRI\"
TYPE | Gear types enhance differently, like an accessory or a piece of armour.
gear_type | Corresponds to a file in the Data folder that describes it's enhancement levels and probabilities.
