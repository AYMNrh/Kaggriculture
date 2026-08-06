"""Deep-dive: THUNDER THUNDER strategy per game (plants, animals, actions)."""
import json, glob, os
from collections import Counter, defaultdict
import statistics

folder = r"C:\Users\rhihi\Downloads\thunder thunder"
replays = sorted(glob.glob(os.path.join(folder, "*.json")))[:6]  # 6 games

def game_stats(path, pidx):
    with open(path, encoding="utf-8") as f:
        rp = json.load(f)
    steps = rp["steps"]
    actions = Counter()
    sells = Counter()
    buys = Counter()
    max_plants = 0
    max_animals = 0
    max_hands = 0
    plant_days = defaultdict(int)
    last_plant = {}
    for i, step in enumerate(steps):
        day = i // 24
        st = step[pidx]
        obs = st.get("observation") or {}
        acts = st.get("action") or {}
        # farms
        farms = obs.get("farms") or []
        if farms:
            farm = farms[pidx] if pidx < len(farms) else farms[0]
            tiles = farm.get("tiles") or []
            plants = sum(1 for row in tiles for t in row
                         if isinstance(t, dict) and t.get("kind") == "PLANT")
            animals = sum(1 for row in tiles for t in row
                          if isinstance(t, dict) and "animal" in t)
            hands = 1 + len(farm.get("hands") or [])
            max_plants = max(max_plants, plants)
            max_animals = max(max_animals, animals)
            max_hands = max(max_hands, hands)
            if day in (5, 8, 10, 12, 14, 16, 18, 20):
                plant_days[day] = max(plant_days[day], plants)
        # actions
        for a in [acts.get("farmer")] + list(acts.get("hands") or []):
            if a and a[0] not in ("PASS", "NORTH", "SOUTH", "EAST", "WEST"):
                actions[a[0]] += 1
        # market
        for m in (acts.get("market") or []):
            if m and m[0] == "SELL" and len(m) >= 3:
                sells[m[1]] += m[2]
            if m and m[0] == "BUY" and len(m) >= 3:
                buys[m[1]] += m[2]
        # PLANT days
        for a in [acts.get("farmer")] + list(acts.get("hands") or []):
            if a and a[0] == "PLANT" and len(a) >= 2:
                last_plant[a[1]] = max(last_plant.get(a[1], 0), day)
    reward = steps[-1][pidx]["reward"]
    return {
        "reward": reward, "actions": actions, "sells": sells, "buys": buys,
        "max_plants": max_plants, "max_animals": max_animals,
        "max_hands": max_hands, "plant_days": dict(plant_days),
        "last_plant": last_plant,
    }

for path in replays:
    with open(path, encoding="utf-8") as f:
        rp = json.load(f)
    n = len(rp["steps"][-1])
    res = [(s["reward"], s["status"]) for s in rp["steps"][-1]]
    p0 = game_stats(path, 0)
    p1 = game_stats(path, 1)
    winner = 0 if p0["reward"] >= p1["reward"] else 1
    w = p0 if winner == 0 else p1
    l = p1 if winner == 0 else p0
    name = os.path.basename(path)
    print(f"=== {name} | P0 ${p0['reward']:,.0f} vs P1 ${p1['reward']:,.0f} | winner P{winner} ===")
    for tag, g in (("WINNER", w), ("LOSER", l)):
        print(f"  {tag}: max plants {g['max_plants']}, animals {g['max_animals']}, hands {g['max_hands']}")
        print(f"    plants by day: {g['plant_days']}")
        print(f"    last plant: {g['last_plant']}")
        print(f"    top actions: {g['actions'].most_common(8)}")
        print(f"    sells: {dict(g['sells'])}")
        if g['buys']:
            print(f"    buys: {dict(g['buys'])}")
    print()
