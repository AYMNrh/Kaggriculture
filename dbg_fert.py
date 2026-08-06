"""Trace fertilizer: produced on tiles vs collected vs sold."""
import main
from kaggle_environments import make

orig = main.agent
log = open("fert_trace.txt", "w")

def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    priv = obs["private"]
    day, hour = obs.get("day"), obs.get("hour")
    if hour == 0 and day % 2 == 0:
        fert_on_tiles = 0
        for row in me["tiles"]:
            for t in row:
                if isinstance(t, dict) and t.get("kind") == "PASTURE":
                    fert_on_tiles += t.get("fertilizer_ready", 0) or t.get("fertilizer", 0) or 0
        acts = [res["farmer"]] + list(res.get("hands") or [])
        collects = sum(1 for a in acts if a and a[0] == "COLLECT_FERTILIZER")
        log.write(f"d{day:2d} money={me['money']:6.0f} fert_on_tiles={fert_on_tiles} "
                  f"shedF={priv['shed'].get('FERTILIZER',0)} collect_acts={collects} "
                  f"| actions={[a for a in acts if a and a[0] not in ('PASS','NORTH','SOUTH','EAST','WEST')][:8]}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
