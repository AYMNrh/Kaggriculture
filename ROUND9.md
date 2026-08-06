# Round 9: do the learning offline; adapt safely online

## Bottom line

Putting a generic RL learner inside `main.py` is mostly hype in this setting. The agent gets one 720-turn trajectory, the economically important choices happen only a few dozen times, their rewards arrive days later, and the process is discarded after the episode. A Q-table receiving 720 highly correlated transitions is not meaningfully trained; it is experimenting with a ladder game and forgetting the result.

The useful version of the idea is:

1. **optimize a small policy offline over many common seeds;**
2. embed the resulting constants or tiny lookup table in `main.py`; and
3. use observations online to select among those pre-trained choices and to close feedback loops around workload and prices.

That is an improving algorithm, but the improvement happens during development. During evaluation it should be a deterministic, state-adaptive policy, not an RL training run.

## Direct answers

### 1. In-episode RL is not a good fit

The nominal 720 samples are misleading. There are only 30 day boundaries, roughly 11 strawberry planting decisions, a handful of land/animal purchase decisions, and one terminal score. Adjacent hourly states are strongly correlated. The policy cannot try an alternative action and rewind the same seed, so it cannot obtain counterfactual rewards. The opponent and the learner's own sales also make price rewards non-stationary.

TD/Q-learning is particularly unsuitable:

- a useful state must include day, inventory, farm composition, crop ages, shop state, prices, opponent effects, and outstanding work, making one-episode visitation effectively unique;
- final money is delayed, while naive shaped rewards such as immediate cash reward selling too early and punish investment;
- exploration is expensive and irreversible: a bad hire ramp or missed planting window cannot be repaired later;
- learning-rate, exploration, and reward-shaping errors can destabilize already good safety invariants such as FEED, WATER, and the six-unit animal floor.

A bandit is only defensible if it chooses among two or three **safe, prevalidated macro-actions**, such as growth admission 4/5/6 for the next day. Even then there are too few comparable trials inside one changing season to identify the better arm. Do not use random exploration on the ladder. At most, an online learner could plausibly add a small tail improvement—roughly **$0 to $2k in favorable episodes**—by adjusting late crop admission or terminal liquidation. A negative average is more likely than a material gain if it is allowed to alter hiring, feeding, watering, or animal allocation.

The best online improvement is not RL. It is a feedback controller: admit more plants tomorrow only if today's mandatory WATER, FEED, and CARE completed early enough and useful actions per crop hand remained healthy; reduce admission when backlog or route length rises. That uses the episode's evidence without pretending it supplies repeated training examples.

### 2. Offline search plus an embedded policy is the right interpretation

Yes. The deterministic seed behavior is an advantage offline: use common random numbers, so every candidate sees the same seed panel, and compare paired score differences. Optimize final bank, not action-level proxy rewards. Use median or mean paired improvement with a lower-tail guard; a ladder policy should not buy a rare peak by creating feed or hydration failures.

Do not start with a high-dimensional neural policy or full offline RL. The current hand-built policy contains strong structure and safety knowledge. Search a small parameter vector around it with random search, successive halving, CMA-ES, or a simple evolutionary strategy. The useful parameters, in priority order, are:

1. **Field admission/capacity:** growth budget by phase, the previous-day completion threshold for raising it, crop-hand workload divisor, and minimum animal-unit floor. This controls the known volume bottleneck.
2. **Hire ramp:** target hands and start/end day for the strawberry ramp. Search it jointly with field admission because extra hands have little value if the plant cap does not use them, and extra plants are unsafe without labor.
3. **Crop mix and seed cash allocation:** strawberry quota, sparse early-melon slots, wheat reserve, and seed budget fractions, conditioned on remaining maturity time and observed demand regime.
4. **A few scheduling priorities:** only priority gaps that change ordering—urgent harvest versus CARE, BUILD versus WATER, and PLANT versus WATER. Searching every numeric priority independently wastes trials because most values produce the same ordering.
5. **Sell timing:** last. Earlier tests already showed that broad milk/wool holding destroys reinvestment and collapsed performance. Restrict this search to small, late, capped holds after capital spending has ended.

The embedded result can be constants, a day-phase table, or a tiny decision tree keyed by observations. It does not need to look like an RL model to capture offline learning.

### 3. Highest-value in-episode adaptations

