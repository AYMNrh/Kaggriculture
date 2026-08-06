"""Trace plant count, water/plant actions, plant deaths day 4-16."""
import main
from kaggle_environments import make

orig = main.agent
log = open("crop_trace.txt", "w")

def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    day, hour = obs.get("day"), obs.get("hour")
    if hour == 0 and 4 <= day <= 16:
        plants = 0
        unwatered = 0
        for row in me["tiles"]:
            for t in row:
                if isinstance(t, dict) and t.get("kind") == "PLANT":
                    plants += 1
                    if not t.get("watered_today"):
                        unwatered += 1
        acts = [res["farmer"]] + list(res.get("hands") or [])
        waters = sum(1 for a in acts if a and a[0] == "WATER")
        plants_ = sum(1 for a in acts if a and a[0] == "PLANT")
        log.write(f"d{day:2d} plants={plants} unwatered={unwatered} water_acts={waters} plant_acts={plants_} "
                  f"| n_hands={len(res.get('hands') or [])}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
