"""Trace day 4-5: market orders + actions."""
import main
from kaggle_environments import make
orig = main.agent
log = open("day45.txt", "w")

def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    day, hour = obs.get("day"), obs.get("hour")
    if day in (4, 5) and hour in (0, 6, 12):
        acts = [res["farmer"]] + list(res.get("hands") or [])
        nonpass = [a for a in acts if a and a[0] not in ("PASS", "NORTH", "SOUTH", "EAST", "WEST")]
        log.write(f"d{day}h{hour} money={me['money']:.0f} n_hands={len(res.get('hands') or [])} "
                  f"| market={res.get('market')} | acts={nonpass[:6]}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
