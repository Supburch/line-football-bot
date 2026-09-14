# -*- coding: utf-8 -*-
"""Team catalog for the "โปรแกรม <ทีม>" (fixtures-by-team) command.

Covers the 4 favorite teams the bot watches (``WATCHED_TEAMS``): Tottenham,
Arsenal, Liverpool and Newcastle. Each canonical team key maps to:
  - ``name_th``: Thai display name shown in the Flex header / messages
  - ``match`` : a lowercase substring guaranteed to appear in the
                football-data.org team name (e.g. "Newcastle United FC"),
                used to filter the API fixture list
  - ``aliases``: every way a user might type the team (Thai, English,
                nickname), matched case-insensitively

Adding a favorite team is as simple as adding one entry below — the rest of
the command pipeline (``command_handler`` / ``flex_builders``) picks it up
automatically.
"""
from typing import Dict, Optional, Union

TEAM_ALIASES: Dict[str, Dict[str, Union[str, list]]] = {
    "arsenal": {
        "name_th": "อาร์เซน่อล",
        "match": "arsenal",
        "aliases": ["อาร์เซน่อล", "อาร์เซนอล", "arsenal", "ปืน", "ปืนใหญ่"],
    },
    "liverpool": {
        "name_th": "ลิเวอร์พูล",
        "match": "liverpool",
        "aliases": ["ลิเวอร์พูล", "ลิเวอพูล", "liverpool", "หงส์", "หงส์แดง"],
    },
    "newcastle": {
        "name_th": "นิวคาสเซิล",
        "match": "newcastle",
        "aliases": ["นิวคาสเซิล", "นิวฯ", "นิว", "newcastle", "newcastle united", "สาลิกา", "สาลิกาดง"],
    },
    "tottenham": {
        "name_th": "สเปอร์ส",
        "match": "tottenham",
        "aliases": [
            "สเปอร์ส",
            "สเปอร์",
            "spurs",
            "tottenham",
            "tottenham hotspur",
            "ไก่",
            "ไก่เดือยทอง",
        ],
    },
}


def resolve_team(text: str) -> Optional[str]:
    """Resolve a command string to a canonical team key, or ``None``.

    Uses the longest matching alias so that, e.g. "หงส์แดง" is preferred over a
    shorter overlapping alias ("หงส์"), and English names match case-insensitively.
    """
    text_lower = text.strip().lower()
    best_key = None
    best_len = 0
    for key, info in TEAM_ALIASES.items():
        for alias in info["aliases"]:
            if alias in text_lower and len(alias) > best_len:
                best_key = key
                best_len = len(alias)
    return best_key


def get_team_name(key: str) -> str:
    """Return the Thai display name for a team key, falling back to the key."""
    info = TEAM_ALIASES.get(key)
    if info:
        return info["name_th"]
    return key.capitalize() if key else ""
