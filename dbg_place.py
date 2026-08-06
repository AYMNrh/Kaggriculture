"""Trace placement actions day 14-15."""
import sys
import main
from kaggle_environments import make

orig = main.agent
log = open("place_trace.txt", "w")

def wrapped(obs):
    res = orig(obs)
    if obs.get("day") in (14, 15):
        me = obs["farms"][obs["player"]]
        priv = obs["private"]
        acts = [res["farmer"]] + list(res.get("hands") or [])
        nonpass = [a for a in acts if a and a[0] != "PASS"]
        if any(a and a[0] in ("PICKUP", "PLACE", "DROP", "BUILD_PASTURE") for a in nonpass):
            log.write(f"d{obs['day']}h{obs['hour']:2d} shedC={priv['shed'].get('COW',0)} "
                      f"shedS={priv['shed'].get('SHEEP',0)} | {[a for a in nonpass if a and a[0] in ('PICKUP','PLACE','DROP','BUILD_PASTURE')]}\n")
            log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
