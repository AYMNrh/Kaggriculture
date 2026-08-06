# Kaggriculture strategy analysis

## Executive conclusion

The role split and fertilization are not inherently incompatible. The failed versions appear to have treated fertilizer as a new shed-to-field logistics system and/or as ordinary crop work. The champion does something simpler: a hand that is already circulating through the animal area collects fertilizer and may later apply that carried unit directly to a crop. In the reference replay, the same unit collects and applies fertilizer on day 11 (unit 7), twice on day 12 (units 3 and 9), and on day 13 (unit 4). The champion also sometimes explicitly picks fertilizer up from the shed, but that is not the only flow.

The correct bridge is therefore a **small carry-state exception inside the animal role**, not removal of the role split and not a general fertilizer job pool. Feeding remains an absolute gate. After an animal unit has wheat or the remaining feed jobs are safely covered, a unit carrying fertilizer can apply it to a nearby high-value crop as a continuation of its route. This preserves the architecture that prevents the animal queue from consuming all labor.

There is a second important correction: fertilization is active for three inclusive days, not one (`kaggriculture.py:419-425`). It does not need to be applied to every plant every day. Furthermore, crop yield is capped. Fertilizer accelerates units into the crop's fixed `max_yield`; it does not double lifetime output beyond that cap (`kaggriculture.py:386-387`, `kaggriculture.py:773-780`). Its value is early cash, earlier tile turnover for non-ongoing crops, and rescuing late plantings—not a blanket 2x lifetime multiplier.

## 1. The core tension and a compatible fertilizer mechanism

### What the environment actually permits

- Every surviving animal makes one fertilizer available at the day boundary, whether fed or not (`kaggriculture.py:783-811`); collection transfers it directly into that unit's inventory (`kaggriculture.py:492-499`). No shed trip is required between collection and application.
- `FERTILIZE` consumes one unit from the acting unit's inventory and marks the crop through `day + 2` (`kaggriculture.py:419-425`). Thus a crop needs at most one application per three-day coverage block.
- For wheat/melon, the bonus is realized when `WATER` occurs in the yield-building age window (`kaggriculture.py:375-388`). For strawberry, production occurs at the end-of-day refresh and requires that day's watering (`kaggriculture.py:767-780`). Fertilizing a crop on a non-production day can still be useful because coverage persists.
- The crop-wide cap remains `max_yield`: 6 wheat/melon and 4 strawberry (`kaggriculture.py:11-16`). A fertilized strawberry reaches four units in two production events instead of four, then receives no further production because `production_count > max_yield` is rejected (`kaggriculture.py:773-780`).

### The champion's observed collect-and-apply flow

The reference replay (`90219149.json`, player 0) contradicts the assumption that fertilization must be owned exclusively by crop hands:

- Day 11, unit 7: `COLLECT_FERTILIZER` at hours 6 and 9, then `FERTILIZE` at hour 12.
- Day 12, unit 3: `COLLECT_FERTILIZER` at hour 5, then `FERTILIZE` at hour 19. Unit 9 collects at hours 4 and 8, then fertilizes at hour 21.
- Day 13, unit 4: collects at hours 5 and 7, fertilizes at hour 12.
- The replay also uses explicit shed pickup in limited cases (for example day 13, unit 7 picks up two fertilizer at hour 3 and fertilizes at hour 11), but this is supplemental rather than the required path.

This suggests a bounded hybrid role:

1. Animal units still exclusively own `FEED`, `CARE`, animal harvest, and fertilizer collection.
2. A unit that already carries fertilizer gains a local `FERTILIZE` continuation only after feed safety is established. It should not walk to the shed merely to fetch fertilizer during the initial experiment.
3. The target should be a nearby premium crop whose coverage expires before its next production opportunity. Reserve that target to the carrying unit.
4. Cap applications globally (initially 1–2/day) and never assign this exception to the farmer if the farmer is the only reliable feed fetcher.

