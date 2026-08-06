Round 2 for Codex — your change #2 (carry-fert idle filler) WORKED.

## Results
- FERTILIZE now fires 5-8/day on days 22-29 (was 0 for the whole campaign)
- Strawberry: 49 sold (was 27) on seed 42
- Final: $106,804 on seed 42 (was $95,654) — +$11k
- 30-episode avg: $94.6-97.0k (was $92.6-94.9k without it)
- Implementation: FERTILIZE applied ONLY via carry-fert idle filler — an animal hand that carries fertilizer applies it to a nearby strawberry/melon when NO animal chores remain. Gated to day >= 20 (fert cheap late ~$20, strawberry peaks $300+). Farmer excluded.

## Current state
- Baseline now: ~$95-97k avg, seed-42 $106.8k, best-known peak $111.2k (pre-fertilize agent)
- Peak hunt running with the new agent to find the new ceiling

## Questions for round 2
1. My fertilize fires 5-8/day late vs the champion's 9-14/day. The bottleneck: the idle filler only fires when animal chores are exhausted. Is there a safe way to raise the application rate? (e.g. allow crop hands to carry fert too; or dedicate one late-game hand to fert+water rounds)
2. Strawberry plants are still capped ~21-30 vs the champion's 57. The plant loop caps via max_early=19 before day 4, then unlimited. What's the actual limiter now — seeds, tile space, or crop-hand planting capacity?
3. Should I extend fertilize to wheat late (the champion fertilizes wheat too per earlier data)?
4. Any other mechanics in the env source worth exploiting (read .venv/Lib/site-packages/kaggle_environments/envs/kaggriculture/kaggriculture.py)?

Be specific and testable. Write ROUND2.md.
