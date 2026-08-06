"""Kaggriculture agent v4 — champion-style animal + premium crop farm.

Replicates the strategy reverse-engineered from the current #1 leaderboard
agent ("StopPlantingStartGameTheorying", 23 replays, $117-156k/game):

  - Day 0: all-in on COWS + SHEEP (not geese!), build pastures, hire hands.
    Scale to 8 cows + 6 sheep = 14 pastures. Milk ($160->$326) and wool
    ($200->$250) prices RISE through the season as town demand drains the
    market; fertilizer (1/day/animal, base $100) is a steady income stream.
  - Wheat: grow ~67 plants for feed + top up via BUY_PRODUCT WHEAT (275/season).
    Every animal eats 1 wheat/day — feed is the binding constraint.
  - Premium crops: STRAWBERRY (plant days 4-14, price $120->$312) and
    MELON (plant days 0-17, $250->$293). No cheap staples beyond feed wheat.
  - Land: NE ~day 7, SW ~day 10. Never SE (75 tiles suffice).
  - Hands: 12-14 hired daily (fib cost, reset daily).
  - SELL TIMING (the actual game theory):
      * FERTILIZER: sell early + daily — its price decays $100->$21 as both
        players flood the market.
      * STRAWBERRY/MILK/WOOL: sell as they come — prices rise with scarcity.
      * WHEAT: hold surplus, sell late when wheat price peaks (~$47).

Entry point: `agent(obs)` (required name for Kaggle submissions).
"""

# ---------------------------------------------------------------------------
CROPS = {
    "WHEAT":      {"seed": 10, "first_yield_day": 2, "max_yield_day": 4, "max_yield": 6, "ongoing": False},
    "CARROT":     {"seed": 20, "first_yield_day": 2, "max_yield_day": 3, "max_yield": 4, "ongoing": False},
    "TOMATO":     {"seed": 50, "first_yield_day": 8, "max_yield_day": 8, "max_yield": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "max_yield": 4, "ongoing": True},
    "MELON":      {"seed": 80, "first_yield_day": 10, "max_yield_day": 12, "max_yield": 6, "ongoing": False},
}
ANIMALS = {
    "GOOSE": {"cost": 300, "structure": "COOP", "first_yield_day": 4, "interval": 1, "max_held": 4, "product": "EGG"},
    "COW":   {"cost": 400, "structure": "PASTURE", "first_yield_day": 8, "interval": 2, "max_held": 6, "product": "MILK"},
    "SHEEP": {"cost": 500, "structure": "PASTURE", "first_yield_day": 6, "interval": 3, "max_held": 6, "product": "WOOL"},
}
LAND_ORDER = ["NE", "SW", "SE"]
LAND_PRICES = {"NE": 1000, "SW": 2000, "SE": 4000}
SEASON_DAYS = 30
MAX_MARKET_ORDERS = 10
MONEY_BUFFER = 150
PLANT_CUTOFF_HOUR = 18
DROP_THRESHOLD = 15

# Champion targets (from replays)
TARGET_COWS = 8
TARGET_SHEEP = 6
HIRE_TARGETS = [(0, 2), (1, 5), (3, 8), (5, 10), (8, 12), (12, 14)]  # (day >=, hands)
WHEAT_FEED_RESERVE = 25      # keep this much wheat in shed for feeding
STRAWBERRY_WINDOW = (4, 14)  # plant days
MELON_WINDOW = (0, 17)

_STATE = {"episode": None}


def _reset_if_new_episode(obs):
    step = obs.get("step", 0)
    if _STATE["episode"] != obs.get("player"):
        _STATE.update(episode=obs.get("player"), last_step=-1,
                      targets={}, last_day=None, planted_today=set())
    if step < _STATE.get("last_step", -1):
        _STATE.update(episode=obs.get("player"),
                      targets={}, last_day=None, planted_today=set())
    _STATE["last_step"] = step


