import random
from datetime import datetime, timezone
from app.config import Config
from app.services.football_service import svc
from app.jobs.monitor_goals import monitor_goals
from app.utils.constants import ACTIVE_COMPETITION

class SchedulerState:
    CURRENT_POLL_MODE = "slow"

def _jitter(base_minutes: int, spread: int = 5) -> int:
    return base_minutes + random.randint(0, spread)

def run_smart_schedule(scheduler):
    from datetime import timedelta
    now_utc = datetime.now(timezone.utc)
    date_from = (now_utc - timedelta(days=1)).strftime("%Y-%m-%d")
    date_to = (now_utc + timedelta(days=1)).strftime("%Y-%m-%d")
    data = svc.fetch(
        f"competitions/{ACTIVE_COMPETITION}/matches?dateFrom={date_from}&dateTo={date_to}",
        ttl=1800,
    )

    if not isinstance(data, dict):
        return

    matches = data.get("matches", [])
    now = datetime.now(Config.TZ)
    in_window = False

    live_matches = []
    for m in matches:
        status = m.get("status", "")
        if status in ["IN_PLAY", "PAUSED"]:
            in_window = True
            live_matches.append(m)
        utc_str = m.get("utcDate", "")
        try:
            dt_utc = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
            dt_bkk = dt_utc.astimezone(Config.TZ)
            diff = abs((now - dt_bkk).total_seconds())
            if diff <= 7200:
                in_window = True
        except Exception:
            pass

    bkk_now = datetime.now(Config.TZ)
    # Aligned with DynamicCompetition cutoff in constants.py (wc_cutoff = 2026-07-20)
    wc_end_buffer = Config.TZ.localize(datetime(2026, 7, 20, 0, 0, 0))
    is_high_speed_allowed = bkk_now < wc_end_buffer

    if in_window:
        if is_high_speed_allowed:
            if SchedulerState.CURRENT_POLL_MODE != "high_speed":
                SchedulerState.CURRENT_POLL_MODE = "high_speed"
                # Safe High-speed polling: 45 seconds (1.33 requests/min), far below the 10 requests/min rate limit!
                scheduler.reschedule_job("goal_monitor", trigger="interval", seconds=45)
        else:
            if SchedulerState.CURRENT_POLL_MODE != "fast":
                SchedulerState.CURRENT_POLL_MODE = "fast"
                scheduler.reschedule_job("goal_monitor", trigger="interval", minutes=_jitter(3, 2))
        monitor_goals(live_matches=live_matches if live_matches else None)
    else:
        if SchedulerState.CURRENT_POLL_MODE != "slow":
            SchedulerState.CURRENT_POLL_MODE = "slow"
            scheduler.reschedule_job("goal_monitor", trigger="interval", minutes=_jitter(20, 10))
