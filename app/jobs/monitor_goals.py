from threading import Lock
from typing import Dict, Tuple
from app.config import Config
from app.services.football_service import svc
from app.services.line_service import broadcast
from app.repositories.supabase_client import update_match_score, get_sent_event, mark_sent_event
from app.utils.helpers import is_watched_match
from app.flex.flex_builders import build_goal_flex
from app.utils.constants import EPL_CODE

last_sent_scores: Dict[str, Tuple[int, int]] = {}
last_sent_lock = Lock()
monitor_lock = Lock()

def monitor_goals():
    if not monitor_lock.acquire(blocking=False):
        return
    try:
        data = svc.fetch(f"competitions/{EPL_CODE}/matches?status=LIVE", ttl=0)
        if not isinstance(data, dict):
            return

        matches = data.get("matches", [])
        if not matches:
            return

        for m in matches:
            home_name = m["homeTeam"]["name"]
            away_name = m["awayTeam"]["name"]
            if not is_watched_match(home_name, away_name):
                continue

            fid = str(m.get("id", ""))
            
            score = m.get("score", {})
            hs = score.get("fullTime", {}).get("home") or score.get("halfTime", {}).get("home") or 0
            as_ = score.get("fullTime", {}).get("away") or score.get("halfTime", {}).get("away") or 0
            
            try:
                hs = int(hs)
                as_ = int(as_)
            except (ValueError, TypeError):
                hs = as_ = 0

            h_logo = m["homeTeam"].get("crest", "")
            a_logo = m["awayTeam"].get("crest", "")

            goals = m.get("goals", [])
            scorer = ""
            minute_s = ""
            if goals:
                last_g = goals[-1]
                scorer = (last_g.get("scorer") or {}).get("name", "")
                minute_s = str(last_g.get("minute", ""))

            with last_sent_lock:
                if last_sent_scores.get(fid) == (hs, as_):
                    continue
                last_sent_scores[fid] = (hs, as_)

            event_key = f"{fid}-{hs}-{as_}"
            if get_sent_event(event_key):
                continue

            broadcast(build_goal_flex(home_name, away_name, hs, as_, h_logo, a_logo, scorer, minute_s))
            mark_sent_event(event_key)
            update_match_score(fid, hs, as_)
    finally:
        monitor_lock.release()
