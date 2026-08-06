"""Deep-dive 3: exact crop mix + live plants per day + watering per crop."""
import json
from collections import defaultdict

path = r"C:\Users\rhihi\Downloads\thunder thunder\90514256.json"
with open(path, encoding="utf-8") as f:
    rp = json.load(f)
steps = rp["steps"]

pidx = 0
# sample hour 20 each day (stable end-of-day view)
for day in range(0, 30, 2):
    i = day * 24 + 20
    st = steps[i][pidx]
    obs = st.get("observation") or {}
    farms = obs.get("farms") or []
    if not farms:
        continue
    farm = farms[pidx] if pidx < len(farms) else farms[0]
    tiles = farm.get("tiles") or []
    crops = defaultdict(int)
    ages = defaultdict(list)
    for row in tiles:
        for t in row:
            if isinstance(t, dict) and t.get("kind") == "PLANT":
                c = t.get("crop")
                crops[c] += 1
                ages[c].append(t.get("age", 0))
    if crops:
        parts = []
        for c in sorted(crops):
            avg_age = sum(ages[c]) / len(ages[c]) if ages[c] else 0
            parts.append(f"{c} {crops[c]} (age~{avg_age:.0f})")
        print(f"d{day:2d}: " + " | ".join(parts))
