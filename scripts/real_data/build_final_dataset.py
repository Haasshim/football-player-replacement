"""
The final join. Combines:
  - current_squads.json  (who's on which club right now, PDF-sourced)
  - bios.json / bios_mononym_by_club.json (fine position + bio, archive 5)
  - player_season_stats.json (real performance numbers, 2 seasons)
  - team_results.json (real standings + big-game factor)
  - UEFA_COEFFICIENTS (researched separately, see comment below)

into data/teams.csv, data/players.csv, data/player_season_stats.csv -
the same shapes the model (src/) and pipeline already expect, so nothing
downstream needs to know this used to be synthetic data.
"""

import json
from pathlib import Path
import pandas as pd

from name_utils import normalize, match_against_lookup, match_with_mononym_fallback
from club_aliases import to_team_id, CANONICAL_TEAMS

HERE = Path(__file__).parent
DATA_DIR = HERE.parent.parent / "data"

# researched 2025/26-season five-year UEFA club coefficients (football-coefficient.eu,
# as of ~April 2026) for clubs with real recent European football; every other
# current club defaults to the UEFA-defined national floor (20% of England's
# five-season association coefficient, ~19.703 as of this research) since that
# is UEFA's own rule for clubs without enough recent European points to exceed it.
# Newcastle is a rough estimate (two recent Champions League campaigns, precise
# up-to-date total not found) - flagged as approximate.
ENGLAND_FLOOR = 19.703
UEFA_COEFFICIENTS = {
    "LIV": 130.0, "MCI": 125.5, "ARS": 113.5, "CHE": 99.25,
    "TOT": 82.0, "AVL": 78.0, "MUN": 76.5,
    "NEW": 35.0,  # approximate - see comment above
}


def coarse_to_primary_position(coarse: str | None) -> str | None:
    return {"GK": "GK", "DEF": "CB", "MID": "CM", "FWD": "ST"}.get(coarse)


def pick_stat_season(stats_entry: dict) -> tuple[str, dict] | tuple[None, None]:
    """Prefers 2025-26, falls back to 2024-25."""
    if not stats_entry:
        return None, None
    if "2025-26" in stats_entry:
        return "2025-26", stats_entry["2025-26"]
    if "2024-25" in stats_entry:
        return "2024-25", stats_entry["2024-25"]
    return None, None


