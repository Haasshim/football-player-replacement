"""
Maps the two real player-stat sources into our unified raw-stat schema
(the same field names src/player_aggregation.py already expects).

2025-26 season: archive 4's two files are merged - the 79-row "whole
season UPDATED" file is richer (has goalsConceded, countRating, etc.) and
preferred per-player when present; the 527-row "until 35th gameday" file
fills in every other player with a slightly smaller field set.

2024-25 season: the standalone CSV uses a different, older-style column
set (no xG/xA, no separate dribble-attempt counts, no split tackles
won/attempted) - those fields are left as None rather than guessed at,
so the aggregator can see what's genuinely missing.

Output: scripts/real_data/player_season_stats.json
  { normalized_name: { "2025-26": {...raw fields..., "_source_row": {club,position_coarse}},
                        "2024-25": {...} } }
"""

import json
import math
import pandas as pd
from pathlib import Path
from name_utils import normalize

OUT_PATH = Path(__file__).parent / "player_season_stats.json"

UPLOADS = Path("/mnt/user-data/uploads")
A4 = Path("/home/claude/uploads_inspect/a4")

POSITION_COARSE_MAP = {
    "G": "GK", "GKP": "GK",
    "D": "DEF", "DEF": "DEF",
    "M": "MID", "MID": "MID",
    "F": "FWD", "FWD": "FWD",
}


def _num(row, col):
    if col not in row or pd.isna(row[col]):
        return None
    return float(row[col])


def _derive_total(won, pct):
    """attempts = won / (pct/100), guarding zero/missing percentage."""
    if won is None or pct is None or pct == 0:
        return None
    return won / (pct / 100.0)


def map_archive4_row(row: dict) -> dict:
    accurate_passes = _num(row, "accuratePasses")
    total_passes = _num(row, "totalPasses")
    ground_won = _num(row, "groundDuelsWon")
    ground_pct = _num(row, "groundDuelsWonPercentage")
    aerial_won = _num(row, "aerialDuelsWon")
    aerial_pct = _num(row, "aerialDuelsWonPercentage")
    long_acc = _num(row, "accurateLongBalls")
    long_pct = _num(row, "accurateLongBallsPercentage")

    return {
        "goals": _num(row, "goals"),
        "assists": _num(row, "assists"),
        "xg": _num(row, "expectedGoals"),
        "xa": _num(row, "expectedAssists"),
        "shots": _num(row, "totalShots"),
        "shots_on_target": _num(row, "shotsOnTarget"),
        "key_passes": _num(row, "keyPasses"),
        "passes_completed": accurate_passes,
        "passes_attempted": total_passes,
        "progressive_passes": None,  # not tracked by this source
        "progressive_carries": None,
        "dribbles_completed": _num(row, "successfulDribbles"),
        "dribbles_attempted": _num(row, "totalContest"),
        "times_dribbled_past": _num(row, "dribbledPast"),
        "tackles": _num(row, "tackles"),
        "tackles_won": _num(row, "tacklesWon"),
        "interceptions": _num(row, "interceptions"),
        "blocks": (_num(row, "blockedShots") or 0) + (_num(row, "outfielderBlocks") or 0),
        "clearances": _num(row, "clearances"),
        "aerial_duels_won": aerial_won,
        "aerial_duels_total": _derive_total(aerial_won, aerial_pct),
        "duels_won": ground_won,
        "duels_total": _derive_total(ground_won, ground_pct),
        "recoveries": _num(row, "ballRecovery"),
        "fouls_committed": _num(row, "fouls"),
        "crosses_completed": _num(row, "accurateCrosses"),
        "crosses_attempted": _num(row, "totalCross"),
        "through_balls": None,
        "touches_in_box": None,
        "passes_long_completed": long_acc,
        "passes_long_attempted": _derive_total(long_acc, long_pct),
        "saves": _num(row, "saves"),
        "goals_against": _num(row, "goalsConceded"),
        "post_shot_xg": None,
        "goals_prevented": _num(row, "goalsPrevented"),
        "clean_sheets": _num(row, "cleanSheet"),
        "minutes_played": _num(row, "minutesPlayed"),
        "matches_played": _num(row, "appearances"),
        "position_coarse": POSITION_COARSE_MAP.get(row.get("position"), None),
        "club": row.get("team_name"),
    }


