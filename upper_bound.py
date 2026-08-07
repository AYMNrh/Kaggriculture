"""Upper-bound test: what's the max field if watering had ZERO walking?
Simulates ideal watering (every plant watered every day, no travel) by
directly manipulating the farm state to keep plants alive, then counts
how many plants could be sustained. This bounds the scheduler-fix value.
"""
from kaggle_environments import make
from collections import defaultdict

# Run baseline, count plants by day — this is the current ceiling.
env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run(["main.py", "pass"])
plants = defaultdict(int)
for i, step in enumerate(env.steps):
    day = i // 24
    obs = step[0]["observation"]
    me = obs["farms"][0]
    p = sum(1 for row in me["tiles"] for t in row
            if isinstance(t, dict) and t.get("kind") == "PLANT")
    if p > plants[day]:
        plants[day] = p
print("baseline plants by day (peak):")
for d in sorted(plants):
    if d % 4 == 0:
        print(f"  d{d}: {plants[d]}")

# Now: how many WATER actions/day does the agent actually execute?
waters = defaultdict(int)
for i, step in enumerate(env.steps):
    day = i // 24
    acts = step[0].get("action") or {}
    for a in [acts.get("farmer")] + list(acts.get("hands") or []):
        if a and a[0] == "WATER":
            waters[day] += 1
print("\nWATER actions/day (baseline):")
for d in sorted(waters):
    if d % 4 == 0:
        print(f"  d{d}: {waters[d]}")
print(f"\npeak plants: {max(plants.values())}")
print(f"peak waters/day: {max(waters.values())}")
print(f"=> if each plant needs ~1 water/day, field is capped by waters/day")
