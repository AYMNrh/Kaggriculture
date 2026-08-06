import main
from kaggle_environments import make

orig = main.agent
calls = {"n": 0}
def wrapped(obs):
    res = orig(obs)
    calls["n"] += 1
    if obs.get("day") == 8 and obs.get("hour") == 0:
        priv = obs["private"]
        print(f"[dbg] day8 h0 | shed { {k:v for k,v in priv['shed'].items() if v>0} }")
        print(f"[dbg] market {res['market']}")
        print(f"[dbg] money {obs['farms'][obs['player']]['money']}")
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
