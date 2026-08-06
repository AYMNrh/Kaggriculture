Round 8 for Codex — my sell-timing hypothesis is DISPROVEN. The real gap is production capacity.

## New hard data (from measuring my agent vs champion replay 90219149)

Realized prices (mine vs pass, seed 42 | champion vs real opponent):
- STRAWBERRY: mine 60 units @ $283 | champ 259 @ $229
- MILK: mine 199 @ $246 | champ 229 @ $185
- WOOL: mine 129 @ $242 | champ 163 @ $121
- WHEAT: mine 196 @ $44 | champ 180 @ $45
- MELON: mine 90 @ $257 | champ 138 @ $179

CONCLUSION 1: My prices are BETTER than the champion's on every product (market is demand-starved vs pass). The entire gap is VOLUME: 199 fewer strawberry = ~$56k missing gross. Not sell timing.

CONCLUSION 2: My agent ALREADY sells in small daily lots (milk 9-21/day, strawberry 1-16/day) — the sell loop runs every turn so the shed never accumulates a dump. Sell-spreading is a non-issue.

CONCLUSION 3: Champion live plants: 39 strawberry + 13 melon + 5 wheat = 57 by day 13-14. Strawberry ramps 2->6->11->16->17->26->32->37->39 (days 5-15), ~2-6 new/day steadily. My field caps at ~22.

CONCLUSION 4: Champion actions/day: day 16 = WATER 46 + FEED 14 + CARE 14 + COLLECT 14 + PICKUP 9 + HARVEST 6 + FERTILIZE 5 + PLANT 4 = ~112 useful actions with 14 hands. Mine: ~66 with 12-13 hands. They get ~1.7x work per day.

## The real question
My role-split architecture caps the field at ~22 plants because crop hands can't water more AND the herd needs its hands. The champion waters 46/day with 14 hands. Options I've tried and failed: planter boost (milk crash), flex scheduler (4 variants), water tiers, budget raises. All regressed.

## What I need from round 8
1. The champion waters 46/day AND cares/feeds 14 animals AND harvests — with 14 hands that's ~8 actions/hand. My hands do ~5-6. Is the champion's efficiency from (a) more hands (14 vs my 12), (b) tighter routing (dense field), or (c) something structural I'm missing? What EXACTLY would let MY agent reach 40+ plants without starving the herd?
2. My hand count peaks at 12-13 (HIRE_TARGETS [(0,5),(4,6),(8,9),(11,10),(14,11),(18,12),(22,14)]). The champion has 14 by day 16. Should I hire 14 earlier (cost: fib(13)+fib(14)=233+377=610/day)? Does that alone unlock the bigger field?
3. Is there a cheap way to reduce WATER action count? (e.g. the champion's 46 waters for 57 plants ≈ 0.8 water/plant/day — some plants skip days safely? I proved alternating dies. But maybe SKIPPING wheat/melon (one-time crops) to save water for strawberry?)
4. Strawberry sells at $283 for me vs $229 for champ — even ONE more strawberry plant ≈ 4 units × $280 = $1,120. A 15-plant strawberry field vs my current ~16: what's the marginal $/plant and what's the cheapest way to add 5-10 plants?
5. Given peak tail exhausted at $118.8k: is field growth the ONLY path to $120k, or is there a non-field lever (fertilize volume, animal count, land timing)?

Read main.py + ROUND7.md. Write ROUND8.md with 2-3 concrete testable changes ranked by expected $ impact. Be specific. Do not modify main.py.
