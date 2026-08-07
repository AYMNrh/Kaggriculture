# Round 11: verdict — the architecture is at its ceiling

## Direct answers
1. **Can the wall be broken inside the role split?** Not with the current global one-tile routing. The role split can remain, but THUNDER-equivalent local work chaining is required for a 40+ field. The dedicated early planter is the last small intervention worth testing before accepting the architectural conclusion.
2. **Would nine crop hands water 40 plants?** No. The formula allocates 9 crop hands, the 6-animal floor permits them — allocation is NOT the hidden cap. Their measured execution rate — 2.8 waters per crop hand per day — IS the cap. Nine hands still produce ~25 waters.
3. **Is there a real $5k+ lever left?** No demonstrated one. Consistent +$5k requires a scheduler rewrite that materially increases useful actions per crop hand. After 17 regressions, assigning it positive expected value without evidence would be wishful thinking.
4. **Is early planting the untested lever?** Yes, narrowly: not a larger numerical budget, but ONE early planter allowed to beat existing-water jobs while the other crop hands remain waterers. It can plausibly recover the missing three plants before day 4. It cannot explain the full 21-water/day THUNDER gap.

## The one test left
Dedicated early planter (days 0-3): one crop hand whose PLANT priority exceeds WATER so plants get admitted early; other crop hands stay waterers. Accept only if day-3 live plants rise with no new weeds and milk/wool within 2%.

## The defensible strategy
If the one-hand days-0-3 test fails its paired panel, stop tuning this architecture. The committed $104-108k baseline + variance/peak hunting is the defensible strategy. Consistent $110k requires replacing global target competition with a genuinely local chained scheduler — not another priority, budget, crop-mix, or watering-rule adjustment.
