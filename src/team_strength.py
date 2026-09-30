"""
Team Strength Index.

Not a trained model: a computed composite score per team, built from
league position, points form, goal difference and UEFA coefficient.
Every input is min-max normalized to 0-1 across the current dataset,
then combined with fixed weights.

The weights (TEAM_STRENGTH_WEIGHTS) are a starting point, not a fitted
result, and are expected to be re-tuned once real season data is loaded.
"""

import pandas as pd

TEAM_STRENGTH_WEIGHTS = {
    "league_position": 0.30,   # inverted: 1st place = best
    "points_per_game_last10": 0.25,
    "goal_difference": 0.20,
    "uefa_coefficient": 0.25,
}


def _min_max_normalize(series: pd.Series, invert: bool = False) -> pd.Series:
    lo, hi = series.min(), series.max()
    if hi == lo:
        # every team identical on this input: contributes nothing, not a divide-by-zero
        return pd.Series(0.5, index=series.index)
    normalized = (series - lo) / (hi - lo)
    return 1 - normalized if invert else normalized


def compute_team_strength(teams_df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a copy of teams_df with a new 0-1 column: team_strength_index.
    """
    df = teams_df.copy()

    position_score = _min_max_normalize(df["final_league_position"], invert=True)
    form_score = _min_max_normalize(df["points_per_game_last10"])
    gd_score = _min_max_normalize(df["goal_difference"])
    uefa_score = _min_max_normalize(df["uefa_coefficient"])

    df["team_strength_index"] = (
        TEAM_STRENGTH_WEIGHTS["league_position"] * position_score
        + TEAM_STRENGTH_WEIGHTS["points_per_game_last10"] * form_score
        + TEAM_STRENGTH_WEIGHTS["goal_difference"] * gd_score
        + TEAM_STRENGTH_WEIGHTS["uefa_coefficient"] * uefa_score
    )
    return df
