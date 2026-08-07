"""Paired A/B: two agent files on IDENTICAL seeds.
Usage: python ab_test.py <fileA.py> <fileB.py> [seeds...]
Default: main.py (baseline) vs pass — or compare any two variants.
Statistical test: paired differences, sign test, win rate."""
import sys, statistics
from kaggle_environments import make
import importlib.util

def load(path):
    spec = importlib.util.spec_from_file_location(
        os.path.splitext(os.path.basename(path))[0], path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.agent

import os
if len(sys.argv) >= 3 and sys.argv[1].endswith(".py") and sys.argv[2].endswith(".py"):
    A_FILE, B_FILE = sys.argv[1], sys.argv[2]
    seed_arg = sys.argv[3] if len(sys.argv) > 3 else None
else:
    A_FILE, B_FILE = "main.py", "main.py"
    seed_arg = sys.argv[1] if len(sys.argv) > 1 else None

SEEDS = [int(x) for x in seed_arg.split(",")] if seed_arg else \
        [42, 100, 500, 853, 207, 964, 3600, 2595, 1008, 1157, 551, 569,
         661, 733, 338, 2003, 200, 333, 4, 1, 0, 2, 3, 5, 6, 7, 8, 9, 10,
         11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]

base = load(A_FILE)
b8 = load(B_FILE)

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
print(f"{os.path.basename(A_FILE)}: mean ${statistics.mean(A):,.0f} med ${statistics.median(A):,.0f}")
print(f"{os.path.basename(B_FILE)}: mean ${statistics.mean(B):,.0f} med ${statistics.median(B):,.0f}")
print(f"paired delta: mean ${statistics.mean(diffs):,.0f} | B wins {wins}/{len(SEEDS)}")
# show biggest deltas
order = sorted(zip(SEEDS, A, B), key=lambda t: t[2] - t[1], reverse=True)
print("top-5 B gains:", [(s, f"${a:,.0f}->${b:,.0f}", f"+${b-a:,.0f}") for s, a, b in order[:5]])
print("top-5 B losses:", [(s, f"${a:,.0f}->${b:,.0f}", f"{b-a:,.0f}") for s, a, b in order[-5:]])
