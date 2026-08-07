"""DATA SCIENCE: does shop unlock order correlate with final money?

Hypothesis (Codex + THUNDER analysis): seeds that unlock strawberry/milk/
wool-demanding shops early (Brunch, Ice Cream, Smoothie, Yarn) should
outperform. If the correlation is real, adaptive shop-aware play is a
concrete lever for consistent $110k.

Analyzes the 36 THUNDER replays: extract unlock timeline per game,
correlate with final money of both players.
"""
import json, glob, os
from collections import defaultdict
import statistics

folder = r"C:\Users\rhihi\Downloads\thunder thunder"
replays = sorted(glob.glob(os.path.join(folder, "*.json")))

# demand mapping: which shops buy which goods (decoded names)
SHOP_GOODS = {
    "BAKERY": ["EGG", "WHEAT"],
    "PIZZA_SHOP": ["MILK", "TOMATO", "WHEAT"],
    "BRUNCH_SPOT": ["EGG", "WHEAT", "STRAWBERRY"],
    "YARN_STORE": ["WOOL"],  # 2x wool
    "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"],
    "PET_CAFE": ["CARROT"],  # 2x carrot
    "SMOOTHIE_SHOP": ["STRAWBERRY", "MILK"],
    "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"],
}

def analyze(path):
    with open(path, encoding="utf-8") as f:
        rp = json.load(f)
    steps = rp["steps"]
    n = len(steps[-1])
    rewards = [s["reward"] for s in steps[-1]]
    # unlock timeline: first day each shop appears
    unlock_day = {}
    for i, step in enumerate(steps):
        day = i // 24
        obs = step[0].get("observation") or {}
        town = obs.get("town") or {}
        shops = town.get("unlocked_shops") or town.get("shops") or []
        for s in shops:
            if isinstance(s, dict):
                name = s.get("name") or str(s)
            else:
                name = str(s)
            if name not in unlock_day:
                unlock_day[name] = day
    return rewards, unlock_day

# gather per-game: final money (both players) + unlock days
games = []
for path in replays:
    rewards, unlocks = analyze(path)
    for r in rewards:
        games.append((r, unlocks))

# correlate: day strawberry-shops unlock vs final money
def shop_day(unlocks, names):
    ds = [d for n, d in unlocks.items() if n in names]
    return min(ds) if ds else 99

berry_shops = {"BRUNCH_SPOT", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP", "FARMERS_MARKET"}
wool_shops = {"YARN_STORE"}
milk_shops = {"PIZZA_SHOP", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP"}

by_berry_day = defaultdict(list)
by_wool_day = defaultdict(list)
by_milk_day = defaultdict(list)
all_rewards = []
for r, unlocks in games:
    all_rewards.append(r)
    by_berry_day[shop_day(unlocks, berry_shops)].append(r)
    by_wool_day[shop_day(unlocks, wool_shops)].append(r)
    by_milk_day[shop_day(unlocks, milk_shops)].append(r)

print(f"games: {len(games)} (2 players x {len(replays)} replays)")
print(f"overall: mean ${statistics.mean(all_rewards):,.0f} "
      f"med ${statistics.median(all_rewards):,.0f} "
      f"min ${min(all_rewards):,.0f} max ${max(all_rewards):,.0f}")
print()
print("=== strawberry-shop unlock day -> final money ===")
for d in sorted(by_berry_day):
    v = by_berry_day[d]
    print(f"  unlock d{d:2d}: n={len(v):3d} mean ${statistics.mean(v):,.0f} med ${statistics.median(v):,.0f}")
print()
print("=== wool-shop (Yarn) unlock day -> final money ===")
for d in sorted(by_wool_day):
    v = by_wool_day[d]
    print(f"  unlock d{d:2d}: n={len(v):3d} mean ${statistics.mean(v):,.0f} med ${statistics.median(v):,.0f}")
print()
print("=== milk-shop unlock day -> final money ===")
for d in sorted(by_milk_day):
    v = by_milk_day[d]
    print(f"  unlock d{d:2d}: n={len(v):3d} mean ${statistics.mean(v):,.0f} med ${statistics.median(v):,.0f}")
