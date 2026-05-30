import re
from typing import Optional
from app.utils.constants import DEFAULT_LOGO, BOT_PREFIX, WATCHED_TEAMS, WATCHED_COUNTRIES, WC_CODE

def safe_url(url: Optional[str]) -> str:
    if not url or not isinstance(url, str):
        return DEFAULT_LOGO
    url = url.strip()
    if url.startswith("http://"):
        url = "https://" + url[len("http://"):]
    if not url.startswith("https://"):
        return DEFAULT_LOGO
    return url

def extract_command(text: str) -> str:
    return re.sub(rf"^\s*{re.escape(BOT_PREFIX)}\s*", "", text, count=1).strip()

def safe_group_id(source) -> str:
    for key in ["group_id", "room_id", "user_id"]:
        val = getattr(source, key, None)
        if val:
            return val
    return ""

def is_watched_match(home: str, away: str, comp_code: Optional[str] = None) -> bool:
    target_list = WATCHED_COUNTRIES if comp_code == WC_CODE else WATCHED_TEAMS
    return any(
        t.lower() in str(home).lower() or t.lower() in str(away).lower()
        for t in target_list
    )
