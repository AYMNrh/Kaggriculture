"""Trace geese v2: daily money, coops, geese, shed contents."""
from kaggle_environments import make
from experiment_geese import geese_agent

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([geese_agent, "pass"])

last_day = -1
for step in env.steps:
    o = step[0].observation
    if o.day != last_day:
        last_day = o.day
        farm = o.farms[0]
        priv = o.private
        coops = geese = 0
        for row in farm["tiles"]:
            for t in row:
                if isinstance(t, dict) and t.get("kind") == "COOP":
                    coops += 1
                    if "animal" in t:
                        geese += 1
        shed = dict(priv["shed"])
        print(f"day {o.day:2d} | money ${farm['money']:7,.0f} | coops {coops:3d} geese {geese:3d} "
              f"| shed {shed} | Wprice {o.market['prices'].get('WHEAT')} Eprice {o.market['prices'].get('EGG')} Fprice {o.market['prices'].get('FERTILIZER')}")
    if o.day >= 20:
        break
final = env.steps[-1]
print("FINAL:", [(s.reward, s.status) for s in final])
