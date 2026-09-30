"""
Parses archive 5 (per-club, per-season bio/roster JSON, 1992-2026) filtered
to the most recent seasons, into one bio record per player keyed by
normalized name, preferring the most recent season available for each.

Output: scripts/real_data/bios.json
  { normalized_name: {full_name, date_of_birth, nationality, height, foot,
                       position_fine, market_value, club_in_season,
                       season, is_loan} }
"""

import json
from pathlib import Path
from name_utils import normalize, nickname_variants
from club_aliases import to_team_id

ARCHIVE5_DIR = Path("/home/claude/uploads_inspect/a5/DATA_JSON")
OUT_PATH = Path(__file__).parent / "bios.json"
MONONYM_INDEX_PATH = Path(__file__).parent / "bios_mononym_by_club.json"

# most recent first: prefer a player's latest available season record
SEASONS_IN_SCOPE = ["Season_2026", "Season_2025", "Season_2024", "Season_2023", "Season_2022"]

POSITION_MAP = {
    "Goalkeeper": "GK",
    "Centre-Back": "CB",
    "Left-Back": "FB",
    "Right-Back": "FB",
    "Defensive Midfield": "DM",
    "Central Midfield": "CM",
    "Attacking Midfield": "AM",
    "Left Midfield": "WING",
    "Right Midfield": "WING",
    "Left Winger": "WING",
    "Right Winger": "WING",
    "Centre-Forward": "ST",
    "Second Striker": "ST",
}


def club_name_from_filename(path: Path) -> str:
    # e.g. "Arsenal_FC_11_2024.json" -> "Arsenal FC"
    stem = path.stem
    parts = stem.split("_")
    # drop the trailing numeric club id and season year
    parts = parts[:-2]
    return " ".join(parts)


def main():
    bios = {}
    coverage_by_season = {}

    for season in SEASONS_IN_SCOPE:
        season_dir = ARCHIVE5_DIR / season
        if not season_dir.exists():
            continue
        count = 0
        for f in season_dir.glob("*.json"):
            club = club_name_from_filename(f)
            data = json.loads(f.read_text())
            for p in data.get("players", []):
                name = p.get("name", "").strip()
                if not name:
                    continue
                key = normalize(name)
                if key in bios:
                    continue  # already have a more recent record for this player
                position_fine = p.get("position", "")
                bios[key] = {
                    "full_name": name,
                    "date_of_birth": p.get("dateOfBirth") or None,
                    "nationality": (p.get("nationality") or [None])[0],
                    "height": p.get("height"),
                    "foot": p.get("foot"),
                    "position_fine": position_fine,
                    "primary_position": POSITION_MAP.get(position_fine),
                    "market_value": p.get("marketValue"),
                    "club_in_season": club,
                    "season": season,
                    "is_loan": bool(p.get("isLoan")),
                }
                count += 1
        coverage_by_season[season] = count

    OUT_PATH.write_text(json.dumps(bios, indent=2))

    # secondary index for mononym players (e.g. archive 5 lists Arsenal's
    # Gabriel Magalhaes simply as "Gabriel"): (team_id, first-name-token) -> key
    mononym_index = {}
    for key, bio in bios.items():
        team_id = to_team_id(bio["club_in_season"])
        if not team_id:
            continue
        first_token = bio["full_name"].split()[0]
        for variant in nickname_variants(first_token):
            mononym_index[f"{team_id}|{normalize(variant)}"] = key
    MONONYM_INDEX_PATH.write_text(json.dumps(mononym_index, indent=2))

    print("bios collected:", len(bios))
    print("new records contributed per season (most-recent-wins):", coverage_by_season)
    missing_position = sum(1 for b in bios.values() if not b["primary_position"])
    print("records with unmapped position:", missing_position)
    print("mononym-by-club index entries:", len(mononym_index))


if __name__ == "__main__":
    main()
