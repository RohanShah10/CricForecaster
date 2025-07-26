from pathlib import Path
import json
from dataclasses import dataclass
from typing import Dict, Union

# Adjust the folder path to where your match JSON files are stored
SCRIPT_DIR = Path(__file__).parent
FOLDER_PATH = SCRIPT_DIR.parent / "ipl_data" / "matches"


@dataclass
class BattingStats:
    balls_faced: int = 0
    runs: int = 0
    fours: int = 0
    sixes: int = 0
    dot_balls: int = 0
    boundary_balls: int = 0
    out: bool = False


def is_wide(delivery: dict) -> bool:
    """Return True if the delivery is a wide ball."""
    return "wides" in delivery.get("extras", {})


def process_delivery(delivery: dict, player: str) -> BattingStats:
    """Process a single delivery for the player and return stats for that delivery."""
    if delivery.get("batter") != player:
        return BattingStats()

    run = delivery.get("runs", {}).get("batter", 0)
    balls_faced = 0
    fours = sixes = dot_balls = boundary_balls = 0

    if not is_wide(delivery):
        balls_faced = 1
        if run == 4:
            fours = 1
            boundary_balls = 1
        elif run == 6:
            sixes = 1
            boundary_balls = 1
        elif run == 0:
            dot_balls = 1

    out = any(wicket.get("player_out") == player for wicket in delivery.get("wickets", []))
    return BattingStats(
        balls_faced=balls_faced,
        runs=run,
        fours=fours,
        sixes=sixes,
        dot_balls=dot_balls,
        boundary_balls=boundary_balls,
        out=out
    )


def process_innings(overs: list, player: str) -> BattingStats:
    """Process all deliveries in an innings for the player and return aggregated stats."""
    stats = BattingStats()
    for over in overs:
        for delivery in over.get("deliveries", []):
            d_stats = process_delivery(delivery, player)
            stats.runs += d_stats.runs
            stats.balls_faced += d_stats.balls_faced
            stats.fours += d_stats.fours
            stats.sixes += d_stats.sixes
            stats.dot_balls += d_stats.dot_balls
            stats.boundary_balls += d_stats.boundary_balls
            if d_stats.out:
                stats.out = True
    return stats


def get_match_files_sorted_by_date(folder_path):
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


def get_batting_stats(player: str) -> Dict[str, Union[int, float]]:
    """
    Gather comprehensive batting stats for a player across all matches.
    Returns a dict with extended metrics.
    """
    matches_played = set()
    innings_played = set()
    highest_score = 0
    outs = 0
    runs = balls_faced = fours = sixes = dot_balls = boundary_balls = 0
    innings_out_flags = {}
    innings_scores = []

    # Use the helper to get sorted match files
    sorted_json_files = get_match_files_sorted_by_date(FOLDER_PATH)

    for json_file in sorted_json_files:
        match_id = json_file.stem
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            for inning_idx, inning in enumerate(data.get("innings", [])):
                overs = inning.get("overs", [])
                stats = process_innings(overs, player)
                if stats.balls_faced > 0:
                    matches_played.add(match_id)
                    innings_played.add((match_id, inning_idx))
                    highest_score = max(highest_score, stats.runs)
                    runs += stats.runs
                    balls_faced += stats.balls_faced
                    fours += stats.fours
                    sixes += stats.sixes
                    dot_balls += stats.dot_balls
                    boundary_balls += stats.boundary_balls
                    innings_scores.append(stats.runs)
                    if stats.out:
                        outs += 1
                        innings_out_flags[(match_id, inning_idx)] = True
                    else:
                        innings_out_flags[(match_id, inning_idx)] = False

    not_outs = sum(1 for out_flag in innings_out_flags.values() if not out_flag)
    innings_count = len(innings_played)
    matches_count = len(matches_played)
    average = runs / (innings_count - not_outs) if (innings_count - not_outs) > 0 else float('inf') if runs > 0 else 0.0
    strike_rate = (runs / balls_faced) * 100 if balls_faced > 0 else 0.0
    dot_ball_percentage = (dot_balls / balls_faced) * 100 if balls_faced > 0 else 0.0
    boundary_percentage = (boundary_balls / balls_faced) * 100 if balls_faced > 0 else 0.0

    # Advanced metrics
    balls_per_boundary = balls_faced / (fours + sixes) if (fours + sixes) > 0 else 0.0
    boundary_to_dot_ratio = (fours + sixes) / dot_balls if dot_balls > 0 else 0.0
    balls_per_dismissal = balls_faced / (innings_count - not_outs) if (innings_count - not_outs) > 0 else 0.0
    fifties = sum(1 for score in innings_scores if 50 <= score < 100)
    hundreds = sum(1 for score in innings_scores if score >= 100)
    consistency = (sum(1 for score in innings_scores if score >= 30) / innings_count * 100) if innings_count > 0 else 0.0

    recent_scores = innings_scores[-5:] if innings_scores else []
    form_index = round(sum(s * w for s, w in zip(recent_scores[::-1], [1.5, 1.3, 1.1, 0.9, 0.7])) / 5, 2) if recent_scores else 0.0

    return {
        "matches": matches_count,
        "innings": innings_count,
        "not_outs": not_outs,
        "runs": runs,
        "average": round(average, 2) if average != float('inf') else average,
        "strike_rate": round(strike_rate, 2),
        "balls_faced": balls_faced,
        "fours": fours,
        "sixes": sixes,
        "highest_score": highest_score,
        "dot_ball_percentage": round(dot_ball_percentage, 2),
        "boundary_percentage": round(boundary_percentage, 2),
        "balls_per_boundary": round(balls_per_boundary, 2),
        "boundary_to_dot_ratio": round(boundary_to_dot_ratio, 2),
        "balls_per_dismissal": round(balls_per_dismissal, 2),
        "fifties": fifties,
        "hundreds": hundreds,
        "consistency": round(consistency, 2),
        "recent_scores": recent_scores,
        "form_index": form_index
    }

