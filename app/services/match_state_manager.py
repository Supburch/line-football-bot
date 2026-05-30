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
        
        # event_key -> {"retry_count": 0, "next_retry_at": timestamp}
        self._failed_events: Dict[str, Dict] = {}
        
        # In-flight set: event_keys currently being broadcast (duplicate guard across restarts)
        self._in_flight: set = set()

    def get_score(self, fid: str) -> Optional[Tuple[int, int]]:
        with self._lock:
            return self._last_sent_scores.get(fid)

    def commit_memory(self, fid: str, hs: int, as_: int, scorer: str = "", minute: str = ""):
        with self._lock:
            self._last_sent_scores[fid] = (hs, as_)
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

    def register_event_failure(self, event_key: str, is_fatal: bool = False):
        """Registers a failure and calculates exponential backoff."""
        with self._lock:
            if is_fatal:
                # Never retry
                self._failed_events[event_key] = {"retry_count": 999, "next_retry_at": 2e10}
                return

            if event_key not in self._failed_events:
                self._failed_events[event_key] = {"retry_count": 0, "next_retry_at": 0}
                
            state = self._failed_events[event_key]
            state["retry_count"] += 1
            
            # Exponential backoff: 1m, 2m, 4m, 8m... max 30m
            delay = min(60 * (2 ** (state["retry_count"] - 1)), 1800)
            state["next_retry_at"] = time.time() + delay
            logger.info({"event": "event_backoff", "event_key": event_key, "retry_in": delay})

    def clear_event_failure(self, event_key: str):
        with self._lock:
            if event_key in self._failed_events:
                del self._failed_events[event_key]

    def cleanup_match(self, fid: str):
        """Cleans up memory state when a match finishes to prevent leaks."""
        with self._lock:
            if fid in self._last_sent_scores: del self._last_sent_scores[fid]
            if fid in self._last_goal_info: del self._last_goal_info[fid]
            if fid in self._pending_var: del self._pending_var[fid]
            logger.info({"event": "match_state_cleaned", "match_id": fid})
