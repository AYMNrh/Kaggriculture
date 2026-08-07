"""Paired A/B: baseline (main.py) vs b8 (main_b8.py) on IDENTICAL seeds.
Statistical test: paired differences, sign test, win rate."""
import sys, statistics
from collections import Counter
from kaggle_environments import make
import importlib.util

def load(name):
    spec = importlib.util.spec_from_file_location(name, f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.agent

SEEDS = [int(x) for x in sys.argv[1].split(",")] if len(sys.argv) > 1 else \
        [42, 100, 500, 853, 207, 964, 3600, 2595, 1008, 1157, 551, 569,
         661, 733, 338, 2003, 200, 333, 4, 1, 0, 2, 3, 5, 6, 7, 8, 9, 10,
         11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]

base = load("main")
b8 = load("main_b8")

A, B = [], []
for seed in SEEDS:
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run([base, "pass"])
    A.append(env.steps[-1][0]["reward"])
    env.run([b8, "pass"])
    B.append(env.steps[-1][0]["reward"])

diffs = [b - a for a, b in zip(A, B)]
wins = sum(1 for d in diffs if d > 0)
print(f"seeds: {len(SEEDS)}")
print(f"baseline: mean ${statistics.mean(A):,.0f} med ${statistics.median(A):,.0f}")
print(f"b8:       mean ${statistics.mean(B):,.0f} med ${statistics.median(B):,.0f}")
print(f"paired delta: mean ${statistics.mean(diffs):,.0f} | b8 wins {wins}/{len(SEEDS)}")
# show biggest deltas
order = sorted(zip(SEEDS, A, B), key=lambda t: t[2] - t[1], reverse=True)
print("top-5 b8 gains:", [(s, f"${a:,.0f}->${b:,.0f}", f"+${b-a:,.0f}") for s, a, b in order[:5]])
print("top-5 b8 losses:", [(s, f"${a:,.0f}->${b:,.0f}", f"{b-a:,.0f}") for s, a, b in order[-5:]])
