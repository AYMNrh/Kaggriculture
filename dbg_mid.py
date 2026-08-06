"""Check agent actions day 3-5."""
import main
from kaggle_environments import make

orig = main.agent
log = open("mid_actions.txt", "w")

def wrapped(obs):
    res = orig(obs)
    day, hour = obs.get("day"), obs.get("hour")
    if 3 <= day <= 5 and hour in (0, 6, 12):
        me = obs["farms"][obs["player"]]
        acts = [res["farmer"]] + list(res.get("hands") or [])
        log.write(f"d{day}h{hour} money={me['money']:.0f} "
                  f"| farmer {res['farmer']} | n_hands {len(res.get('hands') or [])} "
                  f"| market {res['market'][:4]}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
