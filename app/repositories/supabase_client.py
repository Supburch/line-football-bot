import time
from datetime import datetime, timedelta
from typing import List
from dataclasses import dataclass
from supabase import create_client
from app.config import Config
from app.utils.logger import logger

@dataclass
class CommitResult:
    success: bool
    event_saved: bool
    score_saved: bool

supabase = None
if Config.SUPABASE_URL and Config.SUPABASE_KEY:
    try:
        supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        logger.info({"event": "supabase_connected"})
    except Exception as e:
        logger.error({"event": "supabase_failed", "error": str(e)})
else:
    logger.warning({"event": "supabase_not_configured"})

def execute_with_retry(query, max_retries=2):
    if not supabase: return None
    for attempt in range(max_retries):
        try:
            return query.execute()
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error({"event": "supabase_query_failed", "error": str(e), "attempts": max_retries})
                return None
            time.sleep(1)

def db_register_group(gid: str):
    if not supabase or not gid: return
    execute_with_retry(supabase.table("football_groups").upsert({"group_id": gid, "active": True}))

def db_get_groups() -> List[str]:
    if not supabase: return []
    res = execute_with_retry(supabase.table("football_groups").select("group_id").eq("active", True))
    if res and res.data:
        return [r["group_id"] for r in res.data]
    return []

def get_sent_event(key: str) -> bool:
    if not supabase: return False
    res = execute_with_retry(supabase.table("sent_events").select("event_key").eq("event_key", key))
    return bool(res and res.data)

def mark_sent_event(key: str):
    if not supabase: return
    execute_with_retry(supabase.table("sent_events").upsert({"event_key": key}))

def commit_match_state(match_id: str, event_key: str, home_score: int, away_score: int) -> CommitResult:
    """Simulates an application-level transaction to commit the match state."""
    if not supabase: 
        return CommitResult(success=True, event_saved=False, score_saved=False)

    # 1. Mark event as sent
    event_res = execute_with_retry(supabase.table("sent_events").upsert({"event_key": event_key}))
    event_saved = getattr(event_res, "data", None) is not None
    
    if not event_saved:
        logger.error({"event": "split_brain_warning", "message": "Failed to save event_key", "event_key": event_key})
        return CommitResult(success=False, event_saved=False, score_saved=False)

    # 2. Update match score (atomic upsert to avoid update-miss-then-insert-fail pattern)
    payload = {
        "match_id": match_id,
        "home_score": home_score,
        "away_score": away_score,
        "updated_at": datetime.now(Config.TZ).isoformat(),
    }
    score_res = execute_with_retry(supabase.table("match_scores").upsert(payload))
    
    score_saved = getattr(score_res, "data", None) is not None
    if not score_saved:
        logger.error({"event": "split_brain_warning", "message": "Failed to save match score after saving event", "match_id": match_id})

    return CommitResult(success=score_saved, event_saved=event_saved, score_saved=score_saved)

def cleanup_sent_events_db():
    if not supabase: return
    cutoff = (datetime.now(Config.TZ) - timedelta(hours=24)).isoformat()
    execute_with_retry(
        supabase.table("sent_events")
        .delete()
        .lt("created_at", cutoff)
        .not_.like("event_key", "dome_fc_image_%")
    )

def get_match_score(match_id: str):
    """Retrieve the last committed score for a match from Supabase.
    Returns (home_score, away_score) tuple or None if not found."""
    if not supabase: return None
    try:
        res = execute_with_retry(
            supabase.table("match_scores").select("home_score,away_score").eq("match_id", match_id)
        )
        if res and res.data:
            row = res.data[0]
            return (int(row["home_score"]), int(row["away_score"]))
    except Exception as e:
        logger.error({"event": "get_match_score_failed", "match_id": match_id, "error": str(e)})
    return None
