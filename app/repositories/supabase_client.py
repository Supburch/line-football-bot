import time
from datetime import datetime, timedelta
from typing import List
from supabase import create_client
from app.config import Config
from app.utils.logger import logger

supabase = None
if Config.SUPABASE_URL and Config.SUPABASE_KEY:
    try:
        supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        logger.info("✅ Supabase connected")
    except Exception as e:
        logger.error(f"❌ Supabase failed: {e}")
else:
    logger.warning("⚠️  Supabase not configured")

def execute_with_retry(query, max_retries=2):
    if not supabase: return None
    for attempt in range(max_retries):
        try:
            return query.execute()
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Supabase query failed after {max_retries} attempts: {e}")
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

def update_match_score(match_id: str, home_score: int, away_score: int):
    if not supabase or not match_id: return
    payload = {
        "match_id": match_id,
        "home_score": home_score,
        "away_score": away_score,
        "updated_at": datetime.now(Config.TZ).isoformat(),
    }
    res = execute_with_retry(supabase.table("match_scores").update(payload).eq("match_id", match_id))
    if not getattr(res, "data", None):
        execute_with_retry(supabase.table("match_scores").insert(payload))

def get_sent_event(key: str) -> bool:
    if not supabase: return False
    res = execute_with_retry(supabase.table("sent_events").select("event_key").eq("event_key", key))
    return bool(res and res.data)

def mark_sent_event(key: str):
    if not supabase: return
    execute_with_retry(supabase.table("sent_events").upsert({"event_key": key}))

def cleanup_sent_events_db():
    if not supabase: return
    cutoff = (datetime.now(Config.TZ) - timedelta(hours=24)).isoformat()
    execute_with_retry(supabase.table("sent_events").delete().lt("created_at", cutoff))
