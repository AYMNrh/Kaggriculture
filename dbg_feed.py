"""Trace feed loop on day 3: unfed animals, feed actions, wheat flow."""
import sys
import main
from kaggle_environments import make

orig = main.agent
log = open("feed_trace.txt", "w")

def wrapped(obs):
    res = orig(obs)
    if obs.get("day") in (3, 4):
        me = obs["farms"][obs["player"]]
        priv = obs["private"]
        unfed = 0
        animals = 0
        for row in me["tiles"]:
            for t in row:
                if isinstance(t, dict) and t.get("kind") == "PASTURE" and "animal" in t:
                    animals += 1
                    if not t.get("fed_today"):
                        unfed += 1
        acts = [res["farmer"]] + list(res.get("hands") or [])
        feeds = sum(1 for a in acts if a and a[0] == "FEED")
        pickups = sum(1 for a in acts if a and a[0] == "PICKUP" and len(a) > 1 and a[1] == "WHEAT")
        inv_wheat = [sum((priv["inventories"][i] or {}).get("WHEAT", 0) for i in range(len(priv["inventories"])))]
        log.write(f"d{obs.get('day')}h{obs.get('hour'):2d} | animals {animals} unfed {unfed} "
                  f"| feed_acts {feeds} pickup_wheat {pickups} "
                  f"| shed_wheat {priv['shed'].get('WHEAT', 0)} inv_wheat {inv_wheat[0]} "
                  f"| market {res['market'][:3]}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
