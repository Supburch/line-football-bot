import time
import threading
from app.config import Config
from app.services.football_service import svc
from app.services.line_service import broadcast, BroadcastResult
from app.repositories.supabase_client import get_sent_event, commit_match_state, get_match_score, mark_sent_event
from app.utils.helpers import is_watched_match, first_not_none
from app.flex.flex_builders import build_goal_flex, build_var_flex, build_penalty_shootout_flex, build_red_card_flex
from app.utils.constants import EPL_CODE, WC_CODE, ACTIVE_COMPETITION, CLEANUP_MATCH_STATUSES, is_live_score_enabled
from app.utils.logger import logger
from app.services.match_state_manager import MatchStateManager

# Initialize the robust, thread-safe state manager
state_manager = MatchStateManager()

# Process-level lock to prevent concurrent execution from smart_schedule + goal_monitor
_monitor_lock = threading.Lock()

def detect_score_transition(fid: str, hs: int, as_: int):
    """Calculates if the score transition is a goal, var, and the goal difference."""
    prev_score = state_manager.get_score(fid)
    if not prev_score:
        return False, False, 0, (0, 0), False
        
    prev_hs, prev_as = prev_score
    prev_total = prev_hs + prev_as
    new_total = hs + as_
    
    is_goal = new_total > prev_total
    is_var = new_total < prev_total
    goal_diff = abs(new_total - prev_total)
    score_shifted = (hs != prev_hs) or (as_ != prev_as)
    
    return is_goal, is_var, goal_diff, prev_score, score_shifted

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
    # Prevent concurrent execution (smart_schedule + goal_monitor can overlap)
    if not _monitor_lock.acquire(blocking=False):
        logger.info("monitor_goals_skipped_concurrent")
        return
    try:
        _monitor_goals_inner(live_matches)
    finally:
        _monitor_lock.release()

def _monitor_goals_inner(live_matches: list = None):
    try:
        # Run TTL eviction cleanup and log health report on every poll
        state_manager.cleanup_expired_states()
        state_manager.log_health_report()

        # WC 26 Temporary Disable: ปิดการแจ้งสกอร์สดช่วง World Cup ชั่วคราว
        if not is_live_score_enabled():
            logger.info("live_score_disabled_wc", extra={"reason": "LIVE_SCORE_WC_DISABLED=True during WC 26"})
            return
        
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
            # BUT first check if there's a final score change to broadcast!
            if status in CLEANUP_MATCH_STATUSES:
                if is_watched_match(home_name, away_name, comp_code):
                    score = m.get("score", {})
                    reg = score.get("regularTime") or {}
                    ft  = score.get("fullTime") or {}
                    ht  = score.get("halfTime") or {}
                    final_hs = first_not_none(reg.get("home"), ft.get("home"), ht.get("home"), 0)
                    final_as = first_not_none(reg.get("away"), ft.get("away"), ht.get("away"), 0)
                    try:
                        final_hs = int(final_hs)
                        final_as = int(final_as)
                    except (ValueError, TypeError):
                        final_hs = final_as = 0
                    
                    prev_score = state_manager.get_score(fid)
                    if prev_score and (final_hs, final_as) != prev_score:
                        new_total = final_hs + final_as
                        old_total = prev_score[0] + prev_score[1]
                        if new_total > old_total:
                            event_key = f"{fid}-{final_hs}-{final_as}"
                            # GOAL notification disabled — only commit state silently.
                            if not get_sent_event(event_key):
                                logger.info("final_whistle_goal_silent", extra={"match_id": fid, "score": f"{final_hs}-{final_as}", "prev": f"{prev_score[0]}-{prev_score[1]}"})
                                commit_match_state(fid, event_key, final_hs, final_as)
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
            is_goal, is_var, goal_diff, prev_score, score_shifted = detect_score_transition(fid, hs, as_)
            
            if not is_goal and not is_var:
                if score_shifted:
                    # Score shifted sides without total changing (e.g., 1-0 to 0-1)
                    state_manager.commit_memory(fid, hs, as_)
                    logger.info("score_shifted_silently", extra={"match_id": fid, "score": f"{hs}-{as_}"})
                # Clear pending var if score bounced back to normal
                state_manager.check_pending_var(fid, (hs, as_))
                continue
                
            # Handle VAR
            if is_var:
                if should_ignore_rollback(goal_diff, status, fid):
                    # Ignore entirely! Do NOT commit memory. If the API glitched to 0-0, 
                    # we want to keep the old valid memory so it doesn't trigger a ghost goal later.
                    logger.warning("suspicious_rollback_memory_retained", extra={"match_id": fid, "kept_score": f"{prev_score[0]}-{prev_score[1]}", "ignored_score": f"{hs}-{as_}"})
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
                # GOAL notification is disabled — only track score silently for VAR detection.
                # Record scorer for VAR reference, then skip broadcasting.
                goals = m.get("goals", [])
                scorer = ""
                minute_s = ""
                if goals:
                    last_g = goals[-1]
                    scorer = (last_g.get("scorer") or {}).get("name", "")
                    minute_s = str(last_g.get("minute", "")).rstrip("'")
                logger.info("goal_tracked_silent", extra={"match_id": fid, "score": f"{hs}-{as_}", "scorer": scorer, "event_key": event_key, "competition": comp_code})
                # Commit memory so future VAR detection works, then continue to next match.
                state_manager.commit_memory(fid, hs, as_, scorer)
                commit_match_state(fid, event_key, hs, as_)
                state_manager.clear_in_flight(event_key)
                # Also check red cards before moving on
                _process_red_cards_for_match(m, fid, home_name, away_name, hs, as_, h_logo, a_logo, comp_code)
                continue

            # Only reach here for VAR broadcasts
            result = broadcast(flex_msg)

            # ALWAYS commit memory after successful broadcast to prevent duplicates.
            # The message was already sent — memory MUST reflect that, regardless of DB result.
            if result in {BroadcastResult.SUCCESS, BroadcastResult.PARTIAL}:
                state_manager.commit_memory(fid, hs, as_, scorer if is_goal else "")
                state_manager.clear_in_flight(event_key)
                
                # Attempt DB commit (best-effort, won't cause duplicate if it fails)
                commit_res = commit_match_state(fid, event_key, hs, as_)
                if commit_res.success:
                    state_manager.clear_event_failure(event_key)
                    logger.info("state_committed", extra={"match_id": fid, "event_key": event_key})
                else:
                    logger.warning("db_commit_failed_after_broadcast", extra={"match_id": fid, "event_key": event_key})
                    
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

            # Check red cards for VAR matches too
            _process_red_cards_for_match(m, fid, home_name, away_name, hs, as_, h_logo, a_logo, comp_code)

    except Exception as e:
        logger.error("monitor_goals_exception", extra={"error": str(e)})


