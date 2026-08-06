# Round 8: buy capacity, then stop wasting it in transit

## Bottom line

The gap is not primarily the two missing hands. It is **two missing hands plus poor work density**.

At day 16 the current target is only 11 hired hands, or 12 total units including the farmer. Moving to 14 hired hands supplies three more units, not two. At the observed champion rate of about eight useful actions per worker-day, that is roughly 24 additional useful actions. The champion performs about 46 more useful actions than this agent, so hiring alone can plausibly recover only half the gap.

The trace in `hand14.txt` shows the other half directly: one crop hand executes only five WATER actions in a day and spends the rest walking, including a six-step return from `(0,0)` toward `(1,5)`. This is not an inherent 24-hour limit. It is assignment fragmentation. Every hour all crop hands greedily claim one globally nearest equal-priority tile; neighboring tiles are claimed by other hands, territories reshuffle, and workers cross through one another's areas. The unused `nearest_job()` comment describes distance-weighted selection, but the actual assignment uses lexicographic `(priority, -distance)` and sticky single-tile targets. The field is reasonably compact; the routes through it are not.

There is also a structural cliff in the role formula:

`n_crop_hands = (plants + min(plantable_count, 20) + 5) // 7`

The extra 20 empty tiles count as workload before they are jobs. At 22 plants this reserves about six crop units. At 40 plants it reserves about nine. With the current day-16 total of 12 units, that leaves only three animal units and guarantees the milk/wool regression seen in growth tests. With 14 hired hands plus the farmer, nine crop units leave six animal units, which is much closer to the current viable herd allocation. Thus **early hiring unlocks a larger field only when paired with an explicit animal floor and better crop routing**.

## Direct answers

1. Champion efficiency is approximately **half labor count and half routing/structure**. Three extra workers can explain about 24 of the 46 missing actions. The rest must come from shorter tours and fewer shed/role interruptions. The exact path to 40+ plants is: hire 14 by the strawberry ramp, reserve at least six total units for the 14-animal service loop, and make the remaining nine crop units own stable local territories instead of globally competing for tiles every hour.
2. Hire 14 earlier, but do not expect hiring alone to create the field. From the current day-16 target of 11 hires, the added daily marginal costs are `fib(11)+fib(12)+fib(13) = 144+233+377 = $754`; `$610` is only the cost of moving from 12 to 14. Cash is already about $13k on day 14 and $21k on day 16 in the traces, so this is affordable then. The right first window is days 11-17, not day 0: those are the last strawberry planting days and the first large watering/harvest overlap.
3. Yes, but not by crop type alone and not by fixed parity. A plant may safely miss one day only when `consecutive_unwatered == 0`; it must be watered when that value is 1. For annuals, watering outside the yield-building window is only survival maintenance. Wheat earns units from ages 2-4 and melon from ages 6-12; skipping a productive-window water can reduce final yield. Strawberries still receive their ordinary scheduled production when unwatered, but a production-day water is required for the fertilizer bonus. Use the tile's state and production calendar, not odd/even days.
4. One ordinary strawberry plant is four sale units: at the measured $283 average, gross value is about `$1,132`. Subtract the $100 seed and labor. Under daily watering it consumes roughly 16-17 WATER actions plus PLANT and harvest work; under safe deferred watering it needs roughly half those waters. Five additional plants are therefore about `$5,660` gross and plausibly `$3.5k-$4.8k` net after seeds, early-hire expense attributable to them, and displaced work. Ten are about `$11.3k` gross, but require the routing fix; they do not fit safely under the current scheduler.
5. Field growth is the highest-ceiling route, but not the only route from $118.8k to $120k. Correctly timed strawberry fertilizer can add up to four extra units per plant over its four production events, worth up to about $1,132 per perfectly covered plant at this seed's realized price. That is enough to close a $1.2k gap without adding ten plants. More animals is inferior while the existing herd is already under-serviced; earlier land is useful only if labor can exploit it. Land itself produces nothing.

## Ranked tests

### 1. Day-11 capacity package: 14 hires, six-unit herd floor, stable crop territories

**Expected final impact: +$4k to +$12k. Highest ceiling and best match to the measured gap.**

Test this as a staged factorial so the result distinguishes labor from routing:

- A: current code.
- B: target 14 hires from day 11 through day 17; no scheduler change.
- C: B plus a hard floor of six total animal units (including the farmer), with every surplus unit assigned to crops.
- D: C plus stable spatial crop territories.

