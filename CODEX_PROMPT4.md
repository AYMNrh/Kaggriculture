Round 4 for Codex — compact-frontier worked, final push to $120k.

## Round 3 results
Your change #2 (bounded PLANT bundles, adjacency-ranked compact frontier) WORKED:
- 30-ep avg: $97.0-98.5k (was $94.6-97.0k) — best ever
- Peak over ~1600 seeds: $112,810 (seed 338) — was $111.2k
- Implementation: growth_budget 3 (days <=7) / 4 (day 8+), plantable sorted by adjacency to existing plants, admitted <= budget/day

Your change #1 (deadline-reserve flex scheduler) FAILED in all variants:
- Reserve = ceil(debts×2.5/hours_left): milk 233->137 (flex stole crop work / reserve too small)
- Reserve = debts×4.0: milk 186, still below baseline
- Hard cap n_crop_hands at 6: milk 184 at day 14
- Dynamic animal-need cap: crops starved, $79-83k
The flex pool merging (animal-side units beyond reserve take combined pool) keeps trading milk for crops no matter the reserve math. Reverted.

## Current state
- avg ~$97-98.5k, peak $112.8k, 100% win rate
- Gap to $120k: ~$7k on peak, ~$22k on average
- Components: late-game fertilize (day>=20 carry-fert idle filler, 5-8/day) + compact-frontier planting + role split + CARE doubling + champion hire ramp

## Questions for round 4
1. The remaining ~$7k on peak: is it still field-size (my max plants ~19-29 vs champion 57), or is the marginal gain now elsewhere (sell timing, market order priority, shed mgmt)?
2. Given flex scheduler failed 4 ways, what's the most surgical way to add crop capacity WITHOUT touching the role split? (e.g. MORE HANDS — raise hire targets? The champion hits 14 by day 21; mine too. What about 15-16 hands?)
3. The champion sells ~1,219 units ≈ $220k gross; I sell ~900. Where's the biggest missing volume: milk (I do 218-233 vs champ 229), wool (99-119 vs 164), strawberry (54 vs 267), melon (60-84 vs 132)?
4. Market mechanics: I verified prices rise all season. The champion holds wheat for the late spike ($25->47). I sell everything. Test a late-game wheat hold (day 25+)?
5. Any bug in my sell/hire/market-order handling worth fixing (10-order cap)?

Read main.py + ROUND3.md. Write ROUND4.md with 2-3 concrete testable changes ranked by expected $ impact. Be specific. Do not modify main.py.
