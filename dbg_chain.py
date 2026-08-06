"""Trace one hand's actions across hours to see job chaining."""
import main
from kaggle_environments import make
orig = main.agent
log = open("chain_trace.txt", "w")

def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    day, hour = obs.get("day"), obs.get("hour")
    if day == 12 and hour >= 6:
        # log all hands' actions this hour
        acts = [res["farmer"]] + list(res.get("hands") or [])
        for i, a in enumerate(acts):
            if a and a[0] not in ("PASS",):
                log.write(f"d{day}h{hour} u{i}: {a[0]}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
