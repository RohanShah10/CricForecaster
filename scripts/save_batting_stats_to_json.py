from pathlib import Path
import json
import sys

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
PLAYERS_FILE = DATA_DIR / "players.json"
OUTPUT_FILE = DATA_DIR / "batting_stats.json"

sys.path.insert(0, str(SCRIPT_DIR))
from get_batting_stats import get_batting_stats

# Load all players
with open(PLAYERS_FILE, "r", encoding="utf-8") as f:
    players = json.load(f)

batting_stats = {}
for player in players:
    stats = get_batting_stats(player)
    batting_stats[player] = stats

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(batting_stats, f, indent=2)
