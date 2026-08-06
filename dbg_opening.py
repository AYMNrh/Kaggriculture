"""Trace day 0-2: opening, placements, animal survival."""
import main
from kaggle_environments import make
orig = main.agent
log = open("opening_trace.txt", "w")

def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    priv = obs["private"]
    day, hour = obs.get("day"), obs.get("hour")
    if day <= 2:
        if hour in (0, 4, 8, 12, 20):
            acts = [res["farmer"]] + list(res.get("hands") or [])
            nonpass = [a for a in acts if a and a[0] not in ("PASS", "NORTH", "SOUTH", "EAST", "WEST")]
            cows = sum(1 for row in me["tiles"] for t in row
                       if isinstance(t, dict) and t.get("animal") == "COW")
            sheep = sum(1 for row in me["tiles"] for t in row
                        if isinstance(t, dict) and t.get("animal") == "SHEEP")
            log.write(f"d{day}h{hour:2d} money={me['money']:.0f} cows={cows} sheep={sheep} "
                      f"| market={res.get('market')} | acts={nonpass[:6]}\n")
            log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
