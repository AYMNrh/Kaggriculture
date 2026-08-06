"""Every hour of day 12: plant/water actions + plant count."""
import main
from kaggle_environments import make
orig = main.agent
log = open("hour12.txt", "w")

def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    day, hour = obs.get("day"), obs.get("hour")
    if day == 13:
        acts = [res["farmer"]] + list(res.get("hands") or [])
        cnt = {}
        for a in acts:
            if a and a[0] not in ("PASS", "NORTH", "SOUTH", "EAST", "WEST"):
                cnt[a[0]] = cnt.get(a[0], 0) + 1
        plants = 0
        for row in me["tiles"]:
            for t in row:
                if isinstance(t, dict) and t.get("kind") == "PLANT":
                    plants += 1
        log.write(f"d{day}h{hour:2d} plants={plants} acts={cnt}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
