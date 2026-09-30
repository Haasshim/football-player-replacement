"""
Computes, per team, a blend of its last 3-4 Premier League seasons'
standings (from archive 3's team-perspective match log) into:
  - a recency-weighted final_league_position / points / goal_difference
  - a big_game_factor_pct: how much better (or worse) the team's points
    per game was against top-half opponents vs bottom-half opponents
    that same season, blended the same way. This replaces per-match
    player-level "big game" weighting, which the real data can't support
    (see README) - it's a real, match-result-derived team property.

Clubs with zero recent top-flight data (this season's newly promoted
Coventry, Hull, Sunderland) get an explicit "no_recent_data" flag instead
of a guessed number.

Output: scripts/real_data/team_results.json
"""

import json
from pathlib import Path
import pandas as pd
from club_aliases import to_team_id, CANONICAL_TEAMS

A3_PATH = Path("/home/claude/uploads_inspect/a3/final_matches.csv")
OUT_PATH = Path(__file__).parent / "team_results.json"

# most recent season weighted highest; only seasons a team actually has
# data for are used, renormalized
SEASON_WEIGHTS = {2025: 0.40, 2024: 0.30, 2023: 0.20, 2022: 0.10}
STRONG_OPPONENT_MAX_POSITION = 10  # top half of a 20-team table


def compute_season_table(season_df: pd.DataFrame) -> dict:
    """Returns {team_id: {points, goal_difference, final_league_position}} for one season."""
    table = {}
    for team, group in season_df.groupby("team"):
        team_id = to_team_id(team)
        if not team_id:
            continue
        points = 0
        gf, ga = 0, 0
        for _, row in group.iterrows():
            if row["result"] == "W":
                points += 3
            elif row["result"] == "D":
                points += 1
            gf += row["gf"]
            ga += row["ga"]
        table[team_id] = {"points": points, "goal_difference": gf - ga, "goals_for": gf}

    ranked = sorted(table.items(), key=lambda kv: (-kv[1]["points"], -kv[1]["goal_difference"], -kv[1]["goals_for"]))
    for pos, (team_id, row) in enumerate(ranked, start=1):
        row["final_league_position"] = pos
    return table


def compute_big_game_factor(season_df: pd.DataFrame, table: dict) -> dict:
    """
    Returns {team_id: big_game_factor_pct} for one season: how a team's
    points-per-game against top-half opponents compares to what their
    overall season form would predict, given how much harder top-half
    opponents are for the league as a whole. A team that is simply good
    overall (and so beats everyone, strong included) nets out to ~0 here;
    a positive number means they specifically raise their level against
    strong opposition beyond what their general level predicts.
    """
    per_team_strong, per_team_all = {}, {}
    for team, group in season_df.groupby("team"):
        team_id = to_team_id(team)
        if not team_id or team_id not in table:
            continue
        strong_pts, strong_games = 0, 0
        all_pts, all_games = 0, 0
        for _, row in group.iterrows():
            pts = 3 if row["result"] == "W" else (1 if row["result"] == "D" else 0)
            all_pts += pts
            all_games += 1
            opp_id = to_team_id(row["opponent"])
            opp_position = table.get(opp_id, {}).get("final_league_position")
            if opp_position is not None and opp_position <= STRONG_OPPONENT_MAX_POSITION:
                strong_pts += pts
                strong_games += 1
        if all_games:
            per_team_all[team_id] = all_pts / all_games
        if strong_games:
            per_team_strong[team_id] = strong_pts / strong_games

    if not per_team_strong or not per_team_all:
        return {}

    league_avg_vs_strong = sum(per_team_strong.values()) / len(per_team_strong)
    league_avg_overall = sum(per_team_all.values()) / len(per_team_all)
    difficulty_discount = league_avg_vs_strong / league_avg_overall if league_avg_overall else 1.0

    factors = {}
    for team_id, ppg_strong in per_team_strong.items():
        overall_ppg = per_team_all.get(team_id)
        if not overall_ppg:
            continue
        expected_ppg_vs_strong = overall_ppg * difficulty_discount
        if expected_ppg_vs_strong == 0:
            continue
        factor = 100 * (ppg_strong / expected_ppg_vs_strong - 1)
        factors[team_id] = max(-75.0, min(100.0, factor))
    return factors


def main():
    df = pd.read_csv(A3_PATH)
    per_season_tables = {}
    per_season_factors = {}

    for season in sorted(df["season"].unique()):
        season_df = df[df["season"] == season]
        table = compute_season_table(season_df)
        per_season_tables[season] = table
        per_season_factors[season] = compute_big_game_factor(season_df, table)

    blended = {}
    for team_id in CANONICAL_TEAMS:
        available_seasons = [s for s in SEASON_WEIGHTS if team_id in per_season_tables.get(s, {})]
        if not available_seasons:
            blended[team_id] = {"no_recent_data": True}
            continue
        total_weight = sum(SEASON_WEIGHTS[s] for s in available_seasons)
        pos_sum = sum(SEASON_WEIGHTS[s] * per_season_tables[s][team_id]["final_league_position"] for s in available_seasons)
        gd_sum = sum(SEASON_WEIGHTS[s] * per_season_tables[s][team_id]["goal_difference"] for s in available_seasons)
        pts_sum = sum(SEASON_WEIGHTS[s] * per_season_tables[s][team_id]["points"] for s in available_seasons)

        factor_seasons = [s for s in available_seasons if team_id in per_season_factors.get(s, {})]
        if factor_seasons:
            factor_weight = sum(SEASON_WEIGHTS[s] for s in factor_seasons)
            big_game_factor = sum(SEASON_WEIGHTS[s] * per_season_factors[s][team_id] for s in factor_seasons) / factor_weight
        else:
            big_game_factor = 0.0

        blended[team_id] = {
            "no_recent_data": False,
            "final_league_position": round(pos_sum / total_weight, 2),
            "goal_difference": round(gd_sum / total_weight, 2),
            "points": round(pts_sum / total_weight, 2),
            "big_game_factor_pct": round(big_game_factor, 1),
            "seasons_used": available_seasons,
        }

    OUT_PATH.write_text(json.dumps(blended, indent=2))
    for team_id, row in blended.items():
        print(team_id, row)


if __name__ == "__main__":
    main()
