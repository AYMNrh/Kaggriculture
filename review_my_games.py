"""Aggressive review v2: identify MY agent by sell fingerprint, compute
W/L + margins, and compare vs the opponents who beat me."""
import json, glob, os
from collections import Counter
import statistics

folder = r"C:\Users\rhihi\Downloads\AYMENRH"
replays = sorted(glob.glob(os.path.join(folder, "*.json")))

# MY fingerprint (pre-B+C config, seed-42): FERT 240-260, WHEAT ~220,
# MILK ~200-210, WOOL ~130-145, STRA ~60-90, MELON ~90
def is_me(sells):
    f = sells.get("FERTILIZER", 0)
    st = sells.get("STRAWBERRY", 0)
    return 150 <= f <= 300 and 30 <= st <= 150

results = []
for path in replays:
    with open(path, encoding="utf-8") as f:
        rp = json.load(f)
    steps = rp["steps"]
    n = len(steps[-1])
    res = [(s["reward"], s["status"]) for s in steps[-1]]
    sells = [Counter() for _ in range(n)]
    for i, step in enumerate(steps):
        for p in range(n):
            acts = step[p].get("action") or {}
            for m in (acts.get("market") or []):
                if m and m[0] == "SELL" and len(m) >= 3:
                    sells[p][m[1]] += m[2]
    me_idx = None
    for p in range(n):
        if is_me(sells[p]):
            me_idx = p
            break
    if me_idx is None:
        me_idx = 0  # fallback
    opp = 1 - me_idx
    w = res[me_idx][0] > res[opp][0]
    results.append({
        "name": os.path.basename(path), "me": res[me_idx][0], "opp": res[opp][0],
        "win": w, "me_sells": dict(sells[me_idx]), "opp_sells": dict(sells[opp]),
    })

wins = [r for r in results if r["win"]]
losses = [r for r in results if not r["win"]]
print(f"RECORD: {len(wins)}W {len(losses)}L / {len(results)}")
print(f"my avg final: ${statistics.mean(r['me'] for r in results):,.0f}")
print(f"  wins avg ${statistics.mean(r['me'] for r in wins):,.0f} | losses avg ${statistics.mean(r['me'] for r in losses):,.0f}")
print(f"opp avg final: ${statistics.mean(r['opp'] for r in results):,.0f}")
print()
print("=== LOSSES (aggressive review focus) ===")
for r in sorted(losses, key=lambda r: r["opp"] - r["me"], reverse=True):
    ms = r["me_sells"]; os_ = r["opp_sells"]
    print(f"{r['name']}: me ${r['me']:,.0f} vs opp ${r['opp']:,.0f}")
    print(f"  me  : " + ", ".join(f"{k} {v}" for k, v in sorted(ms.items(), key=lambda x: -x[1])[:6]))
    print(f"  opp : " + ", ".join(f"{k} {v}" for k, v in sorted(os_.items(), key=lambda x: -x[1])[:6]))
print()
print("=== WINS (margins) ===")
for r in sorted(wins, key=lambda r: r["me"] - r["opp"]):
    print(f"{r['name']}: me ${r['me']:,.0f} vs opp ${r['opp']:,.0f} (Δ{'+' if r['me']>r['opp'] else ''}{r['me']-r['opp']:,.0f})")
