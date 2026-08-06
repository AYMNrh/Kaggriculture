"""Max hands per day."""
import main
from kaggle_environments import make
orig = main.agent
maxh = {}
def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    day = obs.get("day")
    n = len(me.get("hands") or [])
    if day is not None:
        maxh[day] = max(maxh.get(day, 0), n)
    return res
env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
for d in sorted(maxh):
    if d % 2 == 0:
        print(f"day {d:2d}: max hands {maxh[d]}")
