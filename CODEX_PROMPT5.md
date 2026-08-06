Round 5 for Codex — big progress from round 4, now ~$100k avg.

## Round 4 results
- Sheep-floor ramp (2 sheep by d5, 4 by d8, 6 by d11; sheep bought before cows when floor unmet): avg 98.3-100.6k, seed-42 $102.2k
- Cap-risk harvest (HARVEST urgent above CARE when yield+1>=6): avg 99.8-101.8k
- Combined: 30-ep avg $99.8-101.8k, all above $100k for the first time
- sell_value mirror fix: REVERTED — regressed seeds 42/300 ($103.1k -> $98.3k avg on 5-seed comparison). The old formula's extra conservatism helped cash flow.
- Risk-tiered watering (must/production/optional rotation): FAILED — melon crashed 84->8 (my yield-window logic skipped production-critical melon). Budget raise to 4/8/4: FAILED (40 plants -> milk 218->196).

## Current config (ded4202)
- avg ~$100k (30-ep: 99.8-101.8k), seed-42 $102.2k, peak so far $112.9k
- Components: role split + CARE + late fertilize (day>=20 carry-fert) + compact-frontier planting (3/4 budget) + sheep floor + cap-risk harvest + champion hire ramp
- Sell volumes (seed 42): wheat 196, fert 258, wool 120, milk 210, melon 60, strawberry 73

## Gap to $120k: ~$7k on peak, ~$20k on average

## Questions for round 5
1. Strawberry is STILL the gap (73 vs champion 267). With avg now $100k, what's the highest-value NEXT move? The field caps at ~19-29 plants — crop hands can't water more AND plant more (the fundamental labor wall).
2. Melon dropped to 60 (was 84 in earlier configs) — the compact-frontier budget allocates fewer melon seeds? Check my crop_for mix during MELON window.
3. Wool 120 vs champion 164 — sheep floor helped; is there more? (Sheep interval 3d + CARE bank. Champion has 6 sheep placed by day 8; mine by day 11?)
4. Is 15 hands worth testing now (the 15th daily hire costs fib 610; last hand 987)? Or is the marginal $ better spent elsewhere?
5. Sell timing: I sell everything continuously. Champion holds wheat for the late spike. Test bounded day-25+ wheat hold?

Read main.py (ded4202) + ROUND4.md. Write ROUND5.md with 2-3 concrete testable changes ranked. Be specific. Do not modify main.py.
