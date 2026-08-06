# Round 4: expand the field inside the proven role split

## Bottom line

The remaining gap is primarily crop volume, especially strawberry, not milk and not market timing. Relative to the champion, the approximate unit gaps are:

| Product | Current | Champion | Missing units | Rough missing gross |
|---|---:|---:|---:|---:|
| Milk | 218–233 | 229 | approximately zero | approximately $0 |
| Wool | 99–119 | 164 | 45–65 | $9k–16k |
| Strawberry | 54 | 267 | 213 | $40k+ |
| Melon | 60–84 | 132 | 48–72 | $12k–20k |

Even allowing for different price realization and substitution between products, strawberry is by far the largest missing volume. The compact-frontier win says geometry mattered, but the current admission cap of four plants per day and the policy of watering every plant every day still hold the live field at 19–29. Market improvements can recover hundreds or a few thousand dollars; they cannot manufacture the missing 200 strawberry units.

There is one important correction to Round 3. The engine sets an established watered plant's `consecutive_unwatered` to zero. One missed day changes it to one and the plant survives; a second consecutive miss changes it to two and creates a weed. A newly planted crop starts at one and therefore must be watered on its planting day. A deliberate alternating rotation is safe if it distinguishes these states. The champion's lower WATER count can therefore be real, not merely a replay denominator mismatch.

Do not test 16 hands first. Hands disappear and are rehired each day. The 15th daily hire costs 610 and the 16th costs another 987, or 1,597 incremental dollars per full day. Also, `n_crop_hands` depends on `crop_workload`, not the total workforce, so extra hands usually enter the animal group and reach crops only after animal work is empty. That is an expensive and poorly targeted crop-capacity purchase.

## Ranked tests

### 1. Risk-tiered watering plus larger compact bundles

**Expected impact: +$8k to +$25k final money; highest upside.** This keeps the hard crop/animal ownership split unchanged and frees capacity only inside the crop role.

Replace the single WATER priority with three tiers:

1. **Must water today:** `consecutive_unwatered >= 1`, plus every coordinate in `planted_today`. Priority above PLANT. Missing one of these kills the crop tonight.
2. **Production water:** a strawberry producing at tonight's refresh, or wheat/melon currently in its yield-building window. Priority above PLANT unless it is already safe and the first version needs a more conservative gate.
3. **Optional rotation water:** `consecutive_unwatered == 0` and no production event tonight. Priority below admitted PLANT.

Keep the compact adjacency ordering, but test admission budgets against the current `3/4` control:

- A: `3/4`, tiered water only;
- B: `4` through day 7, `6` from day 8 onward;
- C: `4` through day 7, `8` on days 8–14, then `4` while planting remains profitable.

Every new plant must immediately enter the must-water tier. Do not merely raise PLANT globally: that repeats the earlier failure because new and safely deferrable water would still be indistinguishable. For optional water, use a stable checkerboard or `(x + y + day) % 2` rotation so the same crop is never skipped twice.

Instrument `must_water_remaining` at hours 12, 18, and 23, same-day planted weeds, plants by crop, and units sold. Reject any variant with a must-water miss or lower milk/wool. Accept if median live plants reaches at least 38 by day 14 and strawberry sold rises by at least 40 units. If B succeeds without misses, C is the direct attempt at the remaining peak gap.

### 2. Pull sheep production forward and protect wool harvests

**Expected impact: +$5k to +$12k.** The milk gap is already closed; wool is the largest animal-side deficit. The purchase code explicitly completes the cow target before regularly topping sheep, so the opening sheep can remain alone until roughly day 10. A sheep placed five days earlier gets one or two additional production events, and daily CARE banks bonuses between its three-day production events.

Test a sheep-floor ramp without changing unit roles or final herd size:

- retain the day-0 opening of 3 cows + 1 sheep;
- require at least 2 sheep in pipeline by day 5, 4 by day 8, and 6 by day 11;
- when below that floor, buy sheep before the next cow; otherwise retain the existing cow-first logic;
- count animals in shed and inventories so a delayed PLACE does not trigger duplicate purchases.

Also make animal HARVEST urgent when waiting through the next production boundary would exceed `max_held = 6`. With daily CARE, sheep can add roughly four units at a production event, so leaving even 3+ wool on the animal risks losing output to the cap. Put cap-risk HARVEST above routine CARE and fertilizer collection, while FEED remains first.

Run the ramp alone, harvest urgency alone, then combined. Log placement day for every sheep, pre-production `yield_units`, units clipped by the six-unit cap, and wool sold. Accept if wool rises by at least 25 units with milk within 2% and crop counts unchanged. This test targets $5k+ of realizable revenue without asking crop hands to do animal work.

### 3. Fix market accounting and test only a bounded terminal wheat hold

**Expected impact: +$0.5k to +$3k.** This is correctness and price realization, not the route to the missing crop volume.

There is a definite mismatch in `main.py`. The submitted wheat sale keeps `max(10, pipeline_animals)` and sells at most 20 units. The later `sell_value` estimate instead subtracts `WHEAT_FEED_RESERVE + total_animals`, does not use the same pipeline count, and does not apply the 20-unit cap. Therefore the comment that it mirrors the sell loop exactly is false. Build the sell orders first and derive expected proceeds from those exact submitted quantities. Use a conservative price estimate because a multi-unit sale is repriced one unit at a time.

The ten-order limit is **per turn**, not per day. Quantity does not consume extra slots. Current day-0/hour-0 turns can nevertheless hit ten distinct orders because sells, up to three hires, animals, three seed types, feed, and land are appended sequentially. Build ranked intents and reserve slots in this order:

1. sales needed to fund the turn and emergency feed;
2. due land and active-window strawberry seed;
3. animal burst and required hires;
4. melon/wheat seed and optional sales.

Log every valid intent omitted after slot ten. Only change ordering if this counter shows land, strawberry seed, or feed being dropped; the existing traces show the cap is reached on some busy turns, but reaching ten is not itself a bug.

For sell timing, test a bounded wheat hold only after reinvestment is effectively over:

- control: current continuous selling;
- hold: from day 25, retain at most 20–30 surplus wheat, always preserving at least 25 free shed slots;
- liquidate all held wheat on day 29, preferably early enough to retry if the order fails.

Do not hold milk, wool, strawberry, or a large wheat balance in the 100-slot shed: end-of-day and explicit DROP silently discard overflow. Wheat rising from roughly $43 to $47 over the hold is only about $80–120 on 20–30 units, so reject the hold if it delays hires, causes any overflow, or fails to liquidate. Its expected value is small; the accounting and order-priority fixes are more important than the speculation.

## Recommended sequence

1. Test risk-tiered watering at the existing `3/4` budget to prove zero deaths, then raise admission to `4/6` and `4/8`.
2. Independently test the sheep-floor ramp and cap-risk harvest priority; combine them with the winning water variant.
3. Fix exact sell budgeting/order intent accounting, then run the bounded day-25 wheat hold as a final small optimization.

The best route to $120k is a 40+ plant field with the current role firewall intact, followed by recovering 25–50 missing wool. Fifteen hands may be worth a later one-day or late-window test; sixteen hands are not a sensible first bet at 987 additional dollars per day for the last hand alone.
