"""Measure target persistence + walking: how many hours does a hand keep
its sticky target before it resets? THUNDER hands do 7-8 useful actions
with few moves — mine do 2-6 with 15 moves. If targets reset every hour,
hands ping-pong. This isolates the scheduler defect precisely."""
from kaggle_environments import make
from collections import defaultdict

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run(["main.py", "pass"])

# track per-unit per-day: consecutive hours on same job tile
# approximate: count action changes (non-move ops) per unit per day
day12_units = defaultdict(list)
for i in range(12*24, 13*24):
    step = env.steps[i]
    acts = step[0].get("action") or {}
    hands = acts.get("hands") or []
    for j, a in enumerate(hands):
        if a:
            day12_units[j].append(a[0])

print("day 12: per-hand action sequence (first 12 hours)")
for j in sorted(day12_units):
    seq = day12_units[j][:12]
    useful = sum(1 for a in seq if a not in ("NORTH","SOUTH","EAST","WEST","PASS"))
    moves = sum(1 for a in seq if a in ("NORTH","SOUTH","EAST","WEST"))
    print(f"  H{j}: {useful} useful / {moves} moves | {seq}")
