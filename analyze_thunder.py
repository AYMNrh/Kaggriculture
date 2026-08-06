"""Analyze THUNDER THUNDER (#1 leaderboard) replays vs my agent.
Replays are from thunder's team submission page - thunder is the SAME
player index in every replay. Determine which index wins most, then use
that consistently.
"""
import json, glob, os
from collections import Counter
import statistics

folder = r"C:\Users\rhihi\Downloads\thunder thunder"
replays = sorted(glob.glob(os.path.join(folder, "*.json")))

# determine which player index thunder is: the one that wins more games
win_count = [0, 0]
for path in replays:
    with open(path, encoding="utf-8") as f:
        rp = json.load(f)
    n = len(rp["steps"][-1])
    res = [(s["reward"], s["status"]) for s in rp["steps"][-1]]
    if res[0][0] > res[1][0]:
        win_count[0] += 1
    elif res[1][0] > res[0][0]:
        win_count[1] += 1
print(f"player 0 wins {win_count[0]}/{len(replays)}, player 1 wins {win_count[1]}/{len(replays)}")
T = 0 if win_count[0] >= win_count[1] else 1
print(f"thunder = player {T}")
print()

sells = [Counter() for _ in range(2)]
finals = [[], []]
for path in replays:
    with open(path, encoding="utf-8") as f:
        rp = json.load(f)
    steps = rp["steps"]
    n = len(steps[-1])
    for i, step in enumerate(steps):
        for p in range(n):
            acts = step[p].get("action") or {}
            for m in (acts.get("market") or []):
                if m and m[0] == "SELL" and len(m) >= 3:
                    sells[p][m[1]] += m[2]
    for p in range(n):
        finals[p].append(steps[-1][p]["reward"])

for p in (T, 1 - T):
    tag = "THUNDER" if p == T else "OPPONENT"
    total = sum(sells[p].values())
    print(f"--- {tag} (player {p}) ---")
    print(f"  total units sold: {total}")
    for item, qty in sells[p].most_common():
        print(f"  {item}: {qty}")
    print(f"  final money: avg ${statistics.mean(finals[p]):,.0f} | min ${min(finals[p]):,.0f} | max ${max(finals[p]):,.0f}")
    print()
