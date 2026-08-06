"""Count plants that become weeds: track plant tiles day by day."""
import main
from kaggle_environments import make
orig = main.agent
log = open("weed_trace.txt", "w")

prev_plants = {}  # (x,y) -> crop

def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    day = obs.get("day")
    if day is not None and 0 <= day <= 20:
        cur = {}
        for y, row in enumerate(me["tiles"]):
            for x, t in enumerate(row):
                if isinstance(t, dict) and t.get("kind") == "PLANT":
                    cur[(x, y)] = t.get("crop", "?")
        # plants that vanished -> died (harvested or weed)
        died = [k for k in prev_plants if k not in cur]
        # check for weed tiles replacing them
        weeds = []
        for y, row in enumerate(me["tiles"]):
            for x, t in enumerate(row):
                if isinstance(t, dict) and t.get("kind") == "WEED":
                    weeds.append((x, y))
        if died or (day % 2 == 0):
            log.write(f"d{day} plants={len(cur)} died={died[:6]} weeds={len(weeds)}\n")
            log.flush()
        prev_plants.clear()
        prev_plants.update(cur)
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
