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

def normalize_team_name(name: str) -> str:
    n = str(name).strip().lower()
    # Strip common suffixes and descriptors to match names safely
    n = n.replace(" fc", "").replace(" afc", "").replace(" united", "").replace(" club", "")
    return n.strip()

def is_exact_team_match(name: str, targets: list[str]) -> bool:
    normalized_name = normalize_team_name(name)
    return any(
        normalized_name == normalize_team_name(target)
        for target in targets
    )

def is_watched_match(home: str, away: str, comp_code: Optional[str] = None) -> bool:
    target_list = WATCHED_COUNTRIES if comp_code == WC_CODE else WATCHED_TEAMS
    return is_exact_team_match(home, target_list) or is_exact_team_match(away, target_list)

def format_minute(minute: object) -> str:
    if minute is None:
        return ""
    minute_str = str(minute).strip()
    if not minute_str:
        return ""
    if minute_str.endswith("'"):
        return minute_str
    return f"{minute_str}'"

from typing import Any

def first_not_none(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None
