"""Analyze top-agent replays: daily strategy trace.

Usage: python analyze_replays.py <replay.json> [replay2.json ...]
Prints per-day: market orders (buy/sell), build/place actions, plant counts,
animal counts, money, shed contents, prices.
"""
import json
import sys
from collections import Counter

ANIMALS = {"GOOSE", "COW", "SHEEP"}
STRUCTS = {"COOP", "PASTURE"}
CROPS = {"WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"}


def analyze(path):
    with open(path) as f:
        d = json.load(f)
    steps = d["steps"]
    info = d.get("info", {})
    teams = info.get("TeamNames", ["?", "?"])
    seeds_info = info.get("seed", "?")
    rewards = d["rewards"]
    print(f"\n{'='*90}")
    print(f"FILE {path.split(chr(92))[-1].split('/')[-1]} | seed={seeds_info} | "
          f"rewards {rewards[0]:,.0f} vs {rewards[1]:,.0f} | teams {teams}")
    print(f"{'='*90}")

    last_day = -1
    for i, step in enumerate(steps):
        p0 = step[0]
        obs = p0["observation"]
        day = obs["day"]
        if day == last_day:
            continue
        last_day = day

        act0 = p0.get("action") or {}
        act1 = step[1].get("action") or {}

        # ---- player 0 farm census ----
        farm0 = obs["farms"][0]
        priv0 = obs["private"]
        census = Counter()
        for row in farm0["tiles"]:
            for t in row:
                if isinstance(t, dict):
                    census[t.get("kind")] += 1
                    if t.get("kind") in STRUCTS and "animal" in t:
                        census["ANIMAL_" + t["animal"]] += 1

        mkt0 = [tuple(o) for o in (act0.get("market") or [])]
        buy = [f"{o[1]}x{o[2]}" for o in mkt0 if o[0] == "BUY_SEED"]
        buyA = [f"{o[1]}x{o[2]}" for o in mkt0 if o[0] == "BUY_ANIMAL"]
        buyP = [f"{o[1]}x{o[2]}" for o in mkt0 if o[0] == "BUY_PRODUCT"]
        sell = [f"{o[1]}x{o[2]}" for o in mkt0 if o[0] == "SELL"]
        hires = sum(1 for o in mkt0 if o[0] == "HIRE")
        land = sum(1 for o in mkt0 if o[0] == "BUY_LAND")

        fa = act0.get("farmer") or ["PASS"]
        ha = act0.get("hands") or []
        builds = [a for a in [fa, *ha] if a and a[0] in ("BUILD_COOP", "BUILD_PASTURE")]
        places = [a for a in [fa, *ha] if a and a[0] == "PLACE"]
        feeds = sum(1 for a in [fa, *ha] if a and a[0] == "FEED")
        colls = sum(1 for a in [fa, *ha] if a and a[0] == "COLLECT_FERTILIZER")
        harvests = sum(1 for a in [fa, *ha] if a and a[0] == "HARVEST")
        waters = sum(1 for a in [fa, *ha] if a and a[0] == "WATER")
        plants_a = sum(1 for a in [fa, *ha] if a and a[0] == "PLANT")

        shed = {k: v for k, v in (priv0.get("shed") or {}).items() if v > 0}
        prices = obs["market"]["prices"]

        only_if = (day in (0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 29)
                   or buy or buyA or buyP or builds or land)
        if not only_if:
            continue

        print(f"day {day:2d} | money ${farm0['money']:8,.0f} | "
              f"plants {census.get('PLANT',0):3d} coops {census.get('COOP',0):2d} "
              f"past {census.get('PASTURE',0):2d} | "
              f"animals {census.get('ANIMAL_GOOSE',0)}/{census.get('ANIMAL_COW',0)}/{census.get('ANIMAL_SHEEP',0)} | "
              f"hands {len(farm0['hands'])} | quad {farm0['unlocked_quadrants']}")
        if buy:
            print(f"    buy_seed  {buy}")
        if buyA:
            print(f"    buy_anim  {buyA}")
        if buyP:
            print(f"    buy_prod  {buyP}")
        if sell:
            print(f"    sell      {sell}")
        if hires:
            print(f"    hire x{hires}")
        if land:
            print(f"    BUY_LAND")
        if builds:
            print(f"    build     {[b[0] for b in builds]}")
        if places:
            print(f"    place     {[p[1] for p in places]}")
        if feeds or colls:
            print(f"    feed x{feeds} collect_fert x{colls}")
        if harvests:
            print(f"    harvest x{harvests}")
        if waters:
            print(f"    water x{waters} plant x{plants_a}")
        if shed:
            print(f"    shed      {shed}")
        if day in (0, 5, 10, 15, 20, 25, 29):
            print(f"    prices    W${prices.get('WHEAT')} C${prices.get('CARROT')} "
                  f"E${prices.get('EGG')} M${prices.get('MILK')} "
                  f"F${prices.get('FERTILIZER')} T${prices.get('TOMATO')}")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        analyze(p)
