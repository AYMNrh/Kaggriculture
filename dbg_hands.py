"""Trace hands count + hire orders across a full day."""
import main
from kaggle_environments import make

orig = main.agent
log = open("hands_trace.txt", "w")

def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    day, hour = obs.get("day"), obs.get("hour")
    if day == 10:
        hires = sum(1 for m in (res.get("market") or []) if m and m[0] == "HIRE")
        log.write(f"d{day}h{hour:2d} hands={len(me.get('hands') or [])} hires_this_turn={hires} "
                  f"| market={res.get('market')}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
