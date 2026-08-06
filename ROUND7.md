# Round 7: turn peak seeds into production

## Bottom line

The highest-value peak change is **actual early-window strawberry fertilization**. Round 6 did not really test it. In both assignment paths, the fertilization block is nested under `if best_key is None and not is_crop_unit`; therefore an animal hand can consider fertilizing only after it has no animal job. Inside that block, `(best_key is None or feed_covered)` is already true because `best_key is necessarily None`. In addition, `feed_jobs` is a static count and is never decremented as FEED jobs are claimed. The advertised FEED-SAFE behavior is consequently still the old idle-only behavior.

Fixing that control-flow error is the best single bet for seed 853. The peak needs only $950, or roughly four extra late strawberries. It does not require approaching the champion's crop count.

The second independent lever is recycling completed melons. `main.py` buys toward 26 melon seeds and even labels the target "replant", but a harvested non-ongoing plant is never dug: annual plants receive HARVEST at maturity and then remain on the board forever at zero yield. Early melons can finish with enough time for a second crop.

## Answers to the five questions

1. **Best peak change:** make FEED-SAFE fertilization real, by allowing a fertilizer-carrying animal hand to leave lower-priority animal work once every outstanding FEED tile has a unit reserved. Test this before changing the crop mix again.
2. **Strawberry 267:** this is fundamentally a much larger cohort. A strawberry is ongoing only for its four scheduled production events; ongoing does not mean infinite production. Normal lifetime output is 4, and perfect fertilizer can raise the four events to at most 8. Sixteen plants therefore cap at 64 normally or 128 perfectly. DIG+replant after the fourth event does not help: a day-4 strawberry finishes around day 20 and a replacement's first output arrives at or beyond the end of the 30-day season. Do not recycle strawberries.
3. **Melon 90:** yes, recycle sufficiently early melons. It is a one-harvest annual, and the current code never removes the exhausted plant. A replacement planted by day 17 can reach its day-12 maximum by day 29. Restrict the test to plants whose replacement has the full 12-day runway; do not dig late melons merely to make the board look empty.
4. **Wool 129:** the remaining plausible lever is cap-safe harvesting immediately before a sheep production refresh. The present `yield_u + 1 >= 6` rule understates a cared sheep's next deposit and can let a multi-unit production event hit the six-unit held cap. This is worth tracing, but it ranks below the two crop changes because it can add travel and compete with FEED/CARE.
5. **Wheat 196:** the quantity is already at champion scale. A day-25 hold is a small price-timing test, not the missing production lever. Test it only after the first two changes and only for true surplus above the herd's remaining feed requirement.

## Ranked tests

### 1. Repair FEED-SAFE early strawberry fertilization

**Expected peak impact: +$1.0k to +$4.0k. Highest confidence; most likely to close the $950 gap by itself.**

Move the carry-fertilizer decision out of the `best_key is None` branch. After the animal pool has been scored and FEED targets have been reserved, permit a carrying animal unit to target a production-eligible strawberry when all FEED jobs are covered, even if CARE, COLLECT, HARVEST, or BUILD work remains.

Use a reservation condition, not `feed_jobs == 0`:

- compute the set of outstanding FEED tile keys;
- consider a FEED covered when it is already in `claimed` (including a sticky target claimed earlier in this assignment pass);
- allow fertilization only when `feed_keys - claimed` is empty;
- retain the two **executed applications** per-turn cap and strawberry-first production-date ordering;
- do not count merely carrying wheat as covering a particular FEED tile.

Because units are assigned sequentially, this initially allows only units processed after all FEED keys have been claimed. That is the safe bounded version. If it remains unreachable, pre-reserve the nearest distinct FEED key for enough wheat-carrying animal units before assignment; do not weaken the test to a raw count of wheat or hands.

Run three arms on seeds 42, 853, and the current top 20 seeds from the hunt, then a common 100-seed panel:

- A: current code;
- B: real FEED-reservation gate, cap 2;
- C: B, cap 1.

Log day/hour, unit, FEED keys/claimed keys, displaced job type, fertilizer application, covered strawberry refreshes, and final strawberry/milk/wool/fertilizer sales. Keep B or C only if FEED completion is unchanged and milk/wool each fall by no more than 2%. The peak success threshold is only four additional late strawberries or at least +$1,000 on seed 853.

### 2. DIG and replant exhausted early melons

**Expected peak impact: +$1.0k to +$3.5k; higher ceiling but more labor risk.**

When a non-ongoing MELON has been harvested and `yield_units == 0`, create a recycle job only when `day <= 17` and a melon seed is available or affordable. Make it a two-stage state transition: DIG the exhausted plant, then let the existing admission logic PLANT MELON on the empty tile and water it that day. A job generated is not a successful recycle; count only a completed DIG followed by a completed PLANT and same-day WATER.

Do not recycle wheat in this test, do not recycle strawberries, and do not raise the 3/4 daily growth budget. Give an empty recycled melon tile first claim on one existing admission slot so recycling cannot silently expand crop workload. Prefer the earliest harvested/closest melon, since every lost day reduces watering margin.

Compare:

- A: current permanent exhausted annuals;
- B: recycle melon through day 17;
- C: conservative cutoff day 16.

Run the same peak panel after selecting test 1's winner. Log exhausted melon tiles, DIG/PLANT/WATER completion, second-crop harvests, missed animal work, total melon units, and final money. Seven additional full melon harvests would explain the 90-to-132 unit gap, but do not require matching 132: even two successful second crops add 12 units, roughly $3k gross at late prices.

### 3. Harvest sheep by next-deposit size, then test a tiny terminal wheat hold

**Expected peak impact: wool +$0.5k to +$2.0k; wheat hold $0 to +$0.8k. Diagnostic priority.**

First trace every sheep production refresh on seeds 42 and 853: pre-refresh held wool, accumulated care bonus, attempted deposit, post-refresh held wool, and discarded units at the six-unit cap. Replace the current `yield_u + 1 >= 6` urgency check only if the trace proves loss. The candidate rule is to raise HARVEST above CARE on the last turn before production whenever `yield_u + projected_next_deposit > 6`. Keep FEED above it. This targets actual cap loss instead of harvesting all sheep more often.

Afterward, test wheat sale timing without changing wheat production:

- control: current sell-surplus-every-turn;
- hold: on days 25-28 retain at most 20 surplus wheat, while reserving `animals * remaining_days` feed if future wheat harvests are not guaranteed; liquidate all surplus on day 29 at the best observed quote/last safe market turn;
- adaptive: hold only when the current wheat quote is below that seed's trailing four-turn maximum, with the same 20-unit cap.

Record realized average price, unsold/overflow wheat, emergency feed purchases, blocked market orders, and final money. Reject the hold if it reduces animal feeding or leaves inventory unsold. With only six more units sold than the champion, wheat volume is not the issue; only realized price can produce a small terminal gain.

## Round order

1. Patch and test the real FEED-reservation gate on seed 853 and the top-20 tail.
2. Fix that winner, then test early-melon recycling on the identical seeds.
3. Trace sheep cap loss before changing harvest priority; run the bounded wheat hold only as a terminal tie-breaker.

Do not wait for the 10,000-seed hunt to finish before running test 1. The hunt can identify a friendlier market path, but the current peak is already close enough that four correctly fertilized strawberries are a more direct route to $120k.
