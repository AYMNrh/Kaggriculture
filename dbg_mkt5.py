"""Trace money + market day 5-8 hour 0 only."""
import main
from kaggle_environments import make

orig = main.agent
log = open("mkt5.txt", "w")

def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    priv = obs["private"]
    day, hour = obs.get("day"), obs.get("hour")
    if hour == 0 and 5 <= day <= 9:
        log.write(f"d{day:2d} money={me['money']:6.0f} shed={ {k:v for k,v in priv['shed'].items() if v>0} } "
                  f"| market={res['market']}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
