import threading
import time
from typing import Dict, Tuple, Optional
from app.utils.logger import logger

class MatchStateManager:
    """
    Encapsulates all memory state for match monitoring.
    Uses RLock to ensure thread-safety across different workers/threads.
    """
    def __init__(self):
        self._lock = threading.RLock()
        
        # fid -> (home_score, away_score)
        self._last_sent_scores: Dict[str, Tuple[int, int]] = {}
        
        # fid -> {"score": (1,0), "scorer": "Salah", "minute": "45"}
        self._last_goal_info: Dict[str, Dict] = {}
        
        # fid -> {"prev": (1,1), "new": (0,1), "ts": timestamp}
        self._pending_var: Dict[str, Dict] = {}
        
        # event_key -> {"retry_count": 0, "next_retry_at": timestamp, "created_at": timestamp}
        self._failed_events: Dict[str, Dict] = {}
        
        # In-flight set: event_keys currently being broadcast (duplicate guard across restarts)
        self._in_flight: set = set()

        # fid -> timestamp (to track match activity for TTL eviction)
        self._last_updated_at: Dict[str, float] = {}

    def get_score(self, fid: str) -> Optional[Tuple[int, int]]:
        with self._lock:
            score = self._last_sent_scores.get(fid)
            if score is not None:
                self._last_updated_at[fid] = time.time()
            return score

    def commit_memory(self, fid: str, hs: int, as_: int, scorer: str = "", minute: str = ""):
        with self._lock:
            self._last_sent_scores[fid] = (hs, as_)
            self._last_updated_at[fid] = time.time()
            if scorer:
                self._last_goal_info[fid] = {
                    "score": (hs, as_),
                    "scorer": scorer,
                    "minute": minute
                }
            # Once committed, clear any pending VAR for this match
            if fid in self._pending_var:
                del self._pending_var[fid]

    def set_pending_var(self, fid: str, prev_score: Tuple[int, int], new_score: Tuple[int, int]):
        with self._lock:
            self._last_updated_at[fid] = time.time()
            self._pending_var[fid] = {
                "prev": prev_score,
                "new": new_score,
                "created_at": time.time()
            }

    def check_pending_var(self, fid: str, current_score: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """
        Returns prev_score if VAR is confirmed (score remained low), otherwise None.
        Also cleans up expired TTLs.
        """
        with self._lock:
            if fid not in self._pending_var:
                return None
            
            pending = self._pending_var[fid]
            # TTL expiration (15 minutes)
            if time.time() - pending["created_at"] > 900:
                logger.warning({"event": "pending_var_expired", "match_id": fid})
                del self._pending_var[fid]
                return None
            
            if pending["new"] == current_score:
                # Confirmed! Score is still low.
                prev_score = pending["prev"]
                return prev_score
            else:
                # Score bounced back or changed, NOT a VAR.
                del self._pending_var[fid]
                return None

    def get_last_scorer(self, fid: str) -> str:
        with self._lock:
            info = self._last_goal_info.get(fid)
            return info.get("scorer", "") if info else ""

    def is_in_flight(self, event_key: str) -> bool:
        """Returns True if this event is currently being processed (duplicate guard)."""
        with self._lock:
            return event_key in self._in_flight

    def mark_in_flight(self, event_key: str):
        """Mark event as currently being processed."""
        with self._lock:
            self._in_flight.add(event_key)

    def clear_in_flight(self, event_key: str):
        """Clear in-flight marker after processing complete or failed."""
        with self._lock:
            self._in_flight.discard(event_key)

    def can_retry_event(self, event_key: str) -> bool:
        """Checks if we are allowed to retry this event based on backoff logic."""
        with self._lock:
            if event_key not in self._failed_events:
                return True
            return time.time() >= self._failed_events[event_key]["next_retry_at"]

    def register_event_failure(self, event_key: str, is_fatal: bool = False) -> bool:
        """
        Registers a failure and calculates exponential backoff.
        Returns True if the event has been finally abandoned (fatal or exceeded MAX_RETRIES = 3),
        meaning it should be deleted from failed_events and match memory should be force-resynced.
        """
        with self._lock:
            if is_fatal:
                self._failed_events.pop(event_key, None)
                return True

            if event_key not in self._failed_events:
                self._failed_events[event_key] = {"retry_count": 0, "next_retry_at": 0, "created_at": time.time()}
                
            state = self._failed_events[event_key]
            state["retry_count"] += 1
            
            if state["retry_count"] >= 3:  # MAX_RETRIES = 3
                self._failed_events.pop(event_key, None)
                logger.warning({"event": "event_abandoned_max_retries", "event_key": event_key})
                return True
            
            # Exponential backoff: 1m, 2m, 4m...
            delay = min(60 * (2 ** (state["retry_count"] - 1)), 1800)
            state["next_retry_at"] = time.time() + delay
            logger.info({"event": "event_backoff", "event_key": event_key, "retry_in": delay})
            return False

    def clear_event_failure(self, event_key: str):
        with self._lock:
            self._failed_events.pop(event_key, None)

    def cleanup_match(self, fid: str):
        """Cleans up memory state when a match finishes to prevent leaks."""
        with self._lock:
            self._last_sent_scores.pop(fid, None)
            self._last_goal_info.pop(fid, None)
            self._pending_var.pop(fid, None)
            self._last_updated_at.pop(fid, None)
            
            # Strict prefix boundary matching for failed events
            expired_events = [
                key
                for key in self._failed_events.keys()
                if key.startswith(f"{fid}-") or key.startswith(f"{fid}_")
            ]
            for event_key in expired_events:
                self._failed_events.pop(event_key, None)
                
            # Strict prefix boundary matching for in-flight markers
            expired_in_flight = [
                key
                for key in self._in_flight
                if key.startswith(f"{fid}-") or key.startswith(f"{fid}_")
            ]
            for event_key in expired_in_flight:
                self._in_flight.discard(event_key)
                
            logger.info({"event": "match_state_cleaned", "match_id": fid})

    def cleanup_expired_states(self, max_age_seconds: float = 43200):
        """
        Automatically purges any match memory or failed events older than max_age_seconds (default 12 hours).
        Protects the process against long-term memory leaks.
        """
        with self._lock:
            now = time.time()
            expired_fids = []
            
            # Find expired matches (no activity for 12 hours)
            for fid, last_active in list(self._last_updated_at.items()):
                if now - last_active > max_age_seconds:
                    expired_fids.append(fid)
                    
            # Purge expired matches
            for fid in expired_fids:
                self._last_sent_scores.pop(fid, None)
                self._last_goal_info.pop(fid, None)
                self._pending_var.pop(fid, None)
                self._last_updated_at.pop(fid, None)
                logger.info({"event": "match_state_evicted_ttl", "match_id": fid})
                
            # Purge old failed events (older than 12 hours)
            expired_events = []
            for event_key, data in list(self._failed_events.items()):
                created = data.get("created_at", now)
                if now - created > max_age_seconds:
                    expired_events.append(event_key)
                    
            for event_key in expired_events:
                self._failed_events.pop(event_key, None)
                logger.info({"event": "failed_event_evicted_ttl", "event_key": event_key})
