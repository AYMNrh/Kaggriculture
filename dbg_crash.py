"""Run main.py in-process with exception capture — find the crash."""
import sys
import traceback
import main
from kaggle_environments import make

orig = main.agent
crash_log = open("crash_log.txt", "w")

def wrapped(obs):
    try:
        return orig(obs)
    except Exception:
        crash_log.write(f"--- step {obs.get('step')} day {obs.get('day')} hour {obs.get('hour')} ---\n")
        crash_log.write(traceback.format_exc())
        crash_log.flush()
        raise

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
crash_log.close()
print("done")
