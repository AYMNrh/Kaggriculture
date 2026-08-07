"""STATISTICAL TOURNAMENT HARNESS for Kaggriculture.

Runs the current main.py against opponents across N seeds and reports
full statistics: mean, median, std, percentiles (p10/p50/p90), min/max,
win rate, and per-product sell volume. Also runs limit tests.

Usage: python stat_tournament.py --episodes N --seeds "42,100,500"
"""
import argparse, os, sys, statistics, time
from collections import Counter, defaultdict
from kaggle_environments import make

def run_game(agents, seed):
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run(agents)
    res = env.steps[-1]
    return [(s["reward"], s["status"]) for s in res]

def sells_of(steps, player):
    c = Counter()
    for step in steps:
        acts = step[player].get("action") or {}
        for m in (acts.get("market") or []):
            if m and m[0] == "SELL" and len(m) >= 3:
                c[m[1]] += m[2]
    return c

def stats(vals):
    if not vals:
        return {}
    return {
        "n": len(vals), "mean": statistics.mean(vals),
        "median": statistics.median(vals),
        "std": statistics.stdev(vals) if len(vals) > 1 else 0,
        "p10": sorted(vals)[max(0, len(vals)//10 - 1)],
        "p90": sorted(vals)[min(len(vals)-1, 9*len(vals)//10)],
        "min": min(vals), "max": max(vals),
    }

def fmt(s):
    return (f"n={s['n']} mean=${s['mean']:,.0f} med=${s['median']:,.0f} "
            f"std=${s['std']:,.0f} p10=${s['p10']:,.0f} p90=${s['p90']:,.0f} "
            f"min=${s['min']:,.0f} max=${s['max']:,.0f}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=30)
    ap.add_argument("--seeds", default=None)
    args = ap.parse_args()

    seeds = [int(x) for x in args.seeds.split(",")] if args.seeds else \
            list(range(0, args.episodes * 37, 37))[:args.episodes]

    configs = [
        ("vs pass",    ["main.py", "pass"]),
        ("vs random",  ["main.py", "random"]),
        ("vs starter", ["main.py", "starter"]),
        ("mirror",     ["main.py", "main.py"]),
    ]

    t0 = time.time()
    for label, agents in configs:
        rewards = []
        sells = Counter()
        wins = 0
        for seed in seeds:
            r = run_game(agents, seed)
            rewards.append(r[0][0])
            if r[0][0] > r[1][0]:
                wins += 1
            st = r[0][1]
            if st != "DONE":
                rewards[-1] = 0
        s = stats(rewards)
        print(f"{label:<12} {fmt(s)} | win {wins}/{len(seeds)} | "
              f"{time.time()-t0:.0f}s")
        # sells for first 3 seeds only (cheap)
        if label == "vs pass":
            for seed in seeds[:3]:
                env = make("kaggriculture",
                           configuration={"episodeSteps": 720, "seed": seed},
                           debug=False)
                env.run(agents)
                c = sells_of(env.steps, 0)
                sells += c
            print(f"           sells(first 3): "
                  f"{', '.join(f'{k} {v}' for k, v in sells.most_common(8))}")

if __name__ == "__main__":
    main()
