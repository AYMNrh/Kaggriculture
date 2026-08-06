"""Daily money + animals trace (in-process, current main.py)."""
import main
from kaggle_environments import make

orig = main.agent

def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    priv = obs["private"]
    day, hour = obs.get("day"), obs.get("hour")
    if hour == 0 and day % 3 == 0:
        cows = sheep = past = plants = 0
        for row in me["tiles"]:
            for t in row:
                if isinstance(t, dict):
                    if t.get("kind") == "PASTURE":
                        past += 1
                        if "animal" in t:
                            if t["animal"] == "COW":
                                cows += 1
                            else:
                                sheep += 1
                    elif t.get("kind") == "PLANT":
                        plants += 1
        print(f"d{day:2d} money=${me['money']:7,.0f} past={past} cows={cows} sheep={sheep} "
              f"plants={plants} shedC={priv['shed'].get('COW',0)} shedS={priv['shed'].get('SHEEP',0)} "
              f"shedW={priv['shed'].get('WHEAT',0)}", flush=True)
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
final = env.steps[-1]
print("FINAL:", [(s.reward, s.status) for s in final])
