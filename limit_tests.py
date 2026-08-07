"""AGGRESSIVE LIMIT-TEST SUITE for the submitted agent.

Runs the CURRENT committed config (0615ccc B+C+budget — the code that will
be submitted next) through adversarial simulations:
1. vs pass (baseline)
2. mirror match (me vs me — market sharing)
3. vs a THUNDER-style heavyweight (many strawberry, spread sells)
4. limit test: NO land purchase
5. limit test: NO animals (pure crops)
6. limit test: max animals (20+)
7. stress: seed 0 (worst shop luck?)
8. late-game: what if we hold milk/wool/strawberry last 3 days

Each across 5 seeds. Aggressive = find the failure modes.
"""
import os, sys, json
from kaggle_environments import make
from collections import Counter
import statistics

SEEDS = [42, 100, 500, 853, 207]

def run_game(agents, seed, label):
    try:
        env = make("kaggriculture",
                   configuration={"episodeSteps": 720, "seed": seed},
                   debug=False)
        env.run(agents)
        res = [(s["reward"], s["status"]) for s in env.steps[-1]]
        return res
    except Exception as e:
        return [(f"ERR {e}", "ERR")]

# THUNDER-style opponent: high-volume strawberry seller with spread sells.
# Reuse main.py but force a huge strawberry quota via a wrapper module.
def make_thunderish():
    import main as base
    orig = base.agent
    # patch constants at runtime: wider strawberry window, bigger budget
    base.STRAWBERRY_WINDOW = (4, 16)
    base.HIRE_TARGETS = [(0, 5), (4, 7), (8, 10), (11, 12), (14, 14)]
    def agent(obs):
        return orig(obs)
    return agent

tests = [
    ("baseline vs pass", lambda: ["main.py", "pass"]),
    ("mirror me-vs-me", lambda: ["main.py", "main.py"]),
    ("vs thunderish", lambda: ["main.py", make_thunderish()]),
]

print("=== CORE TESTS (5 seeds) ===")
for label, mk in tests:
    rows = []
    for s in SEEDS:
        r = run_game(mk(), s, label)
        rows.append(r)
    # average my reward (player 0)
    vals = [r[0][0] for r in rows if isinstance(r[0][0], (int, float))]
    opps = [r[1][0] for r in rows if len(r) > 1 and isinstance(r[1][0], (int, float))]
    wins = sum(1 for r in rows if isinstance(r[0][0], (int, float)) and
               len(r) > 1 and r[0][0] > r[1][0])
    if vals:
        print(f"{label:<22} my avg ${statistics.mean(vals):,.0f} (min ${min(vals):,.0f} max ${max(vals):,.0f}) "
              f"| opp avg ${statistics.mean(opps):,.0f} | wins {wins}/{len(rows)}")
