from pathlib import Path
import json
from typing import List

SCRIPT_DIR = Path(__file__).parent
FOLDER_PATH = SCRIPT_DIR.parent / "ipl_data" / "matches"


def is_wide(delivery: dict) -> bool:
    """Return True if the delivery is a wide ball."""
    return "wides" in delivery.get("extras", {})


def is_no_ball(delivery: dict) -> bool:
    """Return True if the delivery is a no ball."""
    return "noballs" in delivery.get("extras", {})


def get_match_files_sorted_by_date(folder_path: Path) -> List[Path]:
    """Return a list of match file paths sorted by the match date in info['dates'][0]."""
    file_date_pairs = []
    
    for json_file in folder_path.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                match_date = data.get("info", {}).get("dates", [None])[0]
                if match_date:
                    file_date_pairs.append((json_file, match_date))
        except (json.JSONDecodeError, KeyError, IndexError):
            continue
    
    file_date_pairs.sort(key=lambda x: x[1])
    return [pair[0] for pair in file_date_pairs]


def process_matches_for_player(player: str, process_innings_func, folder_path: Path = FOLDER_PATH):
    """
    Generic function to process all matches for a player.
    
    Args:
        player: Player name to search for
        process_innings_func: Function that processes innings and returns stats
        folder_path: Path to match files
    
    Returns:
        Tuple of (matches_played, innings_played, all_stats)
    """
    matches_played = set()
    innings_played = set()
    all_stats = []
    
    sorted_json_files = get_match_files_sorted_by_date(folder_path)
    
    for json_file in sorted_json_files:
        match_id = json_file.stem
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            for inning_idx, inning in enumerate(data.get("innings", [])):
                overs = inning.get("overs", [])
                stats = process_innings_func(overs, player)
                
                # Check if player participated in this innings
                if hasattr(stats, 'balls_faced') and stats.balls_faced > 0:  # Batting
                    matches_played.add(match_id)
                    innings_played.add((match_id, inning_idx))
                    all_stats.append((match_id, inning_idx, stats))
                elif hasattr(stats, 'balls') and stats.balls > 0:  # Bowling
                    matches_played.add(match_id)
                    innings_played.add((match_id, inning_idx))
                    all_stats.append((match_id, inning_idx, stats))
    
    return matches_played, innings_played, all_stats 