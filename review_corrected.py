"""Correct real-game analysis: my agent = the one capping at ~20-25 plants
(max_plants < 40). Winners = 50+ plants. This is unambiguous."""
import json, glob, os
from collections import Counter

folder = r"C:\Users\rhihi\Downloads\AYMENRH"
results = []
for path in sorted(glob.glob(os.path.join(folder, "*.json"))):
    with open(path, encoding="utf-8") as f:
        rp = json.load(f)
    steps = rp["steps"]
    n = len(steps[-1])
    rewards = [s["reward"] for s in steps[-1]]
    maxp = [0, 0]
    for i, step in enumerate(steps):
        for p in range(n):
            obs = step[p].get("observation") or {}
            farms = obs.get("farms") or []
            if farms:
                f0 = farms[p] if p < len(farms) else farms[0]
                cnt = sum(1 for row in f0.get("tiles", []) for t in row
                          if isinstance(t, dict) and t.get("kind") == "PLANT")
                maxp[p] = max(maxp[p], cnt)
    # my agent caps ~20-25 plants; identify by LOW max_plants
    me = 0 if maxp[0] <= maxp[1] else 1
    opp = 1 - me
    w = rewards[me] > rewards[opp]
    results.append((os.path.basename(path), rewards[me], rewards[opp],
                    maxp[me], maxp[opp], w))

wins = sum(1 for r in results if r[5])
print(f"games: {len(results)} | CORRECTED record: {wins}W {len(results)-wins}L")
print(f"{'game':<14} {'me$':>8} {'opp$':>8} {'myP':>4} {'oppP':>4} {'W/L'}")
for name, me, opp, mp, op, w in results:
    print(f"{name:<14} {me:>8,.0f} {opp:>8,.0f} {mp:>4} {op:>4} {'W' if w else 'L'}")
import statistics
mine = [r[1] for r in results]
print(f"\nmy avg: ${statistics.mean(mine):,.0f} | my median: ${statistics.median(mine):,.0f}")
print(f"my avg max_plants: {statistics.mean(r[3] for r in results):.0f}")
print(f"opp avg max_plants: {statistics.mean(r[4] for r in results):.0f}")
