"""
Every dataset spells club names differently (football-data.co.uk style
short names in archive 2, FBref-style full names in archive 3, plain
names in the stat CSVs, "X FC" folder names in archive 5, and the PL's
own names in the PDF). This maps every variant to one canonical team_id
for the 20 clubs in the 2026/27 Premier League.
"""

from name_utils import normalize

CANONICAL_TEAMS = {
    "BOU": "AFC Bournemouth",
    "ARS": "Arsenal",
    "AVL": "Aston Villa",
    "BRE": "Brentford",
    "BHA": "Brighton & Hove Albion",
    "CHE": "Chelsea",
    "COV": "Coventry City",
    "CRY": "Crystal Palace",
    "EVE": "Everton",
    "FUL": "Fulham",
    "HUL": "Hull City",
    "IPS": "Ipswich Town",
    "LEE": "Leeds United",
    "LIV": "Liverpool",
    "MCI": "Manchester City",
    "MUN": "Manchester United",
    "NEW": "Newcastle United",
    "NFO": "Nottingham Forest",
    "SUN": "Sunderland",
    "TOT": "Tottenham Hotspur",
}

_ALIASES = {
    "BOU": ["bournemouth", "afc bournemouth"],
    "ARS": ["arsenal", "arsenal fc"],
    "AVL": ["aston villa"],
    "BRE": ["brentford", "brentford fc"],
    "BHA": ["brighton", "brighton and hove albion", "brighton & hove albion"],
    "CHE": ["chelsea", "chelsea fc"],
    "COV": ["coventry", "coventry city"],
    "CRY": ["crystal palace"],
    "EVE": ["everton", "everton fc"],
    "FUL": ["fulham", "fulham fc"],
    "HUL": ["hull", "hull city"],
    "IPS": ["ipswich", "ipswich town"],
    "LEE": ["leeds", "leeds united"],
    "LIV": ["liverpool", "liverpool fc"],
    "MCI": ["man city", "manchester city"],
    "MUN": ["man united", "man utd", "manchester united", "manchester utd"],
    "NEW": ["newcastle", "newcastle utd", "newcastle united"],
    "NFO": ["nott'm forest", "nott'ham forest", "nottingham forest"],
    "SUN": ["sunderland", "sunderland afc"],
    "TOT": ["tottenham", "tottenham hotspur"],
}

# build the reverse lookup once, keyed by normalize()d alias
_ALIAS_TO_ID = {}
for team_id, aliases in _ALIASES.items():
    for alias in aliases:
        _ALIAS_TO_ID[normalize(alias)] = team_id


def to_team_id(raw_name: str) -> str | None:
    """Returns the canonical team_id for any known spelling, or None."""
    return _ALIAS_TO_ID.get(normalize(raw_name))
