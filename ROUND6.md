# Round 6: raise the tail with production-timed fertilizer

## Bottom line

The 2,000-seed result says the remaining $5.4k is primarily a configuration problem, not a seed-search problem. More sampling can still find a better town-shop path, but seed 207 at $114,594 after 2,000 trials makes a jump to $120k from sampling alone unlikely. Make one real production change first, then hunt the new tail.

The best change is to move strawberry fertilization forward from day 20 to the actual production window. The current gate misses the first three production dates of the earliest strawberries. This has a plausible $3k--$8k ceiling without enlarging the field or permanently reallocating hands.

## What the environment source establishes

- An ongoing strawberry has four scheduled production events, every two days, beginning 10 days after planting. Normal maximum lifetime output is therefore 4 units per plant.
- Fertilizer adds 2 rather than 1 at a production event. It is active for the application day and the next two days. With timely harvests preventing the 4-unit held cap from binding, the theoretical lifetime maximum is 8 units per strawberry plant.
- Thus a cohort of 12--16 strawberry plants supports 48--64 units without fertilizer and at most 96--128 with perfect fertilizer, watering, harvesting, and no cap loss. The observed 67 is already above the unfertilized ceiling for roughly 12--15 plants and is consistent with partial late fertilizer.
- A reported 267 strawberries cannot come from the current 12--16-plant cohort. It requires at least 34 plants even at the absolute fertilized maximum, or 67 plants without fertilizer. A champion cohort around 50--57 plants plus partial fertilization makes 267 entirely feasible. It is principally a different field-size/labor regime, not evidence that this field can reach 267 through routing alone.
- Market orders execute before town demand on each turn. The town then consumes goods and refreshes prices. Selling one turn after a town-consumption tick can get the post-demand quote, but the increment from one tick is small and delaying early cash can damage compounding. This is a terminal timing refinement, not a $5k primary lever.
- `BUY_SEED` is fixed at the crop's seed cost and does not affect crop-product market inventory. `BUY_PRODUCT` is allowed only for wheat and fertilizer, uses the dynamic product price, consumes shed capacity, and changes market inventory. There is no melon/strawberry product-arbitrage path.
- Seeds do not consume shed space. End-of-day carried inventory is automatically deposited and overflow is silently discarded. This makes a shed headroom check valuable, but there is no profitable overflow trick.
- `DIG` is free but costs a unit-turn and only removes a plant, weed, or empty structure. Weeds have no sale value. Digging is worthwhile only when a weed blocks an intended compact-frontier admission or when a harvested annual must be replanted.
- Shops unlock randomly every three days and consume goods every four turns; the town center consumes every 12 turns with demand increasing on days 10 and 20. Favorable strawberry/milk/wool shop unlocks are a genuine seed-dependent tail source. They explain why additional sampling still has some value, but the strategy cannot control which shop unlocks.

## Ranked tests

### 1. Fertilize strawberries by their next production date

**Expected peak impact: +$3k to +$8k. Highest probability of closing the gap.**

Replace the blanket `day >= 20` carry-fertilizer gate with a production-aware target beginning around day 13. Do not create shed-fetch fertilizer jobs and do not divert a hand before animal chores; retain the proven carry-only, animal-idle continuation. Change only which crop gets the fertilizer already carried after animal work is clear.

For every live strawberry, calculate the refresh that creates its next output as `planted_day + 10 - 1 + 2*k`, for `k=0..3`. The output is visible the following day (`planted_day + 10 + 2*k`), but fertilizer must be on the tile before that end-of-day refresh. Admit it as a fertilizer target when:

- it still has a future production event;
- that refresh is today, tomorrow, or the following day;
- `fertilized_until_day` does not already cover that event; and
- among eligible targets, the earliest next production date wins, then shortest distance.

Prefer strawberry over melon. A single application can cover two strawberry events because coverage is inclusive through `day + 2`; for example, a day-4 strawberry fertilized during day 13 affects the end-of-day refreshes on days 13 and 15, whose output is visible on days 14 and 16. At late prices, two extra strawberry units are roughly $500--$620 gross versus selling one fertilizer for roughly $20--$100. Even one extra unit usually wins comfortably.

