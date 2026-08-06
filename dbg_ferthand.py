"""Trace the hand carrying fertilizer day 16 h2-h10."""
import main
from kaggle_environments import make
orig = main.agent
log = open("ferthand.txt", "w")

def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    day, hour = obs.get("day"), obs.get("hour")
    if day == 16 and 2 <= hour <= 10:
        n_units = 1 + len(me.get("hands") or [])
        acts = [res["farmer"]] + list(res.get("hands") or [])
        for i in range(n_units):
            inv = obs["private"]["inventories"][i] or {}
            if inv.get("FERTILIZER", 0) > 0:
                log.write(f"d{day}h{hour} unit{i} inv={ {k:v for k,v in inv.items() if v>0} } act={acts[i]}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