For D, sort live crop tiles by a fixed space-filling order (a serpentine row order is sufficient), split that ordered list into contiguous slices for crop units, and let each unit choose the nearest highest-priority job inside its own slice. Keep a tile in the same unit's slice all day. Permit global spill only after that slice has no WATER, PLANT, or crop HARVEST job. Put new planting sites on the frontier of a slice and assign their same-day WATER to that same owner. Do not use a new flexible role auction.

This directly attacks the observed six-step deadhead trips while preserving the successful role isolation. On days 11-14, raise the admission ceiling only when the previous day completed all FEED jobs, all CARE jobs, and all mandatory plant waters. Try 6 admissions/day first; do not jump to an uncapped field.

Log per day and per role: hired hands, useful actions, movement actions, PASS actions, plants alive, plants admitted/died, WATER completion, FEED/CARE completion, and Manhattan distance between consecutive executed jobs for each unit. The acceptance gates are:

- at least 90 useful actions/day by day 14 and 100 by day 16;
- at least 35 live plants by day 14 and 40 by day 16;
- zero animal escapes and no decline in daily FEED completion;
- milk and wool each no worse than 3% below control;
- median crop-hand useful actions at least 7/day.

If B gains less than $2k, hiring alone is disproven. If D raises useful actions materially without raising plant survival, seed/admission supply is then the remaining limiter. Run seed 42 first, then seeds 853 and the established top-20 panel, then 100 common seeds.

### 2. State-safe water deferral outside value-producing days

**Expected final impact: +$2k to +$7k through capacity for 5-10 more strawberries; medium risk.**

Replace blanket WATER eligibility with a `must_water` predicate for this experiment:

- always water a newly planted tile that day;
- always water when `consecutive_unwatered >= 1`;
- always water an annual during its yield-building window while below its attainable cap: wheat ages 2-4, melon ages 6-12;
- always water a strawberry on a scheduled production day when it is fertilizer-covered;
- otherwise allow the tile to defer water for this day.

This is not the failed alternating scheme. Fixed alternation can repeatedly skip the same plant after scheduling delays or mishandle new plants. The observation's `consecutive_unwatered` field is the authoritative safety guard. No tile with value 1 is ever skipped.

Run it first at the current 3/4 admission budget to measure freed actions without confounding growth. Then combine it with test 1C/D and increase admissions from 4 to 6 on days 4-14. Rank deferred candidates lowest when they are strawberries approaching a production date and highest when they are pre-window melons or already-maxed annuals.

Log mandatory versus deferred waters, end-of-day `consecutive_unwatered`, weeds created, annual final yield per plant, fertilized strawberry production, and displaced animal work. Reject on any hydration death or more than 2% loss of wheat/melon units per planted cohort. Success is at least eight WATER actions saved per day with unchanged cohort yield; that is approximately one additional worker-day of capacity and should support five extra strawberries without touching the herd.

### 3. Production-date fertilizer as the non-field bridge

**Expected final impact: +$1.2k to +$5k. Lowest structural risk; enough to clear the current peak by itself.**

Round 7 identified that the current FEED-safe gate is unreachable in practice: fertilization is evaluated only after `best_key is None`, while `feed_jobs` is a static count rather than the set of FEED jobs already reserved. Test the Round 7 reservation fix after the capacity tests, but narrow it to strawberry production dates.

Pre-reserve every outstanding FEED tile to wheat-carrying animal units. Once all FEED tiles have distinct reservations, allow at most two fertilizer-carrying animal units per turn to divert from CARE/COLLECT to a strawberry whose next production refresh falls within `day..day+2`. Require that strawberry to be watered on its actual covered production day. Preserve the six-unit animal floor and never divert a reserved feeder.

Compare caps of one and two applications per turn. Track additional strawberry units, not merely FERTILIZE actions. At $283 per unit, only five additional units are needed to clear $1.4k. Keep the change if milk and wool remain within 2% of control and it adds at least five strawberry units on seed 853 or raises the established peak above $120k.

## Recommended order

Run test 1 as A/B/C/D first. It will answer whether the missing capacity is payroll or travel rather than mixing both into another failed scheduler variant. Apply test 2 only to the best capacity arm; it is a capacity multiplier, not a standalone growth policy. Use test 3 as the low-field-risk bridge to $120k after the production architecture is selected.

Do not add animals or buy land earlier in these tests. Fourteen animals already create 42 daily FEED/CARE/COLLECT actions before harvest and logistics, and existing unlocked land has unused production capacity. The immediate scarce inputs are executed worker-hours and short routes.
