from dataclasses import dataclass
from typing import Dict, Union
from cricket_utils import is_wide, is_no_ball, process_matches_for_player


@dataclass
class BowlingStats:
    overs: float = 0.0
    balls: int = 0
    runs_conceded: int = 0
    wickets: int = 0
    dot_balls: int = 0
    boundary_balls: int = 0
    extras: int = 0
    wides: int = 0
    no_balls: int = 0


def process_delivery_bowling(delivery: dict, player: str) -> BowlingStats:
    """Process a single delivery for the bowler and return stats for that delivery."""
    if delivery.get("bowler") != player:
        return BowlingStats()

    # Calculate runs conceded: batter runs + wides + no-balls (but not byes/leg-byes)
    batter_runs = delivery.get("runs", {}).get("batter", 0)
    extras_runs = 0
    if "extras" in delivery:
        if is_wide(delivery) or is_no_ball(delivery):
            extras_runs = delivery.get("runs", {}).get("extras", 0)
    runs_conceded = batter_runs + extras_runs

    # Count legal balls and categorize them
    balls = 0
    dot_balls = boundary_balls = extras = wides = no_balls = 0
    wickets = 0

    if not is_wide(delivery) and not is_no_ball(delivery):
        balls = 1
        if batter_runs == 0:
            dot_balls = 1
        elif batter_runs == 4 or batter_runs == 6:
            boundary_balls = 1

    # Count extras
    if "extras" in delivery:
        extras += 1
        if is_wide(delivery):
            wides = 1
        elif is_no_ball(delivery):
            no_balls = 1

    # Count wickets (excluding run outs)
    if "wickets" in delivery:
        for wicket in delivery["wickets"]:
            if wicket.get("kind") != "run out":
                wickets += 1

    return BowlingStats(
        overs=0.0,
        balls=balls,
        runs_conceded=runs_conceded,
        wickets=wickets,
        dot_balls=dot_balls,
        boundary_balls=boundary_balls,
        extras=extras,
        wides=wides,
        no_balls=no_balls
    )


def process_innings_bowling(overs: list, player: str) -> BowlingStats:
    """Process all deliveries in an innings for the bowler and return aggregated stats."""
    stats = BowlingStats()
    
    for over in overs:
        over_stats = BowlingStats()
        
        for delivery in over.get("deliveries", []):
            d_stats = process_delivery_bowling(delivery, player)
            over_stats.runs_conceded += d_stats.runs_conceded
            over_stats.balls += d_stats.balls
            over_stats.wickets += d_stats.wickets
            over_stats.dot_balls += d_stats.dot_balls
            over_stats.boundary_balls += d_stats.boundary_balls
            over_stats.extras += d_stats.extras
            over_stats.wides += d_stats.wides
            over_stats.no_balls += d_stats.no_balls
        
        # Accumulate stats if bowler bowled legal balls in this over
        if over_stats.balls > 0:
            stats.runs_conceded += over_stats.runs_conceded
            stats.balls += over_stats.balls
            stats.wickets += over_stats.wickets
            stats.dot_balls += over_stats.dot_balls
            stats.boundary_balls += over_stats.boundary_balls
            stats.extras += over_stats.extras
            stats.wides += over_stats.wides
            stats.no_balls += over_stats.no_balls
    
    return stats


def get_bowling_stats(player: str) -> Dict[str, Union[int, float]]:
    """Gather comprehensive bowling stats for a player across all matches."""
    matches_played, innings_played, all_stats = process_matches_for_player(player, process_innings_bowling)
    
    overs = 0.0
    balls = runs_conceded = wickets = 0
    dot_balls = boundary_balls = extras = wides = no_balls = 0
    innings_wickets = []

    for match_id, inning_idx, stats in all_stats:
        overs += stats.overs
        balls += stats.balls
        runs_conceded += stats.runs_conceded
        wickets += stats.wickets
        dot_balls += stats.dot_balls
        boundary_balls += stats.boundary_balls
        extras += stats.extras
        wides += stats.wides
        no_balls += stats.no_balls
        innings_wickets.append(stats.wickets)

    # Return None if player has never bowled
    if balls == 0:
        return None

    matches_count = len(matches_played)
    innings_count = len(innings_played)
    
    # Calculate overs from total balls (complete overs + decimal for remaining balls)
    complete_overs = balls // 6
    remaining_balls = balls % 6
    overs = complete_overs + (remaining_balls / 10.0)
    
    # Calculate bowling metrics
    total_balls = balls + wides + no_balls
    average = runs_conceded / wickets if wickets > 0 else 0.0
    economy = (runs_conceded / overs) if overs > 0 else 0.0
    strike_rate = (balls / wickets) if wickets > 0 else 0.0
    dot_ball_percentage = (dot_balls / balls) * 100 if balls > 0 else 0.0
    boundary_percentage = (boundary_balls / balls) * 100 if balls > 0 else 0.0

    # Advanced metrics
    balls_per_wicket = balls / wickets if wickets > 0 else 0.0
    extras_percentage = (extras / total_balls) * 100 if total_balls > 0 else 0.0
    three_wicket_hauls = sum(1 for wickets_in_innings in innings_wickets if wickets_in_innings >= 3)
    five_wicket_hauls = sum(1 for wickets_in_innings in innings_wickets if wickets_in_innings >= 5)
    
    # Form calculation based on recent performances
    recent_wickets = innings_wickets[-5:] if innings_wickets else []
    form_index = round(sum(w * weight for w, weight in zip(recent_wickets[::-1], [1.5, 1.3, 1.1, 0.9, 0.7])) / 5, 2) if recent_wickets else 0.0

    return {
        "matches": matches_count,
        "innings": innings_count,
        "overs": round(overs, 1),
        "balls": balls,
        "runs_conceded": runs_conceded,
        "wickets": wickets,
        "average": round(average, 2),
        "economy": round(economy, 2),
        "strike_rate": round(strike_rate, 2),
        "dot_ball_percentage": round(dot_ball_percentage, 2),
        "boundary_percentage": round(boundary_percentage, 2),
        "extras": extras,
        "wides": wides,
        "no_balls": no_balls,
        "extras_percentage": round(extras_percentage, 2),
        "balls_per_wicket": round(balls_per_wicket, 2),
        "three_wicket_hauls": three_wicket_hauls,
        "five_wicket_hauls": five_wicket_hauls,
        "recent_wickets": recent_wickets,
        "form_index": form_index
    }


if __name__ == "__main__":
    # Example usage
    player_name = "YS Chahal"
    stats = get_bowling_stats(player_name)
    print(f"Bowling stats for {player_name}:")
    for key, value in stats.items():
        print(f"{key}: {value}")
