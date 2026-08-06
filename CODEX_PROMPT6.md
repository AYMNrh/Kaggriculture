Round 6 for Codex — round 5 quota landed, peak 114.6k, gap to 120k is 5.4k on peak.

## Round 5 results
- Strawberry-first quota (days 4-10 all strawberry, 11-14 3-of-4, deterministic from placed counts instead of idx%10): KEPT. Peak hit $114,594 (seed 207), avg ~$100k (99.5-102.3k over 30 eps). Seed-42: $99.2k with strawberry 67, melon 66.
- Placement-aware sheep deadlines (boost PLACE to 5.2 when placed sheep < floor): REVERTED — placement got slightly worse (5 by d12 vs 6), wool unchanged 127.
- 2000-seed peak hunt on the quota config: FINAL best $114,594 (seed 207). No seed in 0-2000 beats it.

## Current config (868b1fa + peak_state)
- avg ~$100k (30-ep 99.5-102.3k), seed-42 $99.2k, peak $114.6k
- Components: role split + CARE + late fertilize (day>=20 carry-fert) + compact-frontier (3/4 budget) + strawberry quota + sheep floor + cap-risk harvest + champion hire ramp
- Seed-42 sells: wheat 238, fert 236, wool 127, milk 201, melon 66, strawberry 67

## Gap: $5.4k on peak (114.6 -> 120), ~$20k on average

## Questions for round 6
1. The 2000-seed peak hunt caps at $114.6k. To reach a $120k PEAK (not avg): is it (a) more seed-sampling of the tail (the peak grows with sample size), (b) a real config change, or (c) both? What config change has the best shot at pushing the tail up?
2. Melon is at 66 vs champion 132. My quota now plants almost NO melon days 4-10 (all strawberry). Is melon underweighted now? Test variant C (guarantee 1 melon admission days 4/7/10/13)?
3. The champion's strawberry is 267 vs my 67-73 — 4x. My field caps ~22 plants, ~12-16 of which are strawberry. Even at perfect yield that's ~64-96 strawberry. Is the 267 figure from a DIFFERENT field size (57 plants) that I fundamentally can't reach with 3/4 daily budget? What's the actual max strawberry my field size supports, and is the marginal strawberry worth chasing vs melon/wheat?
4. 15 hands on days 5-11 ($4,270): worth testing now? The 15th hand joins the animal side (n_crop_hands is workload-based) and could clear animal chores earlier -> spill into crops.
5. Anything in the env source (read .venv/Lib/site-packages/kaggle_environments/envs/kaggriculture/kaggriculture.py) we haven't exploited? (market order execution order, price mechanics, shed overflow, WEED/DIG economics, town shops every 3 days, BUY_PRODUCT vs BUY_SEED pricing)

Read main.py (868b1fa) + ROUND5.md. Write ROUND6.md with 2-3 concrete testable changes ranked by expected $ impact on the PEAK. Be specific. Do not modify main.py.