This avoids every failure mode in the briefing: no simultaneous fertilizer pickups, no inventory-scan race, no farmer role flip, no crop hand hauling, and no diversion before feeding. A dedicated fertilizer hand is a weaker first experiment: it imposes a full daily hire/role cost even on travel-heavy or low-value days. It becomes reasonable only after the herd is stable, at 11+ hands, and only if traces show several carried fertilizer units repeatedly returning to the shed unused.

### Fertilizer target economics

Do not rank targets simply as “strawberry first.” Rank the *next realizable marginal unit*:

- Late strawberry is strongest because acceleration can move units inside the season and strawberry has the highest relevant rising price.
- A melon in its yield-building window can reach cap sooner, be harvested sooner, and free a tile for the day 11–13 planting burst.
- Wheat is lower-value except where early harvest funds land/animals or feed is threatened.
- Never reapply while `fertilized_until_day >= day` unless extending coverage is deliberately supported; otherwise three-day coverage is wasted.

The opportunity cost is the fertilizer sale price plus travel/actions. Early fertilizer near $100 needs to create or accelerate a sufficiently valuable unit; late fertilizer near $20 is much easier to justify. This argues for a date/value gate, not unconditional daily application.

## 2. How the champion mass-plants while maintaining a dense field

The premise “water 41 existing plants and also plant 13–14” overstates the required daily maintenance. Plants die only at two consecutive unwatered days (`kaggriculture.py:747-763`). An established, previously watered plant may skip today and survive. A new plant starts with `consecutive_unwatered = 1`, however, so it must be watered on its planting day or it reaches two at that day's refresh and becomes a weed (`kaggriculture.py:201-212`, `kaggriculture.py:755-763`).

The reference replay shows the rotation directly:

| Day | Plants at hour 0 | `PLANT` actions | `WATER` actions | Plants visible at hour 23 | Watered at hour 23 |
|---:|---:|---:|---:|---:|---:|
| 11 | 29 | 13 | 41 | 37 | 36 |
| 12 | 37 | 14 | 39 | 46 | 35 |
| 13 | 46 | 8 | 40 | 54 | 37 |

Counts are observations/actions at replay step boundaries, so they are not a conservation equation (harvest, decay, and the final action intervene), but they establish the mechanism: the champion tolerates a rotating backlog rather than watering every standing crop each day. On days 11–13 it has 9–10 hands for most of the day, or roughly 240 unit-turns before the farmer; 39–41 water operations plus 8–14 plants are feasible because movement and animal work share the remaining capacity. Plant actions are distributed from morning through hour 23, not emitted in one burst. New plants are watered as urgent jobs, while established plants with zero prior misses may be deferred.

`main.py` does not exploit this mechanic. It creates an identical priority-4 water job for every unwatered crop (`main.py:372-387`) and cannot distinguish “must water today” (new or `consecutive_unwatered == 1`) from “safe to rotate.” More importantly, the claimed planter specialization is not implemented: `job_prio_for` accepts `is_planter` but returns the original priority unchanged (`main.py:574-577`). The comments at `main.py:563-567` therefore describe behavior that does not exist. Since water is priority 4 and plant is 3.2, every crop unit—including the nominal planter—takes all available water before planting.

This is why previous global plant-priority increases failed: they put old optional watering and new life-critical watering on the wrong sides of one blunt threshold. The needed scheduler is not “plant > water”; it is:

1. water crops that will die tonight, including every newly planted crop;
2. reserve one planter when seeds/space/payback exist;
3. water production-critical premium crops and then ordinary rotation crops;
4. plant;
5. use remaining time on safe-to-defer watering.

## 3. Code and mechanic review

### High-confidence bugs or mismatches

1. **The dedicated planter is a no-op.** As noted above, `job_prio_for` never adjusts priorities (`main.py:574-577`). This directly blocks the documented mass-planting design.

2. **Sell budgeting does not mirror the sell loop.** The actual sell loop keeps `max(10, pipeline_animals)` wheat and caps the submitted wheat sale at 20 (`main.py:156-166`). `sell_value` instead subtracts `WHEAT_FEED_RESERVE` (25) plus only placed animals, does not use pipeline animals, and does not cap wheat at 20 (`main.py:180-187`). The comment claiming an exact mirror is false. This can understate proceeds in common states and overstate them when surplus exceeds the submitted 20-unit order. Market prices also change per unit during order execution (`kaggriculture.py:560-605`), so `qty * current_price` is only an estimate.

