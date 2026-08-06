"""Cross-replay strategy summary: what does the top agent buy/build/sell?

For each replay, extract per player: animals bought & when, structures built,
crops planted (first/last day, types), hands hired, land bought, total sells
by product, final money, and win/loss.
"""
import json
import glob
import sys
from collections import Counter, defaultdict

ANIMALS = {"GOOSE", "COW", "SHEEP"}


def summarize(path):
    with open(path) as f:
        d = json.load(f)
    steps = d["steps"]
    info = d.get("info", {})
    teams = info.get("TeamNames", ["?", "?"])
    rewards = d["rewards"]
    n_players = len(steps[0])

    out = []
    for p in range(n_players):
        s = {
            "team": teams[p] if p < len(teams) else "?",
            "reward": rewards[p],
            "animals_bought": Counter(),   # type -> count
            "animals_first_day": {},       # type -> day first bought
            "structures": Counter(),       # COOP/PASTURE -> count
            "crops_planted": Counter(),    # crop -> count
            "crops_first_day": {},         # crop -> first day planted
            "crops_last_day": {},          # crop -> last day planted
            "hands_max": 0,
            "land_days": [],
            "sells": Counter(),            # product -> total units
            "buys_wheat_feed": 0,
            "final_farm": Counter(),
        }
        last_day = -1
        for step in steps:
            o = step[p]["observation"]
            act = step[p].get("action") or {}
            day = o["day"]
            farm = o["farms"][p]
            # market orders
            for m in (act.get("market") or []):
                if m and m[0] == "BUY_ANIMAL" and len(m) >= 3:
                    s["animals_bought"][m[1]] += m[2]
                    s["animals_first_day"].setdefault(m[1], day)
                elif m and m[0] == "SELL" and len(m) >= 3:
                    s["sells"][m[1]] += m[2]
                elif m and m[0] == "BUY_LAND":
                    s["land_days"].append(day)
                elif m and m[0] == "BUY_PRODUCT" and m[1] == "WHEAT":
                    s["buys_wheat_feed"] += m[2]
            # unit actions
            units = [act.get("farmer")] + list(act.get("hands") or [])
            for a in units:
                if a and a[0] == "PLANT" and len(a) >= 2:
                    s["crops_planted"][a[1]] += 1
                    s["crops_first_day"].setdefault(a[1], day)
                    s["crops_last_day"][a[1]] = day
                elif a and a[0] in ("BUILD_COOP", "BUILD_PASTURE"):
                    s["structures"][a[0][6:]] += 1
            s["hands_max"] = max(s["hands_max"], len(farm.get("hands") or []))
        # final farm census
        for row in steps[-1][p]["observation"]["farms"][p]["tiles"]:
            for t in row:
                if isinstance(t, dict):
                    if t.get("kind") in ("COOP", "PASTURE"):
                        s["final_farm"][t["kind"]] += 1
                        if "animal" in t:
                            s["final_farm"]["ANIMAL_" + t["animal"]] += 1
                    elif t.get("kind") == "PLANT":
                        s["final_farm"]["PLANT_" + t["crop"]] += 1
        out.append(s)
    return teams, rewards, out


def fmt_s(s):
    anim = ", ".join(f"{k}x{v} (d{s['animals_first_day'].get(k,0)})"
                     for k, v in s["animals_bought"].most_common()) or "none"
    crops = ", ".join(f"{k}x{v} d{s['crops_first_day'].get(k,0)}-{s['crops_last_day'].get(k,0)}"
                      for k, v in s["crops_planted"].most_common()) or "none"
    sells = ", ".join(f"{k}x{v}" for k, v in s["sells"].most_common(8)) or "none"
    return (f"  animals[{anim}]\n"
            f"  crops[{crops}]  structs[{dict(s['structures'])}]\n"
            f"  hands_max={s['hands_max']} land_days={s['land_days']} "
            f"wheat_feed_bought={s['buys_wheat_feed']}\n"
            f"  sells[{sells}]\n"
            f"  final_farm[{dict(s['final_farm'])}]")


def main(pattern):
    files = sorted(glob.glob(pattern))
    print(f"{len(files)} replays\n")
    for path in files:
        teams, rewards, players = summarize(path)
        fname = path.split("\\")[-1].split("/")[-1]
        print(f"=== {fname} | {teams[0]} ${rewards[0]:,.0f} vs {teams[1]} ${rewards[1]:,.0f} ===")
        for i, s in enumerate(players):
            print(f"  [P{i} {s['team']}]")
            print(fmt_s(s))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else
         r"C:\Users\rhihi\Downloads\strategies of stopplantinstartgametheorying\*.json")
