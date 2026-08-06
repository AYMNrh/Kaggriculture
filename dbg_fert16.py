"""Deep trace fertilize chain day 16."""
import main
from kaggle_environments import make
orig = main.agent
log = open("fert16.txt", "w")

def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    priv = obs["private"]
    day, hour = obs.get("day"), obs.get("hour")
    if day == 16 and hour in (0, 1, 2, 4):
        n_units = 1 + len(me.get("hands") or [])
        fert_shed = priv["shed"].get("FERTILIZER", 0)
        fert_invs = [ (obs["private"]["inventories"][i] or {}).get("FERTILIZER", 0) for i in range(n_units) ]
        acts = [res["farmer"]] + list(res.get("hands") or [])
        log.write(f"d{day}h{hour} units={n_units} fert_shed={fert_shed} fert_invs={fert_invs}\n")
        log.write(f"  acts: {[a for a in acts if a and a[0] not in ('PASS','NORTH','SOUTH','EAST','WEST')][:8]}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
