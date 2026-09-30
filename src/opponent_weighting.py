"""
Computes a per-match weight for every player appearance, so that
season-level stats can be aggregated as a weighted average rather
than a flat one.

Two things drive the weight:
  1. How much of the match the player actually played (minutes_played / 90,
     capped at 1.0) - a substitute cameo should not count as much as a
     full 90.
  2. How strong the opponent was relative to the player's own team
     (the "big game" factor) - beating a stronger side counts for more
     than doing the same against a weaker one.

difficulty = opponent_strength / own_team_strength
match_weight = minutes_fraction * (1 + k * max(0, difficulty - 1))

k defaults to 0.75: a game against a side exactly as strong as your own
team gets the base weight; a game against a side twice as strong gets
roughly 1.75x the base weight. k is tunable.
"""

import pandas as pd

DEFAULT_K = 0.75


def compute_match_weights(
    player_match_stats: pd.DataFrame,
    fixtures: pd.DataFrame,
    teams_with_strength: pd.DataFrame,
    k: float = DEFAULT_K,
) -> pd.DataFrame:
    """
    Returns player_match_stats with three extra columns:
      opponent_team_id, difficulty, match_weight
    """
    strength_lookup = teams_with_strength.set_index("team_id")["team_strength_index"]

    fixtures = fixtures.copy()
    fixtures["home_opponent_for_away"] = fixtures["home_team_id"]
    fixtures["away_opponent_for_home"] = fixtures["away_team_id"]

    merged = player_match_stats.merge(
        fixtures[["fixture_id", "home_team_id", "away_team_id"]],
        on="fixture_id",
        how="left",
    )

    def opponent_id(row):
        if row["team_id"] == row["home_team_id"]:
            return row["away_team_id"]
        return row["home_team_id"]

    merged["opponent_team_id"] = merged.apply(opponent_id, axis=1)
    merged["own_strength"] = merged["team_id"].map(strength_lookup)
    merged["opponent_strength"] = merged["opponent_team_id"].map(strength_lookup)

    # if strength is missing for either side, treat the game as neutral difficulty
    merged["difficulty"] = (merged["opponent_strength"] / merged["own_strength"]).fillna(1.0)
    merged.loc[merged["own_strength"] == 0, "difficulty"] = 1.0

    minutes_fraction = (merged["minutes_played"] / 90.0).clip(upper=1.0)
    difficulty_factor = 1 + k * (merged["difficulty"] - 1).clip(lower=0)
    merged["match_weight"] = minutes_fraction * difficulty_factor

    return merged.drop(columns=["home_team_id", "away_team_id"])
