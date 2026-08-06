"""Land unlock + tile usage over time."""
import main
from kaggle_environments import make
orig = main.agent
log = open("land_trace.txt", "w")
def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    day, hour = obs.get("day"), obs.get("hour")
    if hour == 0 and day in (0, 2, 4, 6, 8, 10, 12, 14):
        board = me["tiles"]
        n = len(board)
        empty = sum(1 for y in range(n) for x in range(n) if board[y][x] is None)
        log.write(f"d{day:2d} land={me.get('unlocked_quadrants')} board={n}x{n} empty={empty} "
                  f"money={me['money']:.0f}\n")
        log.flush()
    return res
env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
