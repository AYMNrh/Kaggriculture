"""Trace plant actions by crop days 0-9."""
import main
from kaggle_environments import make
from collections import Counter
orig = main.agent
log = open("early_crops.txt", "w")

def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    day, hour = obs.get("day"), obs.get("hour")
    if hour == 12 and day <= 9:
        plants = Counter()
        for row in me["tiles"]:
            for t in row:
                if isinstance(t, dict) and t.get("kind") == "PLANT":
                    plants[t["crop"]] += 1
        log.write(f"d{day} plants={dict(plants)}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
