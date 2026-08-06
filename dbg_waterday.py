"""Count water/plant actions per day across all hours."""
import main
from kaggle_environments import make

orig = main.agent
log = open("water_day.txt", "w")

counts = {}

def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    day = obs.get("day")
    acts = [res["farmer"]] + list(res.get("hands") or [])
    waters = sum(1 for a in acts if a and a[0] == "WATER")
    plants = sum(1 for a in acts if a and a[0] == "PLANT")
    c = counts.setdefault(day, [0, 0, 0])  # [water, plant, hands]
    c[0] += waters
    c[1] += plants
    if len(res.get("hands") or []) > c[2]:
        c[2] = len(res.get("hands") or [])
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
for d in sorted(counts):
    w, p, h = counts[d]
    log.write(f"day {d:2d}: water_acts_total={w:3d} plant_acts_total={p:3d} max_hands={h:2d}\n")
log.close()
print("done")
