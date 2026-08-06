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
HIRE_TARGETS = [(0, 5), (4, 6), (8, 9), (11, 10), (14, 11), (18, 12), (22, 14)]  # champion ramp
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


def _hire_cost(n_already_today):
    """fib cost: 1,1,2,3,5,8... indexed from n=0."""
    a, b = 1, 1
    for _ in range(n_already_today):
        a, b = b, a + b
    return a


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
    # 2. Market orders — cash-flow discipline + champion-scale production
    # ------------------------------------------------------------------
    market_orders = []

    # 2a. SELL everything except a feed-wheat reserve. The champion sells
    # 190 wheat/season (43 by day 8!) — wheat is the early cash engine that
    # Sell grown wheat aggressively — the champion treats it as CASH and
    # BUYS feed wheat as needed (day 5: sells 40 wheat, then buys 1-2
    # wheat/hour for the herd). Reserve only what today's herd needs
    # (1 wheat/animal/day), NOT a big hoard: the champion's day-5 income
    # (40 wheat ≈ $1,500) funds NE land day 7 + the animal ramp. Hoarding
    # grown wheat starves the cash engine.
    pipeline_animals = (total_animals + shed.get("COW", 0) + shed.get("SHEEP", 0)
                        + sum((private["inventories"][i] or {}).get(a, 0)
                              for i in range(num_units) for a in ("COW", "SHEEP")))
    wheat_reserve = max(10, pipeline_animals)
    for item, qty in shed.items():
        if qty <= 0 or len(market_orders) >= MAX_MARKET_ORDERS:
            continue
        if item == "WHEAT":
            surplus = qty - wheat_reserve
            if surplus > 0:
                market_orders.append(["SELL", "WHEAT", min(surplus, 20)])
        elif item in ("GOOSE", "COW", "SHEEP"):
            continue  # never sell animals
        else:
            market_orders.append(["SELL", item, qty])

    # ---- cash budget for the turn ----
    # The champion spends to near-zero for the first ~10 days, reinvesting
    # everything into animals/land/seeds, then compounds hard. Sells are
    # queued FIRST and fund the buys later in the same market list, so the
    # effective budget is cash + what this turn's sells will actually bring
    # in. sell_value mirrors the sell loop EXACTLY (surplus wheat only,
    # never the feed reserve, never animals) so the budget never counts
    # phantom income. Keep only a tiny emergency buffer.
    sell_value = 0
    for item, qty in shed.items():
        if qty <= 0 or item in ("GOOSE", "COW", "SHEEP"):
            continue
        if item == "WHEAT":
            surplus = qty - WHEAT_FEED_RESERVE - total_animals
            qty = max(0, surplus)
        sell_value += qty * obs["market"]["prices"].get(item, 0)
    op_buffer = 60
    investable = money + 0.6 * sell_value - op_buffer

    # 2b. Hire hands — the champion front-loads labor: 5 hands day 0
    # ($12/day), 7 day 1, 9 day 2, 12 day 3, 14 by day 4-5 ($376-986/day).
    # Hands are CHEAP early; the capacity pays for itself via more crops
    # watered/planted + animals fed/cared/collected. Front-loading is what
    # lets the champion do 18 PLANT + 27 WATER day 0-1 while also building
    # 4 pastures. The cash gate (`money >= next hire cost`) prevents
    # bankrupting the ramp.
    #
    # IMPORTANT: spread hires across the DAY (max 3-4/turn) instead of
    # dumping them all at hour 0. The champion hires 2-3 per hour over
    # hours 1-9. Hiring all at h0 eats the 10-order market cap and blocks
    # sells/seeds/animals for the rest of the day.
    target_hands = HIRE_TARGETS[0][1]
    for d, nh in HIRE_TARGETS:
        if day >= d:
            target_hands = nh
    hires_today = me.get("hires_today", 0)
    hire_budget = 3  # max hires this turn; spread across the day
    while (len(market_orders) < MAX_MARKET_ORDERS
           and hires_today < target_hands
           and hire_budget > 0
           and investable >= _hire_cost(hires_today)):
        market_orders.append(["HIRE"])
        hires_today += 1
        hire_budget -= 1

    # 2c. Buy animals: 8 cows + 6 sheep, ALL-IN day 0 (champion opening),
    # then top up in SPARSE BURSTS. The champion buys animals on only ~6
    # days (d0: 3c+1s, d5: 1c+1s, d7: 1c, d8: 3s, d9: 1c, d11: 2c) with
    # 2-5 days between, letting cash accumulate to $700-2,300 per burst.
    # Buying 1 cow EVERY hour money allows keeps the agent permanently
    # broke — it can never save for the big purchases or land.
    #
    # Land FIRST: NE day ~7, SW day ~10. 25 locked tiles cap planting at
    # ~4/day — premium crops (strawberry/melon = $100k+ for the champion)
    # need the unlocked space. Reserve cash for land before animal buys.
    cows = animals.get("COW", 0)
    sheep = animals.get("SHEEP", 0)
    cows_in_pipeline = cows + shed.get("COW", 0) + sum(
        (private["inventories"][i] or {}).get("COW", 0) for i in range(num_units))
    sheep_in_pipeline = sheep + shed.get("SHEEP", 0) + sum(
        (private["inventories"][i] or {}).get("SHEEP", 0) for i in range(num_units))

    if day == 0 and hour == 0:
        # Champion opening: 3 cows + 1 sheep + melon/wheat seeds + feed
        # wheat + hires in one turn. Spend down to ~$200, never further.
        opening = [["BUY_ANIMAL", "COW", 3], ["BUY_ANIMAL", "SHEEP", 1]]
        if money > 800:
            opening.append(["BUY_SEED", "MELON", 7])
        if money > 500:
            opening.append(["BUY_SEED", "WHEAT", 10])
        if money > 500:
            opening.append(["BUY_PRODUCT", "WHEAT", 12])
        for o in opening:
            if len(market_orders) < MAX_MARKET_ORDERS:
                market_orders.append(o)
    elif hour == 0 and day >= 2:
        # ONE burst per day, only when genuinely flush. Champion buys at
        # money $700-2,300; cows first, sheep after cows fill.
        if (cows_in_pipeline < TARGET_COWS
                and investable > ANIMALS["COW"]["cost"] + 250):
            n_cows = 2 if investable > 2 * ANIMALS["COW"]["cost"] + 600 else 1
            market_orders.append(["BUY_ANIMAL", "COW", n_cows])
            investable -= ANIMALS["COW"]["cost"] * n_cows
        elif (sheep_in_pipeline < TARGET_SHEEP
                and investable > ANIMALS["SHEEP"]["cost"] + 250):
            n_sheep = 2 if investable > 2 * ANIMALS["SHEEP"]["cost"] + 700 else 1
            market_orders.append(["BUY_ANIMAL", "SHEEP", n_sheep])
            investable -= ANIMALS["SHEEP"]["cost"] * n_sheep
        # Once cows are full, keep topping sheep.
        if (len(market_orders) < MAX_MARKET_ORDERS
                and cows_in_pipeline >= TARGET_COWS
                and sheep_in_pipeline < TARGET_SHEEP
                and investable > ANIMALS["SHEEP"]["cost"] + 250):
            market_orders.append(["BUY_ANIMAL", "SHEEP", 1])
            investable -= ANIMALS["SHEEP"]["cost"]

    # 2d. Feed wheat: buy ONLY in a true emergency (shed wheat below the
    # herd's daily need). Growing wheat is 3-5x cheaper than buying it —
    # the champion buys just 275/season and grows 67 plants. Buying 5/day
    # at $30-40 was draining the entire fertilizer income stream.
    feed_gap = total_animals - shed.get("WHEAT", 0)
    if (len(market_orders) < MAX_MARKET_ORDERS and feed_gap > 0
            and investable > 100 and day < 28):
        n_feed = min(feed_gap, 4)
        market_orders.append(["BUY_PRODUCT", "WHEAT", n_feed])
        investable -= n_feed * obs["market"]["prices"].get("WHEAT", 30)

    # 2e. Seeds — buy in BURSTS (champion: strawberry 2-7/day on ~9 days,
    # melon 1-5, wheat 1-6; totals 41/26/67). Strawberry is TIME-CRITICAL
    # (window days 4-14, price $120->$312): its buying gate must be LOW so
    # seeds get bought even with modest cash. Melon/wheat gate on money.
    def buy_seed(crop, target_stock, want_per_buy, max_pct=0.5):
        nonlocal investable
        if len(market_orders) >= MAX_MARKET_ORDERS:
            return
        stock = seeds.get(crop, 0)
        want = min(want_per_buy, max(0, target_stock - stock))
        if want <= 0 or investable <= 0:
            return
        cost = CROPS[crop]["seed"]
        # never spend more than max_pct of remaining budget on seeds this turn
        affordable = min(want, investable // cost,
                         max(1, int(investable * max_pct) // cost))
        if affordable > 0:
            market_orders.append(["BUY_SEED", crop, affordable])
            investable -= affordable * cost

    if hour == 0 and day > 0 and investable > 50:
        if STRAWBERRY_WINDOW[0] <= day <= STRAWBERRY_WINDOW[1]:
            buy_seed("STRAWBERRY", 41, 3, 0.3)   # champion volume: 41 total
    if hour == 0 and day > 0 and money > 250:
        if MELON_WINDOW[0] <= day <= MELON_WINDOW[1]:
            buy_seed("MELON", 26, 4, 0.3)        # champion: 26 total (replant)
        # Wheat target scales with the field: champion grows 67 for feed
        # + cash as the farm expands to 50+ plants.
        buy_seed("WHEAT", 60, 6, 0.4)

    # 2f. Land: NE ~day 7, SW ~day 10. NEVER SE — the champion never buys
    # it ($4k for tiles that don't pay back; NW+NE+SW = 75 tiles suffice).
    # Gate on investable (cash + this turn's sells), so wheat sales fund it.
    if len(market_orders) < MAX_MARKET_ORDERS:
        for q in ("NE", "SW"):
            if q not in me["unlocked_quadrants"]:
                if investable > LAND_PRICES[q]:
                    market_orders.append(["BUY_LAND"])
                    investable -= LAND_PRICES[q]
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

    board_h = len(board)
    board_w = len(board[0]) if board_h else 0
    for y in range(board_h):
        for x in range(board_w):
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
                    # CARE doubles milk/wool/egg production: each fed+cared
                    # day banks +1 bonus, consumed on the next production
                    # day. The champion cares every animal daily — this is
                    # a free 2x on the highest-value products.
                    if not t.get("cared_today"):
                        add_job(x, y, 5.5, ["CARE"])
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

    # Fertilize premium crops. Codex finding (replay 90219149): the
    # champion's ANIMAL units collect fertilizer and apply it directly to
    # nearby crops as a continuation of their route (day 11 unit 7,
    # day 12 units 3/9, day 13 unit 4) — no shed round trip. FERTILIZE
    # marks coverage through day+2 (3 days, kaggriculture.py:419-425) and
    # accelerates toward the fixed max_yield cap; its value is early cash
    # + rescuing late plantings, not a blanket 2x.
    # NOTE: FERTILIZE is applied ONLY via the carry-fert idle filler in
    # the assignment loop (animal hand that already carries fert applies
    # it when no animal chores remain). We do NOT create FERTILIZE jobs
    # here — a hand picking the job without carrying fert would fail
    # silently (the action consumes from inventory).

    # Build pastures only up to animals actually in the pipeline (bought or
    # placed) — don't squat on 14 tiles while planting is starved. The
    # champion scales pastures WITH animals and plants crops from day 0.
    # BUILD NEAR THE SHED: animals need 3+ trips/day (feed/collect/harvest),
    # crops only 1 (water). Proximity to the shed is worth more for animals.
    if hour <= PLANT_CUTOFF_HOUR:
        # Build pastures to house the pipeline (placed + shed + carried).
        # When animals are WAITING in the shed with no home, building is
        # the top job (above water) — animals are the money engine. When
        # all animals are housed, planting/watering wins.
        pipeline_animals = (cows + sheep + shed.get("COW", 0) + shed.get("SHEEP", 0)
                            + sum((private["inventories"][i] or {}).get(a, 0)
                                  for i in range(num_units) for a in ("COW", "SHEEP")))
        want_pastures = min(TARGET_COWS + TARGET_SHEEP, pipeline_animals)
        built_pastures = struct.get("PASTURE", 0)
        empty_pastures = built_pastures - cows - sheep
        shortage = max(0, want_pastures - built_pastures)
        build_budget = min(4, shortage)
        # Animals waiting -> build beats WATER(4)/CARE(5.5)/FEED(6 is still
        # top since feeding existing animals matters more).
        build_prio = 6.5 if shortage > 0 else 3.0
        empty_cells = [(x, y) for y in range(n) for x in range(n)
                       if board[y][x] is None]
        empty_cells.sort(key=lambda c: min(_manhattan(c, s) for s in shed_tiles))
        for (x, y) in empty_cells:
            if built_pastures < want_pastures and build_budget > 0:
                add_job(x, y, build_prio, ["BUILD_PASTURE"])
                built_pastures += 1
                build_budget -= 1

    # Plant crops (strawberry in window, melon in window, wheat always).
    # Champion mix: ~67 wheat + 41 strawberry (days 4-14) + 26 melon
    # (days 0-17) — INTERLEAVED, not all-one-crop. During the strawberry
    # window ~50% strawberry / 30% melon / 20% wheat; before it, melon/
    # wheat; after it, wheat/melon.
    if hour <= PLANT_CUTOFF_HOUR:
        def crop_for(x, y, idx):
            if STRAWBERRY_WINDOW[0] <= day <= STRAWBERRY_WINDOW[1]:
                # Strawberry is the champion's #1 income (267 sold @ $120-312).
                # During its window, plant 80% strawberry, 20% melon/wheat.
                r = idx % 10
                if r < 8:
                    return "STRAWBERRY"
                if r < 9:
                    return "MELON"
                return "WHEAT"
            if MELON_WINDOW[0] <= day <= MELON_WINDOW[1]:
                return "MELON" if idx % 3 < 2 else "WHEAT"
            return "WHEAT"

        plantable = [(x, y) for y in range(n) for x in range(n)
                     if board[y][x] is None and day + 4 <= SEASON_DAYS - 1]
        placed = {"WHEAT": 0, "MELON": 0, "STRAWBERRY": 0}
        # Before the strawberry window (days 4-14), RESERVE ~10 tiles for
        # strawberries. The NW quadrant is only 25 tiles; over-planting
        # wheat/melon (19 plants) fills it and strawberries have nowhere
        # to go when their window opens — the champion plants ~16 crops
        # days 0-3 and keeps room for the #1 income crop. Count existing
        # plants + this turn's placements.
        if day < STRAWBERRY_WINDOW[0]:
            max_early = 19  # champion has 19 plants by day 4
        else:
            max_early = 999
        # BOUNDED COMPACT-FRONTIER PLANTING (Codex round 3 #2): admit at
        # most growth_budget new plants/day, ranked by adjacency to the
        # existing field (dense carpet = short walks). Each admitted
        # PLANT creates a same-day WATER obligation — the planted_today
        # loop below covers it. The old loop emitted jobs for EVERY free
        # tile (scattered field, long walks, no growth pressure).
        growth_budget = 3 if day <= 7 else 4  # champion plants 8-14 late, but
        # only after the field is established; early growth must not
        # outrun watering capacity
        plant_positions = [(x, y) for y in range(n) for x in range(n)
                           if isinstance(board[y][x], dict)
                           and board[y][x].get("kind") == "PLANT"]
        if plant_positions:
            plantable.sort(key=lambda c: -sum(1 for p in plant_positions
                                              if _manhattan(c, p) == 1))
        admitted = 0
        for idx, (x, y) in enumerate(plantable):
            if (x, y) in _STATE["planted_today"]:
                continue
            total_plants = plants + sum(placed.values())
            if total_plants >= max_early:
                break
            if admitted >= growth_budget:
                break
            crop = crop_for(x, y, idx)
            if placed[crop] >= seeds.get(crop, 0):
                # fall back to the next crop with seeds left
                for alt in ("WHEAT", "MELON", "STRAWBERRY"):
                    if placed[alt] < seeds.get(alt, 0):
                        crop = alt
                        break
                else:
                    crop = None
            if crop is None:
                break
            add_job(x, y, 3.2, ["PLANT", crop])
            placed[crop] += 1
            admitted += 1

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
            # Distance-weighted: a PLANT 1 tile away (3.2*10-1=31) beats a
            # WATER 12 tiles away (4.0*10-12=28). Priority alone made hands
            # walk across the map for marginally-higher-prio jobs, wasting
            # 5-7 hours per action — the champion works locally.
            score = prio * 10 - d
            if best is None or score > best:
                best = score
                best_key = key
        return best_key

    # How many units are needed for logistics (fetch & drop)? ONE or TWO
    # dedicated fetchers is enough: each carries 3 wheat = 3 feeds, cycles
    # a few times/day = 12-18 feeds/day from 2 fetchers, covering 14
    # animals. Every extra fetcher is a hand NOT planting/watering — the
    # crop die-off was caused by 6 units queueing at the shed all day.
    feed_jobs = sum(1 for v in jobs.values() if v[1][0] == "FEED")
    place_jobs = [k for k, v in jobs.items() if v[1][0] == "PLACE"]
    fetch_needed = min(2, max(1, (feed_jobs + 5) // 6)) + (1 if place_jobs else 0)
    units_carrying = sum(1 for i in range(num_units)
                         if any((private["inventories"][i] or {}).get(a, 0) > 0
                                for a in ANIMALS))

    # ROLE SPLIT: dedicate the LAST N hands to crops (WATER/PLANT/DIG/
    # HARVEST on plants). Animal chores (FEED/CARE/COLLECT at prio 5-6)
    # would otherwise hog every unit and plants die — the champion waters
    # 39-41/day while feeding 14 animals by having hands for both. Crop
    # ROLE SPLIT (proven): crop hands (WATER/PLANT/DIG/HARVEST-on-plants)
    # NEVER take animal chores (FEED/CARE/COLLECT at prio 5-6) — those
    # hog every unit and plants die. Animal hands take animal jobs first,
    # then spill into crops when the herd is done.
    crop_ops = {"WATER", "PLANT", "DIG"}
    crop_work = {}
    animal_work = {}
    for k, (prio, action) in jobs.items():
        op = action[0]
        if op in crop_ops:
            crop_work[k] = [prio, action]
        elif op == "HARVEST":
            tile = board[k[1]][k[0]]
            is_plant = (isinstance(tile, dict) and tile.get("kind") == "PLANT")
            (crop_work if is_plant else animal_work)[k] = [prio, action]
        else:
            animal_work[k] = [prio, action]

    plantable_count = sum(1 for y in range(n) for x in range(n)
                          if board[y][x] is None and day + 4 <= SEASON_DAYS - 1)
    crop_workload = plants + max(0, min(plantable_count, 20))
    n_crop_hands = max(1, min(num_units - 2, (crop_workload + 5) // 7))
    # Farmer (unit 0) is ALWAYS an animal unit — primary feed/place/collect
    # worker. Without the floor it flips crop<->animal across the day.
    animal_unit_count = max(1, num_units - n_crop_hands)

    claimed = set()
    farmer_action = ["PASS"]
    hands_actions = []
    fetch_slots = fetch_needed
    fert_fetch_slots = 1  # only ONE hand fetches fertilizer per turn

    # Iterate CROP units FIRST: they must claim their jobs before the
    # animal hands' "spill into crops" fallback steals them. Unit idx maps
    # to the action lists — crop units are the LAST n_crop_hands, so build
    # an ordered list of indices with crops first. Hands actions must be
    # stored by unit index (hands[0] <-> idx 1), NOT append order.
    #
    # Within the crop role, the FIRST crop unit is the PLANTER (boosts
    # PLANT priority) and the rest are WATERERS (boost WATER) — this
    # mirrors the champion's day-4 mix of 26 water + 9 plant actions:
    # dedicated planters keep the field growing while waterers keep
    # everything alive.
    def set_hand_action(idx, action):
        hand_idx = idx - 1  # units[0] is farmer, hands[0] is idx 1
        while len(hands_actions) <= hand_idx:
            hands_actions.append(["PASS"])
        hands_actions[hand_idx] = action

    def job_prio_for(k, is_planter):
        """Role-adjusted priority (planter boost DISABLED — reverts the
        milk/wool crash: boosting PLANT for one hand still grew plants,
        which inflated the crop-hand count and starved the herd)."""
        prio, action = jobs[k]
        return prio, action

    unit_order = (list(range(animal_unit_count, num_units))
                  + list(range(animal_unit_count)))
    for order_idx, idx in enumerate(unit_order):
        utype, pos = units[idx]
        is_crop_unit = idx >= animal_unit_count
        is_planter = is_crop_unit and idx == animal_unit_count
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
                set_hand_action(idx, action)
            continue

        # CARRY-FERTILIZER continuation DISABLED (v1 regressed: it fired
        # BEFORE animal job selection, so hands carrying fert diverted to
        # fertilize instead of feeding — milk 247->168, wool 104->64).
        # Re-enable only as a post-animal-chores idle filler (see the
        # job-pick fallback below), not a pre-emptive branch.

        # Carrying an animal? Its job is a matching empty structure — place
        # it, don't get distracted by feed/water jobs. (Animal units only.)
        carried_animal = next((a for a in ANIMALS if inv.get(a, 0) > 0), None)
        if carried_animal is not None and not is_crop_unit:
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
                set_hand_action(idx, action)
            continue

        # FEED needs wheat in inventory. Only the fetch_needed ANIMAL units
        # do the fetching — crop hands never queue at the shed.
        if (not is_crop_unit and inv.get("WHEAT", 0) == 0
                and feed_jobs > 0 and fetch_slots > 0):
            fetch_slots -= 1
            if tuple(pos) in [tuple(t) for t in shed_tiles]:
                action = ["PICKUP", "WHEAT", 3]
            else:
                action = move_toward(pos, min(shed_tiles, key=lambda s: _manhattan(pos, s)))
            if utype == "farmer":
                farmer_action = action
            else:
                set_hand_action(idx, action)
            continue

        # PLACE needs the animal in inventory: fetch from shed first.
        if (not is_crop_unit and place_jobs
                and inv.get("COW", 0) == 0 and inv.get("SHEEP", 0) == 0):
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
                    set_hand_action(idx, action)
                continue

        # Sticky target: keep it UNLESS the job is gone or executed — but a
        # crop unit never sticks to an animal job (and vice versa).
        target = _STATE.get("targets", {}).get(idx)
        if target is not None:
            tkey = tuple(target)
            in_pool = (tkey in crop_work) if is_crop_unit else (tkey in animal_work)
            if in_pool and tkey in jobs and tkey not in claimed:
                key = tkey
                claimed.add(key)
                if pos[0] == key[0] and pos[1] == key[1]:
                    action = jobs[key][1]
                else:
                    action = move_toward(pos, key)
            else:
                _STATE.setdefault("targets", {}).pop(idx, None)
                pool = crop_work if is_crop_unit else animal_work
                key = None
                best = None
                best_key = None
                for k in pool:
                    if k in claimed:
                        continue
                    prio, _ = job_prio_for(k, is_planter)
                    d = _manhattan(pos, k)
                    score = (prio, -d)
                    if best is None or score > best:
                        best = score
                        best_key = k
                if best_key is None and not is_crop_unit:
                    # Animal hand idle: carry-fert apply takes priority
                    # over crop watering — the champion's route
                    # continuation (collect->apply in one loop), and the
                    # fertilizer is already in hand (no shed trip). Set
                    # key+action DIRECTLY (the tile is not a jobs entry).
                    if inv.get("FERTILIZER", 0) > 0 and day >= 20:
                        # LATE-GAME ONLY: fert is cheap (~$20) after day 20
                        # and strawberry prices peak ($300+) — the
                        # champion's fertilize volume explodes days 21-28.
                        # Early fert ($100+) is worth more sold.
                        fert_targets = [(x, y) for y in range(n) for x in range(n)
                                        if isinstance(board[y][x], dict)
                                        and board[y][x].get("kind") == "PLANT"
                                        and board[y][x].get("fertilized_until_day", -1) < day
                                        and board[y][x]["crop"] in ("STRAWBERRY", "MELON")
                                        and (x, y) not in claimed]
                        if fert_targets:
                            fk = min(fert_targets, key=lambda k: _manhattan(pos, k))
                            claimed.add(fk)
                            if pos[0] == fk[0] and pos[1] == fk[1]:
                                action = ["FERTILIZE"]
                            else:
                                action = move_toward(pos, fk)
                            _STATE.setdefault("targets", {})[idx] = list(fk)
                            if utype == "farmer":
                                farmer_action = action
                            else:
                                set_hand_action(idx, action)
                            continue
                    for k in crop_work:
                        if k in claimed:
                            continue
                        prio, _ = job_prio_for(k, False)
                        d = _manhattan(pos, k)
                        score = (prio, -d)
                        if best is None or score > best:
                            best = score
                            best_key = k
                key = best_key
                if key is None:
                    action = ["PASS"]
                else:
                    claimed.add(key)
                    if pos[0] == key[0] and pos[1] == key[1]:
                        action = jobs[key][1]
                    else:
                        action = move_toward(pos, key)
                    _STATE.setdefault("targets", {})[idx] = list(key)
        else:
            _STATE.setdefault("targets", {}).pop(idx, None)
            pool = crop_work if is_crop_unit else animal_work
            key = None
            best = None
            best_key = None
            for k in pool:
                if k in claimed:
                    continue
                prio, _ = job_prio_for(k, is_planter)
                d = _manhattan(pos, k)
                score = (prio, -d)
                if best is None or score > best:
                    best = score
                    best_key = k
            if best_key is None and not is_crop_unit:
                # Animal hand idle: carry-fert apply takes priority
                # over crop watering — the champion's route
                # continuation (collect->apply in one loop), and the
                # fertilizer is already in hand (no shed trip). Set
                # key+action DIRECTLY (the tile is not a jobs entry).
                if inv.get("FERTILIZER", 0) > 0 and day >= 20:
                    # LATE-GAME ONLY: fert is cheap (~$20) after day 20
                    # and strawberry prices peak ($300+) — the champion's
                    # fertilize volume explodes days 21-28. Early fert
                    # ($100+) is worth more sold.
                    fert_targets = [(x, y) for y in range(n) for x in range(n)
                                    if isinstance(board[y][x], dict)
                                    and board[y][x].get("kind") == "PLANT"
                                    and board[y][x].get("fertilized_until_day", -1) < day
                                    and board[y][x]["crop"] in ("STRAWBERRY", "MELON")
                                    and (x, y) not in claimed]
                    if fert_targets:
                        fk = min(fert_targets, key=lambda k: _manhattan(pos, k))
                        claimed.add(fk)
                        if pos[0] == fk[0] and pos[1] == fk[1]:
                            action = ["FERTILIZE"]
                        else:
                            action = move_toward(pos, fk)
                        _STATE.setdefault("targets", {})[idx] = list(fk)
                        if utype == "farmer":
                            farmer_action = action
                        else:
                            set_hand_action(idx, action)
                        continue
                for k in crop_work:
                    if k in claimed:
                        continue
                    prio, _ = job_prio_for(k, False)
                    d = _manhattan(pos, k)
                    score = (prio, -d)
                    if best is None or score > best:
                        best = score
                        best_key = k
            key = best_key
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
            hand_idx = idx - 1  # units[0] is farmer, hands[0] is idx 1
            while len(hands_actions) <= hand_idx:
                hands_actions.append(["PASS"])
            hands_actions[hand_idx] = action
            if action[0] == "PLANT":
                _STATE["planted_today"].add((pos[0], pos[1]))

    return {"farmer": farmer_action, "hands": hands_actions, "market": market_orders}
