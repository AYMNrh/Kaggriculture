"""Trace crop hand h8's full day 14 — every action + position."""
import main
from kaggle_environments import make
orig = main.agent
log = open("hand14.txt", "w")

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
        hands = res.get("hands") or []
        # h8 = hand index 8 -> unit idx 9
        h8 = hands[8] if len(hands) > 8 else None
        pos = me["hands"][8] if len(me.get("hands") or []) > 8 else None
        inv = (obs["private"]["inventories"][9] or {}) if len(obs["private"]["inventories"]) > 9 else {}
        log.write(f"d{day}h{hour:2d} h8_pos={pos} inv={ {k:v for k,v in inv.items() if v>0} } action={h8}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
