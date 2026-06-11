import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
        }
        
        # Determine if there's an 'event' in the message or extra
        if record.msg:
            if isinstance(record.msg, dict):
                log_record.update(record.msg)
            else:
                log_record["message"] = record.getMessage()

        # Add any extra arguments passed via extra=...
        _EXTRA_FIELDS = {
            "match_id", "score", "scorer", "event_key", "event",
            "error", "diff", "diff_hrs", "competition", "days_left",
            "retry_in", "status", "count", "threshold", "group_id",
            "active_matches", "failed_events", "in_flight", "pending_var",
            "uptime_hours", "attempts",
        }
        for field in _EXTRA_FIELDS:
            val = getattr(record, field, None)
            if val is not None:
                log_record[field] = val
        
        return json.dumps(log_record)

def setup_logger(name: str = "footballbot") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid adding multiple handlers if already set up
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        
    return logger

logger = setup_logger()
