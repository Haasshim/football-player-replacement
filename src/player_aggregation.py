"""
Turns raw match-by-match stats into one weighted "profile" per player:
a set of per-90 rates and percentages, aggregated using the match_weight
computed in opponent_weighting.py (so tougher opponents and fuller
appearances count for more), plus a big_game_delta_pct feature per
position showing how much the player's weighted output differs from
their flat, unweighted output.
"""

import pandas as pd

# derived per-90 stat name -> raw counting column it is built from
RATE_STAT_MAP = {
    "goals_p90": "goals",
    "assists_p90": "assists",
    "xg_p90": "xg",
    "xa_p90": "xa",
    "shots_p90": "shots",
    "shots_on_target_p90": "shots_on_target",
    "key_passes_p90": "key_passes",
    "progressive_passes_p90": "progressive_passes",
    "progressive_carries_p90": "progressive_carries",
    "dribbles_completed_p90": "dribbles_completed",
    "dribbles_attempted_p90": "dribbles_attempted",
    "times_dribbled_past_p90": "times_dribbled_past",
    "tackles_p90": "tackles",
    "tackles_won_p90": "tackles_won",
    "interceptions_p90": "interceptions",
    "blocks_p90": "blocks",
    "clearances_p90": "clearances",
    "aerial_duels_won_p90": "aerial_duels_won",
    "duels_won_p90": "duels_won",
    "recoveries_p90": "recoveries",
    "fouls_committed_p90": "fouls_committed",
    "crosses_completed_p90": "crosses_completed",
    "through_balls_p90": "through_balls",
    "touches_in_box_p90": "touches_in_box",
    "saves_p90": "saves",
    "goals_against_p90": "goals_against",
    "psxg_prevented_p90": "psxg_prevented_raw",  # synthetic column, added below
}

# derived pct stat name -> (numerator raw column, denominator raw column)
PCT_STAT_MAP = {
    "pass_completion_pct": ("passes_completed", "passes_attempted"),
    "shot_accuracy_pct": ("shots_on_target", "shots"),
    "dribble_success_pct": ("dribbles_completed", "dribbles_attempted"),
    "tackle_success_pct": ("tackles_won", "tackles"),
    "aerial_duel_pct": ("aerial_duels_won", "aerial_duels_total"),
    "duel_win_pct": ("duels_won", "duels_total"),
    "cross_accuracy_pct": ("crosses_completed", "crosses_attempted"),
    "long_pass_accuracy_pct": ("passes_long_completed", "passes_long_attempted"),
    "save_pct": ("saves", "shots_faced"),  # shots_faced is synthetic, added below
}


def _weighted_rate(df: pd.DataFrame, raw_cols: list[str], weight_col: str | None, minutes_col: str) -> float:
    weight = df[weight_col] if weight_col else 1.0
    numerator = (df[raw_cols].sum(axis=1) * weight).sum()
    denom = ((df[minutes_col] / 90.0) * weight).sum()
    return float(numerator / denom) if denom else 0.0


def _weighted_ratio(df: pd.DataFrame, num_col: str, den_col: str, weight_col: str) -> float:
    weight = df[weight_col]
    numerator = (df[num_col] * weight).sum()
    denom = (df[den_col] * weight).sum()
    return float(numerator / denom) if denom else 0.0


def _weighted_mean(df: pd.DataFrame, col: str, weight_col: str) -> float:
    weight = df[weight_col]
    denom = weight.sum()
    return float((df[col] * weight).sum() / denom) if denom else 0.0


def aggregate_player_stats(
    weighted_match_stats: pd.DataFrame,
    players_df: pd.DataFrame,
    position_config: dict,
) -> pd.DataFrame:
    """
    weighted_match_stats: output of opponent_weighting.compute_match_weights
    players_df: the players table (for primary_position, club, name)
    position_config: the loaded position_weights.json

    Returns one row per player with every derived stat plus big_game_delta_pct.
    """
    df = weighted_match_stats.copy()
    df["shots_faced"] = df["saves"] + df["goals_against"]
    df["psxg_prevented_raw"] = df["post_shot_xg"] - df["goals_against"]

    players_lookup = players_df.set_index("player_id")
    rows = []

    for player_id, group in df.groupby("player_id"):
        if player_id not in players_lookup.index:
            continue
        info = players_lookup.loc[player_id]
        position = info["primary_position"]

        row = {
            "player_id": player_id,
            "full_name": info.get("full_name", player_id),
            "primary_position": position,
            "club": info.get("club", None),
            "matches_played": len(group),
            "total_minutes": float(group["minutes_played"].sum()),
        }

        for p90_name, raw_col in RATE_STAT_MAP.items():
            row[p90_name] = _weighted_rate(group, [raw_col], "match_weight", "minutes_played")

        for pct_name, (num_col, den_col) in PCT_STAT_MAP.items():
            row[pct_name] = _weighted_ratio(group, num_col, den_col, "match_weight")

        row["clean_sheet_pct"] = _weighted_mean(group, "clean_sheet", "match_weight")

        composite_p90_names = position_config.get(position, {}).get("big_game_composite_stats", [])
        composite_raw_cols = [RATE_STAT_MAP[name] for name in composite_p90_names if name in RATE_STAT_MAP]
        if composite_raw_cols:
            flat = _weighted_rate(group, composite_raw_cols, None, "minutes_played")
            weighted = _weighted_rate(group, composite_raw_cols, "match_weight", "minutes_played")
            row["big_game_delta_pct"] = ((weighted - flat) / flat * 100) if flat else 0.0
        else:
            row["big_game_delta_pct"] = 0.0

        rows.append(row)

    return pd.DataFrame(rows)
