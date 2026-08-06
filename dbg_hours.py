"""Hour-by-hour money + full market list day 4-5."""
import main
from kaggle_environments import make

orig = main.agent
log = open("hour_trace.txt", "w")

def wrapped(obs):
    res = orig(obs)
    day, hour = obs.get("day"), obs.get("hour")
    if 4 <= day <= 5:
        me = obs["farms"][obs["player"]]
        priv = obs["private"]
        log.write(f"d{day}h{hour:2d} money={me['money']:6.0f} shedF={priv['shed'].get('FERTILIZER',0)} "
                  f"shedW={priv['shed'].get('WHEAT',0)} shedC={priv['shed'].get('COW',0)} "
                  f"| market={res['market']}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
