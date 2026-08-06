"""Verify role split at day 12."""
import main
from kaggle_environments import make
orig = main.agent
log = open("role_trace.txt", "w")

def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    day, hour = obs.get("day"), obs.get("hour")
    if day == 12 and hour == 8:
        # recompute n_crop_hands like the agent does
        plants = 0
        for row in me["tiles"]:
            for t in row:
                if isinstance(t, dict) and t.get("kind") == "PLANT":
                    plants += 1
        n_units = 1 + len(me.get("hands") or [])
        n_crop = max(1, min(n_units - 2, (plants + 10) // 6))
        animal_count = n_units - n_crop
        log.write(f"day12h8 units={n_units} plants={plants} n_crop={n_crop} animal_units={animal_count}\n")
        log.write(f"hands_in_obs={len(me.get('hands') or [])}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
