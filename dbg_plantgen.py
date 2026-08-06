"""Inspect plant job generation at day 13 h5."""
import main
from kaggle_environments import make
orig = main.agent
log = open("plantgen.txt", "w")

# Monkeypatch add_job to capture PLANT jobs
real_add_job = None

def wrapped(obs):
    global real_add_job
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    priv = obs["private"]
    day, hour = obs.get("day"), obs.get("hour")
    if day == 13 and hour == 5:
        board = me["tiles"]
        n = len(board)
        seeds = priv["seeds"]
        # replicate the plant loop exactly
        plantable = [(x, y) for y in range(n) for x in range(n)
                     if board[y][x] is None and day + 4 <= 30 - 1]
        log.write(f"day13h5 plantable={len(plantable)} seeds={ {k: v for k, v in seeds.items() if v > 0} }\n")
        placed = {"WHEAT": 0, "MELON": 0, "STRAWBERRY": 0}
        gen = []
        for idx, (x, y) in enumerate(plantable[:25]):
            if (x, y) in main._STATE.get("planted_today", set()):
                continue
            def crop_for(x, y, idx):
                if 4 <= day <= 14:
                    r = idx % 10
                    if r < 8:
                        return "STRAWBERRY"
                    if r < 9:
                        return "MELON"
                    return "WHEAT"
                if 0 <= day <= 17:
                    return "MELON" if idx % 3 < 2 else "WHEAT"
                return "WHEAT"
            crop = crop_for(x, y, idx)
            if placed[crop] >= seeds.get(crop, 0):
                for alt in ("WHEAT", "MELON", "STRAWBERRY"):
                    if placed[alt] < seeds.get(alt, 0):
                        crop = alt
                        break
                else:
                    crop = None
            if crop is None:
                break
            gen.append(crop)
            placed[crop] += 1
        log.write(f"generated first 25 plant jobs: {gen}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
