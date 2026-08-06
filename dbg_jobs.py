"""Inspect jobs dict + board state day 11."""
import main
from kaggle_environments import make

orig = main.agent
log = open("jobs_trace.txt", "w")

# Monkeypatch to capture jobs: replicate the agent's internals via tracing.
# Simpler: check board state and whether empty cells exist.
def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    priv = obs["private"]
    day, hour = obs.get("day"), obs.get("hour")
    if day == 11 and hour == 5:
        board = me["tiles"]
        n = len(board)
        empty = sum(1 for y in range(n) for x in range(n) if board[y][x] is None)
        pasture = 0
        cows = sheep = 0
        plants = 0
        for y in range(n):
            for x in range(n):
                t = board[y][x]
                if isinstance(t, dict):
                    k = t.get("kind")
                    if k == "PASTURE":
                        pasture += 1
                        if "animal" in t:
                            if t["animal"] == "COW":
                                cows += 1
                            else:
                                sheep += 1
                    elif k == "PLANT":
                        plants += 1
        acts = [res["farmer"]] + list(res.get("hands") or [])
        log.write(f"d{day}h{hour} board={n}x{n} empty={empty} past={pasture} cows={cows} sheep={sheep} "
                  f"plants={plants} shedC={priv['shed'].get('COW',0)} shedS={priv['shed'].get('SHEEP',0)} "
                  f"| actions={[a for a in acts if a and a[0] not in ('PASS','NORTH','SOUTH','EAST','WEST')][:15]}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
