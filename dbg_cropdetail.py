"""Trace strawberry/melon: planted, alive, harvested, sold."""
import main
from kaggle_environments import make

orig = main.agent
log = open("crop_detail.txt", "w")

def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    priv = obs["private"]
    day, hour = obs.get("day"), obs.get("hour")
    if hour == 0 and 6 <= day <= 18:
        crops = {}
        for row in me["tiles"]:
            for t in row:
                if isinstance(t, dict) and t.get("kind") == "PLANT":
                    c = t["crop"]
                    crops[c] = crops.get(c, 0) + 1
        acts = [res["farmer"]] + list(res.get("hands") or [])
        h = sum(1 for a in acts if a and a[0] == "HARVEST")
        log.write(f"d{day:2d} plants={crops} harvest_acts={h} "
                  f"seeds={ {k: v for k, v in priv['seeds'].items() if v > 0} }\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