3. **CARE is stronger than the comments say.** CARE does not simply double the next yield. Every fed+cared day adds one pending bonus (`kaggriculture.py:807-808`), and all pending bonus is consumed on a fed production day (`kaggriculture.py:800-806`). A cow with a two-day interval can produce base + roughly two banked units; a sheep with a three-day interval can produce base + roughly three. `main.py` correctly cares daily, but its “free 2x” explanation at `main.py:362-365` understates the mechanic. Missing collection can then hit `max_held = 6` and discard production via the `min` cap (`kaggriculture.py:20-22`, `kaggriculture.py:805`). Animal harvest urgency should rise sharply when `yield_units + pending_care_bonus + 1 >= max_held` on an imminent production day.

4. **Planting payoff cutoff is only four days.** `day + 4 <= season end` (`main.py:446`, `main.py:543-544`) permits strawberry and melon planting far too late to reach first yield (10 days; `kaggriculture.py:15-16`, harvest gate at `kaggriculture.py:395-412`). Current named windows stop premium buying/selection earlier, limiting damage, but fallback seeds and wheat can still be scheduled using a cutoff unrelated to crop maturity. Payback should be crop-specific.

5. **`fert_fetch_slots` is dead state.** It is initialized but never read (`main.py:555`). This is harmless now because fertilization is disabled, but it is evidence that prior fertilizer routing was only partially removed and should not be revived piecemeal.

### Shed overflow and inventory behavior

- Shed capacity is shared across all products and animals. Buys fail if the shed is full (`kaggriculture.py:639-663`).
- `DROP` deletes the entire carried inventory even when only part fits; overflow is discarded (`kaggriculture.py:327-340`). End-of-day automatic deposit likewise discards overflow (`kaggriculture.py:821-856`).
- `main.py` drops at carried inventory 15 but has no shed-room test (`main.py:588-598`). With sell-every-turn this may be rare, but a full/near-full shed can silently destroy milk, wool, fertilizer, wheat, or an animal. Add trace counters before strategy work; if observed, route a unit to drop only when room exists or rely on earlier sales to create room.

### Market order cap and execution order

Only the first ten submitted orders are processed (`kaggriculture.py:528-537`). Quantity within an order is not ten orders: one `SELL item qty` is one queue slot and executes per unit (`kaggriculture.py:560-605`). `main.py` generally respects the cap, but hires are appended before animals, feed, seeds, and land (`main.py:191-318`). On crowded turns, three hire slots plus many distinct shed sales can prevent time-critical seeds/land from ever being appended. Because the sell loop iterates every positive shed key and fertilizer/milk/wool/crops are distinct, this is plausible. Log rejected-by-cap intents by category; if present, reserve slots for land, emergency feed, and the active premium seed before optional hires or low-value sells.

### `first_yield_day` semantics

The constants in `main.py` match the environment for cows (8), sheep (6), and crops (`main.py:26-36`; `kaggriculture.py:11-22`). Production is based on **placement day**, not purchase day (`kaggriculture.py:215-227`, `kaggriculture.py:800-801`), so an animal sitting in the shed or inventory delays its entire production clock. This makes PLACE/build latency more expensive than its current generic priority suggests. Ongoing crop production similarly occurs at the boundary into `next_day`; a strawberry planted day 4 first produces during the day-13-to-14 refresh (`kaggriculture.py:767-778`). Tests and profitability cutoffs should use that exact timing.

## 4. Ranked, testable changes

### 1. Implement risk-tiered watering plus a real planter (highest expected impact: +$10k to +$30k)

This attacks the main strawberry/melon gap without touching animal ownership.

Code-level change:

- When building plant jobs, assign separate priorities:
  - `WATER_URGENT = 7.0` if `consecutive_unwatered >= 1` (also covers newly planted crops once they exist);
  - `WATER_PRODUCTION = 4.4` for a premium crop producing tonight or a non-ongoing crop currently in its yield-building window;
  - `WATER_ROTATION = 3.0` for an established crop with zero misses;
  - `PLANT = 4.0` for the one designated planter only, remaining 3.2 for other crop units.
