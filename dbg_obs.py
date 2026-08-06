"""Inspect obs structure keys."""
import main
from kaggle_environments import make

orig = main.agent
log = open("obs_keys.txt", "w")

def wrapped(obs):
    res = orig(obs)
    if obs.get("day") == 0 and obs.get("hour") in (0, 1):
        log.write(f"day0h{obs['hour']} obs keys: {list(obs.keys())}\n")
        if "market" in obs:
            log.write(f"  market type: {type(obs['market'])}, keys: {list(obs['market'].keys()) if isinstance(obs['market'], dict) else obs['market']}\n")
        log.write(f"  action: {res}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
