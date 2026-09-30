"""
Shared name-handling utilities for joining the PDF roster (which lists
"Lastname(s), Firstname(s)") against stat datasets that use natural
"Firstname Lastname" display names, and for fuzzy-matching across
datasets with different accenting/spelling.
"""

import re
import unicodedata

# letters that don't decompose under NFKD (not base+combining-accent), so
# they survive naive accent-stripping unless mapped explicitly
_MANUAL_CHAR_MAP = str.maketrans({
    "\u00d8": "O", "\u00f8": "o",  # Ø ø
    "\u00c6": "AE", "\u00e6": "ae",  # Æ æ
    "\u0110": "D", "\u0111": "d",  # Đ đ
    "\u00de": "Th", "\u00fe": "th",  # Þ þ
    "\u0141": "L", "\u0142": "l",  # Ł ł
    "\u1e9e": "SS", "\u00df": "ss",  # ẞ ß
    "\u0152": "OE", "\u0153": "oe",  # Œ œ
})

# common football nickname <-> given-name equivalences, tried in both directions
_NICKNAMES = {
    "max": "maximilian", "maximillian": "maximilian", "maximiliano": "maximilian",
    "ben": "benjamin", "benji": "benjamin",
    "matt": "matthew", "matty": "matthew",
    "alex": "alexander", "sasha": "alexander",
    "tom": "thomas", "tommy": "thomas",
    "will": "william", "billy": "william", "liam": "william",
    "nick": "nicholas", "nico": "nicholas",
    "sam": "samuel", "sammy": "samuel",
    "josh": "joshua",
    "dan": "daniel", "danny": "daniel",
    "mike": "michael", "mikey": "michael", "micky": "michael", "mick": "michael",
    "chris": "christopher", "kit": "christopher",
    "rob": "robert", "bobby": "robert", "robbie": "robert",
    "jack": "john", "jamie": "james", "jim": "james", "jimmy": "james",
    "charlie": "charles", "harry": "harold",
    "ed": "edward", "eddie": "edward", "teddy": "edward",
    "joe": "joseph", "joey": "joseph",
    "andy": "andrew", "drew": "andrew",
    "tony": "anthony",
    "steve": "stephen", "stevie": "stephen",
    "dave": "david", "davey": "david",
    "pat": "patrick", "paddy": "patrick",
    "fred": "frederick", "freddie": "frederick",
}


def normalize(name: str) -> str:
    """Lowercase, strip accents/diacritics, keep only letters/spaces/hyphens."""
    if not name:
        return ""
    name = name.translate(_MANUAL_CHAR_MAP)
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_only = "".join(c for c in nfkd if not unicodedata.combining(c))
    ascii_only = ascii_only.lower()
    ascii_only = re.sub(r"[^a-z\s\-']", " ", ascii_only)
    ascii_only = re.sub(r"\s+", " ", ascii_only).strip()
    return ascii_only


def nickname_variants(first_name: str) -> list[str]:
    """Returns [first_name] plus any known nickname/formal-name equivalents."""
    key = first_name.lower()
    variants = {key}
    if key in _NICKNAMES:
        variants.add(_NICKNAMES[key])
    for nick, formal in _NICKNAMES.items():
        if formal == key:
            variants.add(nick)
    return list(variants)


def reconstruct_name_candidates(raw_name: str) -> list[str]:
    """
    raw_name is "Lastname(s), Firstname(s)" as printed in the PL squad list.
    Real-world "popular" names use inconsistent parts of multi-word surnames
    (e.g. "Guimaraes Rodriguez Moura, Bruno" -> "Bruno Guimaraes", but
    "Dos Santos Magalhaes, Gabriel" -> "Gabriel Magalhaes") so this returns
    every contiguous substring of the surname tokens combined with the
    first given name, for the caller to test against a known-name lookup.
    """
    if "," not in raw_name:
        return [raw_name]
    last_block, first_block = raw_name.split(",", 1)
    last_tokens = last_block.strip().split()
    given_tokens = first_block.strip().split()
    if not given_tokens or not last_tokens:
        return [raw_name]

    surname_substrings = []
    n = len(last_tokens)
    for i in range(n):
        for j in range(i + 1, n + 1):
            surname_substrings.append(" ".join(last_tokens[i:j]))

    candidates = []
    # try every given-name token (not just the first - covers mononym cases
    # like "Pereira De Albuquerque..., Antonio Joao" -> commonly "Joao Pereira")
    # combined with every nickname variant, against every surname substring
    for given_token in given_tokens:
        for given_variant in nickname_variants(given_token):
            for surname in surname_substrings:
                candidates.append(f"{given_variant} {surname}")
    candidates.append(f"{first_block.strip()} {last_block.strip()}")
    candidates.sort(key=len, reverse=True)
    return candidates


def match_against_lookup(raw_name: str, lookup: dict) -> str | None:
    """
    lookup: normalized_name -> anything. Tries every reconstruction of
    raw_name and returns the first normalized key that hits, or None.
    """
    for candidate in reconstruct_name_candidates(raw_name):
        key = normalize(candidate)
        if key in lookup:
            return key
    return None


def match_with_mononym_fallback(raw_name: str, lookup: dict, team_id: str, mononym_index: dict) -> str | None:
    """
    Tries the normal surname-based match first; if that fails, falls back
    to a club-scoped given-name-only lookup, for players some sources list
    by a single name (e.g. Arsenal's "Gabriel" for Gabriel Magalhaes).
    Club-scoping avoids false hits between unrelated players who share a
    first name at different clubs.
    """
    hit = match_against_lookup(raw_name, lookup)
    if hit:
        return hit
    if "," not in raw_name or not team_id:
        return None
    _, first_block = raw_name.split(",", 1)
    given_tokens = first_block.strip().split()
    for given_token in given_tokens:
        for variant in nickname_variants(given_token):
            idx_key = f"{team_id}|{normalize(variant)}"
            if idx_key in mononym_index:
                return mononym_index[idx_key]
    return None
