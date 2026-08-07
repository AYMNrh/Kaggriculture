"""Measure crop-hand efficiency: useful actions per crop hand per day.

Codex round-10 acceptance gate: median crop worker >= 7 useful actions/day.
THUNDER does ~8. If territories deliver this, the field can grow; if not,
the scheduler is still the bottleneck.
"""
from kaggle_environments import make
from collections import defaultdict, Counter

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run(["main.py", "pass"])

# track each hand's position + action per hour
useful_by_unit = defaultdict(int)
move_by_unit = defaultdict(int)
pass_by_unit = defaultdict(int)
for i, step in enumerate(env.steps):
    day = i // 24
    obs = step[0]["observation"]
    acts = step[0].get("action") or {}
    # units: farmer (idx 0) + hands
    hand_acts = acts.get("hands") or []
    entries = [(-1, acts.get("farmer"))]
    for j in range(len(hand_acts)):
        entries.append((j, hand_acts[j]))
    for uidx, a in entries:
        if not a:
            continue
        op = a[0]
        if op in ("NORTH", "SOUTH", "EAST", "WEST"):
            move_by_unit[day, uidx] += 1
        elif op == "PASS":
            pass_by_unit[day, uidx] += 1
        else:
            useful_by_unit[day, uidx] += 1

# crop hands are the LAST n_crop_hands units (idx >= animal_unit_count)
# farmer is idx -1 (or 0)... approximate: crop hands are the higher indices
print("day | unit: useful / moves / passes")
for day in (8, 12, 16):
    print(f"--- day {day} ---")
    for uidx in sorted(set([u for (d, u) in useful_by_unit if d == day])):
        u = useful_by_unit[day, uidx]
        m = move_by_unit[day, uidx]
        p = pass_by_unit[day, uidx]
        print(f"  unit {uidx:2d}: useful={u:2d} moves={m:2d} passes={p:2d}")
