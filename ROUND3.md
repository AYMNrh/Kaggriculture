# Round 3: the wall is scheduling, not raw field density

## Bottom line

The champion is not getting 50% more throughput merely from a denser field, and it cannot be sustainably rotating water across live plants. The engine turns any plant that misses one full day of water into a weed (`consecutive_unwatered >= 2`); a new plant is even less forgiving because it starts at 1. If the replay reports 57 plants but only 41 WATER actions on day 14, those numbers are almost certainly not the same denominator/time slice: 57 may be a peak or cumulative planted count, while 41 is the live plants that still required water after same-turn harvest/removal. Do not copy a deliberate water rotation.

The current bottleneck is the **hard, asymmetric role partition**. It estimates crop demand as:

```text
crop_workload = live_plants + min(free_plantable_tiles, 20)
n_crop_hands = ceil(crop_workload / 7)
```

Thus empty land is counted as if 20 additional crops already require service. At 29 live plants this requests `ceil(49/7) = 7` crop units, not merely the number needed to water 29 plants. Those units cannot help the herd while any crop job exists; animal units may help crops only after all animal jobs disappear. This explains why every planting boost converts milk and wool into plants.

The champion's likely advantage is a work-conserving scheduler plus short local routes: allocate enough labor to meet both end-of-day deadlines, then let every unit take useful nearby work. The present agent instead reserves whole workers for the entire turn and measures demand in objects, not remaining travel/action turns.

## Answers to the four questions

### 1. Is field density the source of the efficiency gap?

It contributes, but the evidence does not support it as the main source of a 50% gap. Even a three-tile average walk leaves ample theoretical capacity in 11 units × 24 turns; the larger loss is idle/blocked capacity created by the role boundary and by sticky one-job reservations.

The density-order experiment was structurally unable to enforce density if it only reordered `plantable`. `main.py` still emits a PLANT job for **every** free tile, all at priority 3.2. Assignment then selects by priority and distance, so a hand already standing on the frontier chooses a nearby outward tile even if that tile was late in the density ordering. Sticky targets preserve that choice while it walks. Ordering candidates changes crop labels and insertion order at most; it does not restrict the geometric frontier.

To test density, admit only a small set of compact frontier cells. Merely sorting all cells is not a density policy.

### 2. What should determine the crop/animal split?

Not plant count alone. It should be determined by **remaining deadline debt in turns**:

- crop debt: unwatered live plants, plus two actions for each proposed new plant, plus estimated route travel;
- animal debt: remaining FEED/CARE/COLLECT/HARVEST actions, wheat pickup trips, plus estimated route travel;
- capacity: units × hours remaining.

Neither side needs an immutable ownership count. Protect each workload with a reserve, but allow all unreserved units to take the nearest useful job. The champion action mix is consistent with local route ownership and deadline reserves, not a fixed `plants / 7` role formula.

### 3. Is the champion watering on rotation?

No sustainable rotation is possible under the engine rules: an existing plant may miss today only if it was watered yesterday, but it becomes a weed at tonight's refresh; a newly planted crop must be watered the same day. Alternating days therefore destroys the field. Treat the 41/57 discrepancy as a replay-accounting question until the live unwatered count at hour 0 is logged from the champion replay. The correct invariant for this agent is still:

```text
end_of_day_unwatered_live_plants == 0
```

### 4. Is another economic lever now more valuable?

No market or shed tweak plausibly closes a 35-plant gap. Sell timing may recover hundreds or a few thousand; fixing labor utilization can unlock dozens of premium crops while retaining milk/wool. Stay on scheduling for the next two controlled tests. Only pivot to markets if the scheduler raises completed actions but cash, rather than seeds or labor, becomes the measured limiter.

## Ranked changes to test

### 1. Replace the hard role split with a deadline-reserve, work-conserving scheduler

This is the highest-value next change.

Keep FEED and WATER as protected obligations, but calculate reserves each hour from **currently unfinished jobs**, not live plant count or free land. A minimal first implementation does not need a sophisticated optimizer:

1. Do not include hypothetical free cells in crop debt. Only admitted PLANT jobs count.
2. Estimate `crop_turn_debt` and `animal_turn_debt` as remaining actions plus a simple travel allowance (start with one travel turn per job; measure and tune later).
3. Reserve the minimum units needed to finish each debt by hour 23: `ceil(turn_debt / max(1, 24-hour))`.
4. Assign protected FEED/WATER work first.
5. Assign every remaining unit from one combined pool using local score, regardless of its former role.
6. After FEED is complete, animal-route units may water/harvest nearby crops immediately; after the day's admitted crop debt is safe, crop-route units may CARE/COLLECT nearby animals.

For the first test, keep all market, planting, and fertilizing logic unchanged. This isolates whether partitioning is the cause.

Log per day: successful actions per unit; movement/PASS/failed-action turns; unfinished FEED, CARE, and WATER at hours 12/18/23; and milk/wool. The decisive metric is not nominal role count but useful actions per unit-day.

**Accept if:** retained plants increase by at least 5 without milk or wool falling more than 2%, and no animal misses FEED. **Reject if:** WATER or FEED debt remains at hour 23; then the reserve underestimated route turns rather than disproving the approach.

### 2. Admit paired PLANT→WATER bundles on a bounded compact frontier

After change 1 is stable, replace “jobs for every empty tile” with at most `growth_budget` admitted cells per day. Rank cells by:

1. adjacency to an existing plant (prefer two or more adjacent crop neighbors);
2. distance to the nearest current crop-route unit;
3. distance to the shed only as a tie-breaker.

Start with `growth_budget = 3` on days 4–7 and `4` on days 8–14. Each admitted cell is a two-action obligation: PLANT plus same-day WATER. Do not admit the next bundle unless projected remaining capacity still covers all existing WATER debt and all animal FEED debt. Stop admission at hour 12, not 18.

This is the corrected water-debt experiment: count only existing unwatered crops **once as today's required work**, not as evidence that the field is unhealthy, and count each proposed new plant as two additional actions. Morning being entirely unwatered is normal.

Run three variants over the same seeds:

- A: scheduler only;
- B: scheduler + bounded bundles, no adjacency term;
- C: scheduler + bounded bundles + compact-frontier ranking.

If B beats A but C is flat, density is not material. If C reduces movement turns and raises completed WATER/PLANT actions, density matters—but only after candidate admission actually constrains the frontier.

**Accept if:** median day-14 live plants reaches at least 35, same-day plant/water misses are zero, and milk/wool remain within 2% of A.

### 3. Preserve local routes by sticky tile ownership through a short job chain

The current code clears a target immediately after every FEED, CARE, COLLECT, WATER, or HARVEST action. Although the same tile is often nearest next turn, greedy unit-order assignment can let an earlier unit claim the newly exposed follow-up job and send the unit already standing there elsewhere.

Test short route ownership:

- on an animal tile, retain ownership through FEED → CARE → COLLECT_FERTILIZER → HARVEST while applicable and while inventory permits;
- after PLANT, retain that tile as the same unit's immediate WATER target if possible;
- release ownership when the chain is complete, supplies are missing, or a protected deadline elsewhere becomes urgent.

This attacks action density directly without changing how many hands either economy receives. It also matches the plausible source of the champion's high actions/hand: several actions at one animal tile and tight crop sweeps, rather than repeated global reassignment.

Test this only after change 1 so its result is not masked by the hard split. **Accept if:** movement turns fall by at least 10% and successful actions rise without new FEED/WATER misses. If it is flat, skip it and investigate market-order/cash timing next.

## Recommended sequence

1. Test the work-conserving deadline scheduler alone.
2. Add bounded paired expansion, then the genuine compact-frontier constraint.
3. Add short route ownership if traces still show units crossing or stealing follow-up jobs.

Do not raise seed purchasing, fertilizer volume, or the field target during test 1. The critical question is whether the same labor force can complete more of the already-generated work without trading away the animal economy.