Run three arms on the same seed set:

- A: current `day >= 20` carry-only rule;
- B: production-aware carry-only rule from day 13, strawberry only;
- C: B plus melon only when no uncovered strawberry production falls within two days.

Log strawberry plants by planted day, fertilizer application day, scheduled production dates covered, strawberry units harvested/sold, fertilizer sold, animal jobs remaining when fertilization occurs, and final money. Reject any implementation that reduces milk or wool by more than 2%; that would mean fertilizer is pre-empting animal work rather than using idle continuation. The target is at least 15 extra strawberries: at late prices that alone is about the required $4k--$5k.

### 2. Guarantee four melon admissions, but treat it as a value-per-tile test

**Expected peak impact: -$1k to +$2k; likely positive only if it replaces low-fertilizer strawberries.**

Test variant C exactly as proposed: guarantee one melon admission on days 4, 7, 10, and 13. Count successful `PLANT` actions, not generated jobs, and reserve a melon seed for the admission. All other admissions retain the current strawberry quota.

Melon is underweighted by count, but not obviously by dollars per scarce tile. A fully watered melon returns up to 6 units once, roughly $1.5k--$1.8k gross, and then frees the tile. A strawberry returns 4 units normally or as many as 8 with well-timed fertilizer, roughly $1.0k--$2.5k gross depending on sale price and coverage. Therefore melon should replace only the weakest four strawberry slots, not restore a broad melon percentage.

Compare on at least the same 30-seed average panel plus seeds 42 and 207. Record crop planted counts/dates, successful yields, watering actions per sold unit, DIG/replant delay, combined melon-plus-strawberry revenue, milk/wool, and final money. Keep C only if combined premium-crop revenue and final money rise; a higher melon count by itself is not success. Test this both before and after the fertilizer winner, because earlier fertilizer raises the opportunity cost of giving up a strawberry tile.

### 3. Add the 15th hand only when a measured animal backlog exists

**Expected peak impact: -$2k to +$1.5k unconditionally; up to +$3k with a strict daily gate. Low priority.**

Do not begin with an unconditional 15 hands on every day 5--11. The marginal hire costs $610 per day, or $4,270 over seven days. Round 5's higher PLACE priority already showed that forcing placement can worsen routing, and the added unit joins the animal side only indirectly through the workload split.

First trace the control at hours 12 and 18 on days 5--11. Test the 15th hand only on a day where all of the following are true at hour 0 (or use the previous day's trace to define a fixed reproducible day mask):

- an animal is waiting in shed/inventory or a placed animal missed FEED/CARE/COLLECT/HARVEST the prior day;
- animal work remains after hour 18 in the control trace; and
- projected extra production has a conservative value above $610.

The clean A/B is current ramp versus 15 hands on the fixed backlog-positive days, not all seven days. Log actions and idle turns of unit 15, animal completion hours, placed-animal dates, wool/milk/fertilizer deltas, crop spillover actions, and final money. Keep it only if it pays back in final money on both the average panel and seed 207. Current evidence says this is less promising than production-timed fertilizer.

## Peak-search decision

Use both configuration improvement and seed sampling, in that order:

1. Evaluate the three ranked tests on a common 30--100-seed panel and explicitly on seeds 42 and 207.
2. Fix the winner, then run a 2,000-seed comparison against the existing peak. If the new config moves seed 207 or the top-20 tail by several thousand dollars, expand the hunt to 10,000 seeds.
3. Do not spend the next round only sampling the unchanged config. With zero improvements in seeds 0--1999, another 2,000 seeds may improve the record modestly, but there is no evidence that its tail reaches $120k.

The random shop schedule makes the peak grow somewhat with sample size: a seed that unlocks strawberry, milk, and wool consumers early will outperform one that unlocks carrot/egg shops. But sampling supplies favorable prices; it does not create the missing production. Earlier strawberry fertilizer is the change most capable of converting a favorable shop seed into the extra $5.4k.
