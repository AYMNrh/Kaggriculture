"""Trace money + shed hour by hour day 2-3 to see if sells execute."""
import main
from kaggle_environments import make

orig = main.agent
log = open("sell_exec.txt", "w")

def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    priv = obs["private"]
    day, hour = obs.get("day"), obs.get("hour")
    if day in (2, 3) and hour in (0, 1, 2, 5, 12, 20, 23):
        log.write(f"d{day}h{hour:2d} money={me['money']:6.0f} shedF={priv['shed'].get('FERTILIZER',0)} "
                  f"shedW={priv['shed'].get('WHEAT',0)} | market={res['market'][:3]}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
