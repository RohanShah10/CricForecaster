import json
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import joblib


# ------------------------------
# Paths
# ------------------------------
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / 'data'
BATTING_STATS_FILE = DATA_DIR / 'batting_stats.json'
TRAINING_DATA_FILE = DATA_DIR / 'training_data.csv'
MODEL_DIR = SCRIPT_DIR.parent / 'models'
MODEL_FILE = MODEL_DIR / 'player_forecast_model.pkl'


# ------------------------------
# Step 1: Load Data and Build Training DataFrame
# ------------------------------
def build_training_data():
    """Convert batting_stats.json into training_data.csv with derived features."""
    with open(BATTING_STATS_FILE, 'r') as f:
        batting_data = json.load(f)

    rows = []
    for player, stats in batting_data.items():
        # Ignore players with no innings
        if stats.get("innings", 0) == 0:
            continue

        # Features from recent scores
        recent_scores = stats.get("recent_scores", [])
        recent_mean = float(np.mean(recent_scores)) if recent_scores else 0.0
        recent_std = float(np.std(recent_scores)) if recent_scores else 0.0
        next_match_runs = recent_scores[-1] if recent_scores else 0  # Target variable

        rows.append({
            "player": player,
            "average": stats.get("average", 0.0),
            "strike_rate": stats.get("strike_rate", 0.0),
            "balls_per_boundary": stats.get("balls_per_boundary", 0.0),
            "boundary_to_dot_ratio": stats.get("boundary_to_dot_ratio", 0.0),
            "balls_per_dismissal": stats.get("balls_per_dismissal", 0.0),
            "form_index": stats.get("form_index", 0.0),
            "consistency": stats.get("consistency", 0.0),
            "recent_mean": recent_mean,
            "recent_std": recent_std,
            "next_match_runs": next_match_runs
        })

    df = pd.DataFrame(rows)
    df.to_csv(TRAINING_DATA_FILE, index=False)
    print(f"Training data saved to {TRAINING_DATA_FILE}")
    return df


# ------------------------------
# Step 2: Train Model
# ------------------------------
def train_model():
    """Train a RandomForestRegressor on player stats and save the model."""
    df = pd.read_csv(TRAINING_DATA_FILE)
    features = [
        "average", "strike_rate", "balls_per_boundary", "boundary_to_dot_ratio",
        "balls_per_dismissal", "form_index", "consistency", "recent_mean", "recent_std"
    ]
    X = df[features]
    y = df["next_match_runs"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    print(f"Model trained. Mean Absolute Error: {mae:.2f}")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_FILE)
    print(f"Model saved to {MODEL_FILE}")
    return model, df


# ------------------------------
# Step 3: Prediction Function
# ------------------------------
def predict_next_runs(player_name: str):
    """Predict the next match runs for a given player using the trained model."""
    if not MODEL_FILE.exists():
        print("Model file not found. Training a new model...")
        build_training_data()
        train_model()

    model = joblib.load(MODEL_FILE)
    df = pd.read_csv(TRAINING_DATA_FILE)
    features = [
        "average", "strike_rate", "balls_per_boundary", "boundary_to_dot_ratio",
        "balls_per_dismissal", "form_index", "consistency", "recent_mean", "recent_std"
    ]
    player_row = df[df['player'] == player_name]
    if player_row.empty:
        print(f"No data available for player: {player_name}")
        return None
    X_player = player_row[features]
    return model.predict(X_player)[0]


# ------------------------------
# Main Script
# ------------------------------
if __name__ == "__main__":
    print("Building training data and training model...")
    df = build_training_data()
    model, _ = train_model()
    # Example prediction
    sample_player = "RG Sharma"
    print(f"Predicted runs for {sample_player}: {predict_next_runs(sample_player):.2f}")