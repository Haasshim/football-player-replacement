"""
Parses the pdftotext -layout output of the Premier League's 2026/27 squad
list announcement into structured per-club rosters.

Output: scripts/real_data/current_squads.json
  { club_name: { "squad": [{"raw_name": "...", "home_grown": bool}],
                 "u21": [{"raw_name": "...", "home_grown": bool, "loan": bool}] } }

raw_name is still in "Lastname(s), Firstname(s)" order at this stage;
name reconstruction into "First Last" happens in match_players.py, where
it can be checked against the real stat datasets.
"""

import json
import re
from pathlib import Path

RAW_PATH = Path(__file__).parent / "squads_raw.txt"
OUT_PATH = Path(__file__).parent / "current_squads.json"

NOISE_PATTERNS = [
    re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4},\s*\d"),   # date/time header
    re.compile(r"^https://"),                          # footer url
    re.compile(r"^\d+/\d+$"),                           # page number "27/45"
    re.compile(r"^\x0c"),                               # form feed
]


def is_noise(line: str) -> bool:
    s = line.strip()
    if not s:
        return True
    return any(p.match(s) for p in NOISE_PATTERNS)


def main():
    lines = RAW_PATH.read_text(encoding="utf-8").split("\n")
    marker_idx = [i for i, l in enumerate(lines) if "25 Squad players" in l]

    clubs = {}
    for k, idx in enumerate(marker_idx):
        # find club name: nearest non-noise line above the marker
        j = idx - 1
        while j >= 0 and is_noise(lines[j]):
            j -= 1
        club_name = lines[j].strip()

        # section runs until the next club's "name line" (or end of roster section)
        end = marker_idx[k + 1] if k + 1 < len(marker_idx) else len(lines)
        # back up 'end' to before the next club name + any noise lines preceding it
        j2 = end - 1
        while j2 > idx and is_noise(lines[j2]):
            j2 -= 1
        section = lines[idx + 1:j2]  # excludes the next club's name line itself

        squad, u21 = [], []
        mode = "squad"
        for raw in section:
            if is_noise(raw):
                continue
            s = raw.strip()
            if "U21 players" in s:
                mode = "u21"
                continue
            if not s or s.endswith(":"):
                continue
            # a player line always contains a comma (Lastname, Firstname)
            if "," not in s:
                continue
            home_grown = s.endswith("*") or s.rstrip().endswith("* (Loan)") or "*" in s.split("(")[0][-2:]
            loan = "(Loan)" in s
            clean = s.replace("(Loan)", "").strip()
            home_grown = clean.endswith("*")
            clean = clean.rstrip("*").strip()
            entry = {"raw_name": clean, "home_grown": home_grown}
            if mode == "u21":
                entry["loan"] = loan
                u21.append(entry)
            else:
                squad.append(entry)

        clubs[club_name] = {"squad": squad, "u21": u21}

    OUT_PATH.write_text(json.dumps(clubs, indent=2))
    total_squad = sum(len(c["squad"]) for c in clubs.values())
    total_u21 = sum(len(c["u21"]) for c in clubs.values())
    print(f"parsed {len(clubs)} clubs, {total_squad} squad players, {total_u21} U21 players")
    for name in clubs:
        print(" -", name, len(clubs[name]["squad"]), "squad +", len(clubs[name]["u21"]), "u21")


if __name__ == "__main__":
    main()