def map_standalone_2425_row(row: dict) -> dict:
    return {
        "goals": _num(row, "Goals"),
        "assists": _num(row, "Assists"),
        "xg": None,  # not tracked by this source
        "xa": None,
        "shots": _num(row, "Shots"),
        "shots_on_target": _num(row, "Shots On Target"),
        "key_passes": None,
        "passes_completed": _num(row, "Successful Passes"),
        "passes_attempted": _num(row, "Passes"),
        "progressive_passes": None,
        "progressive_carries": _num(row, "Progressive Carries"),
        "dribbles_completed": None,
        "dribbles_attempted": None,
        "times_dribbled_past": None,
        "tackles": _num(row, "Tackles"),
        "tackles_won": _num(row, "Tackles"),  # no won/attempt split in this source
        "interceptions": _num(row, "Interceptions"),
        "blocks": _num(row, "Blocks"),
        "clearances": _num(row, "Clearances"),
        "aerial_duels_won": _num(row, "aDuels Won"),
        "aerial_duels_total": _num(row, "Aerial Duels"),
        "duels_won": _num(row, "gDuels Won"),
        "duels_total": _num(row, "Ground Duels"),
        "recoveries": _num(row, "Possession Won"),
        "fouls_committed": _num(row, "Fouls"),
        "crosses_completed": _num(row, "Successful Crosses"),
        "crosses_attempted": _num(row, "Crosses"),
        "through_balls": _num(row, "Through Balls"),
        "touches_in_box": None,
        "passes_long_completed": None,
        "passes_long_attempted": None,
        "saves": _num(row, "Saves"),
        "goals_against": _num(row, "Goals Conceded"),
        "post_shot_xg": None,
        "goals_prevented": _num(row, "Goals Prevented"),
        "clean_sheets": _num(row, "Clean Sheets"),
        "minutes_played": _num(row, "Minutes"),
        "matches_played": _num(row, "Appearances"),
        "position_coarse": POSITION_COARSE_MAP.get(row.get("Position"), None),
        "club": row.get("Club"),
    }


def main():
    result = {}

    # --- 2025-26: merge the rich 79-row file (preferred) with the broad 527-row file ---
    rich = pd.read_csv(A4 / "premier_league_complete_stats_whole2025-2026_season_UPDATED.csv")
    broad = pd.read_csv(A4 / "premier_league_complete_stats_until35thGameDayOnSeason2025-26.csv")

    rich_names_used = set()
    for _, row in rich.iterrows():
        name = row["player_name"]
        key = normalize(name)
        result.setdefault(key, {})["2025-26"] = map_archive4_row(row.to_dict())
        result[key]["2025-26"]["full_name"] = name
        rich_names_used.add(key)

    broad_added, broad_skipped = 0, 0
    for _, row in broad.iterrows():
        name = row["player_name"]
        key = normalize(name)
        if key in rich_names_used:
            broad_skipped += 1
            continue
        result.setdefault(key, {})["2025-26"] = map_archive4_row(row.to_dict())
        result[key]["2025-26"]["full_name"] = name
        broad_added += 1

    # --- 2024-25: standalone CSV ---
    std = pd.read_csv(UPLOADS / "epl_player_stats_24_25.csv")
    std.columns = [c.strip() for c in std.columns]
    for _, row in std.iterrows():
        name = row["Player Name"]
        key = normalize(name)
        result.setdefault(key, {})["2024-25"] = map_standalone_2425_row(row.to_dict())
        result[key]["2024-25"]["full_name"] = name

    OUT_PATH.write_text(json.dumps(result, indent=2, default=lambda x: None if (isinstance(x, float) and math.isnan(x)) else x))

    n_2526 = sum(1 for v in result.values() if "2025-26" in v)
    n_2425 = sum(1 for v in result.values() if "2024-25" in v)
    n_both = sum(1 for v in result.values() if "2025-26" in v and "2024-25" in v)
    print(f"players with 2025-26 stats: {n_2526} (from rich file: {len(rich_names_used)}, from broad file: {broad_added}, broad-skipped-as-dupe: {broad_skipped})")
    print(f"players with 2024-25 stats: {n_2425}")
    print(f"players with both seasons: {n_both}")
    print(f"total distinct players across both seasons: {len(result)}")


if __name__ == "__main__":
    main()
