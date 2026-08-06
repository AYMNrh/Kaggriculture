"""Trace shed contents + sell orders day 3-5."""
import main
from kaggle_environments import make
orig = main.agent
log = open("shed35.txt", "w")

def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    priv = obs["private"]
    day, hour = obs.get("day"), obs.get("hour")
    if day in (3, 4, 5) and hour == 0:
        shed = {k: v for k, v in priv["shed"].items() if v > 0}
        sells = [m for m in (res.get("market") or []) if m and m[0] == "SELL"]
        log.write(f"d{day} money={me['money']:.0f} shed={shed} sells={sells}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
