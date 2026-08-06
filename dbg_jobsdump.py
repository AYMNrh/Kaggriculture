"""Dump the jobs dict at day 12 h8 by monkeypatching job generation."""
import main
import kaggle_environments.envs.kaggriculture.kaggriculture as kenv
from kaggle_environments import make

# Patch main's agent to capture the jobs dict: we can't easily, so trace
# the add_job calls via a wrapper on the module-level function.
orig_agent = main.agent
log = open("jobs_dump.txt", "w")

import types

def wrapped(obs):
    res = orig_agent(obs)
    me = obs["farms"][obs["player"]]
    priv = obs["private"]
    day, hour = obs.get("day"), obs.get("hour")
    if day == 12 and hour == 8:
        # Recompute what jobs WOULD be generated: replicate plant loop
        board = me["tiles"]
        n = len(board)
        seeds = priv["seeds"]
        plantable = [(x, y) for y in range(n) for x in range(n)
                     if board[y][x] is None and day + 4 <= 30 - 1]
        log.write(f"day12h8 plantable tiles: {len(plantable)}\n")
        log.write(f"seeds: { {k: v for k, v in seeds.items() if v > 0} }\n")
        # Check planted_today state
        log.write(f"planted_today: {main._STATE.get('planted_today')}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
