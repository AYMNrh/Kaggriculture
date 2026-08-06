"""Battle-test main.py against the built-in agents (pass/random/starter).

Usage: python battle_test.py [--episodes N] [--fast]
Runs N seeded episodes per matchup, reports avg money + win rate.
"""
import argparse
import random
import sys

from kaggle_environments import make, evaluate


def run_matchup(my_agent, opponent, episodes, fast=False):
    wins = 0
    losses = 0
    ties = 0
    my_money = []
    opp_money = []
    steps = 360 if fast else 720

    for ep in range(episodes):
        seed = random.randint(0, 2**31 - 1)
        env = make(
            "kaggriculture",
            configuration={"episodeSteps": steps, "seed": seed},
            debug=False,
        )
        env.run([my_agent, opponent])
        final = env.steps[-1]
        r0 = final[0].reward
        r1 = final[1].reward
        my_money.append(r0)
        opp_money.append(r1)
        if r0 > r1:
            wins += 1
        elif r0 < r1:
            losses += 1
        else:
            ties += 1

    print(f"vs {opponent:<8} | {episodes} eps | W {wins} L {losses} T {ties} "
          f"| my avg ${sum(my_money)/len(my_money):,.0f} opp avg ${sum(opp_money)/len(opp_money):,.0f} "
          f"| win% {100*wins/episodes:.0f}")
    return wins, losses, ties


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=10)
    ap.add_argument("--fast", action="store_true", help="short 360-step games for quick iteration")
    args = ap.parse_args()

    for opp in ["pass", "random", "starter"]:
        run_matchup("main.py", opp, args.episodes, fast=args.fast)


if __name__ == "__main__":
    main()
