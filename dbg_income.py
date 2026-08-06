"""Daily money + sells + hands + land days 0-14."""
import main
from kaggle_environments import make

orig = main.agent
log = open("income_trace.txt", "w")

def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    day, hour = obs.get("day"), obs.get("hour")
    if hour == 0 and day <= 14:
        sells = [m for m in (res.get("market") or []) if m and m[0] == "SELL"]
        buys = [m for m in (res.get("market") or []) if m and m[0] != "SELL"]
        log.write(f"d{day:2d} money={me['money']:6.0f} hands={len(me.get('hands') or [])} "
                  f"land={me.get('unlocked_quadrants')} | SELL {sells} | BUY {buys[:5]}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
