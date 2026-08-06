"""Count jobs dict at day 14 h12."""
import main
from kaggle_environments import make
orig = main.agent
log = open("jobs14.txt", "w")

def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    day, hour = obs.get("day"), obs.get("hour")
    if day == 14 and hour == 12:
        n_units = 1 + len(me.get("hands") or [])
        plants = sum(1 for row in me["tiles"] for t in row
                     if isinstance(t, dict) and t.get("kind") == "PLANT")
        n = len(me["tiles"])
        plantable_count = sum(1 for y in range(n) for x in range(n) if me["tiles"][y][x] is None)
        crop_workload = plants + max(0, min(plantable_count, 20))
        n_crop = max(1, min(n_units - 2, (crop_workload + 5) // 7))
        animal_count = n_units - n_crop
        log.write(f"d{day} units={n_units} plants={plants} plantable={plantable_count} n_crop={n_crop} animal_units={animal_count}\n")
        # Count what the agent's hands returned
        acts = [res["farmer"]] + list(res.get("hands") or [])
        from collections import Counter
        cnt = Counter()
        for a in acts:
            if a:
                cnt[a[0]] += 1
        log.write(f"returned actions: {dict(cnt)}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
