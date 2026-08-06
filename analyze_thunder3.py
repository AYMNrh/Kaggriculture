"""Deep-dive 2: how do the 61-plant agents water so little?
Check per-day WATER counts + live plants + crop mix on one replay."""
import json, os
from collections import Counter, defaultdict

path = r"C:\Users\rhihi\Downloads\thunder thunder\90514256.json"
with open(path, encoding="utf-8") as f:
    rp = json.load(f)
steps = rp["steps"]

for pidx in (0, 1):
    print(f"===== player {pidx} =====")
    daily = defaultdict(lambda: defaultdict(int))
    crops = Counter()
    last_plant = {}
    for i, step in enumerate(steps):
        day = i // 24
        st = step[pidx]
        obs = st.get("observation") or {}
        acts = st.get("action") or {}
        farms = obs.get("farms") or []
        if farms:
            farm = farms[pidx] if pidx < len(farms) else farms[0]
            tiles = farm.get("tiles") or []
            for row in tiles:
                for t in row:
                    if isinstance(t, dict) and t.get("kind") == "PLANT":
                        crops[t.get("crop")] += 1  # cumulative (sampled every hour) - for mix only
        for a in [acts.get("farmer")] + list(acts.get("hands") or []):
            if a and a[0] in ("WATER", "PLANT", "FERTILIZE", "HARVEST"):
                daily[day][a[0]] += 1
            if a and a[0] == "PLANT" and len(a) >= 2:
                last_plant[a[1]] = max(last_plant.get(a[1], -1), day)
    print("  daily WATER/PLANT/FERTILIZE/HARVEST:")
    for d in sorted(daily):
        c = daily[d]
        if any(c.values()):
            print(f"    d{d:2d}: W {c['WATER']:3d} P {c['PLANT']:3d} F {c['FERTILIZE']:3d} H {c['HARVEST']:3d}")
    print(f"  last plant day: {last_plant}")
    print()
