from datetime import datetime, timedelta, timezone
from app.config import Config
from app.utils.logger import logger
from app.services.football_service import svc
from app.services.line_service import broadcast
from app.repositories.supabase_client import get_sent_event, mark_sent_event
from app.utils.helpers import is_watched_match
from app.utils.constants import WATCHED_TEAMS, ACTIVE_COMPETITION

def check_weekly_summary():
    now = datetime.now(timezone.utc)
    monday = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
    sunday = (now - timedelta(days=now.weekday()) + timedelta(days=6)).strftime("%Y-%m-%d")

    data = svc.fetch(
        f"competitions/{ACTIVE_COMPETITION}/matches?dateFrom={monday}&dateTo={sunday}",
        ttl=300,
    )
    if not isinstance(data, dict):
        return

    matches = data.get("matches", [])
    watched = [m for m in matches if is_watched_match(
        m["homeTeam"]["name"], m["awayTeam"]["name"]
    )]

    if not watched:
        return

    finished_statuses = {"FINISHED"}
    if not all(m.get("status") in finished_statuses for m in watched):
        return

    summary_key = f"weekly-summary-{monday}"
    if get_sent_event(summary_key):
        return

    matchday = watched[0].get("matchday", "?")
    lines = [
        "📋 สรุปผลประจำสัปดาห์",
        f"(Matchday {matchday})",
        "─" * 25,
    ]

    for m in watched:
        home = m["homeTeam"]["name"]
        away = m["awayTeam"]["name"]
        hs = m.get("score", {}).get("fullTime", {}).get("home", 0) or 0
        as_ = m.get("score", {}).get("fullTime", {}).get("away", 0) or 0

        home_w = any(t.lower() in home.lower() for t in WATCHED_TEAMS)
        away_w = any(t.lower() in away.lower() for t in WATCHED_TEAMS)

        if home_w and away_w:
            lines.append(f"⚽ {home} {hs} - {as_} {away}")
        elif home_w:
            emoji = "✅" if hs > as_ else ("❌" if hs < as_ else "🔺")
            lines.append(f"{emoji} {home} {hs} - {as_} {away}")
        elif away_w:
            emoji = "✅" if as_ > hs else ("❌" if as_ < hs else "🔺")
            lines.append(f"{emoji} {home} {hs} - {as_} {away}")

    lines.append("─" * 25)
    broadcast("\n".join(lines))
    mark_sent_event(summary_key)
    logger.info(f"✅ Weekly summary sent for {monday}")
