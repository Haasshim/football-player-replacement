"""
Turns season-total raw stats (data/player_season_stats.csv) into the same
derived per-90/percentage feature set the similarity engine expects -
computed directly from totals since this is already one row per player
per season, not match-by-match.

big_game_delta_pct here is a team-level number (see
scripts/real_data/parse_team_results.py): every player on the same team
in the same season gets the same value, since the source data can only
support a team-level "strength of schedule" signal, not a genuine
player-by-player one. This is documented in the README.
"""

import pandas as pd

RATE_STAT_MAP = {
    "goals_p90": "goals", "assists_p90": "assists", "xg_p90": "xg", "xa_p90": "xa",
    "shots_p90": "shots", "shots_on_target_p90": "shots_on_target", "key_passes_p90": "key_passes",
    "progressive_passes_p90": "progressive_passes", "progressive_carries_p90": "progressive_carries",
    "dribbles_completed_p90": "dribbles_completed", "dribbles_attempted_p90": "dribbles_attempted",
    "times_dribbled_past_p90": "times_dribbled_past", "tackles_p90": "tackles",
    "tackles_won_p90": "tackles_won", "interceptions_p90": "interceptions", "blocks_p90": "blocks",
    "clearances_p90": "clearances", "aerial_duels_won_p90": "aerial_duels_won",
    "duels_won_p90": "duels_won", "recoveries_p90": "recoveries",
    "fouls_committed_p90": "fouls_committed", "crosses_completed_p90": "crosses_completed",
    "through_balls_p90": "through_balls", "touches_in_box_p90": "touches_in_box",
    "saves_p90": "saves", "goals_against_p90": "goals_against",
}

PCT_STAT_MAP = {
    "pass_completion_pct": ("passes_completed", "passes_attempted"),
    "shot_accuracy_pct": ("shots_on_target", "shots"),
    "dribble_success_pct": ("dribbles_completed", "dribbles_attempted"),
    "tackle_success_pct": ("tackles_won", "tackles"),
    "aerial_duel_pct": ("aerial_duels_won", "aerial_duels_total"),
    "duel_win_pct": ("duels_won", "duels_total"),
    "cross_accuracy_pct": ("crosses_completed", "crosses_attempted"),
    "long_pass_accuracy_pct": ("passes_long_completed", "passes_long_attempted"),
}


def _rate(row: pd.Series, raw_col: str) -> float:
    total = row.get(raw_col)
    minutes = row.get("minutes_played")
    if pd.isna(total) or not minutes:
        return float("nan")
    return float(total) / (minutes / 90.0)


def _pct(row: pd.Series, num_col: str, den_col: str) -> float:
    num, den = row.get(num_col), row.get(den_col)
    if pd.isna(num) or pd.isna(den) or not den:
        return float("nan")
    return float(num) / float(den)


def aggregate_season_stats(
    player_season_stats: pd.DataFrame,
    players_df: pd.DataFrame,
    teams_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Returns one row per player_id with every derived stat, joined against
    players_df for position/name/club and teams_df for the big-game factor.
    """
    big_game_by_team = teams_df.set_index("team_id")["big_game_factor_pct"].to_dict()
    players_lookup = players_df.set_index("player_id")

    rows = []
    for _, stat_row in player_season_stats.iterrows():
        player_id = stat_row["player_id"]
        if player_id not in players_lookup.index:
            continue
        info = players_lookup.loc[player_id]

        row = {
            "player_id": player_id,
            "full_name": info["full_name"],
            "primary_position": info["primary_position"],
            "club": info["club"],
            "matches_played": stat_row.get("matches_played"),
            "total_minutes": stat_row.get("minutes_played"),
            "season_used": stat_row.get("season_used"),
        }

        for p90_name, raw_col in RATE_STAT_MAP.items():
            row[p90_name] = _rate(stat_row, raw_col)

        for pct_name, (num_col, den_col) in PCT_STAT_MAP.items():
            row[pct_name] = _pct(stat_row, num_col, den_col)

        matches = stat_row.get("matches_played")
        clean_sheets = stat_row.get("clean_sheets")
        row["clean_sheet_pct"] = (
            float(clean_sheets) / matches if matches and not pd.isna(clean_sheets) else float("nan")
        )

        goals_prevented = stat_row.get("goals_prevented")
        if not pd.isna(goals_prevented) and stat_row.get("minutes_played"):
            row["psxg_prevented_p90"] = float(goals_prevented) / (stat_row["minutes_played"] / 90.0)
        else:
            row["psxg_prevented_p90"] = float("nan")

        row["big_game_delta_pct"] = big_game_by_team.get(info["club"], 0.0)

        rows.append(row)

    return pd.DataFrame(rows)