- Make `job_prio_for` actually override the score: for `is_planter`, return at least 4.1 for `PLANT`, but never above urgent water. For waterers, retain the tiered priorities.
- After a successful `PLANT`, record the tile as is already done (`main.py:757-765`) and ensure its synthetic water job is urgent, not ordinary priority 4 (`main.py:386-387`).
- Use a crop-specific final planting test: wheat needs enough days to first harvest; melon/strawberry need 10 days plus practical harvest time. Preserve the existing explicit strategy windows initially.

Test criteria over the same seed suite:

- animal survival and fed/cared rates must not regress by more than 1%;
- zero newly planted crops should become weeds that night;
- plants should reach at least 40 by day 12 and 50 by day 16;
- day 11–13 should show 8+ plant actions/day while urgent-water misses remain zero;
- compare strawberry/melon units sold, not merely final money.

### 2. Add carried-fertilizer continuation to animal units (expected +$4k to +$15k; highly uncertain until traced)

Do not add shed fetching in version A.

Code-level change, before sticky animal-job selection but **after** feed pickup/placement safety:

- Compute whether all unfed animals are claimed/coverable by units currently carrying wheat. A conservative first gate is `feed_jobs == 0`, or hour >= 10 with no animal at `consecutive_unfed >= 1` and enough wheat-carrying capacity for remaining feed jobs.
- If an animal unit has `inv.get("FERTILIZER", 0) > 0`, choose the nearest unclaimed eligible premium plant within a small radius (start at Manhattan distance <= 3). Emit/move toward `FERTILIZE` even though it is outside the animal pool; keep the target sticky while the fertilizer remains carried.
- Eligibility: `fertilized_until_day < day`; expected production within the three-day coverage; strawberry first, then in-window melon, then wheat only under a cash/feed gate.
- Global cap: one application/day for the first A/B test, then two. Exclude unit 0 initially.
- Sell shed fertilizer as today. Carried fertilizer is invisible to the market sell loop and will auto-drop at day end, so unused units remain monetizable next day.

Test criteria:

- traces must show actual `FERTILIZE` actions and the same unit previously collecting the consumed fertilizer;
- no reduction in daily FEED/CARE completion;
- measure incremental crop units harvested before season end, fertilizer units no longer sold, and action/travel cost;
- require marginal crop revenue to exceed forgone fertilizer sale revenue. If it does not, restrict to late strawberries rather than declaring the routing mechanism a failure.

### 3. Protect production/logistics from caps: urgent animal harvest + market/shed slot accounting (expected +$2k to +$8k)

Code-level change:

- Raise animal `HARVEST` above routine CARE/COLLECT when the next production event can hit `max_held`; calculate days from `placed_day`, `first_yield_day`, and interval exactly as the environment does (`kaggriculture.py:799-805`).
- Replace `sell_value` with the exact submitted sell orders: sum only each order's submitted quantity, using a conservative quote or current price, rather than resurveying the shed with different wheat logic.
- Before appending hires/sells, reserve market slots for emergency feed, due land purchase, and active-window strawberry seed. Alternatively build intents, rank them, then take ten.
- Track `shed_used`, `shed_room`, attempted deposit quantity, and discarded overflow. Do not send a loaded unit to `DROP` when there is no room.

Test criteria:

- zero shed-overflow loss and zero animal product cap loss;
- no intended land/critical seed/emergency-feed order omitted due to the ten-order limit;
- earlier animal placement and unchanged care completion;
- final-money improvement across seeds rather than a single peak.

## Recommended experiment order

Run change 1 alone first: it has the clearest causal connection to the replay and fixes a definite no-op. Then layer change 2 onto the winning scheduler, beginning with one carried application per day and no shed pickup. Run change 3 independently as an instrumentation/correctness branch, then combine only the portions whose counters demonstrate real losses. This separation matters: prior fertilizer attempts changed routing, inventory, and priorities simultaneously, so a regression did not establish that fertilizer itself was uneconomic or incompatible with the role split.
