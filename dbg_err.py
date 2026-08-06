"""In-process full run with reward + exception capture."""
import traceback
import main
from kaggle_environments import make

orig = main.agent
errs = []

def wrapped(obs):
    try:
        return orig(obs)
    except Exception:
        tb = traceback.format_exc()
        day, hour = obs.get("day"), obs.get("hour")
        errs.append((day, hour, tb))
        return {"farmer": ["PASS"], "hands": [], "market": []}

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
final = env.steps[-1]
print("statuses:", [(s.status, s.reward) for s in final])
print("n_errors:", len(errs))
for day, hour, tb in errs[:3]:
    print(f"--- error day {day} hour {hour} ---")
    print(tb[:1200])