def _process_red_cards_for_match(m: dict, fid: str, home_name: str, away_name: str,
                                  hs: int, as_: int, h_logo: str, a_logo: str, comp_code: str):
    """Detect and broadcast red card events (RED_CARD / YELLOW_RED_CARD) for a watched match."""
    try:
        bookings = m.get("bookings", [])
        if not bookings:
            return

        for booking in bookings:
            card_type = booking.get("type", "")
            if card_type not in {"RED_CARD", "YELLOW_RED_CARD"}:
                continue

            player_info = booking.get("player") or {}
            player_name = player_info.get("name", "")
            team_info = booking.get("team") or {}
            team_name = team_info.get("name", "")
            minute_val = booking.get("minute", "")

            # Build a unique event key for this red card
            safe_player = (player_name or "unknown").replace(" ", "_")
            rc_event_key = f"{fid}-{card_type}-{safe_player}-{minute_val}"

            if get_sent_event(rc_event_key):
                continue  # Already notified

            flex_msg = build_red_card_flex(
                home_name, away_name, hs, as_, h_logo, a_logo,
                player=player_name, team=team_name, minute=minute_val,
                card_type=card_type, comp_code=comp_code
            )
            logger.info("red_card_detected", extra={"match_id": fid, "player": player_name,
                                                     "team": team_name, "minute": minute_val,
                                                     "type": card_type, "event_key": rc_event_key})
            result = broadcast(flex_msg)
            if result in {BroadcastResult.SUCCESS, BroadcastResult.PARTIAL}:
                mark_sent_event(rc_event_key)
                logger.info("red_card_notified", extra={"event_key": rc_event_key})
            else:
                logger.warning("red_card_broadcast_failed", extra={"event_key": rc_event_key, "result": str(result)})
    except Exception as e:
        logger.error("red_card_detection_exception", extra={"match_id": fid, "error": str(e)})


def log_state_manager_health():
    """Forces state manager health logging at fixed interval."""
    state_manager.log_health_report(force=True)