The highest-value adaptation overall is **capacity feedback**, even though it does not use shops: replace the fixed `3/6/4` growth schedule with a bounded controller. Keep FEED/WATER safety hard-coded. Raise the next day's admission cap by one only after a clean service day; lower it by one after missed mandatory work, late completion, or falling useful-actions-per-worker. Clamp it to an offline-tested range. This directly targets the measured crop-volume bottleneck and reacts to seed-specific congestion.

Of adaptations specifically using `town.unlocked_shops` and `market.prices`, the best two are:

1. **Demand-conditioned crop admission, not wholesale farm switching.** Treat an unlocked shop as a leading indicator of future demand and the current price/slope as confirmation. At each new plant slot, compare offline-estimated remaining-season marginal value for the crops that can still mature. Tilt only the flexible slots; preserve feed wheat and the proven strawberry core. A shop signal matters most before an irreversible seed/plant decision. It should not cause existing fields or the animal engine to be rebuilt.
2. **Late, capped liquidation timing.** Track an exponential or four-turn price slope in `_STATE`. Only after the last productive reinvestment window, hold a small amount of a premium good when its price is rising and no cash-funded purchase is pending, then force liquidation with a generous safety margin before episode end. Never hold fertilizer; never hold feed wheat below the remaining feed requirement; never let holding block hires, land, animals, or strawberry seeds.

“Reduce sales when glutting” is just the second rule viewed through price impact. It is unsafe as a general rule because current sales fund compounding and the ten-order queue is finite. “Hold every rising good” repeats the already failed $42k-style price-holding experiment. The gate must be late, cash-aware, and capped.

Also, do not double-count shop information. If unlocking a shop immediately changes demand and that effect is already visible in the current price and slope, price is the better sufficient signal. Shops add value only insofar as they predict demand that has not yet appeared fully in the quote. Establish this offline by measuring conditional future price paths after each unlock.

### 4. Cross-episode persistence is definitively out

Under the stated evaluation constraints, there is no legal or reliable cross-game learning channel. Python globals such as `_STATE` persist only within the current process/episode. The filesystem is reset, network ingress/egress is forbidden, and a fresh sandbox process removes memory state. Environment variables, caches, filenames, timing, opponent signaling, or attempted external calls are not legitimate substitutes.

What is legal is **development-time learning embedded in the submitted source**: fixed weights, thresholds, tables, or generated decision-tree code computed offline before submission. The policy may also remember observations earlier in the same episode in `_STATE`. It cannot update the submitted source or carry those updates to the next ladder game.

### 5. With 50–100k environment steps, tune field admission

The single highest-value target is the **days 8–14 growth/admission cap**, evaluated together with its safety backoff rule. This is the current fixed `growth_budget = 6` region and directly governs how many premium plants enter the field during the short strawberry window. It has more upside than sell timing and much denser evidence than changing the entire hire policy.

Fifty to one hundred thousand steps are only about **69–139 full episodes**, so this is not enough for broad RL or a large evolutionary vector. Use the budget as a paired, low-dimensional racing experiment:

- candidates: mid-window caps 4, 5, 6, 7, and optionally an adaptive cap in `[4, 7]`;
- adaptive gate: raise only after all mandatory FEED/WATER completed and crop-hand useful-action or completion-hour thresholds were met; otherwise hold or reduce;
- first stage: 5–8 common seeds per candidate;
- second stage: spend the remaining episodes on the best two candidates over fresh common seeds plus the established tail seeds;
- score: paired final-money delta, rejecting any candidate with animal escape, hydration death, or material milk/wool regression.

If one extra dimension is affordable, search the day-11-to-14 hire target jointly as a binary choice, current versus one fewer/more. Do not spend this compute tuning sell thresholds: prior evidence says the gap is production volume, and a few dollars of price improvement on a bounded inventory cannot compete with several additional productive strawberries.

## Concrete recommendation

Do **not** add Q-learning, TD learning, or exploratory bandits to the submitted agent. First implement an offline harness that evaluates small parameterized variants on identical seeds. Tune the strawberry-window admission controller, embed the winner, and then add deterministic shop/price conditioning only after an ablation proves that shop unlocks predict future price beyond the quote itself.

For an “agent that improves during the game,” use two transparent pieces of episode memory: yesterday's service/capacity metrics and recent price slopes. They are cheap, legal, explainable, and much less likely to damage a 104–108k policy than a learner trying to infer long-horizon value from its only game.
