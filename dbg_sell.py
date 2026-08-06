"""Check: does a SELL order actually execute? Trace shed + money hour by hour on day 16."""
import sys
import main
from kaggle_environments import make

orig = main.agent
log = open("sell_trace.txt", "w")

def wrapped(obs):
    res = orig(obs)
    if obs.get("day") == 16:
        priv = obs["private"]
        me = obs["farms"][obs["player"]]
        log.write(f"h{obs.get('hour'):2d} money={me['money']:8.0f} "
                  f"shed_MELON={priv['shed'].get('MELON', 0):3d} "
                  f"shed_WHEAT={priv['shed'].get('WHEAT', 0):3d} "
                  f"price_MELON={obs['market']['prices'].get('MELON')} "
                  f"market={res['market']}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
