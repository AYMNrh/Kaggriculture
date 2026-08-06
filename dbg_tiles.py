"""Check tiles structure."""
import main
from kaggle_environments import make
orig = main.agent
log = open("tiles_dbg.txt", "w")
def wrapped(obs):
    me = obs["farms"][obs["player"]]
    tiles = me["tiles"]
    log.write(f"day {obs.get('day')} tiles type={type(tiles)} len={len(tiles)}\n")
    if isinstance(tiles, list) and tiles and isinstance(tiles[0], list):
        log.write(f"rows={len(tiles)} cols={len(tiles[0])}\n")
    log.flush()
    return orig(obs)
env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 42}, debug=False)
env.run([wrapped, "pass"])
log.close()
print("done")
