"""Count plant jobs generated vs empty tiles day 12-13."""
import main
from kaggle_environments import make
orig = main.agent
log = open("plantjobs.txt", "w")

def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    priv = obs["private"]
    day, hour = obs.get("day"), obs.get("hour")
    if day in (12, 13) and hour in (0, 4, 8, 12):
        board = me["tiles"]
        n = len(board)
        empty = sum(1 for y in range(n) for x in range(n) if board[y][x] is None)
        acts = [res["farmer"]] + list(res.get("hands") or [])
        plants = [a for a in acts if a and a[0] == "PLANT"]
        waters = [a for a in acts if a and a[0] == "WATER"]
        log.write(f"d{day}h{hour:2d} empty={empty} seeds={ {k: v for k, v in priv['seeds'].items() if v > 0} } "
                  f"| plant_acts={len(plants)} water_acts={len(waters)} hands={len(res.get('hands') or [])}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
