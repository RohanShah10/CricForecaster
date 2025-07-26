import json
import numpy as np
import pandas as pd

from pathlib import Path

SCRIPT_DIR = SCRIPT_DIR = Path(__file__).parent
BATTING_STATS_DIR = SCRIPT_DIR.parent / 'data' / 'batting_stats.json' 
OUTPUT_DIR = SCRIPT_DIR.parent / 'data' / 'training_data.csv'

with open(BATTING_STATS_DIR) as f:
    batting_data = json.load(f)

rows = []
for player, stats in batting_data.items():
    # Ignore players who have never batted
    if stats["innings"] == 0:
        continue

    # Features derived from recent scores
    recent_scores = stats.get("recent_scores", {})
    recent_mean = np.mean(recent_scores) if recent_scores else 0
    recent_std = np.std(recent_scores) if recent_scores else 0
    next_match_runs = recent_scores[-1] if recent_scores else 0 # Target variable

    rows.append({
        "player": player,
        "average": stats["average"],
        "strike_rate": stats["strike_rate"],
        "balls_per_boundary": stats.get("balls_per_boundary", 0),
        "boundary_to_dot_ratio": stats.get("boundary_to_dot_ratio", 0),
        "balls_per_dismissal": stats.get("balls_per_dismissal", 0),
        "form_index": stats.get("form_index", 0),
        "consistency": stats.get("consistency", 0),
        "recent_mean": recent_mean,
        "recent_std": recent_std,
        "next_match_runs": next_match_runs
    })

df = pd.DataFrame(rows)
df.to_csv(OUTPUT_DIR, index=False)

