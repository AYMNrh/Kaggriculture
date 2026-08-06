Read CODEX_BRIEFING.md first — it contains all the empirical context. Then read main.py and the env source (.venv/Lib/site-packages/kaggle_environments/envs/kaggriculture/kaggriculture.py).

Your mission: help get this Kaggriculture agent from ~$95k avg to $120k+.

Debate and analyze the core tension: the role split (crop hands vs animal hands) is PROVEN essential (removal = $5.6k collapse), but it blocks the champion's dense-field + daily-fertilize strategy. The fertilize mechanic has failed 6+ times.

Deliver a written analysis in ANALYSIS.md containing:
1. Your assessment of the core tension — is there a mechanism to get fertilize working WITH the role split? Think about: animal hands that COLLECT fertilizer applying it as part of their loop; a dedicated fertilize hand; the champion's actual collect-and-apply flow.
2. Analysis of the champion's mass-planting bursts (13-14/day on days 11-13) — what mechanism lets their hands plant while watering 41 plants?
3. Review main.py for bugs or missed mechanics (read the env source carefully — check first_yield_day, CARE bonus, FERTILIZE, max_held, shed overflow, market order caps).
4. Propose 2-3 concrete TESTABLE changes ranked by expected $ impact, with exact code-level suggestions.

Do NOT modify main.py. Write your analysis to ANALYSIS.md and be specific and rigorous — cite env source line numbers where relevant.
