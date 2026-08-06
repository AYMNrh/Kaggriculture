"""Trace hire logic day 20."""
import main
from kaggle_environments import make
orig = main.agent
log = open("hire_dbg.txt", "w")
def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    day, hour = obs.get("day"), obs.get("hour")
    if day == 20 and hour < 6:
        hires = [m for m in (res.get("market") or []) if m and m[0] == "HIRE"]
        log.write(f"d{day}h{hour} hands={len(me.get('hands') or [])} money={me['money']:.0f} "
                  f"| hires_this_turn={len(hires)} | market={res.get('market')}\n")
        log.flush()
    return res
env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
