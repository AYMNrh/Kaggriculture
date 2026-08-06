# Kaggriculture — agent dev loop

Local dev setup for the [Kaggriculture](https://www.kaggle.com/competitions/kaggriculture)
Kaggle simulation competition (farming-sim agents, $50k prize pool, ends 2026-09-30).

## Quick start

```bash
# venv already created; activate or use the python directly
.venv/Scripts/python.exe battle_test.py --episodes 10   # vs pass/random/starter
.venv/Scripts/python.exe battle_test.py --episodes 30   # bigger sample
```

`main.py` is the agent (entry point: `agent(obs)` — the required name for submissions).

## Current status

Baseline v2 ("labor-scaled staple farmer"):
- wheat + carrot staple farming, 60/40 mix
- hires farm hands aggressively (fib cost 1,1,2,3…/day — near-free labor)
- caps planting at watering capacity (~8 plants/unit) so nothing dies as weeds
- sticky per-unit job targets + reservation to stop units converging on the same tile
- DROP logistics: units carrying >= 15 items return to the shed (shed cap is 100)
- buys land only after labor >= 4 hands and cash > $2.5k
- sells everything in the shed every turn

Results (30 episodes, full 720-turn season, random seeds):
- vs pass:    100% win  (avg $8,968 vs $3,000)
- vs random:  100% win  (avg $8,803 vs $2)
- vs starter: 100% win  (avg $8,666 vs $3,460)

## Key mechanics learned (see env source in
`.venv/Lib/site-packages/kaggle_environments/envs/kaggriculture/kaggriculture.py`)

- 720 turns = 24 turns/day × 30 days. Winner = most money in bank at end.
- **New seed starts with `consecutive_unwatered=1`** — planting day counts as the
  first missed day. Must water on the same day or it becomes a weed overnight.
- WATER once/day (subsequent = no-op). FERTILIZE: doubles per-day yield bonus 3 days.
- One-time crops (wheat/carrot/melon): yield grows with watering during the bonus
  window [ceil(max_yield_day/2), max_yield_day]; harvest at max_yield_day, decay
  starts next day. Ongoing (tomato/strawberry): production on schedule, max 4.
- Animals: FEED consumes wheat **from the acting unit's inventory** (pickup first).
  CARE banks +1 on next production; COLLECT_FERTILIZER 1/animal/day.
- SELL drains the shed (harvests land there at end-of-day; overflow >100 discarded).
  Only WHEAT and FERTILIZER can be bought back (BUY_PRODUCT).
- Market: price moves dynamically per unit traded, per-resource shape functions.
  Premium goods (strawberry/melon/milk/wool) crash to $1 on modest gluts.
- Farm hands: `HIRE` costs `fib(n)` per day (1,1,2,3,5,8…), reset daily; hands
  disappear end-of-day, must re-hire each day. Spawn shed-adjacent.
- Land: NE $1k → SW $2k → SE $4k.

## Submitting (requires Kaggle account)

```bash
# one-time auth (browser flow; or generate token at
# https://www.kaggle.com/settings/api and save to ~/.kaggle/access_token)
.venv/Scripts/kaggle.exe auth login

# accept rules on the website first: https://www.kaggle.com/competitions/kaggriculture
.venv/Scripts/kaggle.exe competitions submit kaggriculture -f main.py -m "baseline v2"
.venv/Scripts/kaggle.exe competitions submissions kaggriculture   # status
.venv/Scripts/kaggle.exe competitions leaderboard kaggriculture -s
```

5 submissions/day max; only latest 2 tracked. Files land in
`/kaggle_simulations/agent/` — keep `main.py` at the root with `agent(obs)`.
