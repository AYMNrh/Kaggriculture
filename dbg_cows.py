"""Track cow buy events + alive count + unfed streaks over time."""
import sys
import main
from kaggle_environments import make

orig = main.agent
log = open("cow_trace.txt", "w")

def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    priv = obs["private"]
    day, hour = obs.get("day"), obs.get("hour")
    # log at each day boundary hour 0
    if hour == 0 and day % 2 == 0:
        cows = sheep = 0
        for row in me["tiles"]:
            for t in row:
                if isinstance(t, dict) and t.get("kind") == "PASTURE" and "animal" in t:
                    if t["animal"] == "COW":
                        cows += 1
                    else:
                        sheep += 1
        buys = [m for m in (res.get("market") or []) if m and m[0] == "BUY_ANIMAL"]
        log.write(f"d{day:2d} | cows {cows} sheep {sheep} | shed C {priv['shed'].get('COW',0)} S {priv['shed'].get('SHEEP',0)} "
                  f"| money {me['money']:7.0f} | buys {buys} | market {res.get('market')[:4]}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