def build_teams(team_results: dict) -> pd.DataFrame:
    rows = []
    for team_id, name in CANONICAL_TEAMS.items():
        res = team_results.get(team_id, {"no_recent_data": True})
        if res.get("no_recent_data"):
            # newly promoted with no recent top-flight data in our archives:
            # a deliberately modest, clearly-flagged default rather than a guess
            row = {
                "team_id": team_id, "team_name": name, "league": "EPL",
                "final_league_position": 17, "points": 38, "goal_difference": -15,
                "points_per_game_last10": 38 / 38,
                "big_game_factor_pct": 0.0,
                "data_confidence": "no_recent_top_flight_data",
            }
        else:
            row = {
                "team_id": team_id, "team_name": name, "league": "EPL",
                "final_league_position": res["final_league_position"],
                "points": res["points"], "goal_difference": res["goal_difference"],
                "points_per_game_last10": res["points"] / 38,
                "big_game_factor_pct": res["big_game_factor_pct"],
                "data_confidence": "recency_weighted_" + "_".join(str(s) for s in res["seasons_used"]),
            }
        row["uefa_coefficient"] = UEFA_COEFFICIENTS.get(team_id, ENGLAND_FLOOR)
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    squads = json.loads((HERE / "current_squads.json").read_text())
    bios = json.loads((HERE / "bios.json").read_text())
    mononym_index = json.loads((HERE / "bios_mononym_by_club.json").read_text())
    player_season_stats = json.loads((HERE / "player_season_stats.json").read_text())
    team_results = json.loads((HERE / "team_results.json").read_text())

    teams_df = build_teams(team_results)

    player_rows = []
    stat_rows = []
    seen_ids = set()

    match_counts = {"bio": 0, "stats": 0, "both": 0, "neither": 0}

    def resolve_and_add(raw_name: str, club_name: str, team_id: str, extra_flags: dict):
        bio_key = match_with_mononym_fallback(raw_name, bios, team_id, mononym_index)
        stats_key = match_against_lookup(raw_name, player_season_stats)

        bio = bios.get(bio_key) if bio_key else None
        stats_entry = player_season_stats.get(stats_key) if stats_key else None
        season_label, stat_row = pick_stat_season(stats_entry)

        if bio and stat_row:
            match_counts["both"] += 1
        elif bio:
            match_counts["bio"] += 1
        elif stat_row:
            match_counts["stats"] += 1
        else:
            match_counts["neither"] += 1

        # resolve display name, preferring the cleanest known source
        if bio:
            full_name = bio["full_name"]
        elif stat_row:
            full_name = stat_row["full_name"]
        else:
            # last-resort reconstruction: given name(s) + full surname block
            last_block, first_block = raw_name.split(",", 1) if "," in raw_name else (raw_name, "")
            full_name = f"{first_block.strip()} {last_block.strip()}".strip()

        player_id = normalize(full_name).replace(" ", "_") + "_" + team_id.lower()
        if player_id in seen_ids:
            player_id += "_2"
        seen_ids.add(player_id)

        primary_position = None
        if bio and bio.get("primary_position"):
            primary_position = bio["primary_position"]
        elif stat_row and stat_row.get("position_coarse"):
            primary_position = coarse_to_primary_position(stat_row["position_coarse"])
        if not primary_position:
            return  # can't place this player in the model without some position signal

        minutes = (stat_row or {}).get("minutes_played") or 0
        data_confidence = "full" if (bio and stat_row) else ("bio_only" if bio else ("stats_only" if stat_row else "none"))

        player_rows.append({
            "player_id": player_id,
            "full_name": full_name,
            "date_of_birth": (bio or {}).get("date_of_birth"),
            "primary_position": primary_position,
            "club": team_id,
            "nationality": (bio or {}).get("nationality"),
            "market_value": (bio or {}).get("market_value"),
            "data_confidence": data_confidence,
            "low_minutes_flag": bool(minutes and minutes < 270),
            "stat_season_used": season_label,
            **extra_flags,
        })

        if stat_row:
            row = {"player_id": player_id, "season_used": season_label}
            for k, v in stat_row.items():
                if k in ("full_name", "position_coarse", "club"):
                    continue
                row[k] = v
            stat_rows.append(row)

    for club_name, groups in squads.items():
        team_id = to_team_id(club_name)
        if not team_id:
            print("WARNING: unrecognized club in PDF roster:", club_name)
            continue
        for p in groups["squad"]:
            resolve_and_add(p["raw_name"], club_name, team_id, {"home_grown": p["home_grown"], "squad_tier": "first_team"})

        # also pull in U21s who already have real senior stats (genuine
        # breakout players), skip pure scholars with no senior involvement
        for p in groups["u21"]:
            stats_key = match_against_lookup(p["raw_name"], player_season_stats)
            if not stats_key:
                continue
            resolve_and_add(p["raw_name"], club_name, team_id, {"home_grown": p["home_grown"], "squad_tier": "u21_breakout"})

    players_df = pd.DataFrame(player_rows)
    stats_df = pd.DataFrame(stat_rows)

    DATA_DIR.mkdir(exist_ok=True)
    teams_df.to_csv(DATA_DIR / "teams.csv", index=False)
    players_df.to_csv(DATA_DIR / "players.csv", index=False)
    stats_df.to_csv(DATA_DIR / "player_season_stats.csv", index=False)

    print(f"teams: {len(teams_df)}")
    print(f"players: {len(players_df)}  (match breakdown: {match_counts})")
    print(f"stat rows: {len(stats_df)}")
    print("players by data_confidence:", players_df["data_confidence"].value_counts().to_dict())
    print("players by squad_tier:", players_df["squad_tier"].value_counts().to_dict())
    print("players by primary_position:", players_df["primary_position"].value_counts().to_dict())


if __name__ == "__main__":
    main()
