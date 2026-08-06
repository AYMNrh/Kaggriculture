"""Trace all unit actions day 0-1."""
import sys
import main
from kaggle_environments import make

orig = main.agent
log = open("actions_trace.txt", "w")

def wrapped(obs):
    res = orig(obs)
    if obs.get("day") <= 1:
        me = obs["farms"][obs["player"]]
        acts = [res["farmer"]] + list(res.get("hands") or [])
        log.write(f"d{obs.get('day')}h{obs.get('hour'):2d} money={me['money']:.0f} "
                  f"| farmer {res['farmer']} | hands {res.get('hands')}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
