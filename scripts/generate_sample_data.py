"""
Generates a small, clearly-synthetic EPL-shaped dataset so the pipeline
can be run and tested end to end before real data is loaded.

This is placeholder data, not real season stats. Team names are real
(for a realistic-looking demo) but every number here is randomly
generated. Replace the CSVs in data/ with real sourced data using the
same column layout described in data/README.md.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 7
rng = np.random.default_rng(SEED)

TEAMS = [
    # team_id, team_name, final_league_position, points, ppg_last10, goal_diff, uefa_coeff
    ("MCI", "Manchester City", 1, 89, 2.3, 55, 106.0),
    ("ARS", "Arsenal", 2, 84, 2.1, 45, 88.0),
    ("LIV", "Liverpool", 3, 79, 1.9, 38, 92.0),
    ("CHE", "Chelsea", 4, 71, 1.7, 22, 61.0),
    ("TOT", "Tottenham Hotspur", 5, 68, 1.6, 15, 54.0),
    ("NEW", "Newcastle United", 6, 63, 1.4, 10, 38.0),
    ("BHA", "Brighton & Hove Albion", 7, 58, 1.3, 4, 22.0),
    ("EVE", "Everton", 8, 45, 1.0, -8, 9.0),
]

SQUAD_TEMPLATE = ["GK", "GK", "CB", "CB", "CB", "FB", "FB", "DM", "CM", "CM", "AM", "WING", "WING", "ST"]

STARTING_POSITIONS = {
    "GK": 1, "CB": 2, "FB": 2, "DM": 1, "CM": 2, "AM": 0, "WING": 2, "ST": 1,
}

FIRST_NAMES = ["James", "Marcus", "Kai", "Bukayo", "Declan", "Mason", "Levi", "Cole",
               "Ezri", "Rico", "Anthony", "Jarrad", "Rasmus", "Kalvin", "Tyrick",
               "Conor", "Emile", "Morgan", "Curtis", "Reece"]
LAST_NAMES = ["Osei", "Whitfield", "Adeyemi", "Doran", "Marsh", "Iwobi", "Colwill",
              "Bright", "Nkunku", "Toney", "Maguire", "Branthwaite", "Gordon",
              "Anderson", "Palmer", "Konate", "Gvardiol", "Rice", "Saka", "Havertz"]

# baseline per-90 rates by position: (mean, std) for pure count stats
COUNT_BASELINES = {
    #                 goals        assists      xg           xa           shots        sot          key_passes   prog_pass    prog_carry   dribbled_past  interceptions  blocks       clearances   recoveries   fouls        through_balls touches_box
    "GK":  dict(goals=(0.0,0.0), assists=(0.0,0.0), xg=(0.0,0.0), xa=(0.0,0.0), shots=(0.0,0.0), shots_on_target=(0.0,0.0), key_passes=(0.05,0.05), progressive_passes=(1.5,0.5), progressive_carries=(0.1,0.1), times_dribbled_past=(0.0,0.0), interceptions=(0.2,0.2), blocks=(0.1,0.1), clearances=(3.0,1.0), recoveries=(2.0,0.5), fouls_committed=(0.05,0.05), through_balls=(0.0,0.0), touches_in_box=(0.0,0.0)),
    "CB":  dict(goals=(0.03,0.03), assists=(0.02,0.02), xg=(0.05,0.03), xa=(0.03,0.02), shots=(0.3,0.2), shots_on_target=(0.1,0.1), key_passes=(0.3,0.2), progressive_passes=(4.5,1.2), progressive_carries=(0.8,0.4), times_dribbled_past=(0.4,0.2), interceptions=(1.8,0.6), blocks=(1.2,0.5), clearances=(4.5,1.3), recoveries=(5.5,1.4), fouls_committed=(0.8,0.3), through_balls=(0.05,0.05), touches_in_box=(0.4,0.2)),
    "FB":  dict(goals=(0.05,0.04), assists=(0.12,0.06), xg=(0.08,0.05), xa=(0.16,0.07), shots=(0.6,0.3), shots_on_target=(0.2,0.15), key_passes=(1.1,0.4), progressive_passes=(3.8,1.0), progressive_carries=(2.4,0.8), times_dribbled_past=(0.8,0.3), interceptions=(1.3,0.5), blocks=(0.7,0.3), clearances=(2.2,0.8), recoveries=(4.8,1.2), fouls_committed=(0.9,0.3), through_balls=(0.2,0.1), touches_in_box=(1.0,0.4)),
    "DM":  dict(goals=(0.05,0.04), assists=(0.08,0.05), xg=(0.06,0.04), xa=(0.1,0.05), shots=(0.7,0.3), shots_on_target=(0.25,0.15), key_passes=(0.9,0.4), progressive_passes=(5.5,1.3), progressive_carries=(1.3,0.5), times_dribbled_past=(0.3,0.2), interceptions=(2.1,0.6), blocks=(1.0,0.4), clearances=(1.8,0.6), recoveries=(6.5,1.5), fouls_committed=(1.1,0.4), through_balls=(0.15,0.1), touches_in_box=(0.5,0.2)),
    "CM":  dict(goals=(0.15,0.08), assists=(0.16,0.08), xg=(0.18,0.08), xa=(0.2,0.08), shots=(1.3,0.5), shots_on_target=(0.45,0.2), key_passes=(1.4,0.5), progressive_passes=(5.0,1.2), progressive_carries=(2.2,0.7), times_dribbled_past=(0.3,0.2), interceptions=(1.4,0.5), blocks=(0.6,0.3), clearances=(1.0,0.4), recoveries=(5.0,1.3), fouls_committed=(0.9,0.3), through_balls=(0.4,0.2), touches_in_box=(1.2,0.5)),
    "AM":  dict(goals=(0.28,0.1), assists=(0.28,0.1), xg=(0.32,0.1), xa=(0.32,0.1), shots=(1.9,0.6), shots_on_target=(0.7,0.3), key_passes=(2.1,0.6), progressive_passes=(4.2,1.1), progressive_carries=(3.0,0.9), times_dribbled_past=(0.15,0.1), interceptions=(0.7,0.3), blocks=(0.2,0.15), clearances=(0.3,0.2), recoveries=(3.5,1.0), fouls_committed=(0.7,0.3), through_balls=(0.6,0.25), touches_in_box=(2.4,0.7)),
    "WING":dict(goals=(0.35,0.12), assists=(0.3,0.1), xg=(0.38,0.12), xa=(0.34,0.1), shots=(2.3,0.7), shots_on_target=(0.9,0.35), key_passes=(1.8,0.55), progressive_passes=(3.0,0.9), progressive_carries=(3.8,1.0), times_dribbled_past=(0.1,0.1), interceptions=(0.5,0.25), blocks=(0.15,0.1), clearances=(0.2,0.15), recoveries=(3.0,0.9), fouls_committed=(0.5,0.25), through_balls=(0.3,0.15), touches_in_box=(2.8,0.8)),
    "ST":  dict(goals=(0.55,0.15), assists=(0.18,0.08), xg=(0.58,0.15), xa=(0.2,0.08), shots=(3.2,0.8), shots_on_target=(1.4,0.4), key_passes=(1.0,0.4), progressive_passes=(1.8,0.6), progressive_carries=(1.6,0.6), times_dribbled_past=(0.05,0.05), interceptions=(0.3,0.15), blocks=(0.1,0.1), clearances=(0.15,0.1), recoveries=(2.2,0.7), fouls_committed=(0.6,0.25), through_balls=(0.1,0.08), touches_in_box=(3.5,0.9)),
}

# baseline per-90 rates for attempted/completed pairs: (attempts_mean, attempts_std, success_rate_mean, success_rate_std)
PCT_BASELINES = {
    "GK":  dict(passes=(28,4,0.78,0.06), dribbles=(0.1,0.1,0.5,0.2), tackles=(0.1,0.1,0.5,0.2), aerial=(0.3,0.2,0.55,0.15), duels=(0.5,0.3,0.55,0.15), crosses=(0.0,0.0,0.5,0.1), long_passes=(8,2,0.62,0.1)),
    "CB":  dict(passes=(58,8,0.88,0.05), dribbles=(0.6,0.3,0.55,0.15), tackles=(1.6,0.5,0.68,0.12), aerial=(4.0,1.0,0.64,0.1), duels=(4.5,1.1,0.58,0.1), crosses=(0.2,0.2,0.35,0.15), long_passes=(6.5,1.8,0.66,0.1)),
    "FB":  dict(passes=(48,7,0.82,0.06), dribbles=(1.8,0.6,0.58,0.13), tackles=(2.1,0.6,0.62,0.12), aerial=(1.2,0.5,0.5,0.15), duels=(4.0,1.0,0.54,0.1), crosses=(3.2,1.0,0.32,0.1), long_passes=(3.5,1.2,0.58,0.12)),
    "DM":  dict(passes=(62,8,0.87,0.05), dribbles=(1.2,0.5,0.6,0.13), tackles=(2.4,0.6,0.64,0.12), aerial=(1.6,0.6,0.55,0.13), duels=(5.2,1.2,0.56,0.1), crosses=(0.4,0.3,0.3,0.15), long_passes=(5.0,1.5,0.6,0.11)),
    "CM":  dict(passes=(52,7,0.85,0.05), dribbles=(1.8,0.6,0.6,0.13), tackles=(1.7,0.5,0.6,0.12), aerial=(1.1,0.5,0.48,0.14), duels=(3.8,1.0,0.53,0.1), crosses=(0.9,0.5,0.3,0.15), long_passes=(3.2,1.1,0.55,0.12)),
    "AM":  dict(passes=(42,6,0.83,0.05), dribbles=(3.0,0.8,0.6,0.12), tackles=(0.9,0.4,0.55,0.13), aerial=(0.5,0.3,0.42,0.15), duels=(2.6,0.8,0.5,0.11), crosses=(1.2,0.6,0.28,0.13), long_passes=(1.4,0.7,0.5,0.13)),
    "WING":dict(passes=(32,5,0.78,0.06), dribbles=(4.5,1.1,0.55,0.12), tackles=(0.7,0.3,0.52,0.13), aerial=(0.4,0.25,0.38,0.14), duels=(2.2,0.7,0.47,0.11), crosses=(3.6,1.1,0.3,0.12), long_passes=(0.6,0.4,0.45,0.14)),
    "ST":  dict(passes=(22,4,0.72,0.07), dribbles=(1.9,0.6,0.5,0.13), tackles=(0.4,0.25,0.5,0.15), aerial=(3.0,0.9,0.46,0.13), duels=(3.6,0.9,0.5,0.11), crosses=(0.3,0.25,0.3,0.15), long_passes=(0.4,0.3,0.45,0.15)),
}

GK_ONLY = dict(saves=(2.6, 0.9), goals_against=(1.15, 0.5), psxg_over_baseline=(0.0, 0.3), clean_sheet_prob=0.32)


def _clip_poisson(mean):
    mean = max(mean, 0.0)
    return int(rng.poisson(mean)) if mean > 0 else 0


def _clip_binomial(n, p):
    p = min(max(p, 0.0), 1.0)
    return int(rng.binomial(n, p)) if n > 0 else 0


def build_teams_df():
    rows = []
    for team_id, name, pos, pts, ppg, gd, uefa in TEAMS:
        rows.append({
            "team_id": team_id, "team_name": name, "league": "EPL",
            "final_league_position": pos, "points": pts,
            "points_per_game_last10": ppg, "goal_difference": gd,
            "uefa_coefficient": uefa,
        })
    return pd.DataFrame(rows)


def build_players_df():
    rows = []
    name_pool = [(f, l) for f in FIRST_NAMES for l in LAST_NAMES]
    rng.shuffle(name_pool)
    idx = 0
    player_quality = {}  # player_id -> (quality, clutch_factor), used only for generation

    for team_id, name, *_ in TEAMS:
        for slot, position in enumerate(SQUAD_TEMPLATE):
            first, last = name_pool[idx % len(name_pool)]
            idx += 1
            player_id = f"{last.lower()}_{first.lower()}_{team_id.lower()}_{slot}"
            dob_year = rng.integers(1996, 2007)
            quality = float(np.clip(rng.normal(0, 1), -2, 2))
            clutch = float(np.clip(rng.normal(0, 0.18), -0.4, 0.4))
            player_quality[player_id] = (quality, clutch)
            rows.append({
                "player_id": player_id,
                "full_name": f"{first} {last}",
                "date_of_birth": f"{dob_year}-0{rng.integers(1,9)}-1{rng.integers(0,9)}",
                "primary_position": position,
                "club": team_id,
                "nationality": "N/A",
            })
    return pd.DataFrame(rows), player_quality


def build_fixtures_df():
    rows = []
    team_ids = [t[0] for t in TEAMS]
    fixture_num = 0
    for i, home in enumerate(team_ids):
        for away in team_ids[i + 1:]:
            fixture_num += 1
            home_goals = int(rng.poisson(1.4))
            away_goals = int(rng.poisson(1.1))
            rows.append({
                "fixture_id": f"F{fixture_num:03d}_{home}_{away}",
                "date": f"2025-{(fixture_num % 9) + 1:02d}-{(fixture_num % 27) + 1:02d}",
                "home_team_id": home, "away_team_id": away,
                "home_score": home_goals, "away_score": away_goals,
            })
    return pd.DataFrame(rows)


def build_match_stats_df(players_df, fixtures_df, player_quality, teams_df):
    team_strength_lookup = {
        row["team_id"]: (row["final_league_position"], row["uefa_coefficient"])
        for _, row in teams_df.iterrows()
    }
    # crude relative strength just for generation flavor (not the real model)
    max_uefa = max(v[1] for v in team_strength_lookup.values())
    strength = {tid: 0.5 + 0.5 * (uefa / max_uefa) for tid, (_, uefa) in team_strength_lookup.items()}

    squads = {}
    for team_id, group in players_df.groupby("club"):
        players_by_pos = {}
        for _, row in group.iterrows():
            players_by_pos.setdefault(row["primary_position"], []).append(row["player_id"])
        squads[team_id] = players_by_pos

    rows = []
    for _, fx in fixtures_df.iterrows():
        for team_id, opp_id in [(fx["home_team_id"], fx["away_team_id"]), (fx["away_team_id"], fx["home_team_id"])]:
            difficulty = strength[opp_id] / strength[team_id]
            starters = []
            bench = []
            for pos, ids in squads[team_id].items():
                n_start = STARTING_POSITIONS.get(pos, 0)
                starters += ids[:n_start]
                bench += ids[n_start:]

            for player_id in starters:
                minutes = int(np.clip(rng.normal(85, 8), 45, 90))
                rows.append(_generate_row(fx["fixture_id"], player_id, team_id, minutes, difficulty, players_df, player_quality))

            for player_id in bench:
                if rng.random() < 0.35:
                    minutes = int(np.clip(rng.normal(20, 12), 1, 45))
                    rows.append(_generate_row(fx["fixture_id"], player_id, team_id, minutes, difficulty, players_df, player_quality))

    return pd.DataFrame(rows)


def _generate_row(fixture_id, player_id, team_id, minutes, difficulty, players_df, player_quality):
    position = players_df.loc[players_df["player_id"] == player_id, "primary_position"].iloc[0]
    quality, clutch = player_quality[player_id]
    # a clutch player's rates get a boost the tougher the opponent; others fade slightly
    difficulty_modifier = 1 + clutch * max(0.0, difficulty - 1) * 2
    quality_modifier = 1 + 0.12 * quality
    minute_frac = minutes / 90.0

    counts = COUNT_BASELINES[position]
    row = {
        "fixture_id": fixture_id, "player_id": player_id, "team_id": team_id,
        "minutes_played": minutes, "position_played": position,
    }
    for stat, (mean, _std) in counts.items():
        adj_mean = mean * minute_frac * difficulty_modifier * quality_modifier
        row[stat] = _clip_poisson(adj_mean)

    pcts = PCT_BASELINES[position]
    def pct_pair(key, attempted_col, completed_col):
        a_mean, _a_std, rate_mean, _rate_std = pcts[key]
        attempted = _clip_poisson(a_mean * minute_frac * quality_modifier)
        rate = min(max(rate_mean * difficulty_modifier, 0.05), 0.98)
        completed = _clip_binomial(attempted, rate)
        row[attempted_col] = attempted
        row[completed_col] = completed

    pct_pair("passes", "passes_attempted", "passes_completed")
    pct_pair("dribbles", "dribbles_attempted", "dribbles_completed")
    pct_pair("tackles", "tackles", "tackles_won")
    pct_pair("aerial", "aerial_duels_total", "aerial_duels_won")
    pct_pair("duels", "duels_total", "duels_won")
    pct_pair("crosses", "crosses_attempted", "crosses_completed")
    pct_pair("long_passes", "passes_long_attempted", "passes_long_completed")

    if position == "GK":
        saves_mean, _ = GK_ONLY["saves"]
        ga_mean, _ = GK_ONLY["goals_against"]
        row["saves"] = _clip_poisson(saves_mean * minute_frac / max(difficulty_modifier, 0.4))
        row["goals_against"] = _clip_poisson(ga_mean * minute_frac * difficulty_modifier)
        row["post_shot_xg"] = round(float(row["goals_against"]) + rng.normal(0, 0.3), 2)
        row["clean_sheet"] = bool(row["goals_against"] == 0)
    else:
        row["saves"] = 0
        row["goals_against"] = 0
        row["post_shot_xg"] = 0.0
        row["clean_sheet"] = False

    for float_col in ("goals", "assists"):
        row[float_col] = int(row[float_col])
    row["xg"] = round(counts["xg"][0] * minute_frac * quality_modifier * difficulty_modifier + rng.normal(0, 0.05), 2)
    row["xa"] = round(counts["xa"][0] * minute_frac * quality_modifier * difficulty_modifier + rng.normal(0, 0.05), 2)
    row["xg"] = max(0.0, row["xg"])
    row["xa"] = max(0.0, row["xa"])

    return row


def main(out_dir: str):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    teams_df = build_teams_df()
    players_df, player_quality = build_players_df()
    fixtures_df = build_fixtures_df()
    match_stats_df = build_match_stats_df(players_df, fixtures_df, player_quality, teams_df)

    teams_df.to_csv(out / "teams.csv", index=False)
    players_df.to_csv(out / "players.csv", index=False)
    fixtures_df.to_csv(out / "fixtures.csv", index=False)
    match_stats_df.to_csv(out / "player_match_stats.csv", index=False)

    print(f"wrote {len(teams_df)} teams, {len(players_df)} players, "
          f"{len(fixtures_df)} fixtures, {len(match_stats_df)} match-stat rows to {out}")


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "data"
    main(out_dir)
