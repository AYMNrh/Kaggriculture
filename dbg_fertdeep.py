"""Deep trace: fertilize job generation + assignment day 14."""
import main
from kaggle_environments import make
orig = main.agent
log = open("fert_deep.txt", "w")

# Wrap add_job via module-level patch
orig_add_job = main.agent.__globals__.get("add_job") if "add_job" in main.agent.__globals__ else None

def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    priv = obs["private"]
    day, hour = obs.get("day"), obs.get("hour")
    if day == 14 and hour == 0:
        n = len(me["tiles"])
        fert_plants = []
        for y in range(n):
            for x in range(n):
                t = me["tiles"][y][x]
                if (isinstance(t, dict) and t.get("kind") == "PLANT"
                        and t.get("fertilized_until_day", -1) < day
                        and t["crop"] in ("STRAWBERRY", "MELON", "WHEAT")):
                    fert_plants.append((x, y, t["crop"]))
        log.write(f"d{day}h{hour} fert_in_shed={priv['shed'].get('FERTILIZER',0)} unfertilized_plants={len(fert_plants)} {fert_plants[:10]}\n")
        acts = [res["farmer"]] + list(res.get("hands") or [])
        log.write(f"all actions: {acts[:8]}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
