"""Inspect crop_work and jobs at day 7 h8 by replicating job gen."""
import main
from kaggle_environments import make
orig = main.agent
log = open("jobsinspect.txt", "w")

def wrapped(obs):
    res = orig(obs)
    me = obs["farms"][obs["player"]]
    priv = obs["private"]
    day, hour = obs.get("day"), obs.get("hour")
    if day == 7 and hour == 8:
        board = me["tiles"]
        n = len(board)
        seeds = priv["seeds"]
        day_v = day
        # Replicate crop_for + plant loop
        def crop_for(x, y, idx):
            if 4 <= day_v <= 14:
                r = idx % 10
                if r < 8:
                    return "STRAWBERRY"
                if r < 9:
                    return "MELON"
                return "WHEAT"
            if 0 <= day_v <= 17:
                return "MELON" if idx % 3 < 2 else "WHEAT"
            return "WHEAT"
        plantable = [(x, y) for y in range(n) for x in range(n)
                     if board[y][x] is None and day_v + 4 <= 30 - 1]
        placed = {"WHEAT": 0, "MELON": 0, "STRAWBERRY": 0}
        jobs = []
        for idx, (x, y) in enumerate(plantable):
            if (x, y) in main._STATE.get("planted_today", set()):
                continue
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
            jobs.append((crop, x, y))
            placed[crop] += 1
        log.write(f"day7h8 plantable={len(plantable)} seeds={ {k: v for k, v in seeds.items() if v > 0} }\n")
        log.write(f"plant jobs generated: {jobs[:12]} ... total {len(jobs)}\n")
        log.write(f"planted_today={main._STATE.get('planted_today')}\n")
        log.flush()
    return res

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
