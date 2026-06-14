import time
from app.config import Config
from app.services.football_service import svc
from app.services.line_service import broadcast, BroadcastResult
from app.repositories.supabase_client import get_sent_event, commit_match_state, get_match_score
from app.utils.helpers import is_watched_match, first_not_none
from app.flex.flex_builders import build_goal_flex, build_var_flex, build_penalty_shootout_flex
from app.utils.constants import EPL_CODE, WC_CODE, ACTIVE_COMPETITION, CLEANUP_MATCH_STATUSES
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
        logger.warning("suspicious_rollback_ignored", extra={"match_id": fid, "diff": goal_diff})
        return True
    if status not in {"IN_PLAY", "PAUSED"}:
        logger.warning("var_ignored_invalid_status", extra={"match_id": fid, "status": status})
        return True
    return False

def monitor_goals(live_matches: list = None):
    try:
        # Run TTL eviction cleanup and log health report on every poll
        state_manager.cleanup_expired_states()
        state_manager.log_health_report()
        
        if live_matches is not None:
            matches = live_matches
        else:
            # Smart Polling: Fetch only the ACTIVE_COMPETITION to save quota
            data = svc.fetch(f"matches?competitions={ACTIVE_COMPETITION}&status=LIVE", ttl=0)
            if not isinstance(data, dict):
                return
            matches = data.get("matches", [])
            
        if not matches:
            return

        for m in matches:
            comp_code = m.get("competition", {}).get("code", EPL_CODE)
            home_name = m["homeTeam"]["name"]
            away_name = m["awayTeam"]["name"]
            status = m.get("status", "")
            fid = str(m.get("id", ""))
            
            # --- NEW: 3.5 Hour Cutoff to prevent Ghost Goals from fluctuating API load balancers ---
            utc_str = m.get("utcDate", "")
            if utc_str:
                try:
                    from datetime import datetime, timezone
                    from app.config import Config
                    dt_utc = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
                    dt_bkk = dt_utc.astimezone(Config.TZ)
                    now_bkk = datetime.now(Config.TZ)
                    diff_seconds = abs((now_bkk - dt_bkk).total_seconds())
                    
                    # 12600 seconds = 3.5 hours. No match lasts longer than 3.5 hours.
                    if diff_seconds > 12600:
                        logger.warning("stale_match_ignored_by_time", extra={"match_id": fid, "diff_hrs": diff_seconds/3600})
                        state_manager.cleanup_match(fid)
                        continue
                except Exception:
                    pass
            # -----------------------------------------------------------------------------------------
            
            # Edge Case 3: Memory Cleanup for finished and irregular matches
            if status in CLEANUP_MATCH_STATUSES:
                state_manager.cleanup_match(fid)
                continue
                
            if not is_watched_match(home_name, away_name, comp_code):
                continue

            score = m.get("score", {})
            # Robust score extraction: regularTime (WC/knockout) > fullTime > halfTime > 0
            # regularTime is the most stable field during live World Cup matches
            reg = score.get("regularTime") or {}
            ft  = score.get("fullTime") or {}
            ht  = score.get("halfTime") or {}
            hs = first_not_none(reg.get("home"), ft.get("home"), ht.get("home"), 0)
            as_ = first_not_none(reg.get("away"), ft.get("away"), ht.get("away"), 0)
            
            try:
                hs = int(hs)
                as_ = int(as_)
            except (ValueError, TypeError):
                hs = as_ = 0

            # Smart Penalty Shootout Tracking
            duration = score.get("duration")
            penalties = score.get("penalties", {})
            pen_hs = penalties.get("home")
            pen_as = penalties.get("away")
            
            is_pso = (duration == "PENALTY_SHOOTOUT") or (pen_hs is not None and pen_as is not None)
            
            if is_pso:
                pen_hs = int(pen_hs) if pen_hs is not None else 0
                pen_as = int(pen_as) if pen_as is not None else 0
                pen_fid = f"{fid}_pen"
                
                # Check memory state for shootout
                if state_manager.get_score(pen_fid) is None:
                    event_key_pen = f"{pen_fid}-{pen_hs}-{pen_as}"
                    if get_sent_event(event_key_pen):
                        state_manager.commit_memory(pen_fid, pen_hs, pen_as)
                    else:
                        state_manager.commit_memory(pen_fid, 0, 0)
                        
                prev_pen = state_manager.get_score(pen_fid)
                if prev_pen is not None:
                    prev_pen_hs, prev_pen_as = prev_pen
                    if pen_hs > prev_pen_hs or pen_as > prev_pen_as:
                        # Shootout score changed!
                        event_key_pen = f"{pen_fid}-{pen_hs}-{pen_as}"
                        
                        if state_manager.can_retry_event(event_key_pen) and not get_sent_event(event_key_pen):
                            if pen_hs > prev_pen_hs:
                                scorer_text = f"🎯 {home_name} SCORED penalty! ({pen_hs} - {pen_as})"
                            else:
                                scorer_text = f"🎯 {away_name} SCORED penalty! ({pen_hs} - {pen_as})"
                                
                            flex_msg = build_penalty_shootout_flex(
                                home_name, away_name, hs, as_, pen_hs, pen_as,
                                h_logo=m["homeTeam"].get("crest", ""),
                                a_logo=m["awayTeam"].get("crest", ""),
                                scorer_text=scorer_text, comp_code=comp_code
                            )
                            
                            result = broadcast(flex_msg)
                            if result in {BroadcastResult.SUCCESS, BroadcastResult.PARTIAL}:
                                commit_res = commit_match_state(pen_fid, event_key_pen, pen_hs, pen_as)
                                if commit_res.success:
                                    state_manager.commit_memory(pen_fid, pen_hs, pen_as)
                                    state_manager.clear_event_failure(event_key_pen)
                                    logger.info("pso_score_committed", extra={"match_id": pen_fid, "event_key": event_key_pen})
                                else:
                                    abandoned = state_manager.register_event_failure(event_key_pen, is_fatal=False)
                                    if abandoned:
                                        state_manager.commit_memory(pen_fid, pen_hs, pen_as)
                            elif result == BroadcastResult.RETRYABLE_FAIL:
                                abandoned = state_manager.register_event_failure(event_key_pen, is_fatal=False)
                                if abandoned:
                                    state_manager.commit_memory(pen_fid, pen_hs, pen_as)
                            else:
                                abandoned = state_manager.register_event_failure(event_key_pen, is_fatal=True)
                                if abandoned:
                                    state_manager.commit_memory(pen_fid, pen_hs, pen_as)
                # Continue loop to skip regular score transition for this match
                continue

            # Only initialize state if we've never seen it in memory
            if state_manager.get_score(fid) is None:
                event_key = f"{fid}-{hs}-{as_}"
                if get_sent_event(event_key):
                    # We already sent this score before we crashed/slept. Load it.
                    state_manager.commit_memory(fid, hs, as_)
                    continue
                else:
                    # RECOVERY CHECK: Query Supabase for the last committed score for this match.
                    # If the DB score matches current API score, it means we already handled this
                    # state before a restart — just load it silently without broadcasting.
                    db_score = get_match_score(fid)
                    if db_score and db_score == (hs, as_):
                        state_manager.commit_memory(fid, hs, as_)
                        logger.info("recovery_from_db_score", extra={"match_id": fid, "score": f"{hs}-{as_}"})
                        continue
                    
                    # SAFE INIT: Always initialize to CURRENT score.
                    # This means we only detect FUTURE goals, never re-fire on restart.
                    # We may miss a goal that happened exactly during a restart window,
                    # but this is infinitely better than sending 5+ duplicate broadcasts.
                    state_manager.commit_memory(fid, hs, as_)
                    logger.info("safe_init_current_score", extra={"match_id": fid, "score": f"{hs}-{as_}"})
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
                    logger.info("var_debounce", extra={"match_id": fid, "score": f"{hs}-{as_}"})
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
            
            # In-flight duplicate guard (prevents double-send during deploy restart)
            if state_manager.is_in_flight(event_key):
                continue
            state_manager.mark_in_flight(event_key)

            # Prepare Payload
            h_logo = m["homeTeam"].get("crest", "")
            a_logo = m["awayTeam"].get("crest", "")
            
            if is_var:
                scorer = state_manager.get_last_scorer(fid)
                flex_msg = build_var_flex(home_name, away_name, hs, as_, h_logo, a_logo, scorer, comp_code=comp_code)
                logger.info("var_detected", extra={"match_id": fid, "event_key": event_key, "scorer_lost": scorer, "competition": comp_code})
            else:
                goals = m.get("goals", [])
                scorer = ""
                minute_s = ""
                if goals:
                    last_g = goals[-1]
                    scorer = (last_g.get("scorer") or {}).get("name", "")
                    minute_s = str(last_g.get("minute", ""))
                    # Strip trailing apostrophe from minute (e.g. "45'" -> "45")
                    minute_s = minute_s.rstrip("'")
                flex_msg = build_goal_flex(home_name, away_name, hs, as_, h_logo, a_logo, scorer, minute_s, comp_code=comp_code)
                logger.info("goal_detected", extra={"match_id": fid, "score": f"{hs}-{as_}", "scorer": scorer, "event_key": event_key, "competition": comp_code})

            # BROADCAST FIRST
            result = broadcast(flex_msg)

            if result in {BroadcastResult.SUCCESS, BroadcastResult.PARTIAL}:
                # COMMIT MATCH STATE AFTER BROADCAST
                commit_res = commit_match_state(fid, event_key, hs, as_)
                
                if commit_res.success:
                    # Commit to memory only if DB commit succeeded (or if no DB)
                    state_manager.commit_memory(fid, hs, as_, scorer if is_goal else "")
                    state_manager.clear_event_failure(event_key)
                    state_manager.clear_in_flight(event_key)
                    logger.info("state_committed", extra={"match_id": fid, "event_key": event_key})
                else:
                    # DB failed, retryable
                    state_manager.clear_in_flight(event_key)
                    abandoned = state_manager.register_event_failure(event_key, is_fatal=False)
                    if abandoned:
                        state_manager.commit_memory(fid, hs, as_)
                    
            elif result == BroadcastResult.RETRYABLE_FAIL:
                logger.warning("broadcast_retryable_fail", extra={"match_id": fid})
                state_manager.clear_in_flight(event_key)
                abandoned = state_manager.register_event_failure(event_key, is_fatal=False)
                if abandoned:
                    state_manager.commit_memory(fid, hs, as_)
            else:
                logger.error("broadcast_fatal_fail", extra={"match_id": fid})
                state_manager.clear_in_flight(event_key)
                abandoned = state_manager.register_event_failure(event_key, is_fatal=True)
                if abandoned:
                    state_manager.commit_memory(fid, hs, as_)

    except Exception as e:
        logger.error("monitor_goals_exception", extra={"error": str(e)})

def log_state_manager_health():
    """Forces state manager health logging at fixed interval."""
    state_manager.log_health_report(force=True)
