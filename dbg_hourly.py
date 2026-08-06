"""Count my agent's non-pass actions per hour on day 11."""
import main
from kaggle_environments import make

orig = main.agent
from collections import Counter
hourly = Counter()
maxhands = 0

def wrapped(obs):
    global maxhands
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    day, hour = obs.get("day"), obs.get("hour")
    if day == 14:
        acts = [res["farmer"]] + list(res.get("hands") or [])
        n = sum(1 for a in acts if a and a[0] != "PASS")
        hourly[hour] += n
        nh = len(res.get("hands") or [])
        if nh > maxhands:
            maxhands = nh
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
print("day 11 actions per hour:", [hourly[h] for h in range(24)])
print("total non-pass:", sum(hourly.values()))
print("max hands:", maxhands)
