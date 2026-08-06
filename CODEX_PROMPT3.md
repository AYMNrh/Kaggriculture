Round 3 for Codex — status update and a stubborn problem.

## What worked (your round 1 change #2)
Late-game carry-fert idle filler (day>=20, animal hand with fert applies to nearby strawberry/melon when animal chores done). FERTILIZE now fires 5-8/day late, strawberry 49->72, seed-42 $106.8k. Baseline now ~$95-97k avg (was $92.6-94.9k).

## The stubborn wall: field size (22-29 plants vs champion's 57)
Every attempt to grow the field regresses the animal economy. Tested and failed:
1. Risk-tiered watering (urgent 5.8/production 4.4/rotation 3.3): neutral on avg
2. Planter boost (one crop hand PLANT->4.4): field grew to 29, strawberry 72, BUT milk 233->160, wool 99->71 (herd starved)
3. Hard cap n_crop_hands at 6: still milk 184 (herd starved at day 8-12 when hands are few)
4. Dynamic cap (animal_needed = animals/4+1): crops starved, $79-83k
5. Density-ordered planting (fill in next to existing plants): flat
6. Water-debt scheduler (cap new plants by water capacity): my first impl counted ALL unwatered plants as debt at morning start (they're all unwatered at h0!), blocked planting entirely

## My diagnosis
The role split allocates crop hands from plant count: `n_crop_hands = (plants + plantable + 5)//7`. When the field grows to 29, this gives 6-7 crop hands, leaving 4-5 animal hands with 11 total hands. 14 animals × 3 chores = 42 actions/day needs ~5 hands. So field growth → animal starvation, no matter the planting mechanism.

The champion has 57 plants AND 14 animals with 11-14 hands. Their day-14 action mix: 41 WATER + 4 PLANT + 14 FEED + 14 CARE + 14 COLLECT + 12 HARVEST = ~99 actions/day with ~11 hands = 9/hand. Mine: ~66 actions/day with 11 hands. They're ~50% more efficient per hand.

## Questions
1. Is the champion's efficiency from FIELD DENSITY (1-2 tile walks vs my 3-5)? If so, why did density-ordered planting not help? (Maybe because my plant loop generates jobs for ALL free tiles, so hands still get far targets?)
2. Should the crop/animal hand split NOT be based on plant count at all? What determines it in the champion?
3. The champion waters 41 plants with ~7 crop hands = 6 plants/hand/day. Mine waters ~19 with 5 hands = 3.8/hand. Even at equal efficiency they'd water 30+. Is the champion NOT watering every plant daily (rotation)?
4. What's the highest-value NEXT change — I've spent many iterations on field growth. Is there a different lever (e.g. sell timing, market order priority, shed management)?

Read main.py current state + ROUND2.md. Write ROUND3.md with 2-3 concrete testable changes, ranked. Do not modify main.py.
