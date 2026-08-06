"""Local multi-agent tournament for Kaggriculture.

The real competition runs 2+ active agents in ONE game sharing a market
(prices move with aggregate supply). My agent has only ever been tested
1-vs-1 vs pass/random/starter — opponents that barely sell. This harness
runs several game configurations to see how the SHARED MARKET affects my
final money and win rate:

  A. [me, pass]              baseline (what I've been testing)
  B. [me, me, pass]          2 copies of my agent + pass (market shared)
  C. [me, me, me, pass]      3 copies + pass (crowded market)
  D. [me, starter, random]   vs the built-in agents together
  E. [me, me, starter]       vs a semi-active opponent

Multiple seeds per config to average out town-shop luck. Reports per
player: avg final money, win count, and (for the market effect) the final
wheat/strawberry/milk prices.
"""
import sys, os, time
from collections import Counter

sys.path.insert(0, r"C:\Users\rhihi\projects\kaggriculture")
os.chdir(r"C:\Users\rhihi\projects\kaggriculture")

from kaggle_environments import make

SEEDS = [42, 100, 500, 853, 964, 1008, 1157, 2595]
# The env is strictly 2-PLAYER (3+ agents raises InvalidArgument) — the
# competition rules confirm: "two players compete on separate farms".
CONFIGS = [
    ("A  me+pass",          ["main.py", "pass"]),
    ("B  me+me  (mirror)",  ["main.py", "main.py"]),
    ("D  me+starter",       ["main.py", "starter"]),
    ("E  me+random",        ["main.py", "random"]),
]


def run_game(agents, seed):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run(agents)
    last = env.steps[-1]
    rewards = [s.reward for s in last]
    statuses = [s.status for s in last]
    # final market prices from any player's observation
    prices = {}
    try:
        obs = last[0]["observation"]
        prices = dict(obs["market"]["prices"])
    except Exception:
        pass
    return rewards, statuses, prices


def main():
    print(f"Tournament: {len(SEEDS)} seeds x {len(CONFIGS)} configs")
    print("=" * 78)
    for name, agents in CONFIGS:
        print(f"\n### {name}  [{', '.join(agents)}]")
        print(f"{'seed':>6} | " + " | ".join(f"{a[:10]:>12}" for a in agents)
              + " | prices(W/S/M)")
        all_rewards = []
        wins = Counter()
        for seed in SEEDS:
            rewards, statuses, prices = run_game(agents, seed)
            all_rewards.append(rewards)
            w = max(rewards)
            for i, r in enumerate(rewards):
                if r == w:
                    wins[i] += 1
            ps = f"{prices.get('WHEAT', 0):.0f}/{prices.get('STRAWBERRY', 0):.0f}/{prices.get('MILK', 0):.0f}"
            print(f"{seed:>6} | " + " | ".join(f"${r:>10,.0f}" for r in rewards)
                  + f" | {ps}")
        # averages
        n = len(SEEDS)
        avgs = [sum(r[i] for r in all_rewards) / n for i in range(len(agents))]
        print("-" * 78)
        print(f"{'AVG':>6} | " + " | ".join(f"${a:>10,.0f}" for a in avgs))
        winstr = " | ".join(f"{wins[i]}/{n}" for i in range(len(agents)))
        print(f"{'WINS':>6} | {winstr}")
        # market effect: my avg in this config vs config A baseline
    print("\n" + "=" * 78)
    print("Market-effect summary (my avg final money):")
    baseline = None
    for name, agents in CONFIGS:
        totals = [0.0] * len(agents)
        n = len(SEEDS)
        for seed in SEEDS:
            rewards, _, _ = run_game(agents, seed)
            for i, r in enumerate(rewards):
                totals[i] += r
        my_idx = 0  # main.py is always player 0
        my_avg = totals[my_idx] / n
        if name.startswith("A"):
            baseline = my_avg
        if baseline:
            delta = (my_avg - baseline) / baseline * 100
            print(f"  {name:16s} my_avg=${my_avg:>10,.0f}  ({delta:+.1f}% vs baseline)")


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"\nTotal time: {time.time() - t0:.0f}s")
