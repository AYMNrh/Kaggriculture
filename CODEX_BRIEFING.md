# Kaggriculture $120k Mission — Codex Briefing

## Goal
Beat **$120,000 end-of-season bank** in the Kaggle Kaggriculture simulation (30-day season = 720 turns, 10x10 farm, shared-price market economy). Current agent: **~$95k average, $111k peak** (seed 1157), 100% win rate vs built-ins. The #1 leaderboard agent ("StopPlantingStartGameTheorying") scores $117-156k.

## Environment facts (verified from env source)
- 4 quadrants: NW (start), NE $1k (day ~7), SW $2k (day ~10), SE $4k (never worth it)
- Animals: COW $400 → MILK $160 base, first_yield_day **8**, interval 2, max_held 6. SHEEP $500 → WOOL $200 base, first_yield_day **6**, interval 3. GOOSE $300 → EGG.
- Crops: wheat 10/25 base, melon 80/250 (non-ongoing, dies day 12), strawberry 100/120 (ongoing, first yield day 10, interval 2), carrot, tomato.
- **CARE mechanic**: fed+cared animal banks +1 pending bonus, consumed on next production day → 2 units instead of 1. Biggest single lever found ($20k → $64k).
- **FERTILIZE**: doubles crop yield on production day (1→2). Champion does 1-14/day from day 9, exploding to 9-14/day late. This is how they sell 267 strawberry from 41 plants.
- Market: prices RISE all season (milk $172→329, strawberry $132→306, wheat $26→50). Fertilizer DECAYS $100→$21 (town never buys it — sell immediately).
- Hands: fib cost (5=$12/day, 9=$88, 12=$376, 14=$986). Champion ramp: 5 day 0, hold 5-6, 8-9 by day 8-10, 10-11 by day 12-14, 12-14 by day 21+.
- Champion opening: day 0 turn 1 all-in 3 cows + 1 sheep, buys animals in sparse bursts (d5: 1c+1s, d7: 1c, d8: 3s, d9: 1c, d11: 2c), ~$700-2300 cash per burst.
- Champion field: 17 plants day 0, 19 by day 4, **28 by day 8, 46 by day 12, 57 by day 16** — dense carpet. They plant in bursts (9-14/day) on days 4-13.
- Champion sells: 267 strawberry + 132 melon + 237 fert + 229 milk + 190 wheat + 164 wool ≈ $220k gross. **Day 0-8: 31 fert + 43 wheat + 5 wool + 18 milk ≈ $8k early cash.**

## Current agent architecture (main.py, ~770 lines)
- **Role split (PROVEN ESSENTIAL)**: crop hands (WATER/PLANT/DIG) never take animal chores; animal hands (FEED/CARE/COLLECT) do animals first, spill into crops when idle. Removing it collapses to $5.6k — animal chores (prio 5-6) hog every unit and crops die.
- Priority ladder: FEED 6 > BUILD 6.5(when shortage) > CARE 5.5 > COLLECT 5 > HARVEST 4.5 > WATER 4 > PLANT 3.2 > DIG 1
- Crop-first iteration order + indexed hand-action assignment (unit idx → actions list, not append order)
- Champion hire ramp HIRE_TARGETS [(0,5),(4,6),(8,9),(11,10),(14,11),(18,12),(22,14)]
- Sell-everything-except-wheat-reserve loop (champion-matching: fert immediately, milk/wool as produced, wheat reserve = pipeline animals + floor 10)
- Day-0 opening: 3 cows + 1 sheep + melon/wheat seeds + feed wheat + hires
- Animal buys in sparse bursts (cows first, sheep after cows fill via elif)
- Seeds: strawberry (41 target, 3/buy, 30% of investable), melon 26, wheat 60
- max_early=19 cap before strawberry window (days 0-3), then unlimited
- Land: NE ~day 7, SW ~day 10, never SE — gated on investable
- Farmer (unit 0) is ALWAYS an animal unit (floor) — prevents the h0 crop-flip bug

## What has been TRIED AND FAILED (regressions, reverted)
1. **FERTILIZE — 6+ implementations, ALL regressed**: fert sold before hands exist; farmer picks up fert at h0 (only unit, classified crop) then flips to animal duty carrying fert stuck in inventory all day; multiple hands fetch fert simultaneously (inventory-scan guard races); animal hands COLLECT fert they can't apply (FERTILIZE is a crop-pool job); dedicated fert-fetch branch + sticky-target handling + carry-fert-go-fertilize branch — each one either broke animal survival (hands diverted from FEED) or never fired (0 FERTILIZE actions in traces).
2. **Price-aware holding** (hold milk/wool for late spike, sell only overflow): collapsed to $42 — cash flow beats price timing; the champion's sell-everything-reinvest model compounds harder.
3. **Single pool** (remove role split, champion-style uniform hands): $5.6k collapse.
4. **PLANT priority boosts** (4.4-4.5 vs WATER 4.0, including day-0-1 burst and land-unlock bursts): all regress — planting up starves watering, plants die within 2 days.
5. **Seed buy rate boosts** (5/day, 50% investable): regressed — crowded the animal budget, cows stalled.
6. **Pasture build-ahead** (build all 14 early): regressed — crowded plant tiles on 25-tile NW before NE unlocks.
7. **Sheep early buying** (interleave with cows at 4-5 cows): regressed — spread budget too thin, cows arrived late.
8. **Crop hand count formula tweaks** (1 per 6, workload-based): marginal, hover around baseline.
9. **Distance-weighted job scoring**: flat to slightly worse.

## The core tension (the $25k gap)
The champion's model = uniform hands, dense 57-plant field, daily fertilize, plant bursts. My model = role split (required to survive), ~21-27 plants, no fertilize, 1-6 plants/day. **The role split that makes the agent work at all is exactly what blocks the dense field + fertilize-daily strategy.** Every priority/structural change to bridge this regresses one of the two pillars.

Remaining gap breakdown vs champion: strawberry 27 vs 267 (~$50k), melon 84 vs 132 (~$12k), wool 104 vs 164 (~$12k), wheat 264 vs 190 (I sell MORE), fert 321 vs 237 (I sell MORE), milk 247 vs 229 (I sell MORE).

## What I want from you (Codex)
1. **Debate the core tension**: is there a way to get fertilize working WITH the role split? (e.g. animal hands that collect fert also apply it as part of the animal loop; or a dedicated fertilize hand that's added when the herd is stable)
2. **Analyze the champion's replant pattern**: they plant 13-14/day on days 11-13 — how do their hands mass-plant while watering 41 plants? What's the actual mechanism?
3. **Propose 2-3 concrete, testable changes** with expected $ impact, ranked.
4. Review main.py for any outright bugs or missed mechanics.

The code is at C:\Users\rhihi\projects\kaggriculture\main.py (WSL: /mnt/c/Users/rhihi/projects/kaggriculture/main.py). Env source: .venv/Lib/site-packages/kaggle_environments/envs/kaggriculture/kaggriculture.py (WSL: /mnt/c/Users/rhihi/projects/kaggriculture/.venv/Lib/site-packages/...). Champion replays: /mnt/c/Users/rhihi/Downloads/strategies of stopplantinstartgametheorying/*.json (23 replays, ~29MB each — 90219149.json is the reference).
