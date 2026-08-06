"""Error capture via file."""
import traceback
import main
from kaggle_environments import make

orig = main.agent
errs = []

def wrapped(obs):
    try:
        return orig(obs)
    except Exception:
        errs.append((obs.get("day"), obs.get("hour"), traceback.format_exc()))
        return {"farmer": ["PASS"], "hands": [], "market": []}

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
with open("err2.txt", "w") as f:
    f.write(f"n_errors: {len(errs)}\n")
    for day, hour, tb in errs[:2]:
        f.write(f"--- day {day} hour {hour} ---\n{tb}\n")
print("done")
