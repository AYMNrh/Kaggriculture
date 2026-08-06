"""Trace every hand action day 12 h8-h11 — find the idle."""
import main
from kaggle_environments import make
orig = main.agent
log = open("idle_trace.txt", "w")

def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    day, hour = obs.get("day"), obs.get("hour")
    if day == 12 and 8 <= hour <= 11:
        acts = [("F", res["farmer"])] + [(f"h{i}", a) for i, a in enumerate(res.get("hands") or [])]
        log.write(f"d{day}h{hour} | " + " ".join(f"{n}:{a}" for n, a in acts) + "\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
