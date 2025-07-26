from pathlib import Path
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
PLAYERS_FILE = DATA_DIR / "players.json"
OUTPUT_FILE = DATA_DIR / "bowling_stats.json"

sys.path.insert(0, str(SCRIPT_DIR))
from get_bowling_stats import get_bowling_stats

# Thread-safe print lock
print_lock = threading.Lock()

def process_player(player):
    """Process a single player and return their bowling stats."""
    stats = get_bowling_stats(player)
    # Only return stats if player has bowled (stats is not None)
    if stats is not None:
        return player, stats
    return None

# Load all players
with open(PLAYERS_FILE, "r", encoding="utf-8") as f:
    players = json.load(f)

bowling_stats = {}

# Use ThreadPool executor for concurrency
with ThreadPoolExecutor(max_workers=10) as executor:
    # Submit all player processing tasks
    futures = [executor.submit(process_player, player) for player in players]
    
    # Collect results as they complete
    for future in as_completed(futures):
        try:
            result = future.result()
            if result is not None:
                player, stats = result
                bowling_stats[player] = stats
                with print_lock:
                    print(f"Completed: {player}")
            else:
                with print_lock:
                    print(f"Skipped: Player has never bowled")
        except Exception as e:
            with print_lock:
                print(f"Error processing player: {e}")

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(bowling_stats, f, indent=2)
    

print(f"Successfully processed {len(bowling_stats)} players") 