"""In-process: dump agent decisions at key points."""
import sys
import main
from kaggle_environments import make

orig = main.agent
log = open("decision_log.txt", "w")

def wrapped(obs):
    res = orig(obs)
    day, hour = obs.get("day"), obs.get("hour")
    if (day, hour) in [(8, 0), (12, 0), (16, 0), (20, 0), (24, 0)]:
        priv = obs["private"]
        me = obs["farms"][obs["player"]]
        log.write(f"day{day} h{hour} money={me['money']:.0f}\n")
        log.write(f"  shed={ {k: v for k, v in priv['shed'].items() if v > 0} }\n")
        log.write(f"  market={res['market']}\n")
        log.write(f"  farmer_act={res['farmer']} hands_acts={res['hands']}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
