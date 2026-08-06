"""Trace money + sells + shed day 8-13."""
import sys
import main
from kaggle_environments import make

orig = main.agent
log = open("flow_trace.txt", "w")

def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    priv = obs["private"]
    if 8 <= obs.get("day") <= 13 and obs.get("hour") == 0:
        log.write(f"d{obs['day']:2d} money={me['money']:7.0f} "
                  f"shed={ {k: v for k, v in priv['shed'].items() if v > 0} }\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
