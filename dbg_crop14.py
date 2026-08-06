"""Full day 14 crop hand trace."""
import main
from kaggle_environments import make
orig = main.agent
log = open("crop14.txt", "w")

def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    day, hour = obs.get("day"), obs.get("hour")
    if day == 14:
        n_units = 1 + len(me.get("hands") or [])
        plants = sum(1 for row in me["tiles"] for t in row
                     if isinstance(t, dict) and t.get("kind") == "PLANT")
        n = len(me["tiles"])
        plantable_count = sum(1 for y in range(n) for x in range(n) if me["tiles"][y][x] is None)
        crop_workload = plants + max(0, min(plantable_count, 20))
        n_crop = max(1, min(n_units - 2, (crop_workload + 5) // 7))
        animal_count = n_units - n_crop
        acts = [("F", res["farmer"])] + [(f"h{i}", a) for i, a in enumerate(res.get("hands") or [])]
        crop_acts = []
        for name, a in acts:
            is_c = (name == "F" and 0 >= animal_count) or (name.startswith("h") and int(name[1:]) + 1 >= animal_count)
            if is_c and a:
                crop_acts.append(f"{name}:{a}")
        log.write(f"d{day}h{hour:2d} n_crop={n_crop} | " + " ".join(crop_acts) + "\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
