"""Trace build + place + fetch day 11-12."""
import main
from kaggle_environments import make

orig = main.agent
log = open("build_trace.txt", "w")

def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    priv = obs["private"]
    day, hour = obs.get("day"), obs.get("hour")
    if day in (11, 12) and hour in (0, 4, 8, 12):
        acts = [res["farmer"]] + list(res.get("hands") or [])
        nonpass = [a for a in acts if a and a[0] not in ("PASS", "NORTH", "SOUTH", "EAST", "WEST")]
        log.write(f"d{day}h{hour:2d} shedC={priv['shed'].get('COW',0)} shedS={priv['shed'].get('SHEEP',0)} "
                  f"n_hands={len(res.get('hands') or [])} | {nonpass[:12]}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
