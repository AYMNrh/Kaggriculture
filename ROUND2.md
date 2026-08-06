# Round 2: fertilization rate and field-size diagnosis

## Bottom line

Do **not** try to match the champion's raw 9–14 FERTILIZE actions/day yet. One application covers the current day plus the next two days. At 5–8 applications/day, the agent can continuously cover roughly 15–24 plants; that is already close to the present 21–30-plant field. The champion needs 9–14/day because it has about 57 plants. First grow and retain a larger field, then scale fertilizer throughput with the number of eligible plants.

The observed strawberry cap is not tile space. The day-10/12/14 traces show 39–43 plantable cells while total plants fall from 23 to 16. Strawberry seed purchases are also low (about 21 bought over days 4–14 in the seed trace), but the sharper failure is crop service capacity/routing: plants are dying and freeing cells. A newly planted tile starts with `consecutive_unwatered = 1`; if it is not watered before that day's refresh it immediately becomes a weed. Every successful expansion therefore costs at least **PLANT + WATER on the same day**, plus travel, while all existing plants also need daily water.

## 1. Safely raising fertilizer application rate

### Recommended change: a bounded late-game premium route

Keep the role split. Let **one animal hand at a time** enter a `fert_route` only after the critical animal work is covered, but do not require the entire animal job pool to be empty.

The safe gate should be state-based:

1. Day >= 20.
2. Hand already carries fertilizer; do not create a shed pickup trip.
3. No unfed animal exists, and no animal has been unfed since yesterday (`consecutive_unfed > 0`).
4. No unharvested animal is near capacity (for example `yield_units >= max_held - 1`).
5. Reserve enough other animal units for remaining CARE/COLLECT/HARVEST jobs. A simple first test is: allow the route only when `remaining_animal_jobs <= 3 * other_animal_units`.
6. Target only a plant whose coverage expires before its next useful production/watering event.
7. Cap actual FERTILIZE actions at `ceil(eligible_premium_plants / 3)` per day, plus at most one rescue application.

This is safer than letting all crop hands carry fertilizer. Crop hands protect the non-negotiable daily water budget; diverting them to animal collection adds long cross-map trips and recreates the regression that caused crop deaths. It is also safer than a permanently dedicated hand, because the animal workload is bursty and feed failure has catastrophic downside.

Implementation detail: persist a distinct target type such as `("FERT", x, y)` rather than storing a bare coordinate in the normal job target table. The current bare-coordinate target can collide semantically with a WATER/HARVEST job at the same tile on the next turn. Clear the target after the FERTILIZE action or if the tile is no longer eligible.

### Production-aware eligibility

The present test `fertilized_until_day < day` refreshes only expired coverage, which is good, but it treats all premium plants equally. Rank targets by expected marginal value:

- Strawberry: next production is on days where `next_day - planted_day - 10 >= 0` and divisible by 2. Fertilizer applied during day `d` affects the end-of-day refresh for `d`; prioritize a strawberry producing tonight, then one producing within the coverage window.
- Melon: fertilizer only adds yield when WATER occurs at age 6–12 (`window_start = (12 + 1) // 2 = 6`). Prefer age 6–10; late applications may merely reach the six-unit cap sooner without adding saleable units.
- Require the plant to be watered today already, or ensure an unclaimed WATER route will reach it. Fertilizer gives no ongoing-crop bonus on an unwatered day.

### Test matrix

Run the same fixed 30 seeds for each variant and log animal escapes, missed feeds, WATER completion, FERTILIZE/day, and crop sales:

| Variant | Change | Expected result |
|---|---|---|
| A | Current idle filler | Control: 5–8/day late |
| B | One carrying animal hand may fertilize after all FEED jobs are done | Likely 7–10/day without herd loss |
| C | B plus CARE reserve gate and daily cap `ceil(premium/3)` | Preferred robust version |
| D | One crop hand allowed to collect/carry fertilizer | High-risk negative control; expect less watering |

Reject a variant if any seed loses an animal, late WATER completion falls by more than 1 plant/day, or milk/wool volume falls more than 2%. Compare median and lower-decile money, not only the mean.

## 2. Why strawberry plants cap at 21–30

### Ranked limiters

1. **Same-day plant/water throughput and route efficiency.** This is directly visible: at days 10–14 there are about 40 free cells, yet plant count shrinks. Tile space therefore is not binding. A new plant that misses same-day WATER dies that night, so issuing many PLANT jobs without reserving water capacity can reduce rather than grow the field.
2. **Strawberry seed cash flow.** The seed log shows purchases of only about 1–3/day and about 21 total through day 14, far below the nominal target 41. The `target_stock` argument is an inventory target, not a cumulative purchase/plant target. It does not itself cap cumulative purchases, but the 30% investable gate and competing wheat/melon orders do.
3. **Land/tile space.** Not currently binding: traces show 39–43 plantable cells. It mattered before the NE/SW unlocks but does not explain the day-10+ plateau.

### Specific capacity fix to test

Introduce a daily expansion budget rather than boosting PLANT priority globally:

```text
safe_new_plants = min(
    available_seeds,
    free_tiles,
    max(0, crop_action_capacity - unwatered_existing - travel_reserve) // 2,
    daily_growth_cap,
)
```

Start with `daily_growth_cap = 4` on days 4–10 and `6` on days 11–14. For every PLANT target admitted, reserve that same coordinate as a same-day WATER obligation. Stop planting after hour 14 rather than 18 unless the planter is already on the target and at least one crop hand is free to water it. The current hour-18 cutoff can create plants with only five turns left to plant, route, and water.

The cleanest scheduler is a two-stage tile state:

