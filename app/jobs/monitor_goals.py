import time
from app.config import Config
from app.services.football_service import svc
from app.services.line_service import broadcast, BroadcastResult
from app.repositories.supabase_client import get_sent_event, commit_match_state
from app.utils.helpers import is_watched_match
from app.flex.flex_builders import build_goal_flex, build_var_flex
from app.utils.constants import EPL_CODE
from app.utils.logger import logger
from app.services.match_state_manager import MatchStateManager

# Initialize the robust, thread-safe state manager
state_manager = MatchStateManager()

def detect_score_transition(fid: str, hs: int, as_: int):
    """Calculates if the score transition is a goal, var, and the goal difference."""
    prev_score = state_manager.get_score(fid)
    if not prev_score:
        return False, False, 0, (0, 0)
        
    prev_hs, prev_as = prev_score
    prev_total = prev_hs + prev_as
    new_total = hs + as_
    
    is_goal = new_total > prev_total
    is_var = new_total < prev_total
    goal_diff = abs(new_total - prev_total)
    
    return is_goal, is_var, goal_diff, prev_score

def should_ignore_rollback(goal_diff: int, status: str, fid: str) -> bool:
    """Edge Case 1 & 2: Ignore rollback if diff > 1 or match is not active."""
    if goal_diff > 1:
        logger.warning({"event": "suspicious_rollback_ignored", "match_id": fid, "diff": goal_diff})
        return True
    if status not in {"IN_PLAY", "PAUSED"}:
        logger.warning({"event": "var_ignored_invalid_status", "match_id": fid, "status": status})
        return True
    return False

def monitor_goals(live_matches: list = None):
    try:
        if live_matches is not None:
            matches = live_matches
        else:
            data = svc.fetch(f"competitions/{EPL_CODE}/matches?status=LIVE", ttl=0)
            if not isinstance(data, dict):
                return
            matches = data.get("matches", [])
            
        if not matches:
            return

        for m in matches:
            home_name = m["homeTeam"]["name"]
            away_name = m["awayTeam"]["name"]
            status = m.get("status", "")
            fid = str(m.get("id", ""))
            
            # Edge Case 3: Memory Cleanup for finished matches
            if status in {"FINISHED", "POSTPONED", "CANCELLED"}:
                state_manager.cleanup_match(fid)
                continue
                
            if not is_watched_match(home_name, away_name):
                continue

            score = m.get("score", {})
            hs = score.get("fullTime", {}).get("home") or score.get("halfTime", {}).get("home") or 0
            as_ = score.get("fullTime", {}).get("away") or score.get("halfTime", {}).get("away") or 0
            
            try:
                hs = int(hs)
                as_ = int(as_)
            except (ValueError, TypeError):
                hs = as_ = 0

            # Only initialize state if we've never seen it, without triggering goal logic
            if state_manager.get_score(fid) is None:
                state_manager.commit_memory(fid, hs, as_)
                continue

            # Detect Transition
            is_goal, is_var, goal_diff, prev_score = detect_score_transition(fid, hs, as_)
            
            if not is_goal and not is_var:
                # Clear pending var if score bounced back to normal
                state_manager.check_pending_var(fid, (hs, as_))
                continue
                
            # Handle VAR
            if is_var:
                if should_ignore_rollback(goal_diff, status, fid):
                    state_manager.commit_memory(fid, hs, as_) # Force resync memory
                    continue
                    
                confirmed_prev = state_manager.check_pending_var(fid, (hs, as_))
                if not confirmed_prev:
                    # First time seeing this drop. Debounce it.
                    logger.info({"event": "var_debounce", "match_id": fid, "score": f"{hs}-{as_}"})
                    state_manager.set_pending_var(fid, prev_score, (hs, as_))
                    continue
                else:
                    # Second poll, score is still low. VAR Confirmed!
                    prev_hs, prev_as = confirmed_prev
                    event_key = f"{fid}-VAR-{prev_hs}-{prev_as}-TO-{hs}-{as_}"
            else:
                event_key = f"{fid}-{hs}-{as_}"

            # Check Backoff
            if not state_manager.can_retry_event(event_key):
                continue
                
            # Check Idempotency (Supabase)
            if get_sent_event(event_key):
                # We already sent this, just ensure memory is synced
                state_manager.commit_memory(fid, hs, as_)
                continue

            # Prepare Payload
            h_logo = m["homeTeam"].get("crest", "")
            a_logo = m["awayTeam"].get("crest", "")
            
            if is_var:
                scorer = state_manager.get_last_scorer(fid)
                flex_msg = build_var_flex(home_name, away_name, hs, as_, h_logo, a_logo, scorer)
                logger.info({"event": "var_detected", "match_id": fid, "event_key": event_key, "scorer_lost": scorer})
            else:
                goals = m.get("goals", [])
                scorer = ""
                minute_s = ""
                if goals:
                    last_g = goals[-1]
                    scorer = (last_g.get("scorer") or {}).get("name", "")
                    minute_s = str(last_g.get("minute", ""))
                flex_msg = build_goal_flex(home_name, away_name, hs, as_, h_logo, a_logo, scorer, minute_s)
                logger.info({"event": "goal_detected", "match_id": fid, "score": f"{hs}-{as_}", "scorer": scorer, "event_key": event_key})

            # BROADCAST FIRST
            result = broadcast(flex_msg)

            if result in {BroadcastResult.SUCCESS, BroadcastResult.PARTIAL}:
                # COMMIT MATCH STATE AFTER BROADCAST
                commit_res = commit_match_state(fid, event_key, hs, as_)
                
                if commit_res.success:
                    # Commit to memory only if DB commit succeeded (or if no DB)
                    state_manager.commit_memory(fid, hs, as_, scorer if is_goal else "")
                    state_manager.clear_event_failure(event_key)
                    logger.info({"event": "state_committed", "match_id": fid, "event_key": event_key})
                else:
                    # DB failed, retryable
                    state_manager.register_event_failure(event_key, is_fatal=False)
                    
            elif result == BroadcastResult.RETRYABLE_FAIL:
                logger.warning({"event": "broadcast_retryable_fail", "match_id": fid})
                state_manager.register_event_failure(event_key, is_fatal=False)
            else:
                logger.error({"event": "broadcast_fatal_fail", "match_id": fid})
                state_manager.register_event_failure(event_key, is_fatal=True)

    except Exception as e:
        logger.error({"event": "monitor_goals_exception", "error": str(e)})
