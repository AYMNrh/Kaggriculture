"""Extract THUNDER's daily schedule tables from all 36 replays.

Produces per-day (mean ± std across replays):
1. Action counts: WATER, PLANT, FEED, CARE, COLLECT_FERTILIZER, HARVEST,
   FERTILIZE, PICKUP, BUILD_PASTURE, PLACE
2. Live plants by crop (sampled once/day at hour 20)
3. Market buys: animals (COW/SHEEP), seeds, land
4. Market sells by product
5. Hiring: max hands per day
6. Money trajectory (hour 0)
"""
import json, glob, os, statistics
from collections import defaultdict, Counter

folder = r"C:\Users\rhihi\Downloads\thunder thunder"
replays = sorted(glob.glob(os.path.join(folder, "*.json")))
print(f"replays: {len(replays)}")

# per-day accumulators: list of per-replay values
DAY_ACTIONS = defaultdict(list)      # day -> Counter of ops
DAY_PLANTS = defaultdict(lambda: defaultdict(list))  # day -> crop -> [counts]
DAY_BUYS = defaultdict(lambda: defaultdict(list))    # day -> item -> [counts]
DAY_SELLS = defaultdict(lambda: defaultdict(list))
DAY_HANDS = defaultdict(list)
DAY_MONEY = defaultdict(list)

for path in replays:
    with open(path, encoding="utf-8") as f:
        rp = json.load(f)
    steps = rp["steps"]
    seen_plants = {}   # day -> crop count (sample at hour 20)
    max_hands = {}
    day_acts = defaultdict(Counter)
    day_buys = defaultdict(Counter)
    day_sells = defaultdict(Counter)
    for i, step in enumerate(steps):
        day = i // 24
        hour = i % 24
        # player 0 = thunder (identified in earlier analysis)
        obs = step[0].get("observation") or {}
        acts = step[0].get("action") or {}
        # actions
        for a in [acts.get("farmer")] + list(acts.get("hands") or []):
            if a and a[0] not in ("NORTH", "SOUTH", "EAST", "WEST"):
                day_acts[day][a[0]] += 1
        # hands count
        nh = len(acts.get("hands") or [])
        if day not in max_hands or nh > max_hands[day]:
            max_hands[day] = nh
        # money at hour 0
        farms = obs.get("farms") or []
        if farms and hour == 0:
            f0 = farms[0]
            if f0:
                money = f0.get("money", 0)
                DAY_MONEY[day].append(money)
        # plants sample at hour 20
        if farms and hour == 20:
            f0 = farms[0] if len(farms) > 0 else None
            if f0:
                crops = Counter()
                for row in f0.get("tiles", []):
                    for t in row:
                        if isinstance(t, dict) and t.get("kind") == "PLANT":
                            crops[t.get("crop")] += 1
                seen_plants[day] = crops
        # market orders
        for m in (acts.get("market") or []):
            if m and len(m) >= 3:
                if m[0] == "SELL":
                    day_sells[day][m[1]] += m[2]
                elif m[0] in ("BUY", "BUY_SEED", "BUY_ANIMAL"):
                    item = m[1]
                    key = f"{m[0]}_{item}"
                    day_buys[day][key] += m[2] if isinstance(m[2], (int, float)) else 1
                elif m[0] == "BUY_LAND":
                    day_buys[day]["BUY_LAND"] += 1
                else:
                    day_buys[day][m[0]] += 1
    # aggregate
    for d, c in day_acts.items():
        for k, v in c.items():
            DAY_ACTIONS[d].append((k, v))
    for d, crops in seen_plants.items():
        for c, n in crops.items():
            DAY_PLANTS[d][c].append(n)
    for d, c in day_buys.items():
        for k, v in c.items():
            DAY_BUYS[d][k].append(v)
    for d, c in day_sells.items():
        for k, v in c.items():
            DAY_SELLS[d][k].append(v)
    for d, n in max_hands.items():
        DAY_HANDS[d].append(n)

# ---- output ----
def mean_std(vals):
    if not vals:
        return None
    return statistics.mean(vals), (statistics.stdev(vals) if len(vals) > 1 else 0)

print("\n=== HANDS by day (mean of max) ===")
for d in sorted(DAY_HANDS):
    m = mean_std(DAY_HANDS[d])
    if m:
        print(f"  d{d:2d}: {m[0]:.1f}")

print("\n=== MONEY by day (hour 0, mean) ===")
for d in sorted(DAY_MONEY):
    m = mean_std(DAY_MONEY[d])
    if m:
        print(f"  d{d:2d}: ${m[0]:,.0f}")

print("\n=== ACTION COUNTS by day (mean) ===")
ops_of_interest = ["WATER", "PLANT", "FEED", "CARE", "COLLECT_FERTILIZER",
                   "HARVEST", "FERTILIZE", "PICKUP", "BUILD_PASTURE", "PLACE",
                   "DROP"]
for d in sorted(DAY_ACTIONS):
    agg = defaultdict(list)
    for k, v in DAY_ACTIONS[d]:
        agg[k].append(v)
    parts = []
    for op in ops_of_interest:
        if op in agg:
            m = mean_std(agg[op])
            if m:
                parts.append(f"{op} {m[0]:.0f}")
    if parts:
        print(f"  d{d:2d}: " + " ".join(parts))

print("\n=== LIVE PLANTS by day (mean of hour-20 sample) ===")
for d in sorted(DAY_PLANTS):
    parts = []
    for c in ("STRAWBERRY", "MELON", "WHEAT"):
        if c in DAY_PLANTS[d]:
            m = mean_std(DAY_PLANTS[d][c])
            if m:
                parts.append(f"{c} {m[0]:.0f}")
    if parts:
        print(f"  d{d:2d}: " + " ".join(parts))

print("\n=== BUYS by day (mean) ===")
for d in sorted(DAY_BUYS):
    parts = []
    for k in sorted(DAY_BUYS[d]):
        m = mean_std(DAY_BUYS[d][k])
        if m and m[0] > 0:
            parts.append(f"{k} {m[0]:.1f}")
    if parts:
        print(f"  d{d:2d}: " + " ".join(parts))

print("\n=== SELLS by day (mean) ===")
for d in sorted(DAY_SELLS):
    parts = []
    for k in ("STRAWBERRY", "MILK", "WOOL", "WHEAT", "MELON", "FERTILIZER"):
        if k in DAY_SELLS[d]:
            m = mean_std(DAY_SELLS[d][k])
            if m and m[0] > 0:
                parts.append(f"{k} {m[0]:.1f}")
    if parts:
        print(f"  d{d:2d}: " + " ".join(parts))
