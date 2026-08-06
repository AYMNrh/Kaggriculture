Round 7 for Codex — round 6 wins landed, gap to 120k now $3.95k on peak.

## Round 6 results
- Production-aware fertilize (target strawberry by next production refresh, day 13+): avg 103.7-104.2k
- Melon variant C (guarantee 1 melon admission days 4/7/10/13): avg 102.8-104.3k, melon 90, seed-42 +$4.2k
- FEED-SAFE gate (fertilize fires when all FEED jobs covered, capped 2/turn, instead of only when animal pool fully empty): avg 103.9-105.6k (best yet), seed-42 $104.7k
- 2000-seed hunt on production-aware config: peak $116,007 (seed 964)
- Feed-safe config re-check of peak seeds: seed 853 improved to $116,050 — new peak

## Current config (8b3d795)
- avg ~$105k (30-ep: 103.9-105.6k), seed-42 $104.7k, peak $116,050 (seed 853)
- Gap to $120k: $3.95k on peak, ~$15k on average
- Seed-42 sells: wheat 196, fert 243, wool 129, milk 199, melon 90, strawberry 60
- 10,000-seed hunt running in background (seeds 2000-12000)

## Honest observation
FERTILIZE still does NOT fire days 13-19 on seed 42 (the feed_jobs==0 gate never triggers mid-game with 14 animals). The avg gain came from better late-game fertilize + the cap. The early-window fertilize remains unreachable with my hand count.

## Questions for round 7
1. The peak is $116k vs champion finals $117-156k. Remaining gap $3.95k. Given the avg is now $105k, what's the single highest-value change for the PEAK (not avg)?
2. Strawberry 60 vs champion 267: I have ~16 strawberry plants max (field caps 22). Even fertilized perfectly that's ~128 units max. Is the champion's 267 from a fundamentally bigger field I can't reach, or is there a way to squeeze more strawberry per tile (e.g. replant after harvest — strawberry is ongoing, does it keep producing after 4 units or should I DIG+replant)?
3. Melon 90 vs champion 132: melon is non-ongoing (one 6-unit harvest at day 12). Should I replant melon after harvest for a second crop?
4. Wool 129 vs champion 164: any remaining wool lever?
5. Wheat: I sell 196, champion 190. Held for late spike? My sell-everything may be leaving money — test bounded day-25 hold?

Read main.py (8b3d795) + ROUND6.md. Write ROUND7.md with 2-3 concrete testable changes ranked by expected $ impact on the PEAK. Be specific. Do not modify main.py.
