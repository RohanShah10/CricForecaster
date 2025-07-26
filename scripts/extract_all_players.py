from pathlib import Path
import json

SCRIPT_DIR = Path(__file__).parent
FOLDER_PATH = SCRIPT_DIR.parent / "ipl_data" / "matches"
OUTPUT_PATH = SCRIPT_DIR.parent / "data" / "players.json"

def extract_unique_players(folder_path: Path) -> set:
    """
    Extracts a set of unique player names from all JSON files in the given folder.
    Assumes each JSON file contains an 'info'->'players' dictionary with team names as keys and lists of player names as values.
    """
    players = set()
    for json_file in folder_path.glob("*json"):
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            teams = data['info']['players']
            for player_list in teams.values():
                players.update(player_list)
    return players

def save_players_to_json(players):
    """
    Saves the sorted list of unique player names to a JSON file.
    Args:
        players (set): Set of unique player names.
        output_path (str or Path): Path to the output JSON file.
    """
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(players), f, ensure_ascii=False, indent=2)


def main():
    """
    Extract and print all unique player names from IPL match data JSON files.
    """
    players = extract_unique_players(FOLDER_PATH)
    save_players_to_json(players)


if __name__ == "__main__":
    main()