"""
Loads the four source CSVs (teams, players, fixtures, player_match_stats)
and checks that the required columns are present. See
data/README.md for the exact schema each file must follow.
"""

from pathlib import Path
import pandas as pd

REQUIRED_COLUMNS = {
    "teams.csv": [
        "team_id", "team_name", "league", "final_league_position",
        "points", "points_per_game_last10", "goal_difference", "uefa_coefficient",
    ],
    "players.csv": [
        "player_id", "full_name", "date_of_birth", "primary_position",
        "club", "nationality",
    ],
    "fixtures.csv": [
        "fixture_id", "date", "home_team_id", "away_team_id",
        "home_score", "away_score",
    ],
    "player_match_stats.csv": [
        "fixture_id", "player_id", "team_id", "minutes_played", "position_played",
        "goals", "assists", "xg", "xa", "shots", "shots_on_target", "key_passes",
        "passes_completed", "passes_attempted", "progressive_passes",
        "progressive_carries", "dribbles_completed", "dribbles_attempted",
        "times_dribbled_past", "tackles", "tackles_won", "interceptions",
        "blocks", "clearances", "aerial_duels_won", "aerial_duels_total",
        "duels_won", "duels_total", "recoveries", "fouls_committed",
        "crosses_completed", "crosses_attempted", "through_balls",
        "touches_in_box", "passes_long_completed", "passes_long_attempted",
        "saves", "goals_against", "post_shot_xg", "clean_sheet",
    ],
}

VALID_POSITIONS = ["GK", "CB", "FB", "DM", "CM", "AM", "WING", "ST"]


class DataValidationError(Exception):
    pass


def _check_columns(df: pd.DataFrame, filename: str) -> None:
    required = REQUIRED_COLUMNS[filename]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise DataValidationError(f"{filename} is missing required columns: {missing}")


def load_data(data_dir: str | Path) -> dict[str, pd.DataFrame]:
    """
    Loads all four CSVs from data_dir and validates their columns.
    Returns a dict with keys: teams, players, fixtures, player_match_stats.
    """
    data_dir = Path(data_dir)
    files = {
        "teams": "teams.csv",
        "players": "players.csv",
        "fixtures": "fixtures.csv",
        "player_match_stats": "player_match_stats.csv",
    }

    tables = {}
    for key, filename in files.items():
        path = data_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Expected file not found: {path}")
        df = pd.read_csv(path)
        _check_columns(df, filename)
        tables[key] = df

    bad_positions = set(tables["players"]["primary_position"].unique()) - set(VALID_POSITIONS)
    if bad_positions:
        raise DataValidationError(
            f"players.csv has unknown primary_position values: {bad_positions}. "
            f"Valid values are: {VALID_POSITIONS}"
        )

    return tables
