"""Experiment v2: proper animal logistics.

BUY_ANIMAL -> shed. PLACE requires the animal in the unit's inventory,
so: PICKUP GOOSE (shed-adjacent) -> walk to empty coop -> PLACE GOOSE.
FEED consumes WHEAT from unit inventory -> PICKUP WHEAT first.
COLLECT_FERTILIZER adds to inventory -> DROP at shed -> SELL.
"""
import random
from kaggle_environments import make

ANIMALS = {"GOOSE": {"cost": 300, "structure": "COOP", "product": "EGG"},
           "COW": {"cost": 400, "structure": "PASTURE", "product": "MILK"},
           "SHEEP": {"cost": 500, "structure": "PASTURE", "product": "WOOL"}}
SHED = [(4, 4), (5, 4), (4, 5), (5, 5)]


def geese_agent(obs):
    player = obs["player"]
    me = obs["farms"][player]
    private = obs["private"]
    day = obs["day"]
    board = me["tiles"]
    n = len(board)
    money = me["money"]
    shed = private["shed"]

    market = []
    for item, qty in shed.items():
        if qty > 0 and item != "WHEAT" and len(market) < 8:
            market.append(["SELL", item, qty])

    # count things
    coops = empty_coops = geese = 0
    for row in board:
        for t in row:
            if isinstance(t, dict) and t.get("kind") == "COOP":
                coops += 1
                if "animal" in t:
                    geese += 1
                else:
                    empty_coops += 1

    empty_tiles = sum(1 for row in board for t in row if t is None)

    # buy geese: 1 goose per coop we'll have; keep money buffer
    target = min(40, empty_tiles + empty_coops + geese)
    if geese < target and money > 1000 and len(market) < 9:
        market.append(["BUY_ANIMAL", "GOOSE", 1])

    # buy wheat for feed if we have geese and shed lacks wheat
    if geese > 0 and shed.get("WHEAT", 0) < 10 and money > 200 and len(market) < 10:
        market.append(["BUY_PRODUCT", "WHEAT", 5])

    # jobs: (prio, pos, action)
    jobs = []

    def add_job(x, y, prio, action):
        jobs.append((prio, (x, y), action))

    for y in range(n):
        for x in range(n):
            t = board[y][x]
            if isinstance(t, dict):
                kind = t.get("kind")
                if kind == "COOP":
                    if "animal" not in t:
                        add_job(x, y, 3, ["PLACE", "GOOSE"])
                    else:
                        if not t.get("fed_today"):
                            add_job(x, y, 5, ["FEED"])
                        if t.get("fertilizer_available"):
                            add_job(x, y, 4, ["COLLECT_FERTILIZER"])
                        if t.get("yield_units", 0) > 0:
                            add_job(x, y, 4, ["HARVEST"])
                elif kind == "WEED":
                    add_job(x, y, 1, ["DIG"])
            elif t is None and day >= 0:
                add_job(x, y, 2, ["BUILD_COOP"])

    units = [("farmer", list(me["farmer"]))] + [("hand", list(h)) for h in me["hands"]]
    claimed = set()
    farmer_action = ["PASS"]
    hands_actions = []

    def manh(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def move(pos, target):
        dx = target[0] - pos[0]
        dy = target[1] - pos[1]
        if abs(dx) >= abs(dy) and dx != 0:
            return ["EAST" if dx > 0 else "WEST"]
        if dy != 0:
            return ["SOUTH" if dy > 0 else "NORTH"]
        return ["PASS"]

    at_shed = lambda pos: tuple(pos) in SHED

    for idx, (utype, pos) in enumerate(units):
        inv = private["inventories"][idx] or {}
        inv_size = sum(inv.values())

        # 0. DROP if inventory is full (fertilizer/eggs accumulate)
        if inv_size >= 12:
            if at_shed(pos):
                action = ["DROP"]
            else:
                action = move(pos, min(SHED, key=lambda s: manh(pos, s)))
            if utype == "farmer":
                farmer_action = action
            else:
                hands_actions.append(action)
            continue

        # 1. If carrying GOOSE and there's an empty coop -> place it
        if inv.get("GOOSE", 0) > 0:
            empty = [k for k in (j[1] for j in jobs if j[2][0] == "PLACE") if k not in claimed]
            if empty:
                key = min(empty, key=lambda k: manh(pos, k))
                claimed.add(key)
                if tuple(pos) == key:
                    action = ["PLACE", "GOOSE"]
                else:
                    action = move(pos, key)
                if utype == "farmer":
                    farmer_action = action
                else:
                    hands_actions.append(action)
                continue

        # 2. Need wheat to feed? pickup from shed first
        if inv.get("WHEAT", 0) == 0 and any(j[2][0] == "FEED" for j in jobs):
            if at_shed(pos):
                action = ["PICKUP", "WHEAT", 5]
            else:
                action = move(pos, min(SHED, key=lambda s: manh(pos, s)))
            if utype == "farmer":
                farmer_action = action
            else:
                hands_actions.append(action)
            continue

        # 3. Need a goose to place? pickup from shed first
        if inv.get("GOOSE", 0) == 0 and any(j[2][0] == "PLACE" for j in jobs) \
                and shed.get("GOOSE", 0) > 0:
            if at_shed(pos):
                action = ["PICKUP", "GOOSE", 1]
            else:
                action = move(pos, min(SHED, key=lambda s: manh(pos, s)))
            if utype == "farmer":
                farmer_action = action
            else:
                hands_actions.append(action)
            continue

        # 4. normal job assignment
        best = None
        best_key = None
        for prio, key, act in jobs:
            if key in claimed:
                continue
            d = manh(pos, key)
            score = (prio, -d)
            if best is None or score > best:
                best = score
                best_key = key
        if best_key is None:
            action = ["PASS"]
        elif tuple(pos) == best_key:
            action = [j[2] for j in jobs if j[1] == best_key][0]
            claimed.add(best_key)
        else:
            action = move(pos, best_key)

        if utype == "farmer":
            farmer_action = action
        else:
            hands_actions.append(action)

    return {"farmer": farmer_action, "hands": hands_actions, "market": market}


if __name__ == "__main__":
    import main
    episodes = 10
    for label, agent in (("crops (current)", main.agent), ("geese v2", geese_agent)):
        total = wins = 0
        for ep in range(episodes):
            seed = random.randint(0, 2**31 - 1)
            env = make("kaggriculture",
                       configuration={"episodeSteps": 720, "seed": seed}, debug=False)
            env.run([agent, "pass"])
            final = env.steps[-1]
            r0, r1 = final[0].reward, final[1].reward
            total += r0
            wins += r0 > r1
        print(f"{label:<16} avg ${total/episodes:,.0f}  wins {wins}/{episodes}")
