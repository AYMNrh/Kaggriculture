# Round 5: improve the value of the constrained field

## Bottom line

The next move should not be another attempt to make the field larger. Round 4 already established the practical labor ceiling: raising admission to `4/8/4` reached 40 plants but transferred too many units into the crop role and cut milk from 218 to 196. Risk-tiered watering was also too fragile. At the present 19--29-plant ceiling, the best remaining crop lever is to make more of those scarce live tiles strawberries, and to plant those strawberries as early as possible.

There are two implementation details behind that recommendation:

1. `crop_for()` does **not** enforce an 80/10/10 planted mix. It uses `idx % 10`, where `idx` is the index in the entire spatially sorted `plantable` list. Entries later skipped because they were planted earlier in the day still affect `idx`, and the ordering changes as the board changes. Seed fallback can alter the mix again. Consequently the actual daily mix is accidental rather than quota-controlled.
2. The sheep floor is a **pipeline purchase** floor. It does not guarantee two sheep placed by day 5, four by day 8, or six by day 11. A sheep in the shed/inventory satisfies the purchasing test even while it earns nothing, and pasture building/placement can lag the purchase.

The wheat hold is safe to test but is a tail optimization. Even a favorable $4 price improvement on 30 units is only $120. It cannot close a material part of the remaining gap.

## Ranked tests

### 1. Replace probabilistic crop selection with a strawberry-first daily quota

**Highest-value next move. Expected impact: +$5k to +$15k, with no larger field required.**

Keep flat watering, the role split, and the proven `3/4` growth budget. Change only crop admission during the strawberry window:

- days 4--10: every admitted plant is `STRAWBERRY` while a strawberry seed is available;
- days 11--14: reserve at least 3 of the 4 daily admissions for `STRAWBERRY`;
- only use `MELON` or `WHEAT` as fallback after the day's strawberry quota is satisfied or strawberry stock is zero;
- preserve emergency wheat/feed logic; this is a planting-mix test, not a feed-policy rewrite.

Implement the quota from **actual admitted jobs**, not `idx % 10`. Track `admitted_by_crop` for the day in `_STATE`, increment it only when a PLANT job is admitted, and choose the next crop from the remaining daily quota. This also makes the test reproducible.

Seed supply must support the quota. The current trace bought only 1--3 strawberry seeds per day, despite a nominal `want_per_buy=3`; the affordability fraction and animal/land spending often reduce it. For the test, buy enough at hour 0 to cover that day's strawberry quota plus a two-seed buffer, before optional melon and wheat seeds. Do not target a stock of 41 as though it were a seasonal purchase counter: `target_stock` is current inventory, so it does not enforce 41 total purchases.

This is also the melon diagnosis. During days 4--14 the source explicitly assigns only one nominal slot in ten to melon, down from the earlier roughly 30% intent. With only 3--4 admissions per day, `idx % 10` can easily give melon zero admissions on many days. The fall from 84 to 60 is therefore consistent with the mix change, not with the compact budget secretly buying fewer melon seeds. Do **not** restore melon share in the primary variant: strawberry is ongoing, higher priced late, and avoids the DIG/replant cycle of a harvested melon. Instead run one diagnostic control:

- A: current `idx % 10` mix;
- B: strawberry-first quota above;
- C: B, but guarantee exactly one melon admission on days 4, 7, 10, and 13.

Log plants **successfully placed** by crop and planted day, not merely jobs generated; also log seeds stranded at day end and sales by crop. Accept B if strawberry sold rises by at least 35 units while `(strawberry revenue + melon revenue)` rises and milk/wool stay within 2% of control. C tells whether a very small explicit melon allocation has better portfolio value; reject it if it merely swaps high-value strawberry units back into melon.

### 2. Make the sheep ramp placement-aware, then test one targeted extra hand

**Expected impact: +$3k to +$9k.** Wool remains the cleanest non-crop gap, but buying more sheep is not the first fix: the target herd already reaches six. The missing variable is earning days.

Split the current floor into two assertions:

- purchase floor: retain 2 sheep in pipeline by day 5, 4 by day 8, 6 by day 11;
- placement deadline: target 2 **placed** by the end of day 5, 4 by the end of day 8, and 6 by the end of day 10 (one day earlier than the current final purchase floor).

When placed sheep are below the deadline, reserve an empty pasture or create one, and put `BUILD_PASTURE`/sheep `PLACE` above non-cap-risk animal work until the backlog is cleared. Count placed sheep directly; a sheep in shed or carried inventory must not satisfy the placement deadline. Keep FEED first and retain the proven cap-risk HARVEST rule. This isolates “more production dates” from “more animals.”

Test placement-aware routing first with the current hand ramp. Only if a deadline is missed because animal work remains queued at hour 18 should the 15th hand be tested, and then only on the relevant days:

- control: current maximum of 14 hands;
- targeted labor: 15 hands on days 5--11 only;
- optional follow-up: 15 hands on days 5--14 only if the first test both meets more placement deadlines and pays back.

The 15th hire costs $610 each day, so days 5--11 cost $4,270. It must produce roughly 18--22 extra wool at plausible prices merely to cover its hire cost, before considering any extra milk/crops. A season-long 15-hand target is therefore not justified yet. Also, `n_crop_hands` is based on `crop_workload`, not workforce size; in most states the added hand joins the animal side. That is useful only if it clears animal chores earlier and then spills into crop jobs. Log placement hour for each sheep, animal jobs remaining at hours 12/18/23, idle actions for the 15th unit, wool/milk units, and final money. Accept the extra hand only on final-money improvement, not on throughput alone.

One nearby issue should be measured during this test: `crop_workload = plants + min(plantable_count, 20)` charges the role splitter for up to 20 hypothetical future plants even though daily admission is only 3--4. This can allocate 5--6 crop hands to a 16--23 plant field. Do not combine a role-formula change with the sheep placement test, but log `plants`, actual crop jobs, `n_crop_hands`, and animal jobs left. If animal queues persist while crop hands idle, that is the strongest candidate for Round 6.

### 3. Test a bounded day-25 wheat hold

**Expected impact: $0 to +$1k; low risk, low ceiling.**

Use a strict terminal hold so it cannot interfere with the early reinvestment engine:

- through day 24: retain current continuous wheat sales;
- days 25--28: preserve the normal feed reserve, then hold at most 30 additional wheat;
- never hold if free shed capacity would fall below 25 slots;
- day 29 hour 0 onward: sell all wheat above the feed needed for the final day, retrying on later turns if necessary.

Run caps of 20 and 30 against control. Record the volume and volume-weighted price of wheat sold, any DROP/overflow loss, market orders omitted at the ten-order limit, emergency feed buys, and final money. The hold wins only if final money improves without overflow or missed liquidation. Do not expand it earlier than day 25: the old conservative `sell_value` formula already helps by restraining spending, but withholding actual early wheat would remove the cash that funds land, sheep, and strawberry seeds.

## Recommended sequence

1. Run the deterministic strawberry quota as A/B/C against the current mix. This attacks the $/tile bottleneck without increasing watering load.
2. Run placement-aware sheep deadlines at 14 hands; add the 15th hand only for days on which the logs prove an animal backlog prevents placement or CARE/HARVEST.
3. Add the 20/30-unit terminal wheat hold only after the production winner is fixed.

The likely Round 5 winner is not “more plants.” It is a field of the same size with materially more early strawberries, plus sheep that are actually in pastures by the floor dates rather than merely somewhere in the purchase pipeline.
