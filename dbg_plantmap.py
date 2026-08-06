"""Map plant locations day 14."""
import main
from kaggle_environments import make
orig = main.agent
log = open("plantmap.txt", "w")

def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    day, hour = obs.get("day"), obs.get("hour")
    if day == 14 and hour == 12:
        n = len(me["tiles"])
        for y in range(n):
            row = []
            for x in range(n):
                t = me["tiles"][y][x]
                if isinstance(t, dict):
                    if t.get("kind") == "PLANT":
                        row.append(t["crop"][0])  # W/M/S
                    elif t.get("kind") == "PASTURE":
                        row.append("P")
                    else:
                        row.append("?")
                else:
                    row.append(".")
            log.write(" ".join(row) + "\n")
        log.write(f"land={me.get('unlocked_quadrants')}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