- Crop unit plants a tile.
- On the next observation, that tile gets emergency WATER priority above every other crop operation.
- Do not admit another plant when the count of `planted_today but not watered_today` is at least the number of free crop hands.

This is materially different from the previously failed global PLANT-priority boost: it bounds expansion by the water debt it creates.

### Seed-side experiment

Track cumulative strawberry seeds purchased and planted in `_STATE`; target **41 cumulative planted**, not 41 currently held. On days 4–10, buy strawberry before melon/wheat seeds and reserve a fixed cash slice for 2–3 strawberry seeds. Do not increase total seed spending blindly.

Run these independently:

- E: scheduler/water-debt change only, unchanged seed purchasing.
- F: cumulative strawberry target and purchase ordering only.
- G: E + F.

Interpretation is straightforward: if E raises retained plants but strawberries remain seed-starved, F is needed; if F raises seed inventory but not retained plants, labor/routing is conclusively binding. Log at day end: crop counts, seeds held, cumulative bought/planted, new plants, same-day-water misses, weeds created, and WATER actions.

## 3. Fertilizing wheat late

Yes, but only as a **third-tier sink** after strawberry and useful melon targets, never as blanket coverage.

For non-ongoing wheat, WATER at ages 2–4 increments held yield; fertilizer changes an increment from +1 to +2, up to the six-unit held cap. Late wheat sells around $45–50 while fertilizer's sale opportunity is around $20–25, so one genuinely additional wheat is profitable before labor cost. However, premium marginal units are worth roughly $290–300, and an unnecessary wheat application can hit the held cap without increasing final harvest.

Eligibility for wheat should therefore be:

- day >= 20;
- hand already carries fertilizer;
- no eligible strawberry or melon target;
- wheat age is 2–4;
- it will be watered today;
- `yield_units <= 4` (so the doubled increment is not mostly clipped at six);
- no urgent animal work and no premium WATER debt.

Test H against the preferred premium-only variant. Expect a small gain, probably hundreds rather than thousands. Reject it if premium fertilization count or water completion falls.

## 4. Other source mechanics worth exploiting

### A. Hire costs reset every day; hands do not persist overnight

`_end_of_day` clears all hands and resets `hires_today`. This means the strategy is buying a fresh daily labor force, and the Fibonacci curve applies within each day only. The relevant optimization is not a season-long ramp of permanent hands but a **daily hand-count schedule**. Audit profit against the full daily Fibonacci sum, and consider late-day hires only if enough turns remain to repay them. A hire near hour 18 is usually poor even when its nominal marginal cost is low.

Test: stop hiring after hour 8 (or make the cutoff depend on remaining crop/animal action debt) while keeping the same target. Measure labor spend and missed jobs.

### B. End-of-day inventory is automatically deposited

All carried inventory is moved to the shed at night, with overflow discarded. A hand carrying fertilizer does not need to route back to the shed late in the day. Conversely, shed capacity 100 can silently destroy overflow at night. Near hour 23, prioritize selling shed contents to create room and harvest/collect carried high-value goods without paying for a DROP route.

Test/log: `shed_total + carried_total` at hour 23 and count theoretical overflow. If nonzero, add an hour-22 capacity-clearing sell before other purchases.

### C. Fertilizer availability is daily, independent of production

Every surviving animal sets `fertilizer_available = True` at every daily refresh. Collection today does not generate another unit until tomorrow. Thus the maximum supply is one per animal per day, and collecting it early only matters for sale cash or routing. For late application, collect from animals geographically close to premium crops; do not send a crop hand from the field to a remote animal just to obtain it.

### D. CARE bonuses bank until a fed production day

CARE on every non-production day is not wasted: each fed+cared day adds one pending unit, all banked bonus is consumed on the next fed production day, subject to the animal's `max_held` cap. Therefore HARVEST before a production refresh matters when held yield is near capacity. Add an explicit near-capacity harvest urgency so banked care is not clipped.

Test: prioritize animal HARVEST above CARE when `yield_units + 1 + pending_care_bonus >= max_held` and the animal produces tonight. Compare milk/wool clipping events.

### E. Non-ongoing crops decay every two turns after lifespan

Wheat/melon yield units decay after `max_lifespan_step`, eventually turning the tile into a weed. Harvesting only when `age >= max_yield_day` is yield-maximizing when service is reliable, but a plant with missed water or a congested route may be worth harvesting earlier to avoid losing held units and to free the tile. A risk-aware harvest at age `max_yield_day - 1` late in the season or under high water debt is worth testing.

### F. Market orders execute sequentially and prices refresh after the turn's market processing

Sales placed first fund later buys in the same action list, which the agent already exploits. The more immediate issue is the ten-order cap: repeated HIRE orders and three seed types can crowd out feed or land. Log rejected/unexecuted intended orders and reserve slots in this order: emergency feed, sales that fund the turn, land/animal burst, strawberry seed, hires, other seeds.

## Recommended order of work

1. Add instrumentation for same-day plant-water misses, crop deaths, cumulative seeds, clipped animal yield, shed overflow, and per-role action counts.
2. Test the bounded expansion/water-debt scheduler (E). This attacks the demonstrated field-size limiter and has the largest upside.
3. Test cumulative strawberry procurement (F), then combine it with E (G).
4. Scale fertilizer using the one-hand post-FEED route (B/C) only after the premium field exceeds roughly 25 plants.
5. Add production-aware wheat fertilization (H) only if premium coverage and WATER remain intact.

The likely path to the champion's fertilization count is therefore **57 retained plants -> roughly 14 renewal applications/day**, not **force 14 applications/day -> hope the field grows**.