def _manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _target_hands(day):
    target = HIRE_TARGETS[0][1]
    for d, n in HIRE_TARGETS:
        if day >= d:
            target = n
    return target


def _shed_tiles(n):
    half = n // 2
    return [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]


def agent(obs):
    _reset_if_new_episode(obs)

    player = obs["player"]
    me = obs["farms"][player]
    private = obs["private"]
    day = obs["day"]
    hour = obs["hour"]
    board = me["tiles"]
    n = len(board)
    farmer_pos = list(me["farmer"])
    hand_positions = [list(h) for h in me["hands"]]
    money = me["money"]
    seeds = private["seeds"]
    shed = private["shed"]
    shed_tiles = _shed_tiles(n)
    num_units = 1 + len(hand_positions)

    if _STATE["last_day"] is not None and day != _STATE["last_day"]:
        _STATE["targets"] = {}
        _STATE["planted_today"] = set()
    _STATE["last_day"] = day
    _STATE["planted_today"] = {(x, y) for (x, y) in _STATE["planted_today"]
                               if board[y][x] is None}

    # ------------------------------------------------------------------
    # 1. Farm census
    # ------------------------------------------------------------------
    plants = 0
    weeds = 0
    empty_tiles = 0
    struct = {}
    animals = {}
    for row in board:
        for t in row:
            if t is None:
                empty_tiles += 1
            elif isinstance(t, dict):
                k = t.get("kind")
                if k == "PLANT":
                    plants += 1
                elif k == "WEED":
                    weeds += 1
                elif k in ("COOP", "PASTURE"):
                    struct[k] = struct.get(k, 0) + 1
                    if "animal" in t:
                        animals[t["animal"]] = animals.get(t["animal"], 0) + 1
    total_animals = sum(animals.values())
    shed_animals = sum(shed.get(a, 0) for a in ANIMALS)

    # ------------------------------------------------------------------
    # 2. Market orders
    # ------------------------------------------------------------------
    market_orders = []

    # 2a. Sell — the game theory. Fertilizer early+often; products as they
    # come; wheat surplus held until late (price peaks).
    for item, qty in shed.items():
        if qty <= 0 or len(market_orders) >= MAX_MARKET_ORDERS:
            continue
        if item == "FERTILIZER":
            market_orders.append(["SELL", item, qty])          # decaying price
        elif item in ("STRAWBERRY", "MILK", "WOOL", "MELON", "EGG"):
            market_orders.append(["SELL", item, qty])          # rising price
        elif item == "WHEAT":
            # sell surplus only (keep feed reserve); hold rest for late spike
            surplus = qty - WHEAT_FEED_RESERVE - total_animals
            if surplus > 0 and day >= 8:
                market_orders.append(["SELL", "WHEAT", min(surplus, 10)])
        elif item in ("GOOSE", "COW", "SHEEP"):
            continue  # never sell animals
        else:
            market_orders.append(["SELL", item, qty])

    if obs.get("day") == 8 and obs.get("hour") == 0:
        print("DBG day8 shed:", {k: v for k, v in private["shed"].items() if v > 0})
        print("DBG day8 market:", market_orders)
        print("DBG day8 money:", money, "animals:", total_animals)
    if obs.get("day") == 8 and obs.get("hour") == 0:
        with open("dbg_out.txt", "a") as f:
            f.write(f"day8 shed: { {k: v for k, v in private['shed'].items() if v > 0} }
")
            f.write(f"day8 market: {market_orders}
")
            f.write(f"day8 money: {money} animals: {total_animals}
")
    if obs.get("day") == 8 and obs.get("hour") == 0:
        with open(r"C:/Users/rhihi/projects/kaggriculture/dbg_out.txt", "a") as f:
            f.write("day8 shed: " + str({k: v for k, v in private["shed"].items() if v > 0}) + "
")
            f.write("day8 market: " + str(market_orders) + "
")
            f.write("day8 money: " + str(money) + " animals: " + str(total_animals) + "
")
    # 2b. Hire hands (cheap fib cost, reset daily).
    target_hands = _target_hands(day)
    hires_today = me.get("hires_today", 0)
    while (len(market_orders) < MAX_MARKET_ORDERS
           and len(hand_positions) + hires_today < target_hands
           and money > 200):
        market_orders.append(["HIRE"])
        hires_today += 1

    # 2c. Buy animals: cows + sheep. Champion goes ALL-IN day 0 (3 cows +
    # 1 sheep + seeds + feed wheat + hires in ONE turn). Buy into the shed,
    # build pastures in parallel. Only the money buffer constrains.
    cows = animals.get("COW", 0)
    sheep = animals.get("SHEEP", 0)
    cows_in_pipeline = cows + shed.get("COW", 0) + sum(
        (private["inventories"][i] or {}).get("COW", 0) for i in range(num_units))
    sheep_in_pipeline = sheep + shed.get("SHEEP", 0) + sum(
        (private["inventories"][i] or {}).get("SHEEP", 0) for i in range(num_units))

    if len(market_orders) < MAX_MARKET_ORDERS:
        # Day 0 all-in: queue the full champion opening in one turn —
        # 3 cows + 1 sheep + melon/wheat seeds + feed wheat + hires.
        if day == 0 and hour == 0:
            opening = [["BUY_ANIMAL", "COW", 3], ["BUY_ANIMAL", "SHEEP", 1]]
            if money > 500:
                opening.append(["BUY_SEED", "MELON", 7])
            if money > 300:
                opening.append(["BUY_SEED", "WHEAT", 10])
            if money > 500:
                opening.append(["BUY_PRODUCT", "WHEAT", 17])
            opening.extend([["HIRE"], ["HIRE"]])
            for o in opening:
                if len(market_orders) < MAX_MARKET_ORDERS:
                    market_orders.append(o)
        elif cows_in_pipeline < TARGET_COWS and money > 300:
            market_orders.append(["BUY_ANIMAL", "COW", 1])
        elif sheep_in_pipeline < TARGET_SHEEP and money > 400:
            market_orders.append(["BUY_ANIMAL", "SHEEP", 1])
        # Once cows are full, keep topping sheep up.
        if len(market_orders) < MAX_MARKET_ORDERS and cows_in_pipeline >= TARGET_COWS \
                and sheep_in_pipeline < TARGET_SHEEP and money > 300:
            market_orders.append(["BUY_ANIMAL", "SHEEP", 1])

    # 2d. Buy wheat for feed when short (cheap early).
    feed_gap = total_animals * 2 + WHEAT_FEED_RESERVE - shed.get("WHEAT", 0)
    if (len(market_orders) < MAX_MARKET_ORDERS and feed_gap > 0
            and money > 300 and day < 25):
        market_orders.append(["BUY_PRODUCT", "WHEAT", min(feed_gap, 8)])

    # 2e. Seeds — buy AGGRESSIVELY like the champion (67 wheat, 41
    # strawberry, 26 melon planted = ~134 tiles). Cheap seeds, big payoff.
    def buy_seed(crop, want):
        if want <= 0 or len(market_orders) >= MAX_MARKET_ORDERS:
            return
        cost = CROPS[crop]["seed"]
        affordable = min(want, max(0, (money - MONEY_BUFFER)) // cost)
        if affordable > 0:
            market_orders.append(["BUY_SEED", crop, affordable])

    if STRAWBERRY_WINDOW[0] <= day <= STRAWBERRY_WINDOW[1]:
        buy_seed("STRAWBERRY", max(0, 30 - seeds.get("STRAWBERRY", 0)))
    if MELON_WINDOW[0] <= day <= MELON_WINDOW[1]:
        buy_seed("MELON", max(0, 20 - seeds.get("MELON", 0)))
    # wheat seeds: keep enough for feed + a cash crop (champion: ~67 total)
    want_wheat_seed = max(0, 40 - seeds.get("WHEAT", 0))
    buy_seed("WHEAT", want_wheat_seed)

    # 2f. Land: NE ~day 7, SW ~day 10 (skip SE).
    if len(market_orders) < MAX_MARKET_ORDERS:
        for q in LAND_ORDER:
            if q not in me["unlocked_quadrants"]:
                if money - 600 > LAND_PRICES[q]:
                    market_orders.append(["BUY_LAND"])
                break

    # ------------------------------------------------------------------
    # 3. Jobs
    # ------------------------------------------------------------------
    # FEED(6) > COLLECT_FERT(5) > HARVEST(4.5) > WATER(4) > PLACE(3.5) >
    # BUILD(3) > FERTILIZE(2.5) > PLANT(2) > DIG(1)
    jobs = {}

    def add_job(x, y, prio, action):
        key = (x, y)
        if key not in jobs or jobs[key][0] < prio:
            jobs[key] = [prio, action]

    for y in range(n):
        for x in range(n):
            t = board[y][x]
            if not isinstance(t, dict):
                continue
            kind = t.get("kind")
            if kind in ("COOP", "PASTURE"):
                if "animal" not in t:
                    # Distribute PLACE jobs by what's actually unplaced:
                    # count animals in shed+inventory vs placed, and give
                    # each empty structure the type with the biggest backlog
                    # (COW and SHEEP share PASTURE — don't always pick COW).
                    backlog = {}
                    for a in ANIMALS:
                        if ANIMALS[a]["structure"] != kind:
                            continue
                        held = (shed.get(a, 0) + sum(
                            (private["inventories"][i] or {}).get(a, 0)
                            for i in range(num_units)))
                        placed_a = animals.get(a, 0)
                        backlog[a] = held - max(0, placed_a - struct.get(kind, 0))
                    best_a = max(backlog, key=backlog.get) if backlog else None
                    if best_a is not None and backlog[best_a] > 0:
                        add_job(x, y, 3.5, ["PLACE", best_a])
                else:
                    a = t["animal"]
                    if not t.get("fed_today"):
                        add_job(x, y, 6, ["FEED"])
                    if t.get("fertilizer_available"):
                        add_job(x, y, 5, ["COLLECT_FERTILIZER"])
                    if t.get("yield_units", 0) > 0:
                        add_job(x, y, 4.5, ["HARVEST"])
            elif kind == "PLANT":
                if not t["watered_today"]:
                    add_job(x, y, 4, ["WATER"])
                else:
                    crop = t["crop"]
                    age = day - t["planted_day"]
                    if CROPS[crop]["ongoing"]:
                        if t.get("yield_units", 0) > 0:
                            add_job(x, y, 4.5, ["HARVEST"])
                    elif age >= CROPS[crop]["max_yield_day"] and t.get("yield_units", 0) > 0:
                        add_job(x, y, 4.5, ["HARVEST"])
            elif kind == "WEED":
                add_job(x, y, 1, ["DIG"])

    for (x, y) in _STATE["planted_today"]:
        add_job(x, y, 4, ["WATER"])

    # Fertilize plants when we carry fertilizer (boost premium crops).
    fert_in_shed = shed.get("FERTILIZER", 0)
    if fert_in_shed > 0 and hour <= PLANT_CUTOFF_HOUR:
        for y in range(n):
            for x in range(n):
                t = board[y][x]
                if (isinstance(t, dict) and t.get("kind") == "PLANT"
                        and t.get("fertilized_until_day", -1) < day
                        and t["crop"] in ("STRAWBERRY", "MELON", "WHEAT")):
                    add_job(x, y, 2.5, ["FERTILIZE"])
                    break  # one fertilize job per turn is plenty

    # Build pastures only up to animals actually in the pipeline (bought or
    # placed) — don't squat on 14 tiles while planting is starved. The
    # champion scales pastures WITH animals and plants crops from day 0.
    if hour <= PLANT_CUTOFF_HOUR:
        pipeline_animals = (cows + sheep + shed.get("COW", 0) + shed.get("SHEEP", 0)
                            + sum((private["inventories"][i] or {}).get(a, 0)
                                  for i in range(num_units) for a in ("COW", "SHEEP")))
        want_pastures = min(TARGET_COWS + TARGET_SHEEP, pipeline_animals + 2)
        built_pastures = struct.get("PASTURE", 0)
        for y in range(n):
            for x in range(n):
                if board[y][x] is None and built_pastures < want_pastures:
                    add_job(x, y, 3, ["BUILD_PASTURE"])
                    built_pastures += 1

    # Plant crops (strawberry in window, melon in window, wheat always).
    if hour <= PLANT_CUTOFF_HOUR:
        def crop_for(x, y, idx):
            if STRAWBERRY_WINDOW[0] <= day <= STRAWBERRY_WINDOW[1]:
                return "STRAWBERRY"
            if MELON_WINDOW[0] <= day <= MELON_WINDOW[1] and idx % 2 == 0:
                return "MELON"
            return "WHEAT"

        plantable = [(x, y) for y in range(n) for x in range(n)
                     if board[y][x] is None and day + 4 <= SEASON_DAYS - 1]
        placed = {"WHEAT": 0, "MELON": 0, "STRAWBERRY": 0}
        for idx, (x, y) in enumerate(plantable):
            if (x, y) in _STATE["planted_today"]:
                continue
            crop = crop_for(x, y, idx)
            if placed[crop] >= seeds.get(crop, 0):
                crop = "WHEAT" if placed["WHEAT"] < seeds.get("WHEAT", 0) else None
            if crop is None:
                break
            add_job(x, y, 2, ["PLANT", crop])
            placed[crop] += 1

    # ------------------------------------------------------------------
    # 4. Assign units (sticky targets + reservation)
    # ------------------------------------------------------------------
    units = [("farmer", farmer_pos)] + [("hand", p) for p in hand_positions]

    def move_toward(pos, target):
        dx = target[0] - pos[0]
        dy = target[1] - pos[1]
        if abs(dx) >= abs(dy) and dx != 0:
            return ["EAST" if dx > 0 else "WEST"]
        if dy != 0:
            return ["SOUTH" if dy > 0 else "NORTH"]
        return ["PASS"]

    def nearest_job(pos, exclude):
        best = None
        best_key = None
        for key, (prio, action) in jobs.items():
            if key in exclude:
                continue
            d = _manhattan(pos, key)
            score = (prio, -d)
            if best is None or score > best:
                best = score
                best_key = key
        return best_key

    # How many units are needed for logistics (fetch & drop)? One at a time
    # is enough for most; scale with the workload. This stops every unit
    # from abandoning real work to stand at the shed.
    feed_jobs = sum(1 for v in jobs.values() if v[1][0] == "FEED")
    place_jobs = [k for k, v in jobs.items() if v[1][0] == "PLACE"]
    fetch_needed = min(3, max(0, feed_jobs - 1)) + (1 if place_jobs else 0)
    units_carrying = sum(1 for i in range(num_units)
                         if any((private["inventories"][i] or {}).get(a, 0) > 0
                                for a in ANIMALS))

    claimed = set()
    farmer_action = ["PASS"]
    hands_actions = []
    fetch_slots = fetch_needed

    for idx, (utype, pos) in enumerate(units):
        inv = private["inventories"][idx] or {}
        inv_size = sum(inv.values())

        # DROP logistics first.
        if inv_size >= DROP_THRESHOLD:
            if tuple(pos) in [tuple(t) for t in shed_tiles]:
                action = ["DROP"]
            else:
                action = move_toward(pos, min(shed_tiles, key=lambda s: _manhattan(pos, s)))
            if utype == "farmer":
                farmer_action = action
            else:
                hands_actions.append(action)
            continue

        # Carrying an animal? Its job is a matching empty structure — place
        # it, don't get distracted by feed/water jobs.
        carried_animal = next((a for a in ANIMALS if inv.get(a, 0) > 0), None)
        if carried_animal is not None:
            target_kind = ANIMALS[carried_animal]["structure"]
            # Any empty matching structure works, claimed or not — the
            # PLACE jobs may all be for the other animal type.
            empty_structs = [(x, y) for y in range(n) for x in range(n)
                             if isinstance(board[y][x], dict)
                             and board[y][x].get("kind") == target_kind
                             and "animal" not in board[y][x]
                             and (x, y) not in claimed]
            key = min(empty_structs, key=lambda k: _manhattan(pos, k)) if empty_structs else None
            if key is not None:
                claimed.add(key)
                if pos[0] == key[0] and pos[1] == key[1]:
                    action = ["PLACE", carried_animal]
                else:
                    action = move_toward(pos, key)
            elif tuple(pos) in [tuple(t) for t in shed_tiles]:
                # No empty structure for this animal right now: return it.
                action = ["DROP"]
            else:
                action = move_toward(pos, min(shed_tiles, key=lambda s: _manhattan(pos, s)))
            if utype == "farmer":
                farmer_action = action
            else:
                hands_actions.append(action)
            continue

        # FEED needs wheat in inventory. Only a few units do the fetching —
        # otherwise everyone abandons planting to queue at the shed.
        if (inv.get("WHEAT", 0) == 0 and feed_jobs > 0 and fetch_slots > 0):
            fetch_slots -= 1
            if tuple(pos) in [tuple(t) for t in shed_tiles]:
                action = ["PICKUP", "WHEAT", 3]
            else:
                action = move_toward(pos, min(shed_tiles, key=lambda s: _manhattan(pos, s)))
            if utype == "farmer":
                farmer_action = action
            else:
                hands_actions.append(action)
            continue

        # PLACE needs the animal in inventory: fetch from shed first.
        if place_jobs and inv.get("COW", 0) == 0 and inv.get("SHEEP", 0) == 0:
            want_animal = None
            for a in ("COW", "SHEEP", "GOOSE"):
                if shed.get(a, 0) > 0 and any(
                        jobs[k][1][1] == a for k in place_jobs):
                    want_animal = a
                    break
            if want_animal is not None and units_carrying < fetch_needed:
                units_carrying += 1
                if tuple(pos) in [tuple(t) for t in shed_tiles]:
                    action = ["PICKUP", want_animal, 1]
                else:
                    action = move_toward(pos, min(shed_tiles, key=lambda s: _manhattan(pos, s)))
                if utype == "farmer":
                    farmer_action = action
                else:
                    hands_actions.append(action)
                continue

        # Sticky target.
        target = _STATE.get("targets", {}).get(idx)
        if target is not None and tuple(target) in jobs and tuple(target) not in claimed:
            key = tuple(target)
            claimed.add(key)
            if pos[0] == key[0] and pos[1] == key[1]:
                action = jobs[key][1]
            else:
                action = move_toward(pos, key)
        else:
            _STATE.setdefault("targets", {}).pop(idx, None)
            key = nearest_job(pos, claimed)
            if key is None:
                action = ["PASS"]
            else:
                claimed.add(key)
                if pos[0] == key[0] and pos[1] == key[1]:
                    action = jobs[key][1]
                else:
                    action = move_toward(pos, key)
                _STATE.setdefault("targets", {})[idx] = list(key)

        if action[0] in ("WATER", "HARVEST", "DIG", "PLANT", "DROP", "FEED",
                         "COLLECT_FERTILIZER", "BUILD_COOP", "BUILD_PASTURE",
                         "PLACE", "FERTILIZE"):
            _STATE.setdefault("targets", {}).pop(idx, None)

        if utype == "farmer":
            farmer_action = action
            if action[0] == "PLANT":
                _STATE["planted_today"].add((pos[0], pos[1]))
        else:
            hands_actions.append(action)
            if action[0] == "PLANT":
                _STATE["planted_today"].add((pos[0], pos[1]))

    return {"farmer": farmer_action, "hands": hands_actions, "market": market_orders}
