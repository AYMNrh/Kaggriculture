"""Peak watcher for Kaggriculture: runs episodes, tracks the best final
amount, and pings Telegram when a NEW PEAK appears. Sends ONLY the amount.

Game-theory note: Kaggriculture's market is a shared-price economy — every
agent's sells move the price. The champion ("StopPlantingStartGameTheorying")
wins by exploiting the price curves (sell early when YOUR volume can push
price up, hold scarce goods, avoid glut products). Peak-tracking across many
seeds finds the best price-realization the agent can achieve.

Usage:
  python peak_watch.py [--episodes N] [--send] [--tag "note"]
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(HERE, "peak_state.json")
BOT_TOKEN = "8578605928:AAGBhcahVB5ejfeI4NyOSjAMxYEYtdH4M5o"
CHAT_ID = "1534029247"
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"best": 0, "best_seed": None, "hits": 0, "history": []}


def save_state(st):
    with open(STATE_FILE, "w") as f:
        json.dump(st, f, indent=1)


def telegram(msg):
    data = json.dumps({"chat_id": CHAT_ID, "text": msg}).encode()
    req = urllib.request.Request(TELEGRAM_URL, data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status
    except Exception as e:
        print(f"[telegram failed] {e}")
        return None


def run_episodes(n):
    """Run n episodes of main.py vs pass, return list of (final_amount, seed_index).
    Seeds span a WIDE range (500-1599) — the peak tail is spread across seed
    families (verified: $108k at seed 551, $105k at seed 1008). Sampling one
    narrow range misses the real best."""
    results = []
    for i in range(n):
        seed = 500 + ((i * 37) % 1100)  # spread across 500-1599
        env_code = f"""
from kaggle_environments import make
import json
env = make('kaggriculture', configuration={{'episodeSteps': 720, 'seed': {seed}}}, debug=False)
env.run(['main.py', 'pass'])
reward = env.steps[-1][0].reward
print(json.dumps({{'reward': reward, 'seed': {seed}}}))
"""
        try:
            out = subprocess.run(
                [sys.executable, "-c", env_code],
                capture_output=True, text=True, timeout=300,
                cwd=HERE,
            ).stdout.strip().splitlines()
            for line in out:
                line = line.strip()
                if line.startswith("{") and "reward" in line:
                    d = json.loads(line)
                    results.append((float(d["reward"]), d["seed"]))
        except Exception as e:
            print(f"[ep {i} failed] {e}")
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=10)
    ap.add_argument("--send", action="store_true", help="actually send telegram")
    ap.add_argument("--report", action="store_true",
                    help="cron mode: print ONLY the new peak amount (silent otherwise)")
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    st = load_state()
    results = run_episodes(args.episodes)
    if not results:
        print("no results")
        sys.exit(1)

    best_this_run = max(results)
    amount, seed = best_this_run
    amounts = [a for a, _ in results]
    avg = sum(amounts) / len(amounts)
    new_peak = amount > st["best"]

    print(f"run: n={len(results)} avg=${avg:,.0f} best=${amount:,.0f} (seed {seed}) "
          f"| stored_best=${st['best']:,.0f} | new_peak={new_peak}")

    if new_peak:
        st["best"] = amount
        st["best_seed"] = seed
        st["hits"] += 1
        st["history"].append({"amount": amount, "seed": seed, "ts": time.strftime("%Y-%m-%d %H:%M")})
        st["history"] = st["history"][-50:]
        save_state(st)
        if args.send:
            tag = f" ({args.tag})" if args.tag else ""
            msg = f"${amount:,.0f}{tag}"
            telegram(msg)
            print(f"[sent] {msg}")
        elif args.report:
            # cron mode: print ONLY the new peak amount (empty = no peak)
            print(f"New Kaggriculture peak: ${amount:,.0f}")
        else:
            print(f"[would send] ${amount:,.0f}")
    else:
        save_state(st)
        if args.report:
            print("")  # silent — nothing to report
        else:
            print(f"[no new peak — best remains ${st['best']:,.0f}]")


if __name__ == "__main__":
    main()
